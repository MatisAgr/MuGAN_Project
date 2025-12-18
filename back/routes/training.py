from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from ..controllers import training_controller

router = APIRouter()

class StartTrainingRequest(BaseModel):
    epochs: int = 20
    learning_rate: float = 0.001
    batch_size: int = 32
    sequence_length: int = 32

@router.post("/start")
async def start_training(request: StartTrainingRequest):
    if training_controller.is_training_active():
        raise HTTPException(status_code=400, detail="Training already in progress")
    
    success = training_controller.start_training(
        total_epochs=request.epochs,
        learning_rate=request.learning_rate,
        batch_size=request.batch_size,
        sequence_length=request.sequence_length
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

class StartPreprocessingRequest(BaseModel):
    sequence_length: int = 32
    train_split: float = 0.9
    max_files: int = 10

@router.post("/preprocess/start")
async def start_preprocessing(request: StartPreprocessingRequest):
    success = training_controller.start_preprocessing(
        sequence_length=request.sequence_length,
        train_split=request.train_split,
        max_files=request.max_files
    )
    if success:
        return {"status": "started"}
    else:
        raise HTTPException(status_code=400, detail="Preprocessing already in progress")

@router.get("/preprocess/status")
async def get_preprocessing_status():
    status = training_controller.get_preprocessing_status()
    return status

@router.get("/preprocess/stats")
async def get_preprocessing_stats():
    stats = training_controller.get_preprocessing_stats()
    if stats:
        return {"stats": stats}
    else:
        return {"stats": None, "message": "No preprocessing stats available"}

@router.post("/preprocess/stop")
async def stop_preprocessing():
    success = training_controller.stop_preprocessing()
    if success:
        return {"status": "stopped"}
    else:
        raise HTTPException(status_code=400, detail="No preprocessing in progress")

@router.websocket("/preprocess/stream")
async def preprocessing_websocket(websocket: WebSocket):
    await websocket.accept()
    print(f"[WEBSOCKET /training/preprocess/stream] Client connected")
    
    async def send_status(status):
        try:
            if websocket.client_state.name == "CONNECTED":
                await websocket.send_json(status)
        except Exception as e:
            print(f"[WEBSOCKET /training/preprocess/stream] Error sending status: {e}")
    
    training_controller.add_preprocess_listener(send_status)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("[WEBSOCKET /training/preprocess/stream] Client disconnected")
    except Exception as e:
        print(f"[WEBSOCKET /training/preprocess/stream] Error: {str(e)}")
    finally:
        training_controller.remove_preprocess_listener(send_status)
        try:
            await websocket.close()
        except Exception as e:
            print(f"[WEBSOCKET /training/preprocess/stream] Error closing: {e}")
