from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from ..controllers import training_controller

router = APIRouter()

class StartTrainingRequest(BaseModel):
    epochs: int = 20
    learning_rate: float = 0.001
    batch_size: int = 32

@router.post("/start")
async def start_training(request: StartTrainingRequest):
    if training_controller.is_training_active():
        raise HTTPException(status_code=400, detail="Training already in progress")
    
    success = training_controller.start_training(
        total_epochs=request.epochs,
        learning_rate=request.learning_rate,
        batch_size=request.batch_size
    )
    if success:
        return {"status": "started", "epochs": request.epochs}
    else:
        raise HTTPException(status_code=500, detail="Failed to start training")

@router.post("/stop")
async def stop_training():
    success = training_controller.stop_training()
    if success:
        return {"status": "stopped"}
    else:
        raise HTTPException(status_code=400, detail="No training in progress")

@router.get("/status")
async def get_training_status():
    is_active = training_controller.is_training_active()
    session = training_controller.get_current_training_session()
    return {
        "is_active": is_active,
        "session": session.model_dump() if session else None
    }

@router.websocket("/stream")
async def training_websocket(websocket: WebSocket):
    await websocket.accept()
    print(f"[WEBSOCKET /training/stream] Client connected")
    
    async def send_stats(stats):
        try:
            await websocket.send_json(stats.model_dump())
        except Exception as e:
            print(f"[WEBSOCKET /training/stream] Error sending stats: {e}")
    
    training_controller.add_training_listener(send_stats)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("[WEBSOCKET /training/stream] Client disconnected")
    except Exception as e:
        print(f"[WEBSOCKET /training/stream] Error: {str(e)}")
    finally:
        training_controller.remove_training_listener(send_stats)
        await websocket.close()

@router.get("/latest-session")
async def get_latest_session():
    session = training_controller.get_latest_training_session()
    if not session:
        return {"session": None}
    return {"session": session.model_dump()}

@router.get("/current-session")
async def get_current_session():
    session = training_controller.get_current_training_session()
    if not session:
        return {"session": None}
    return {"session": session.model_dump()}
