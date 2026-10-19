import os
import base64
import winsound
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()

client = SarvamAI(
    api_subscription_key=os.getenv("SARVAM_API_SUBSCRIPTION_KEY")
)

# Replace these with valid Bulbul v4 Flash speaker IDs.
speakers = [
    "kavitha_te_narration",
   
]

sample_text = (
    "హాయ్! ఎలా ఉన్నావు? "
    "చెప్పు, నీకు నేను ఎలా help చేయగలను?"
)

for speaker in speakers:
    print(f"\nTesting speaker: {speaker}")

    try:
        audio = client.text_to_speech.convert(
            text=sample_text,
            model="bulbul:v4-flash",
            speaker=speaker,
            language_code="te-IN",
            pace=1.4,
            output_audio_codec="wav",
        )

        audio_bytes = base64.b64decode(audio.audios[0])

        filename = f"test_{speaker}.wav"
        with open(filename, "wb") as f:
            f.write(audio_bytes)

        print(f"Saved: {filename}")
        winsound.PlaySound(
            filename,
            winsound.SND_FILENAME
        )

    except Exception as error:
        print(f"Could not test {speaker}: {error}")