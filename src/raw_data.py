import json
from pymongo import MongoClient

def inserer_json_mongodb():
    # Connexion à MongoDB local
    client = MongoClient("mongodb://localhost:27017/")

    # Choisis ta base et ta collection
    db = client["MuseGAN_DB"]          # nom de la base
    collection = db["raw_data"]   # nom de la collection

    # Charger le fichier JSON nettoyé
    fichier = "maestro_clean.json"
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Vérifier si c'est une liste ou un seul objet
        if isinstance(data, list):
            result = collection.insert_many(data)
            print(f"{len(result.inserted_ids)} documents insérés dans MongoDB.")
        else:
            result = collection.insert_one(data)
            print(f"1 document inséré dans MongoDB.")

    except Exception as e:
        print(f"Erreur lors de l'insertion : {e}")

if __name__ == "__main__":
    inserer_json_mongodb()
