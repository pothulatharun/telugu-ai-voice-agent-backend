import os
import io
import csv
import importlib.metadata
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from business_config import (
    get_business_config,
    save_business_config,
    get_supabase_settings,
    get_headers,
)
from exotel_bridge import router as exotel_router

# Load environment variables first.
load_dotenv()

# WhatsApp stays disabled unless explicitly turned off in the environment.
WHATSAPP_TEST_MODE = (
    os.getenv("WHATSAPP_TEST_MODE", "true").strip().lower() == "true"
)

app = FastAPI(title="AI Lead Calling Backend")


@app.get("/")
def home():
    return {
        "status": "running",
        "service": "AI Lead Calling Backend",
    }


@app.get("/diagnostics/sarvam")
def check_sarvam_installation():
    try:
        version = importlib.metadata.version("sarvamai")
        return {
            "installed": True,
            "version": version,
        }
    except importlib.metadata.PackageNotFoundError:
        return {
            "installed": False,
            "message": "Sarvam SDK is not installed",
        }


app.include_router(exotel_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://pothulatharun.github.io",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


def send_whatsapp_form(
    phone_number: str,
    customer_name: str,
    form_url: str,
):
    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

    if not token or not phone_number_id:
        raise RuntimeError(
            "WhatsApp environment variables are missing."
        )

    url = (
        f"https://graph.facebook.com/v23.0/"
        f"{phone_number_id}/messages"
    )

    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {
            "body": (
                f"Hi {customer_name}, thank you for your interest! "
                f"Please fill out this form: {form_url}"
            )
        },
    }

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    response.raise_for_status()
    return response.json()


class LeadInterest(BaseModel):
    business_id: str = "demo_business"
    business_name: str = "Default Business"
    customer_name: str = "Unknown"
    phone_number: str
    interested: bool
    whatsapp_consent: bool = False


class BusinessConfigRequest(BaseModel):
    business_id: str
    business_name: str
    google_form_url: HttpUrl


@app.post("/lead-interest")
def mark_lead_interest(lead: LeadInterest):
    print("Received lead data:", lead.model_dump())
    print("WhatsApp consent:", lead.whatsapp_consent)

    business = get_business_config(lead.business_id)

    if not business:
        return {
            "success": False,
            "message": "Business configuration not found",
        }

    result = {
        "success": True,
        "message": "Lead interest recorded",
        "business_name": business["business_name"],
        "customer_name": lead.customer_name,
        "phone_number": lead.phone_number,
        "interested": lead.interested,
        "whatsapp_consent": lead.whatsapp_consent,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "whatsapp_sent": False,
    }

    # Both interest and explicit consent are required.
    if not lead.interested or not lead.whatsapp_consent:
        result["message"] = (
            "Lead recorded; WhatsApp not sent because interest "
            "or consent is missing."
        )
        return result

    # Do not send WhatsApp during testing.
    if WHATSAPP_TEST_MODE:
        result["message"] = (
            "Lead recorded in test mode; WhatsApp sending is disabled."
        )
        return result

    form_url = business["google_form_url"]

    try:
        whatsapp_response = send_whatsapp_form(
            phone_number=lead.phone_number,
            customer_name=lead.customer_name,
            form_url=form_url,
        )

        result["whatsapp_sent"] = True
        result["whatsapp_message_id"] = (
            whatsapp_response.get("messages", [{}])[0].get("id")
        )
        result["message"] = (
            "Lead recorded and WhatsApp message accepted by API."
        )

    except Exception as exc:
        print("WhatsApp sending failed:", str(exc))
        result["success"] = False
        result["message"] = (
            "Lead recorded, but WhatsApp sending failed."
        )

    return result


@app.post("/business-config")
def update_business_config(config: BusinessConfigRequest):
    saved = save_business_config(
        business_id=config.business_id,
        business_name=config.business_name,
        google_form_url=str(config.google_form_url),
    )

    return {
        "success": True,
        "message": "Business configuration saved",
        "business": saved,
    }


@app.get("/business-config/{business_id}")
def read_business_config(business_id: str):
    config = get_business_config(business_id)

    if config is None:
        raise HTTPException(
            status_code=404,
            detail="Business settings not found",
        )

    return config


@app.post("/upload-leads/{business_id}")
async def upload_leads(
    business_id: str,
    file: UploadFile = File(...),
):
    config = get_business_config(business_id)

    if config is None:
        raise HTTPException(
            status_code=404,
            detail="Business settings not found",
        )

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file",
        )

    try:
        content = await file.read(2 * 1024 * 1024 + 1)

        if len(content) > 2 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="CSV must be 2 MB or smaller",
            )

        reader = csv.DictReader(
            io.StringIO(content.decode("utf-8-sig"))
        )

        if not reader.fieldnames:
            raise HTTPException(
                status_code=400,
                detail="CSV needs a header row",
            )

        headers = {
            header.strip().lower()
            for header in reader.fieldnames
            if header
        }

        if not {"customer_name", "phone_number"}.issubset(headers):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Headers must include customer_name and phone_number"
                ),
            )

        rows = []

        for row in reader:
            values = {
                (key or "").strip().lower(): (value or "").strip()
                for key, value in row.items()
            }

            name = values.get("customer_name", "")
            phone = values.get("phone_number", "")

            if name and phone:
                rows.append({
                    "business_id": business_id,
                    "customer_name": name,
                    "phone_number": phone,
                    "interested": False,
                    "whatsapp_consent": False,
                })

        if not rows:
            raise HTTPException(
                status_code=400,
                detail="No valid leads found",
            )

        url, _ = get_supabase_settings()

        response = requests.post(
            f"{url}/rest/v1/leads",
            headers={
                **get_headers(),
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            json=rows,
            timeout=30,
        )
        response.raise_for_status()

        return {
            "message": "Leads uploaded successfully",
            "business_id": business_id,
            "uploaded_count": len(rows),
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="CSV must use UTF-8 encoding",
        )
    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Could not save leads",
        )
    finally:
        await file.close()