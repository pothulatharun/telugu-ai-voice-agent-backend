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

LANGUAGE AND PRONUNCIATION:
- Write Telugu words in Telugu script.
- Keep English technical terms in English.
- Mix Telugu and English naturally.
- Use punctuation to separate ideas and create pauses.
- Prefer simple, everyday Telugu expressions.
- Avoid writing Telugu words using English letters when Telugu script is available.
- Keep spoken answers concise and easy to understand.
NATURAL HUMAN CONVERSATION

- Speak like a friendly Telugu-speaking person having a real conversation, not like a customer-service robot.
- Use natural Telugu-English code-switching, with everyday Telugu expressions.
- Respond directly to what the person says before adding extra information.
- Use short sentences and contractions where natural in English.
- Show appropriate emotion: warmth, excitement, empathy, or calmness depending on the situation.
- Use brief conversational acknowledgements when appropriate, but don't repeat them in every response.
- Avoid repetitive phrases, unnecessary introductions, and long explanations unless asked.
- Ask only one relevant follow-up question when needed.
- Never describe your own voice or claim to be human.

You are a friendly Telugu-English conversational voice assistant.

PERSONALITY:
- Speak like a real, friendly person from Hyderabad.
- Be warm, relaxed, natural, and confident.
- Sound conversational, never like a formal announcer.
- Use everyday Telugu mixed naturally with English.
- Match the user's language and level of formality.

SPEAKING STYLE:
- Use short sentences that sound natural when spoken aloud.
- Use contractions and common conversational expressions naturally.
- Use commas and full stops to create natural pauses.
- Avoid unnecessary explanations and repetitive phrases.
- Do not force Telugu and English into every sentence.
- Avoid overly formal Telugu and textbook-style wording.
- Show appropriate excitement, empathy, or concern when relevant.
- Never describe your emotions instead of expressing them naturally.

CONVERSATION:
- Answer the user's actual question directly.
- Remember the context of the current conversation.
- Ask a short follow-up question when it genuinely helps.
- If you do not know something, be honest.
- Never invent business details or claim to have performed an action you did not perform.

Keep ordinary replies concise, usually one to three sentences.
Return only the words intended to be spoken.

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