import json
import unicodedata
from pathlib import Path

def nettoyer_maestro_generique():
    # Définition des chemins dynamiques
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    
    fichier_entree = DATA_DIR / 'maestro-v2.0.0.json'
    fichier_sortie = DATA_DIR / 'maestro_clean.json'

    try:
        if not fichier_entree.exists():
            print(f" Erreur : Le fichier {fichier_entree} est introuvable.")
            return

        with open(fichier_entree, 'r', encoding='utf-8') as f:
            data = json.load(f)

        donnees_nettoyees = []
        seen = set()

        def clean_value(val):
            """Nettoie et uniformise les valeurs (accents, espaces, arrondis)"""
            if val is None:
                return None
            if isinstance(val, str):
                val = val.strip()
                # Normalisation Unicode pour supprimer les accents et caractères spéciaux
                val = unicodedata.normalize('NFKD', val).encode('ascii', 'ignore').decode('utf-8')
                return val if val != "" else None
            if isinstance(val, (int, float)):
                return round(val, 2)
            return val

        for item in data:
            # Nettoyage des noms de fichiers (extraction du nom seul)
            midi_propre = clean_value(item.get("midi_filename", "").replace('\\', '/').split('/')[-1])
            audio_propre = clean_value(item.get("audio_filename", "").replace('\\', '/').split('/')[-1])

            nouveau_doc = {
                "composer": clean_value(item.get("canonical_composer")),
                "title": clean_value(item.get("canonical_title")),
                "year": clean_value(item.get("year")),
                "duration": clean_value(item.get("duration")),
                "midi_filename": midi_propre,
                "audio_filename": audio_propre,
                "split": clean_value(item.get("split"))
            }

            # On ne garde que les champs qui ne sont pas None
            nouveau_doc = {k: v for k, v in nouveau_doc.items() if v is not None}

            # Détection des doublons (clé unique basée sur compositeur, titre et fichier MIDI)
            key = (
                str(nouveau_doc.get("composer", "")).lower(),
                str(nouveau_doc.get("title", "")).lower(),
                str(nouveau_doc.get("midi_filename", "")).lower()
            )

            if key not in seen and nouveau_doc:
                donnees_nettoyees.append(nouveau_doc)
                seen.add(key)

        with open(fichier_sortie, 'w', encoding='utf-8') as f_out:
            json.dump(donnees_nettoyees, f_out, indent=4, ensure_ascii=False)

        print(f"Nettoyage terminé : {len(donnees_nettoyees)} entrées uniques sauvegardées.")

    except Exception as e:
        print(f"Erreur lors du nettoyage : {e}")

if __name__ == "__main__":
    nettoyer_maestro_generique()