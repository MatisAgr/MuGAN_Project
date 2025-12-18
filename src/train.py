import os
import argparse
import json
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow import keras

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
MODELS_DIR = PROJECT_DIR / "models" / "music_vae"

MAX_PITCHES = 4
VOCAB_SIZE = 130
NUM_DURATION_CLASSES = 8
NUM_TIME_SHIFT_CLASSES = 16


def build_model(sequence_length: int, learning_rate: float = 0.001) -> keras.Model:
    inputs = keras.Input(shape=(sequence_length, MAX_PITCHES + 2))
    
    x = keras.layers.LSTM(256, return_sequences=True)(inputs)
    x = keras.layers.Dropout(0.3)(x)
    x = keras.layers.LSTM(128, return_sequences=False)(x)
    x = keras.layers.Dropout(0.3)(x)
    
    x = keras.layers.Dense(256, activation='relu')(x)
    x = keras.layers.Dense(128, activation='relu')(x)
    
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
                model_dir: str = None):
    if model_dir is None:
        model_dir = str(MODELS_DIR)
    
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
    
    print(f"metrics saved: {metrics_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="train music generation model")
    parser.add_argument("--data_dir", type=str, default=str(DATA_DIR))
    parser.add_argument("--model_dir", type=str, default=str(MODELS_DIR))
    parser.add_argument("--num_epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--learning_rate", type=float, default=0.001)
    
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
