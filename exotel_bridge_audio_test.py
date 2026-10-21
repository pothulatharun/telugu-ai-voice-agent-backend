from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import base64
import json
from pathlib import Path

router = APIRouter()

# Test audio file; this does not modify your production backend.
PCM_PATH = Path(__file__).resolve().parent / "test_tone_8khz.pcm"

# 20 ms of 8 kHz, mono, 16-bit PCM = 320 bytes.
CHUNK_SIZE = 320
CHUNK_INTERVAL_SECONDS = 0.02


@router.websocket("/exotel/test-stream")
async def exotel_stream(websocket: WebSocket):
    await websocket.accept()
    print("Test WebSocket connected")

    try:
        while True:
            message = await websocket.receive_text()

            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                print("Ignoring invalid JSON message")
                continue

            event = data.get("event", "unknown")

            if event == "connected":
                print("WebSocket connection confirmed")

            elif event == "start":
                start = data.get("start", {})

                stream_sid = (
                    data.get("stream_sid")
                    or start.get("stream_sid")
                )

                if not stream_sid:
                    print("Missing stream_sid; cannot send audio")
                    continue

                if not PCM_PATH.is_file():
                    print("PCM audio file not found:", PCM_PATH)
                    continue

                pcm_audio = PCM_PATH.read_bytes()

                if not pcm_audio:
                    print("PCM audio file is empty")
                    continue

                print("Test stream started:", stream_sid)
                print("Audio file:", PCM_PATH)
                print("PCM bytes:", len(pcm_audio))

                packets_sent = 0

                for offset in range(0, len(pcm_audio), CHUNK_SIZE):
                    chunk = pcm_audio[offset:offset + CHUNK_SIZE]

                    # Stop sending if the WebSocket has disconnected.
                    if websocket.client_state.name != "CONNECTED":
                        print("Client disconnected during playback")
                        break

                    payload = base64.b64encode(chunk).decode("ascii")

                    outgoing_message = {
                        "event": "media",
                        "stream_sid": stream_sid,
                        "media": {
                            "payload": payload
                        }
                    }

                    await websocket.send_text(
                        json.dumps(outgoing_message)
                    )

                    packets_sent += 1
                    await asyncio.sleep(CHUNK_INTERVAL_SECONDS)

                print("Audio packets sent:", packets_sent)
                print("Test audio playback finished")

            elif event == "stop":
                print("Test stream stopped")
                break

            else:
                print("Received event:", event)

    except WebSocketDisconnect:
        print("Test client disconnected")

    except Exception as error:
        print("Test bridge error:", type(error).__name__)

    finally:
        print("Test WebSocket handler finished")