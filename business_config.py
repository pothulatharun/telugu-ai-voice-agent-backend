businesses = {
    "demo_business": {
        "business_name": "Demo Business",
        "google_form_url": "https://forms.gle/REPLACE_WITH_FORM_LINK",
    }
}


def get_business_config(business_id: str):
    return businesses.get(business_id)


def save_business_config(
    business_id: str,
    business_name: str,
    google_form_url: str,
):
    businesses[business_id] = {
        "business_name": business_name,
        "google_form_url": google_form_url,
    }

    return businesses[business_id]