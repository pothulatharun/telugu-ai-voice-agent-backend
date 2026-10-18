from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import base64
import json

router = APIRouter()


@router.websocket("/exotel/stream")
async def exotel_stream(websocket: WebSocket):
    await websocket.accept()
    print("Exotel WebSocket connected")

    stream_sid = None
    media_messages = 0
    audio_bytes = 0

    try:
        while True:
            message = await websocket.receive_text()

            try:
                event_data = json.loads(message)
            except json.JSONDecodeError:
                print("Received a non-JSON message")
                continue

            event = event_data.get("event", "unknown")

            if event == "connected":
                print("Exotel connection handshake received")

            elif event == "start":
                start_data = event_data.get("start", {})
                stream_sid = (
                    event_data.get("stream_sid")
                    or start_data.get("stream_sid")
                )

                media_format = start_data.get("media_format", {})

                print("Exotel call stream started")
                print("Stream SID:", stream_sid)
                print("Audio encoding:", media_format.get("encoding"))
                print("Sample rate:", media_format.get("sample_rate"))
                print("Bit rate:", media_format.get("bit_rate"))

            elif event == "media":
                media_data = event_data.get("media", {})
                payload = media_data.get("payload", "")

                try:
                    decoded_audio = base64.b64decode(
                        payload, validate=True
                    )
                except (ValueError, TypeError):
                    print("Received an invalid audio payload")
                    continue

                media_messages += 1
                audio_bytes += len(decoded_audio)

                # Log metadata only; never print the audio itself.
                if media_messages == 1 or media_messages % 50 == 0:
                    print(
                        f"Audio packets: {media_messages}, "
                        f"total audio bytes: {audio_bytes}"
                    )

            elif event == "stop":
                stop_data = event_data.get("stop", {})
                print("Exotel call stream stopped")
                print("Stop reason:", stop_data.get("reason"))
                print("Total audio packets:", media_messages)
                print("Total audio bytes:", audio_bytes)
                break

            else:
                print("Exotel event:", event)

    except WebSocketDisconnect:
        print("Exotel WebSocket disconnected")
    except Exception as error:
        print("WebSocket handler error:", type(error).__name__)