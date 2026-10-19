import asyncio
import os

from dotenv import load_dotenv
from sarvamai import AsyncSarvamAI

load_dotenv()

api_key = os.getenv("SARVAM_API_SUBSCRIPTION_KEY")

if not api_key:
    raise RuntimeError(
        "SARVAM_API_SUBSCRIPTION_KEY was not found in .env"
    )


async def main():
    client = AsyncSarvamAI(
        api_subscription_key=api_key
    )

    print("Connecting to Sarvam...")
    print("Speak Telugu and English when prompted.")

    async with client.speech_to_text_realtime_streaming.connect(
        language_code="auto",
        model="saaras:v4",
        stream_type="fast",
        encoding="linear16",
        sample_rate=16000,
    ) as ws:
        print("Connected successfully.")
        print("Next, we will connect microphone audio.")


if __name__ == "__main__":
    asyncio.run(main())