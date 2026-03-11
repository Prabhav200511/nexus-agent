from fastapi import APIRouter, WebSocket

router = APIRouter()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()

            await websocket.send_json({
                "success": True,
                "data": f"Echo: {data}",
                "error": None
            })

    except Exception:
        await websocket.close()