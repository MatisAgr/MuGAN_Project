import json
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pathlib import Path

def inserer_json_mongodb():
    # 1. Charger les variables du .env
    load_dotenv()
    
    # 2. Définir le chemin dynamique
    BASE_DIR = Path(__file__).resolve().parent.parent
    # On utilise ce nom de variable partout
    chemin_json = BASE_DIR / "data" / "maestro_clean.json"

    # 3. Connexion MongoDB via variables d'environnement
    # On ajoute une valeur par défaut au cas où le .env soit mal lu
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME")
    col_name = os.getenv("COLLECTION_RAW")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[col_name]
    
    try:
        # CORRECTION ICI : utiliser 'chemin_json' au lieu de 'fichier'
        with open(chemin_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Vérifier si c'est une liste ou un seul objet
        if isinstance(data, list):
            if len(data) > 0:
                result = collection.insert_many(data)
                print(f"{len(result.inserted_ids)} documents insérés dans {db_name}.{col_name}")
            else:
                print(" Le fichier JSON est vide.")
        else:
            result = collection.insert_one(data)
            print(f"1 document inséré dans {db_name}.{col_name}")

    except FileNotFoundError:
        print(f"Erreur : Le fichier est introuvable à l'adresse : {chemin_json}")
    except Exception as e:
        print(f"Erreur lors de l'insertion : {e}")

if __name__ == "__main__":
    inserer_json_mongodb()