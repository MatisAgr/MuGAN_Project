import os
import json
import argparse
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import matplotlib.pyplot as plt

tf.config.set_visible_devices([], 'GPU')
tf.data.experimental.enable_debug_mode()
PROJECT_DIR = Path(__file__).parent.parent
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
MODELS_DIR = PROJECT_DIR / "models" / "music_vae"


def build_model(sequence_length: int, vocab_size: int = 128, learning_rate: float = 0.001) -> keras.Model:
    """
    Construit un modèle RNN simple pour la génération musicale.
    
    Args:
        sequence_length: Longueur des séquences d'entrée
        vocab_size: Nombre de notes uniques (0-127 pour MIDI)
        learning_rate: Learning rate pour l'optimiseur Adam
        
    Returns:
        Modèle Keras compilé
    """
    model = keras.Sequential([
        layers.Embedding(vocab_size + 2, 64),
        
        layers.LSTM(128, return_sequences=True),
        layers.Dropout(0.2),
        
        layers.LSTM(64, return_sequences=False),
        layers.Dropout(0.2),
        
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.2),
        layers.Dense(64, activation='relu'),
        
        layers.Dense(vocab_size + 2, activation='softmax')
    ])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model


def prepare_data(sequences: np.ndarray, sequence_length: int):
    """
    Prépare les données pour l'entraînement.
    Crée des paires (input, target) à partir des séquences.
    Optimisé pour limiter l'utilisation mémoire.
    
    Args:
        sequences: Array de séquences (num_sequences, sequence_length)
        sequence_length: Longueur des séquences
        
    Returns:
        Tuple (X, y) prêts pour l'entraînement
    """
    X = []
    y = []
    
    for seq in sequences:
        X.append(seq)
        y.append(seq[-1])
    
    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int32)
    
    X = np.where(X == -1, 128, X).astype(np.int32)
    y = np.where(y == -1, 128, y).astype(np.int32)
    
    return X, y


def save_metrics_json(history, model_dir: str, num_epochs: int, batch_size: int, learning_rate: float = 0.001):
    """
    Sauvegarde les métriques d'entraînement en format JSON.
    Écrase le fichier précédent à chaque exécution.
    
    Args:
        history: Objet History retourné par model.fit()
        model_dir: Dossier où sauvegarder le fichier JSON
        num_epochs: Nombre d'epochs d'entraînement
        batch_size: Taille des batches utilisée
        learning_rate: Learning rate utilisé pour l'entraînement
    """
    metrics_path = os.path.join(model_dir, "training_metrics.json")
    
    metrics = {
        "num_epochs": num_epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "loss": history.history.get('loss', []),
        "accuracy": history.history.get('accuracy', []),
        "val_loss": history.history.get('val_loss', []),
        "val_accuracy": history.history.get('val_accuracy', []),
        "final_metrics": {
            "loss": float(history.history['loss'][-1]),
            "accuracy": float(history.history['accuracy'][-1]),
            "val_loss": float(history.history['val_loss'][-1]),
            "val_accuracy": float(history.history['val_accuracy'][-1]),
            "epochs_trained": len(history.history['loss'])
        }
    }
    
    # Convertir les listes numpy en listes Python (pour JSON)
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
                learning_rate: float = 0.001):
    """
    Entraîne le modèle de génération musicale.
    
    Args:
        train_dir: Dossier contenant les données prétraitées
        model_dir: Dossier pour sauvegarder le modèle
        num_epochs: Nombre d'epochs d'entraînement
        batch_size: Taille des batches
        sequence_length: Longueur des séquences
        learning_rate: Learning rate pour l'optimiseur Adam
    """
    os.makedirs(model_dir, exist_ok=True)
    
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
    X_train, y_train = prepare_data(train_sequences, sequence_length)
    X_val, y_val = prepare_data(val_sequences, sequence_length)
    
    print(f"X_train shape: {X_train.shape}")
    print(f"y_train shape: {y_train.shape}")
    
    print("\nmodel building...")
    model = build_model(sequence_length, learning_rate=learning_rate)
    print("model built")
    
    print("\nmodel summary:")
    model.summary()
    
    # Callbacks
    checkpoint = keras.callbacks.ModelCheckpoint(
        os.path.join(model_dir, 'best_model.h5'),
        monitor='val_loss',
        save_best_only=True,
        verbose=1
    )
    
    early_stop = keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=3,
        verbose=1
    )
    
    # Entraîner le modèle
    print("\ntraining start...")
    print(f"learning rate: {learning_rate}")
    print(f"epochs: {num_epochs}")
    print(f"batch size: {batch_size}")
    history = model.fit(
        X_train, y_train,
        epochs=num_epochs,
        batch_size=batch_size,
        validation_data=(X_val, y_val),
        callbacks=[checkpoint, early_stop],
        verbose=1
    )
    
    # Sauvegarder le modèle final
    final_model_path = os.path.join(model_dir, 'model_final.h5')
    model.save(final_model_path)
    print(f"\n💾 Modèle sauvegardé: {final_model_path}")
    
    # Sauvegarder l'architecture
    with open(os.path.join(model_dir, 'model_config.json'), 'w') as f:
        f.write(model.to_json())
    
    # Tracer les courbes d'apprentissage
    print("\n� Génération des graphiques...")
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('Loss during training')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['accuracy'], label='Training Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
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

