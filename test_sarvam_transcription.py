import asyncio
import base64
import os
import wave

from dotenv import load_dotenv
from sarvamai import AsyncSarvamAI, RealtimeAudioInput, RealtimeEnd

load_dotenv()

API_KEY = os.getenv("SARVAM_API_SUBSCRIPTION_KEY")
AUDIO_FILE = "microphone_test.wav"


async def main():
    if not API_KEY:
        raise RuntimeError("SARVAM_API_SUBSCRIPTION_KEY is missing from .env")

    # Read the locally recorded WAV file.
    with wave.open(AUDIO_FILE, "rb") as wav:
        channels = wav.getnchannels()
        sample_rate = wav.getframerate()
        sample_width = wav.getsampwidth()
        audio = wav.readframes(wav.getnframes())

    if channels != 1 or sample_width != 2 or sample_rate != 16000:
        raise ValueError(
            f"Expected mono 16-bit, 16000 Hz audio; got "
            f"{channels} channel(s), {sample_width * 8}-bit, {sample_rate} Hz."
        )

    client = AsyncSarvamAI(api_subscription_key=API_KEY)

    async with client.speech_to_text_realtime_streaming.connect(
        language_code="auto",
        model="saaras:v4",
        stream_type="fast",
        encoding="linear16",
        sample_rate=16000,
    ) as ws:
        print("Connected. Sending your recording...")

        # Send audio in small chunks.
        chunk_size = 16000 * 2 // 2  # 0.5 seconds of mono 16-bit audio
        for start in range(0, len(audio), chunk_size):
            chunk = audio[start:start + chunk_size]
            await ws.send_realtime_audio_input(
                RealtimeAudioInput(
                    audio=base64.b64encode(chunk).decode("utf-8")
                )
            )
            await asyncio.sleep(0.5)

        await ws.send_realtime_end(RealtimeEnd())
        print("Audio sent. Waiting for transcript...")

        async for message in ws:
            if message.event in ("transcript.partial", "transcript.final"):
                print(f"{message.event}: {message.text}")
            elif message.event == "error":
                print("Sarvam error:", message)
                break


if __name__ == "__main__":
    asyncio.run(main())