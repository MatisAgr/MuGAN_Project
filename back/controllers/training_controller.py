import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Callable, Dict
from models.training_stats import TrainingStats
from models.training_session import TrainingSession, TrainingEpoch, TrainingSessionResponse
from database_config import get_database
from bson import ObjectId

current_session: Optional[TrainingSession] = None
training_task: Optional[asyncio.Task] = None
training_listeners: List[Callable] = []
should_stop_training = False
_train_model = None
_preprocess_fn = None
_training_loop = None

preprocess_task: Optional[asyncio.Task] = None
preprocess_status = {"is_running": False, "progress": 0, "message": "Ready"}
preprocess_listeners: List[Callable] = []

def _get_train_model():
    global _train_model
    if _train_model is None:
        sys.path.append(str(Path(__file__).parent.parent.parent / "src"))
        from train import train_model as tm
        _train_model = tm
    return _train_model

def _get_preprocess_fn():
    global _preprocess_fn
    if _preprocess_fn is None:
        sys.path.append(str(Path(__file__).parent.parent.parent / "src"))
        from preprocess import preprocess_dataset
        _preprocess_fn = preprocess_dataset
    return _preprocess_fn

def get_training_collection():
    db = get_database()
    return db["training_stats"]

async def _run_training_background(total_epochs: int, learning_rate: float = 0.001, batch_size: int = 32, sequence_length: int = 32):
    global current_session, training_listeners, should_stop_training, _training_loop
    
    print(f"[TRAINING CONTROLLER] Starting real training for {total_epochs} epochs with LR={learning_rate}, BS={batch_size}")
    
    _training_loop = asyncio.get_event_loop()
    collection = get_training_collection()
    should_stop_training = False
    
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
    
    def stats_callback(stats_dict):
        try:
            stats = TrainingStats(**stats_dict)
            
            epoch_data = TrainingEpoch(
                epoch=stats.epoch,
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
                        "current_epoch": stats.epoch,
                        "elapsed_time": stats.time_elapsed
                    },
                    "$push": {"epochs_data": epoch_data.model_dump()}
                }
            )
            
            current_session.current_epoch = stats.epoch
            current_session.elapsed_time = stats.time_elapsed
            current_session.epochs_data.append(epoch_data)
            
            if _training_loop:
                for listener in training_listeners:
                    try:
                        asyncio.run_coroutine_threadsafe(listener(stats), _training_loop)
                    except Exception as e:
                        print(f"[TRAINING CONTROLLER] Error notifying listener: {e}")
            
            print(f"[TRAINING CONTROLLER] Epoch {stats.epoch}/{total_epochs} - Loss: {stats.loss:.4f}, Acc: {stats.accuracy:.4f}")
        except Exception as e:
            print(f"[TRAINING CONTROLLER] Error in stats_callback: {e}")
    
    def check_stop():
        return should_stop_training
    
    try:
        project_dir = Path(__file__).parent.parent.parent
        train_dir = str(project_dir / "data" / "processed")
        model_dir = str(project_dir / "models" / "music_vae")
        
        train_model_fn = _get_train_model()
        
        loop = asyncio.get_event_loop()
        history = await loop.run_in_executor(
            None,
            train_model_fn,
            train_dir,
            model_dir,
            total_epochs,
            batch_size,
            sequence_length,
            learning_rate,
            stats_callback,
            check_stop
        )
        
        if should_stop_training:
            collection.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {
                        "status": "stopped",
                        "end_time": datetime.utcnow()
                    }
                }
            )
            if current_session:
                current_session.status = "stopped"
                current_session.end_time = datetime.utcnow()
            print(f"[TRAINING CONTROLLER] Training stopped by user")
        else:
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
            print(f"[TRAINING CONTROLLER] Training completed successfully")
            
    except asyncio.CancelledError:
        print("[TRAINING CONTROLLER] Training was cancelled")
        should_stop_training = True
        if current_session:
            current_session.status = "stopped"
            collection.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {"status": "stopped", "end_time": datetime.utcnow()}}
            )
        raise
    except Exception as e:
        print(f"[TRAINING CONTROLLER] Error during training: {e}")
        import traceback
        traceback.print_exc()
        if current_session:
            current_session.status = "error"
            collection.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {"status": "error", "end_time": datetime.utcnow()}}
            )
        raise

def start_training(total_epochs: int = 20, learning_rate: float = 0.001, batch_size: int = 32, sequence_length: int = 32) -> bool:
    global training_task, current_session, should_stop_training
    
    if training_task and not training_task.done():
        print("[TRAINING CONTROLLER] Training already in progress")
        return False
    
    should_stop_training = False
    training_task = asyncio.create_task(_run_training_background(total_epochs, learning_rate, batch_size, sequence_length))
    print(f"[TRAINING CONTROLLER] Started real training task")
    return True

def stop_training() -> bool:
    global training_task, current_session, should_stop_training
    
    if not training_task or training_task.done():
        print("[TRAINING CONTROLLER] No training in progress")
        return False
    
    should_stop_training = True
    training_task.cancel()
    print("[TRAINING CONTROLLER] Requested training stop")
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

async def _run_preprocessing_background(sequence_length: int = 32, train_split: float = 0.9, max_files: int = 10):
    global preprocess_status, preprocess_task
    
    preprocess_status["is_running"] = True
    preprocess_status["progress"] = 0
    preprocess_status["message"] = "Starting preprocessing..."
    
    print(f"[PREPROCESS CONTROLLER] Starting data preprocessing with {max_files} files")
    
    current_loop = asyncio.get_event_loop()
    
    def notify_listeners_sync(progress, message):
        global preprocess_listeners
        for listener in preprocess_listeners:
            try:
                asyncio.run_coroutine_threadsafe(
                    listener({"progress": progress, "message": message, "is_running": preprocess_status["is_running"]}),
                    current_loop
                )
            except Exception as e:
                print(f"[PREPROCESS CONTROLLER] Error notifying listener: {e}")
    
    def progress_callback(progress, message):
        preprocess_status["progress"] = progress
        preprocess_status["message"] = message
        print(f"[PREPROCESS CONTROLLER] {progress}% - {message}")
        notify_listeners_sync(progress, message)
    
    try:
        project_dir = Path(__file__).parent.parent.parent
        data_dir = str(project_dir / "data")
        output_dir = str(project_dir / "data" / "processed")
        
        preprocess_status["message"] = "Loading preprocessing function..."
        preprocess_fn = _get_preprocess_fn()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            preprocess_fn,
            data_dir,
            output_dir,
            sequence_length,
            train_split,
            progress_callback,
            max_files
        )
        
        preprocess_status["is_running"] = False
        
        print("[PREPROCESS CONTROLLER] Preprocessing completed successfully")
        
        import json
        stats_file = Path(output_dir) / "stats.txt"
        if stats_file.exists():
            stats = {}
            with open(stats_file, 'r') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.strip().split(':', 1)
                        try:
                            stats[key.strip()] = float(value.strip()) if '.' in value else int(value.strip())
                        except:
                            stats[key.strip()] = value.strip()
            return stats
        
    except Exception as e:
        print(f"[PREPROCESS CONTROLLER] Error during preprocessing: {e}")
        import traceback
        traceback.print_exc()
        preprocess_status["is_running"] = False
        preprocess_status["message"] = f"Error: {str(e)}"
        raise

def start_preprocessing(sequence_length: int = 32, train_split: float = 0.9, max_files: int = 10) -> bool:
    global preprocess_task, preprocess_status
    
    if preprocess_task and not preprocess_task.done():
        print("[PREPROCESS CONTROLLER] Preprocessing already in progress")
        return False
    
    preprocess_task = asyncio.create_task(_run_preprocessing_background(sequence_length, train_split, max_files))
    print("[PREPROCESS CONTROLLER] Started preprocessing task")
    return True

def get_preprocessing_status() -> Dict:
    return preprocess_status

def get_preprocessing_stats() -> Optional[Dict]:
    project_dir = Path(__file__).parent.parent.parent
    stats_file = project_dir / "data" / "processed" / "stats.txt"
    
    if not stats_file.exists():
        return None
    
    stats = {}
    with open(stats_file, 'r') as f:
        for line in f:
            if ':' in line:
                key, value = line.strip().split(':', 1)
                try:
                    stats[key.strip()] = float(value.strip()) if '.' in value else int(value.strip())
                except:
                    stats[key.strip()] = value.strip()
    
    return stats

def add_preprocess_listener(listener: Callable):
    global preprocess_listeners
    preprocess_listeners.append(listener)
    print(f"[PREPROCESS CONTROLLER] Added listener, total: {len(preprocess_listeners)}")

def remove_preprocess_listener(listener: Callable):
    global preprocess_listeners
    if listener in preprocess_listeners:
        preprocess_listeners.remove(listener)
        print(f"[PREPROCESS CONTROLLER] Removed listener, remaining: {len(preprocess_listeners)}")
