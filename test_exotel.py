import asyncio
import json
import websockets

URL = "wss://telugu-ai-voice-agent-backend.onrender.com/exotel/stream"


async def main():
    async with websockets.connect(URL) as ws:
        await ws.send(json.dumps({"event": "connected"}))

        await ws.send(json.dumps({
            "event": "start",
            "stream_sid": "test-stream-123",
            "start": {
                "media_format": {
                    "encoding": "audio/linear16",
                    "sample_rate": 8000,
                    "bit_rate": 16
                }
            }
        }))

        await ws.send(json.dumps({
            "event": "media",
            "media": {
                "payload": "AQAAAA=="
            }
        }))

        await ws.send(json.dumps({
            "event": "stop",
            "stop": {"reason": "test"}
        }))

        print("WebSocket event test completed.")


asyncio.run(main())