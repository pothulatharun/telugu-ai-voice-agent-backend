import os
import base64
import winsound
import sounddevice as sd
import scipy.io.wavfile as wav

from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()

api_key = os.getenv("SARVAM_API_SUBSCRIPTION_KEY")

if not api_key:
    raise ValueError("API key not found. Check your .env file.")

client = SarvamAI(api_subscription_key=api_key)

SAMPLE_RATE = 16000
DURATION = 6

messages = [
    {
        "role": "system",
        "content": """
You are a friendly, natural Telugu-English voice assistant.
Speak like a real person in a casual conversation.
Mix everyday Telugu with simple English naturally.
Use a friendly Hyderabad/Telangana conversational style.
Avoid formal Telugu, robotic wording, and long answers.
Use natural conversational pauses through punctuation.
Never invent information about a business or service.
Respond in the same language style as the user.
"""
    }
]


def listen_to_user():
    input("\nPress Enter when you are ready to speak...")
    print("🎤 Listening... Speak now!")

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )
    sd.wait()

    wav.write("mic_input.wav", SAMPLE_RATE, audio)
    print("Recognizing your speech...")

    with open("mic_input.wav", "rb") as audio_file:
        result = client.speech_to_text.transcribe(
            file=audio_file,
            model="saaras:v4",
            language_code="te-IN"
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
        reasoning_effort=None
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
        output_audio_codec="wav"
    )

    audio_bytes = base64.b64decode(audio.audios[0])

    with open("agent_reply.wav", "wb") as f:
        f.write(audio_bytes)

    winsound.PlaySound(
        "agent_reply.wav",
        winsound.SND_FILENAME
    )


print("🤖 Telugu AI Voice Agent started!")
print("Say 'exit' to stop the conversation.")

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