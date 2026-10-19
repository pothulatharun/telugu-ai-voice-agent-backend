import os
import base64
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()

api_key = os.getenv("SARVAM_API_SUBSCRIPTION_KEY")

if not api_key:
    raise ValueError("API key not found. Check your .env file.")

client = SarvamAI(api_subscription_key=api_key)
text = (
    "నమస్కారం అండి! ఎలా ఉన్నారు? "
    "చెప్పండి, మీకు ఏం సహాయం కావాలి? "
    "నేను మీకు సహాయం చేస్తాను."
)

print("Generating Telugu voice...")

response = client.text_to_speech.convert(
    model="bulbul:v4-flash",
    text=text,
    language_code="te-IN",
    speaker="kavitha_te_narration",
    pace=1.4,
    temperature=0.85,
    output_audio_codec="wav",
)

audio_bytes = base64.b64decode(response.audios[0])

with open("telugu_voice.wav", "wb") as audio_file:
    audio_file.write(audio_bytes)

print("Done! Audio saved as telugu_voice.wav")