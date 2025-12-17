"""
Script d'entraînement d'un modèle de génération musicale avec TensorFlow/Keras.
Entraîne un modèle sur les séquences de notes MIDI prétraitées.
"""

import os
import json
import argparse
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import matplotlib.pyplot as plt

# Configuration TensorFlow
tf.config.set_visible_devices([], 'GPU')  # Force CPU si GPU problématique
tf.data.experimental.enable_debug_mode()  # Mode debug pour meilleur diagnostique

# Déterminer le dossier du projet (parent du dossier src)
PROJECT_DIR = Path(__file__).parent.parent
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
MODELS_DIR = PROJECT_DIR / "models" / "music_vae"


def build_model(sequence_length: int, vocab_size: int = 128) -> keras.Model:
    """
    Construit un modèle RNN simple pour la génération musicale.
    
    Args:
        sequence_length: Longueur des séquences d'entrée
        vocab_size: Nombre de notes uniques (0-127 pour MIDI)
        
    Returns:
        Modèle Keras compilé
    """
    model = keras.Sequential([
        # Couche d'embedding pour représenter les notes
        layers.Embedding(vocab_size + 2, 64),
        
        # LSTM pour capturer les dépendances
        layers.LSTM(128, return_sequences=True),
        layers.Dropout(0.2),
        
        # LSTM supplémentaire
        layers.LSTM(64, return_sequences=False),
        layers.Dropout(0.2),
        
        # Couches fully connected
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.2),
        layers.Dense(64, activation='relu'),
        
        # Output layer - prédire la prochaine note
        layers.Dense(vocab_size + 2, activation='softmax')
    ])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
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
        # Prendre la séquence entière comme input, prédire la dernière note
        X.append(seq)
        y.append(seq[-1])
    
    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int32)
    
    # Remplacer les valeurs -1 (silence) par un index spécial (128)
    X = np.where(X == -1, 128, X).astype(np.int32)
    # Les targets peuvent aussi contenir -1, remplacer par 128
    y = np.where(y == -1, 128, y).astype(np.int32)
    
    return X, y


def save_metrics_json(history, model_dir: str, num_epochs: int, batch_size: int):
    """
    Sauvegarde les métriques d'entraînement en format JSON.
    Écrase le fichier précédent à chaque exécution.
    
    Args:
        history: Objet History retourné par model.fit()
        model_dir: Dossier où sauvegarder le fichier JSON
        num_epochs: Nombre d'epochs d'entraînement
        batch_size: Taille des batches utilisée
    """
    metrics_path = os.path.join(model_dir, "training_metrics.json")
    
    metrics = {
        "num_epochs": num_epochs,
        "batch_size": batch_size,
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
    
    print(f"💾 Métriques sauvegardées: {metrics_path}")
    
    return metrics_path



def train_model(train_dir: str,
                model_dir: str,
                num_epochs: int = 20,
                batch_size: int = 32,
                sequence_length: int = 32):
    """
    Entraîne le modèle de génération musicale.
    
    Args:
        train_dir: Dossier contenant les données prétraitées
        model_dir: Dossier pour sauvegarder le modèle
        num_epochs: Nombre d'epochs d'entraînement
        batch_size: Taille des batches
        sequence_length: Longueur des séquences
    """
    os.makedirs(model_dir, exist_ok=True)
    
    print("=" * 60)
    print("🎓 ENTRAÎNEMENT DU MODÈLE DE GÉNÉRATION MUSICALE")
    print("=" * 60)
    
    # Charger les données
    print("\n📂 Chargement des données...")
    train_path = os.path.join(train_dir, "train_sequences.npy")
    val_path = os.path.join(train_dir, "validation_sequences.npy")
    
    if not os.path.exists(train_path):
        print(f"❌ Fichier non trouvé: {train_path}")
        print("   Avez-vous exécuté preprocess.py d'abord?")
        return
    
    train_sequences = np.load(train_path)
    val_sequences = np.load(val_path)
    
    print(f"✅ Données d'entraînement chargées: {train_sequences.shape}")
    print(f"✅ Données de validation chargées: {val_sequences.shape}")
    
    # Préparer les données
    print("\n🔄 Préparation des données...")
    X_train, y_train = prepare_data(train_sequences, sequence_length)
    X_val, y_val = prepare_data(val_sequences, sequence_length)
    
    print(f"✅ X_train shape: {X_train.shape}")
    print(f"✅ y_train shape: {y_train.shape}")
    
    # Construire le modèle
    print("\n🏗️ Construction du modèle...")
    model = build_model(sequence_length)
    print("✅ Modèle construit!")
    
    # Afficher le résumé du modèle
    print("\n📊 Résumé du modèle:")
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
    print("\n🚀 Démarrage de l'entraînement...")
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
    plt.title('Perte lors de l\'entraînement')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['accuracy'], label='Training Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.title('Précision lors de l\'entraînement')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True)
    
    graph_path = os.path.join(model_dir, 'training_history.png')
    plt.savefig(graph_path, dpi=100, bbox_inches='tight')
    print(f"✅ Graphiques sauvegardés: {graph_path}")
    
    # Sauvegarder les métriques en JSON (écrase le fichier précédent)
    print("\n📊 Sauvegarde des métriques d'entraînement...")
    save_metrics_json(history, model_dir, num_epochs, batch_size)
    
    print("\n" + "=" * 60)
    print("✅ ENTRAÎNEMENT TERMINÉ!")
    print(f"📁 Modèles sauvegardés dans: {model_dir}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entraînement du modèle de génération musicale")
    parser.add_argument("--train_dir", type=str, default=str(DATA_PROCESSED_DIR),
                        help="Dossier contenant les données prétraitées")
    parser.add_argument("--model_dir", type=str, default=str(MODELS_DIR),
                        help="Dossier pour sauvegarder le modèle")
    parser.add_argument("--num_epochs", type=int, default=20,
                        help="Nombre d'epochs")
    parser.add_argument("--batch_size", type=int, default=32,
                        help="Taille des batches")
    parser.add_argument("--sequence_length", type=int, default=32,
                        help="Longueur des séquences")
    
    args = parser.parse_args()
    
    print(f"📁 Dossier du projet: {PROJECT_DIR}")
    print(f"📁 Données d'entraînement: {args.train_dir}")
    print(f"📁 Modèles: {args.model_dir}\n")
    
    train_model(
        train_dir=args.train_dir,
        model_dir=args.model_dir,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        sequence_length=args.sequence_length
    )

