import os
import sounddevice as sd
import scipy.io.wavfile as wav
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()

api_key = os.getenv("SARVAM_API_SUBSCRIPTION_KEY")

if not api_key:
    raise ValueError("Sarvam API key not found in your .env file.")

client = SarvamAI(api_subscription_key=api_key)

SAMPLE_RATE = 16000
DURATION = 5

print("Speak in Telugu or Telugu-English after recording starts.")
input("Press Enter to start recording...")

print("Recording... Speak now!")

audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="int16"
)
sd.wait()

wav.write("mic_test.wav", SAMPLE_RATE, audio)
print("Recording complete. Sending audio to Sarvam...")

try:
    with open("mic_test.wav", "rb") as audio_file:
        result = client.speech_to_text.transcribe(
            file=audio_file,
            model="saaras:v4",
            language_code="te-IN"
        )

    recognized_text = result.transcript.strip()

    print("\nYou said:")
    print(recognized_text if recognized_text else "(No speech recognized)")

except Exception as error:
    print("\nSpeech recognition failed.")
    print("Error:", error)