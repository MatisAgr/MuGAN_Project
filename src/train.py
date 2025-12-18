import os
import argparse
import json
import time
from pathlib import Path
from typing import Callable, Optional
import numpy as np
import tensorflow as tf
from tensorflow import keras

from config import (MAX_PITCHES, VOCAB_SIZE, NUM_DURATION_CLASSES, NUM_TIME_SHIFT_CLASSES,
                    LSTM_UNITS_1, LSTM_UNITS_2, DENSE_UNITS_1, DENSE_UNITS_2, DROPOUT_RATE)

# tf.config.set_visible_devices([], 'GPU')
tf.data.experimental.enable_debug_mode()
PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
MODELS_DIR = PROJECT_DIR / "models" / "music_vae"


class TrainingCallback(keras.callbacks.Callback):
    def __init__(self, total_epochs: int, stats_callback: Optional[Callable] = None, start_time: float = None, should_stop: Optional[Callable] = None):
        super().__init__()
        self.total_epochs = total_epochs
        self.stats_callback = stats_callback
        self.start_time = start_time or time.time()
        self.epoch_start_time = None
        self.should_stop = should_stop
    
    def on_epoch_begin(self, epoch, logs=None):
        self.epoch_start_time = time.time()
        if self.should_stop and self.should_stop():
            self.model.stop_training = True
    
    def on_epoch_end(self, epoch, logs=None):
        if self.stats_callback and logs:
            elapsed_time = time.time() - self.start_time
            epoch_time = time.time() - self.epoch_start_time
            eta = epoch_time * (self.total_epochs - epoch - 1)
            
            stats = {
                "epoch": epoch + 1,
                "total_epochs": self.total_epochs,
                "loss": float(logs.get('loss', 0)),
                "accuracy": float(logs.get('pitch_accuracy', 0)),
                "val_loss": float(logs.get('val_loss', 0)),
                "val_accuracy": float(logs.get('val_pitch_accuracy', 0)),
                "learning_rate": float(keras.backend.get_value(self.model.optimizer.lr)),
                "batch_size": int(self.params.get('batch_size', 32)),
                "time_elapsed": elapsed_time,
                "eta": eta,
                "pitch_loss": float(logs.get('pitch_loss', 0)),
                "pitch_accuracy": float(logs.get('pitch_accuracy', 0)),
                "duration_loss": float(logs.get('duration_loss', 0)),
                "duration_accuracy": float(logs.get('duration_accuracy', 0)),
                "val_pitch_loss": float(logs.get('val_pitch_loss', 0)),
                "val_pitch_accuracy": float(logs.get('val_pitch_accuracy', 0)),
                "val_duration_loss": float(logs.get('val_duration_loss', 0)),
                "val_duration_accuracy": float(logs.get('val_duration_accuracy', 0))
            }
            
            self.stats_callback(stats)
        
        if self.should_stop and self.should_stop():
            self.model.stop_training = True


def build_model(sequence_length: int, vocab_size: int = 128, learning_rate: float = 0.001) -> keras.Model:
    """
    Build a 6-head LSTM model for polyphonic music generation.
    
    Architecture:
    - Input: sequences of shape (sequence_length, MAX_PITCHES + 2)
    - 2x LSTM layers (LSTM_UNITS_1 and LSTM_UNITS_2 units) with DROPOUT_RATE
    - 2x Dense layers (DENSE_UNITS_1 and DENSE_UNITS_2 units) with ReLU
    - 6 output heads: 4 pitch heads + 1 duration head + 1 time_shift head
    
    Each output head uses softmax activation with sparse categorical crossentropy loss.
    Hyperparameters are defined in config.py for easy tuning.
    
    Args:
        sequence_length: Length of input sequences.
        learning_rate: Adam optimizer learning rate.
        
    Returns:
        Compiled Keras Model.
    """
    inputs = keras.Input(shape=(sequence_length, MAX_PITCHES + 2))
    
    x = keras.layers.LSTM(LSTM_UNITS_1, return_sequences=True)(inputs)
    x = keras.layers.Dropout(DROPOUT_RATE)(x)
    x = keras.layers.LSTM(LSTM_UNITS_2, return_sequences=False)(x)
    x = keras.layers.Dropout(DROPOUT_RATE)(x)
    
    x = keras.layers.Dense(DENSE_UNITS_1, activation='relu')(x)
    x = keras.layers.Dense(DENSE_UNITS_2, activation='relu')(x)
    
    pitch_outputs = []
    for i in range(MAX_PITCHES):
        pitch_out = keras.layers.Dense(VOCAB_SIZE, activation='softmax', name=f'pitch_{i}')(x)
        pitch_outputs.append(pitch_out)
    
    duration_output = keras.layers.Dense(NUM_DURATION_CLASSES, activation='softmax', name='duration')(x)
    time_shift_output = keras.layers.Dense(NUM_TIME_SHIFT_CLASSES, activation='softmax', name='time_shift')(x)
    
    outputs = pitch_outputs + [duration_output, time_shift_output]
    
    model = keras.Model(inputs=inputs, outputs=outputs)
    
    losses = {}
    for i in range(MAX_PITCHES):
        losses[f'pitch_{i}'] = 'sparse_categorical_crossentropy'
    losses['duration'] = 'sparse_categorical_crossentropy'
    losses['time_shift'] = 'sparse_categorical_crossentropy'
    
    metrics = {}
    for i in range(MAX_PITCHES):
        metrics[f'pitch_{i}'] = 'accuracy'
    metrics['duration'] = 'accuracy'
    metrics['time_shift'] = 'accuracy'
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss=losses,
        metrics=metrics
    )
    
    return model


def load_data(data_dir: str = None):
    """
    Load preprocessed training and validation sequences.
    
    Loads .npy files created by preprocess.py. Expected format:
    - train_sequences.npy: array of shape (n_samples, sequence_length, 6)
    - validation_sequences.npy: array of shape (n_val, sequence_length, 6)
    
    Splits sequences into X (features, first 31 timesteps) and y (targets, last timestep).
    
    Args:
        data_dir: Directory containing .npy files. Uses DATA_DIR if None.
        
    Returns:
        Tuple of (X_train, y_train, X_val, y_val). Returns (None, None, None, None) if files not found.
    """
    if data_dir is None:
        data_dir = str(DATA_DIR)
    
    train_path = os.path.join(data_dir, "train_sequences.npy")
    val_path = os.path.join(data_dir, "validation_sequences.npy")
    
    if not os.path.exists(train_path):
        print(f"training file not found: {train_path}")
        print("run preprocess.py first")
        return None, None, None, None
    
    train_data = np.load(train_path)
    val_data = np.load(val_path) if os.path.exists(val_path) else None
    
    X_train = train_data[:, :-1, :]
    y_train = train_data[:, -1, :]
    
    if val_data is not None:
        X_val = val_data[:, :-1, :]
        y_val = val_data[:, -1, :]
    else:
        X_val, y_val = None, None
    
    print(f"training data: {X_train.shape}")
    if X_val is not None:
        print(f"validation data: {X_val.shape}")
    
    return X_train, y_train, X_val, y_val


def prepare_targets(y_data):
    """
    Convert target array into dictionary format for multi-head model training.
    
    Splits the last event (shape (n_samples, 6)) into 6 separate tensors:
    - pitch_0, pitch_1, pitch_2, pitch_3: indices 0-3 (pitch class predictions)
    - duration: index 4 (duration class prediction)
    - time_shift: index 5 (time shift class prediction)
    
    Args:
        y_data: Array of shape (n_samples, 6) containing target events.
        
    Returns:
        Dictionary with keys 'pitch_0', 'pitch_1', 'pitch_2', 'pitch_3', 'duration', 'time_shift'.
    """
    targets = {}
    for i in range(MAX_PITCHES):
        targets[f'pitch_{i}'] = y_data[:, i].astype(np.int32)
    targets['duration'] = y_data[:, MAX_PITCHES].astype(np.int32)
    targets['time_shift'] = y_data[:, MAX_PITCHES + 1].astype(np.int32)
    return targets


def train_model(model: keras.Model,
                X_train: np.ndarray,
                y_train: np.ndarray,
                X_val: np.ndarray = None,
                y_val: np.ndarray = None,
                num_epochs: int = 20,
                batch_size: int = 64,
                sequence_length: int = 32,
                learning_rate: float = 0.001,
                stats_callback: Optional[Callable] = None,
                should_stop: Optional[Callable] = None,
                model_dir: str = None):
  
    """
    Train the music generation model.
    
    Uses callbacks:
    - ModelCheckpoint: saves best model based on validation loss
    - EarlyStopping: stops training if validation loss plateaus (patience=5)
    - ReduceLROnPlateau: reduces learning rate if loss plateaus (factor=0.5, patience=3)
    
    Args:
        model: Compiled Keras model.
        X_train: Training features of shape (n_train, 31, 6).
        y_train: Training targets of shape (n_train, 6).
        X_val: Validation features. If None, no validation is used.
        y_val: Validation targets. If None, no validation is used.
        num_epochs: Number of training epochs.
        batch_size: Batch size for training.
        model_dir: Directory to save models. Uses MODELS_DIR if None.
        
    Returns:
        Keras History object with training/validation metrics.
    """
    
    if model_dir is None:
        model_dir = str(MODELS_DIR)


    os.makedirs(model_dir, exist_ok=True)
    start_time = time.time()

    
    os.makedirs(model_dir, exist_ok=True)
    
    y_train_dict = prepare_targets(y_train)
    y_val_dict = prepare_targets(y_val) if y_val is not None else None
    
    callbacks = [
        keras.callbacks.ModelCheckpoint(
            os.path.join(model_dir, "best_model.h5"),
            monitor='val_loss' if y_val is not None else 'loss',
            save_best_only=True,
            verbose=1
        ),
        keras.callbacks.EarlyStopping(
            monitor='val_loss' if y_val is not None else 'loss',
            patience=5,
            restore_best_weights=True
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss' if y_val is not None else 'loss',
            factor=0.5,
            patience=3,
            min_lr=1e-6
        )
    ]
    
    validation_data = (X_val, y_val_dict) if X_val is not None else None
    
    history = model.fit(
        X_train, y_train_dict,
        validation_data=validation_data,
        epochs=num_epochs,
        batch_size=batch_size,
        callbacks=callbacks
    )
    
    final_model_path = os.path.join(model_dir, "model_final.h5")
    model.save(final_model_path)
    print(f"final model saved: {final_model_path}")
    
    return history


def save_metrics(history, model_dir: str, learning_rate: float):
    """
    Save training metrics to JSON file.
    
    Extracts all metrics from the training history and saves to training_metrics.json.
    Includes learning rate and number of epochs trained.
    
    Args:
        history: Keras History object from model.fit().
        model_dir: Directory where to save the metrics file.
        learning_rate: Learning rate used during training.
    """
    metrics = {
        'learning_rate': learning_rate,
        'epochs_trained': len(history.history['loss']),
        'final_loss': float(history.history['loss'][-1]),
        'history': {}
    }
    
    for key, values in history.history.items():
        metrics['history'][key] = [float(v) for v in values]
    
    metrics_path = os.path.join(model_dir, 'training_metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    # Callbacks
    callbacks_list = [
        keras.callbacks.ModelCheckpoint(
            os.path.join(model_dir, 'best_model.h5'),
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        ),
        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=3,
            verbose=1
        )
    ]
    
    if stats_callback:
        training_cb = TrainingCallback(
            total_epochs=num_epochs,
            stats_callback=stats_callback,
            start_time=start_time,
            should_stop=should_stop
        )
        callbacks_list.append(training_cb)
    
    print("\ntraining start...")
    print(f"learning rate: {learning_rate}")
    print(f"epochs: {num_epochs}")
    print(f"batch size: {batch_size}")
    
    try:
        history = model.fit(
            X_train, {'pitch': y_pitch_train, 'duration': y_duration_train},
            epochs=num_epochs,
            batch_size=batch_size,
            validation_data=(X_val, {'pitch': y_pitch_val, 'duration': y_duration_val}),
            callbacks=callbacks_list,
            verbose=1
        )
    except KeyboardInterrupt:
        print("\ntraining interrupted by user")
        return None
    
    print(f"metrics saved: {metrics_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="train music generation model")
    parser.add_argument("--data_dir", type=str, default=str(DATA_DIR),
                        help="directory containing preprocessed data (default: data/processed/)")
    parser.add_argument("--model_dir", type=str, default=str(MODELS_DIR),
                        help="directory to save trained model (default: models/music_vae/)")
    parser.add_argument("--num_epochs", type=int, default=20,
                        help="number of training epochs (default: 20)")
    parser.add_argument("--batch_size", type=int, default=64,
                        help="training batch size (default: 64)")
    parser.add_argument("--learning_rate", type=float, default=0.001,
                        help="optimizer learning rate (default: 0.001)")
    
    args = parser.parse_args()
    
    print(f"project folder: {PROJECT_DIR}")
    print(f"data: {args.data_dir}")
    print(f"models: {args.model_dir}\n")
    
    X_train, y_train, X_val, y_val = load_data(args.data_dir)
    
    if X_train is None:
        exit(1)
    
    sequence_length = X_train.shape[1]
    
    model = build_model(sequence_length, args.learning_rate)
    model.summary()
    
    history = train_model(
        model,
        X_train, y_train,
        X_val, y_val,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        model_dir=args.model_dir
    )
    
    save_metrics(history, args.model_dir, args.learning_rate)
    
    print("\ntraining complete")
