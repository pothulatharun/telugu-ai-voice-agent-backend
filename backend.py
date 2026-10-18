import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from datetime import datetime, timezone
from business_config import get_business_config, save_business_config

load_dotenv()

app = FastAPI(title="AI Lead Calling Backend")

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


@app.get("/")
def home():
    return {
        "status": "running",
        "service": "AI Lead Calling Backend",
    }


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

    # Never send WhatsApp unless both conditions are true.
    if not lead.interested or not lead.whatsapp_consent:
        result["message"] = (
            "Lead recorded; WhatsApp not sent because interest "
            "or consent is missing."
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
        # Log the error without returning credentials or API details
        # to the caller.
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
            detail="Business settings not found"
        )

    return config