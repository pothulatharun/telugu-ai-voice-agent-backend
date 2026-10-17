import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()


def get_supabase_settings():
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_KEY", "")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be configured."
        )

    return url, key


def get_headers():
    _, key = get_supabase_settings()

    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def get_business_config(business_id: str):
    url, _ = get_supabase_settings()

    response = requests.get(
        f"{url}/rest/v1/businesses",
        headers=get_headers(),
        params={
            "business_id": f"eq.{business_id}",
            "select": "business_id,business_name,google_form_url",
            "limit": "1",
        },
        timeout=20,
    )
    response.raise_for_status()

    rows = response.json()
    return rows[0] if rows else None


def save_business_config(
    business_id: str,
    business_name: str,
    google_form_url: str,
):
    url, _ = get_supabase_settings()

    payload = {
        "business_id": business_id,
        "business_name": business_name,
        "google_form_url": google_form_url,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    response = requests.post(
        f"{url}/rest/v1/businesses",
        headers={
            **get_headers(),
            "Prefer": "resolution=merge-duplicates,return=representation",
        },
        params={"on_conflict": "business_id"},
        json=payload,
        timeout=20,
    )
    response.raise_for_status()

    rows = response.json()
    if not rows:
        return get_business_config(business_id)

    return rows[0]