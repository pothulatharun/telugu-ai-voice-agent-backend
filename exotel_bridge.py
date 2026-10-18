from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()


@router.websocket("/exotel/stream")
async def exotel_stream(websocket: WebSocket):
    await websocket.accept()
    print("Exotel WebSocket connected")

    try:
        while True:
            message = await websocket.receive_text()

            try:
                event = json.loads(message)
                print("Exotel event:", event.get("event", "unknown"))
            except json.JSONDecodeError:
                print("Received a non-JSON message")

    except WebSocketDisconnect:
        print("Exotel WebSocket disconnected")