import json
import unicodedata

def nettoyer_maestro_generique():
    fichier_entree = 'maestro-v2.0.0.json'
    fichier_sortie = 'maestro_clean.json'

    try:
        with open(fichier_entree, 'r', encoding='utf-8') as f:
            data = json.load(f)

        donnees_nettoyees = []
        seen = set()

        def clean_value(val):
            """Nettoie et uniformise les valeurs"""
            if val is None:
                return None
            if isinstance(val, str):
                # Supprimer espaces et normaliser accents
                val = val.strip()
                val = unicodedata.normalize('NFKD', val).encode('ascii', 'ignore').decode('utf-8')
                # Si la chaîne est vide après nettoyage, on ignore
                if val == "":
                    return None
                return val
            if isinstance(val, (int, float)):
                return round(val, 2)  # uniformiser les nombres
            return val

        for item in data:
            midi_brut = item.get("midi_filename", "").replace('\\', '/')
            midi_propre = clean_value(midi_brut.split('/')[-1])

            audio_brut = item.get("audio_filename", "").replace('\\', '/')
            audio_propre = clean_value(audio_brut.split('/')[-1])

            nouveau_doc = {
                "composer": clean_value(item.get("canonical_composer")),
                "title": clean_value(item.get("canonical_title")),
                "year": clean_value(item.get("year")),
                "duration": clean_value(item.get("duration")),
                "midi_filename": midi_propre,
                "audio_filename": audio_propre,
                "split": clean_value(item.get("split"))
            }

            # Supprimer les champs vides ou None
            nouveau_doc = {k: v for k, v in nouveau_doc.items() if v is not None}

            # Vérifier doublons (clé unique = composer + title + midi_filename)
            key = (nouveau_doc.get("composer"), nouveau_doc.get("title"), nouveau_doc.get("midi_filename"))
            if key not in seen and nouveau_doc:
                donnees_nettoyees.append(nouveau_doc)
                seen.add(key)

        with open(fichier_sortie, 'w', encoding='utf-8') as f_out:
            json.dump(donnees_nettoyees, f_out, indent=4, ensure_ascii=False)

        print(f" Nettoyage terminé : {len(donnees_nettoyees)} entrées uniques")
        print(f"Le fichier '{fichier_sortie}' est prêt pour MongoDB.")

    except Exception as e:
        print(f" Erreur : {e}")

if __name__ == "__main__":
    nettoyer_maestro_generique()
