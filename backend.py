from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timezone
from business_config import get_business_config, save_business_config
from pydantic import HttpUrl
app = FastAPI(title="AI Lead Calling Backend")


class LeadInterest(BaseModel):
    business_name: str = "Default Business"
    customer_name: str = "Unknown"
    phone_number: str
    interested: bool
    whatsapp_consent: bool = False


@app.get("/")
def home():
    return {"status": "running", "service": "AI Lead Calling Backend"}


@app.post("/lead-interest")
def mark_lead_interest(lead: LeadInterest):
    print("Received lead data:", lead.model_dump())
    print("WhatsApp consent:", lead.whatsapp_consent)
    return {
        "success": True,
        "message": "Lead interest recorded",
        "business_name": lead.business_name,
        "customer_name": lead.customer_name,
        "phone_number": lead.phone_number,
        "interested": lead.interested,
        "whatsapp_consent": lead.whatsapp_consent,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
class BusinessConfigRequest(BaseModel):
    business_id: str
    business_name: str
    google_form_url: HttpUrl


@app.post("/business-config")
def update_business_config(config: BusinessConfigRequest):
    saved = save_business_config(
        business_id=config.business_id,
        business_name=config.business_name,
        google_form_url=str(config.google_form_url),
    )

    return {
        "success": True,
        "business": saved,
    }