import os
import json
import argparse
import time
from pathlib import Path
from typing import Callable, Optional
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import matplotlib.pyplot as plt

# tf.config.set_visible_devices([], 'GPU')
tf.data.experimental.enable_debug_mode()
PROJECT_DIR = Path(__file__).parent.parent
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
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
        if self.should_stop and self.should_stop():
            self.model.stop_training = True
            return
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


def build_model(sequence_length: int, vocab_size: int = 128, learning_rate: float = 0.001) -> keras.Model:
    """
    2 sorties: pitch et duration.
    sequence_length: longueur des séquences d'entrée
    vocab_size: nombre de notes uniques (0-127 pour MIDI)
    learning_rate: learning rate pour l'optimiseur Adam
    """
    inputs = keras.Input(shape=(sequence_length, 2))
    
    x = layers.LSTM(128, return_sequences=True)(inputs)
    x = layers.Dropout(0.2)(x)
    
    x = layers.LSTM(64, return_sequences=False)(x)
    x = layers.Dropout(0.2)(x)
    
    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(64, activation='relu')(x)
    
    pitch_output = layers.Dense(vocab_size + 2, activation='softmax', name='pitch')(x)
    duration_output = layers.Dense(5, activation='softmax', name='duration')(x)
    
    model = keras.Model(inputs=inputs, outputs=[pitch_output, duration_output])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss={
            'pitch': 'sparse_categorical_crossentropy',
            'duration': 'sparse_categorical_crossentropy'
        },
        metrics={
            'pitch': 'accuracy',
            'duration': 'accuracy'
        }
    )
    
    return model


def prepare_data(sequences: np.ndarray, sequence_length: int):
    """
    sépare pitch et duration et crée des paires (input, target).
    sequences: array de séquences (num_sequences, sequence_length, 2)
    sequence_length: longueur des séquences
    """
    X = []
    y_pitch = []
    y_duration = []
    
    for seq in sequences:
        X.append(seq)
        y_pitch.append(int(seq[-1, 0]))
        y_duration.append(int(seq[-1, 1]))
    
    X = np.array(X, dtype=np.float32)
    y_pitch = np.array(y_pitch, dtype=np.int32)
    y_duration = np.array(y_duration, dtype=np.int32)
    
    X = np.where(X == -1, 128, X)
    X = np.where(X == 0, 0, X).astype(np.float32)
    y_pitch = np.where(y_pitch == -1, 128, y_pitch).astype(np.int32)
    y_duration = np.where(y_duration <= 0, 0, y_duration).astype(np.int32)
    
    return X, y_pitch, y_duration


def save_metrics_json(history, model_dir: str, num_epochs: int, batch_size: int, learning_rate: float = 0.001):
    """
    sauvegarde les métriques d'entraînement en format JSON.
    gère 2 sorties: pitch et duration.
    history: objet History retourné par model.fit()
    model_dir: dossier où sauvegarder le fichier JSON
    num_epochs: nombre d'epochs d'entraînement
    batch_size: taille des batches utilisée
    learning_rate: learning rate utilisé pour l'entraînement
    """
    metrics_path = os.path.join(model_dir, "training_metrics.json")
    
    metrics = {
        "num_epochs": num_epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "pitch_loss": history.history.get('pitch_loss', []),
        "pitch_accuracy": history.history.get('pitch_accuracy', []),
        "duration_loss": history.history.get('duration_loss', []),
        "duration_accuracy": history.history.get('duration_accuracy', []),
        "val_pitch_loss": history.history.get('val_pitch_loss', []),
        "val_pitch_accuracy": history.history.get('val_pitch_accuracy', []),
        "val_duration_loss": history.history.get('val_duration_loss', []),
        "val_duration_accuracy": history.history.get('val_duration_accuracy', []),
        "final_metrics": {
            "pitch_loss": float(history.history['pitch_loss'][-1]),
            "pitch_accuracy": float(history.history['pitch_accuracy'][-1]),
            "duration_loss": float(history.history['duration_loss'][-1]),
            "duration_accuracy": float(history.history['duration_accuracy'][-1]),
            "val_pitch_loss": float(history.history['val_pitch_loss'][-1]),
            "val_pitch_accuracy": float(history.history['val_pitch_accuracy'][-1]),
            "val_duration_loss": float(history.history['val_duration_loss'][-1]),
            "val_duration_accuracy": float(history.history['val_duration_accuracy'][-1]),
            "epochs_trained": len(history.history['pitch_loss'])
        }
    }
    
    for key in metrics:
        if isinstance(metrics[key], list):
            metrics[key] = [float(x) for x in metrics[key]]
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"metrics saved: {metrics_path}")
    
    return metrics_path



def train_model(train_dir: str,
                model_dir: str,
                num_epochs: int = 20,
                batch_size: int = 32,
                sequence_length: int = 32,
                learning_rate: float = 0.001,
                stats_callback: Optional[Callable] = None,
                should_stop: Optional[Callable] = None):
    """
    train_dir: dossier contenant les données prétraitées
    model_dir: dossier pour sauvegarder le modèle
    num_epochs: nombre d'epochs d'entraînement
    batch_size: taille des batches
    sequence_length: longueur des séquences
    learning_rate: learning rate pour l'optimiseur Adam
    stats_callback: fonction appelée à chaque epoch avec les statistiques
    should_stop: fonction qui retourne True si l'entraînement doit être arrêté
    """
    os.makedirs(model_dir, exist_ok=True)
    start_time = time.time()
    
    print("=" * 60)
    print("training model")
    print("=" * 60)
    
    print("\nloading data...")
    train_path = os.path.join(train_dir, "train_sequences.npy")
    val_path = os.path.join(train_dir, "validation_sequences.npy")
    
    if not os.path.exists(train_path):
        print(f"error: file not found: {train_path}")
        print("   have you executed preprocess.py first?")
        return
    
    train_sequences = np.load(train_path)
    val_sequences = np.load(val_path)
    
    print(f"training data loaded: {train_sequences.shape}")
    print(f"validation data loaded: {val_sequences.shape}")
    
    print("\ndata preparation...")
    X_train, y_pitch_train, y_duration_train = prepare_data(train_sequences, sequence_length)
    X_val, y_pitch_val, y_duration_val = prepare_data(val_sequences, sequence_length)
    
    print(f"X_train shape: {X_train.shape}")
    print(f"y_pitch_train shape: {y_pitch_train.shape}")
    print(f"y_duration_train shape: {y_duration_train.shape}")
    
    print("\nmodel building...")
    model = build_model(sequence_length, learning_rate=learning_rate)
    print("model built")
    
    print("\nmodel summary:")
    model.summary()
    
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
    
    # save model
    final_model_path = os.path.join(model_dir, 'model_final.h5')
    model.save(final_model_path)
    print(f"\nmodele sauvegardé {final_model_path}")
    
    # save architecture
    with open(os.path.join(model_dir, 'model_config.json'), 'w') as f:
        f.write(model.to_json())
    
    # plot training curves
    print("\ngraph gen")
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(history.history['pitch_loss'], label='Training Pitch Loss')
    plt.plot(history.history['val_pitch_loss'], label='Validation Pitch Loss')
    plt.plot(history.history['duration_loss'], label='Training Duration Loss')
    plt.plot(history.history['val_duration_loss'], label='Validation Duration Loss')
    plt.title('Loss during training')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['pitch_accuracy'], label='Training Pitch Accuracy')
    plt.plot(history.history['val_pitch_accuracy'], label='Validation Pitch Accuracy')
    plt.plot(history.history['duration_accuracy'], label='Training Duration Accuracy')
    plt.plot(history.history['val_duration_accuracy'], label='Validation Duration Accuracy')
    plt.title('Accuracy during training')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True)
    
    graph_path = os.path.join(model_dir, 'training_history.png')
    plt.savefig(graph_path, dpi=100, bbox_inches='tight')
    print(f"graphs saved: {graph_path}")
    
    print("\nmetrics saving...")
    save_metrics_json(history, model_dir, num_epochs, batch_size, learning_rate)
    
    print("\n" + "=" * 60)
    print("training complete!")
    print(f"models saved in: {model_dir}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entraînement du modèle de génération musicale")
    parser.add_argument("--train_dir", type=str, default=str(DATA_PROCESSED_DIR),
                        help="folder containing preprocessed data")
    parser.add_argument("--model_dir", type=str, default=str(MODELS_DIR),
                        help="folder to save the model")
    parser.add_argument("--num_epochs", type=int, default=20,
                        help="number of epochs")
    parser.add_argument("--batch_size", type=int, default=32,
                        help="batch size")
    parser.add_argument("--sequence_length", type=int, default=32,
                        help="sequence length")
    parser.add_argument("--learning_rate", type=float, default=0.001,
                        help="learning rate for Adam optimizer")
    
    args = parser.parse_args()
    
    print(f"project folder: {PROJECT_DIR}")
    print(f"training data: {args.train_dir}")
    print(f"models: {args.model_dir}\n")
    
    train_model(
        train_dir=args.train_dir,
        model_dir=args.model_dir,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        sequence_length=args.sequence_length,
        learning_rate=args.learning_rate
    )

