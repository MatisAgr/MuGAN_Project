import asyncio
import random
from datetime import datetime
from typing import Optional, List, Callable
from ..models.training_stats import TrainingStats
from ..models.training_session import TrainingSession, TrainingEpoch, TrainingSessionResponse
from ..database_config import get_database
from bson import ObjectId

current_session: Optional[TrainingSession] = None
training_task: Optional[asyncio.Task] = None
training_listeners: List[Callable] = []

def get_training_collection():
    db = get_database()
    return db["training_stats"]

async def _run_training_background(total_epochs: int, learning_rate: float = 0.001, batch_size: int = 32):
    global current_session, training_listeners
    
    print(f"[TRAINING CONTROLLER] Starting background training for {total_epochs} epochs with LR={learning_rate}, BS={batch_size}")
    
    collection = get_training_collection()
    
    current_session = TrainingSession(
        total_epochs=total_epochs,
        current_epoch=0,
        status="running",
        start_time=datetime.utcnow(),
        elapsed_time=0,
        epochs_data=[]
    )
    
    result = collection.insert_one(current_session.model_dump(exclude={"session_id"}))
    session_id = str(result.inserted_id)
    current_session.session_id = session_id
    print(f"[TRAINING CONTROLLER] Created new training session: {session_id}")
    
    start_time = datetime.utcnow()
    
    try:
        for epoch in range(1, total_epochs + 1):
            base_loss = 2.5 - (epoch / total_epochs) * 2.0
            base_acc = 0.3 + (epoch / total_epochs) * 0.65
            
            loss = base_loss + random.uniform(-0.1, 0.1)
            accuracy = base_acc + random.uniform(-0.05, 0.05)
            val_loss = loss + random.uniform(0, 0.2)
            val_accuracy = accuracy - random.uniform(0, 0.05)
            
            elapsed_time = (datetime.utcnow() - start_time).total_seconds()
            eta = ((total_epochs - epoch) * elapsed_time / epoch) if epoch > 0 else 0
            
            stats = TrainingStats(
                epoch=epoch,
                total_epochs=total_epochs,
                loss=round(loss, 4),
                accuracy=round(accuracy, 4),
                val_loss=round(val_loss, 4),
                val_accuracy=round(val_accuracy, 4),
                learning_rate=learning_rate,
                batch_size=batch_size,
                time_elapsed=elapsed_time,
                eta=eta
            )
            
            epoch_data = TrainingEpoch(
                epoch=epoch,
                loss=stats.loss,
                accuracy=stats.accuracy,
                val_loss=stats.val_loss,
                val_accuracy=stats.val_accuracy,
                learning_rate=learning_rate,
                batch_size=batch_size,
                timestamp=datetime.utcnow()
            )
            
            collection.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {
                        "current_epoch": epoch,
                        "elapsed_time": elapsed_time
                    },
                    "$push": {"epochs_data": epoch_data.model_dump()}
                }
            )
            
            current_session.current_epoch = epoch
            current_session.elapsed_time = elapsed_time
            current_session.epochs_data.append(epoch_data)
            
            for listener in training_listeners:
                try:
                    await listener(stats)
                except Exception as e:
                    print(f"[TRAINING CONTROLLER] Error notifying listener: {e}")
            
            print(f"[TRAINING CONTROLLER] Epoch {epoch}/{total_epochs} - Loss: {stats.loss:.4f}, Acc: {stats.accuracy:.4f}")
            
            await asyncio.sleep(2)
        
        collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": "completed",
                    "end_time": datetime.utcnow()
                }
            }
        )
        
        if current_session:
            current_session.status = "completed"
            current_session.end_time = datetime.utcnow()
        
        print(f"[TRAINING CONTROLLER] Background training completed")
    except asyncio.CancelledError:
        print("[TRAINING CONTROLLER] Training was cancelled")
        if current_session:
            current_session.status = "stopped"
        raise
    except Exception as e:
        print(f"[TRAINING CONTROLLER] Error during training: {e}")
        if current_session:
            current_session.status = "error"
        raise

def start_training(total_epochs: int = 20, learning_rate: float = 0.001, batch_size: int = 32) -> bool:
    global training_task, current_session
    
    if training_task and not training_task.done():
        print("[TRAINING CONTROLLER] Training already in progress")
        return False
    
    training_task = asyncio.create_task(_run_training_background(total_epochs, learning_rate, batch_size))
    print(f"[TRAINING CONTROLLER] Started background training task")
    return True

def stop_training() -> bool:
    global training_task, current_session
    
    if not training_task or training_task.done():
        print("[TRAINING CONTROLLER] No training in progress")
        return False
    
    training_task.cancel()
    print("[TRAINING CONTROLLER] Cancelled training task")
    return True

def add_training_listener(listener: Callable):
    global training_listeners
    training_listeners.append(listener)
    print(f"[TRAINING CONTROLLER] Added listener, total: {len(training_listeners)}")

def remove_training_listener(listener: Callable):
    global training_listeners
    if listener in training_listeners:
        training_listeners.remove(listener)
        print(f"[TRAINING CONTROLLER] Removed listener, remaining: {len(training_listeners)}")

def is_training_active() -> bool:
    global training_task
    return training_task is not None and not training_task.done()

def get_latest_training_session() -> Optional[TrainingSessionResponse]:
    collection = get_training_collection()
    session = collection.find_one(sort=[("start_time", -1)])
    
    if not session:
        return None
    
    session["session_id"] = str(session.pop("_id"))
    return TrainingSessionResponse(**session)

def get_current_training_session() -> Optional[TrainingSessionResponse]:
    global current_session
    
    if current_session and current_session.status == "running":
        collection = get_training_collection()
        session = collection.find_one({"_id": ObjectId(current_session.session_id)})
        
        if session:
            session["session_id"] = str(session.pop("_id"))
            return TrainingSessionResponse(**session)
    
    return None
