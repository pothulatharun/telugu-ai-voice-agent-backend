import os
import base64
import csv
import winsound
import sounddevice as sd
import scipy.io.wavfile as wav
import requests

from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()

api_key = os.getenv("SARVAM_API_SUBSCRIPTION_KEY")

if not api_key:
    raise ValueError("API key not found. Check your .env file.")

client = SarvamAI(api_subscription_key=api_key)

SAMPLE_RATE = 16000
DURATION = 6
LEADS_CSV = "leads.csv"


def load_leads():
    """Load customer names and phone numbers from the CSV file."""
    leads = []

    with open(LEADS_CSV, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("The CSV file is empty or missing headers.")

        # Match column names even if capitalization or spaces differ.
        columns = {
            name.strip().lower(): name
            for name in reader.fieldnames
            if name
        }

        name_column = columns.get("customer name")
        phone_column = columns.get("phone number")

        if not name_column or not phone_column:
            raise ValueError(
                "CSV must contain 'Customer name' and 'Phone number' columns."
            )

        for row in reader:
            name = (row.get(name_column) or "").strip()
            phone = (row.get(phone_column) or "").strip()

            if name and phone:
                leads.append({
                    "customer_name": name,
                    "phone_number": phone,
                })

    return leads
BACKEND_URL = "https://telugu-ai-voice-agent-backend.onrender.com"
BUSINESS_ID = os.getenv("VAANI_BUSINESS_ID", "demo_business")


def get_business_config(business_id):
    """Retrieve this business's settings from the live backend."""
    url = f"{BACKEND_URL}/business-config/{business_id}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        business = response.json()

        required_fields = [
            "business_id",
            "business_name",
            "google_form_url",
        ]
        if not all(field in business for field in required_fields):
            raise RuntimeError(
                "Business configuration is missing required fields."
            )

        print("\nBusiness:", business["business_name"])
        print("Business ID:", business["business_id"])

        return business

    except requests.RequestException as error:
        print("\nCould not retrieve business configuration.")
        print("Check the backend connection and business ID.")
        raise RuntimeError(
            "Business configuration unavailable."
        ) from error
def submit_lead_result(
    customer_name,
    phone_number,
    interested,
    whatsapp_consent,
    business_id="demo_business",
):
    url = f"{BACKEND_URL}/lead-interest"

    payload = {
        "business_id": business_id,
        "customer_name": customer_name,
        "phone_number": phone_number,
        "interested": interested,
        "whatsapp_consent": whatsapp_consent,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()
    print("\nBackend response:", result)
    return result

messages = [
    {
        "role": "system",
        "content": """
LANGUAGE AND PRONUNCIATION:
- Write Telugu words in Telugu script.
- Keep English technical terms in English.
- Mix Telugu and English naturally.
- Use punctuation to create natural pauses.
- Prefer simple, everyday Telugu expressions.
- Keep spoken answers concise and easy to understand.

NATURAL HUMAN CONVERSATION:
- Speak like a friendly Telugu-speaking person from Hyderabad.
- Be warm, relaxed, natural, and confident.
- Respond directly to what the person says.
- Use short sentences and natural contractions.
- Show appropriate empathy or excitement when relevant.
- Avoid repetitive acknowledgements and unnecessary introductions.
- Ask only one relevant follow-up question when needed.
- Never claim to be human.
- Never invent business details or claim to have performed an action
  that you did not perform.

Keep ordinary replies concise, usually one to three sentences.
Return only the words intended to be spoken.
"""
    }
]


def listen_to_user():
    input("\nPress Enter when you are ready to speak...")
    print("Listening... Speak now!")

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )
    sd.wait()

    wav.write("mic_input.wav", SAMPLE_RATE, audio)
    print("Recognizing your speech...")

    with open("mic_input.wav", "rb") as audio_file:
        result = client.speech_to_text.transcribe(
            file=audio_file,
            model="saaras:v4",
            language_code="te-IN",
        )

    text = result.transcript.strip()
    print("You:", text if text else "(No speech recognized)")
    return text


def generate_reply(user_text):
    messages.append({"role": "user", "content": user_text})

    response = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=messages,
        max_tokens=180,
        reasoning_effort=None,
    )

    answer = response.choices[0].message.content.strip()
    messages.append({"role": "assistant", "content": answer})

    print("\nAI:", answer)
    return answer


def speak_reply(answer):
    audio = client.text_to_speech.convert(
        text=answer,
        model="bulbul:v4-flash",
        speaker="kavitha_te_narration",
        language_code="te-IN",
        pace=1.5,
        output_audio_codec="wav",
    )

    audio_bytes = base64.b64decode(audio.audios[0])

    with open("agent_reply.wav", "wb") as audio_file:
        audio_file.write(audio_bytes)

    winsound.PlaySound(
        "agent_reply.wav",
        winsound.SND_FILENAME,
    )
def test_voice_lead_qualification(customer_name, phone_number):
    print(f"\nVaani AI: Are you interested in learning more, {customer_name}?")
    interest = input("Test customer's answer (yes/no): ").strip().lower()
    interested = interest in ("yes", "y")

    whatsapp_consent = False

    if interested:
        print(
            "Vaani AI: Would you like me to send the form link "
            "to your WhatsApp?"
        )
        consent = input(
            "Test customer's explicit WhatsApp consent (yes/no): "
        ).strip().lower()
        whatsapp_consent = consent in ("yes", "y")

    print("\n--- Simulation Result ---")
    print("Customer:", customer_name)
    print("Interested:", interested)
    print("Simulated WhatsApp consent:", whatsapp_consent)
    print("No backend submission or WhatsApp message was sent.")
    
def main():
    # Load business settings before starting the microphone.
    business = get_business_config(BUSINESS_ID)

    # Keep business details available for future lead-call integration.
    business_name = business["business_name"]
    google_form_url = business["google_form_url"]

    print("\nVaani AI voice assistant started!")
    print("Configured business:", business_name)
    print("Say 'exit' to stop the conversation.")

    # These variables are loaded successfully, but this version does not
    # yet qualify leads, initiate phone calls, or send WhatsApp messages.
    _ = google_form_url

    while True:
        try:
            user_text = listen_to_user()

            if not user_text:
                print("I couldn't recognize that. Let's try again.")
                continue

            if user_text.lower().strip() in ["exit", "quit", "stop"]:
                print("AI: Sare, malli matladudham. Bye!")
                break

            answer = generate_reply(user_text)
            speak_reply(answer)

        except KeyboardInterrupt:
            print("\nVoice agent stopped.")
            break

        except Exception as error:
            print("\nSomething went wrong:", error)
            print("Check your connection and try again.")

if __name__ == "__main__":
    print("Vaani AI")
    print("1. Start voice assistant")
    print("2. Test lead interest and consent")

    choice = input("Choose 1 or 2: ").strip()

    if choice == "1":
        main()

    elif choice == "2":
        leads = load_leads()

        if not leads:
            print("No valid leads found in leads.csv.")
        else:
            lead = leads[0]
            test_voice_lead_qualification(
                customer_name=lead["customer_name"],
                phone_number=lead["phone_number"],
            )

    else:
        print("Invalid choice. Run the program again.")