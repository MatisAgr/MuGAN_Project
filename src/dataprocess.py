import os, zipfile, requests
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DATA_DIR = "C:\\kh\\midi"

if not os.path.exists(DATA_DIR) or not os.listdir(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Download
    r = requests.get("https://www.kaggle.com/api/v1/datasets/download/imsparsh/lakh-midi-clean",
                     auth=(os.environ["KAGGLE_USERNAME"], os.environ["KAGGLE_KEY"]), stream=True)
    with open("data.zip", "wb") as f:
        for chunk in tqdm(r.iter_content(8192), total=int(r.headers.get('content-length', 0))//8192):
            f.write(chunk)
    
    # Extract only .mid files
    with zipfile.ZipFile("data.zip") as zf:
        for m in tqdm([f for f in zf.namelist() if f.endswith('.mid')]):
            name = os.path.basename(m)[:100] + ".mid" if len(os.path.basename(m)) > 100 else os.path.basename(m)
            open(os.path.join(DATA_DIR, name), "wb").write(zf.read(m))
    
    os.remove("data.zip")

print(f"Dataset: {DATA_DIR} ({len(os.listdir(DATA_DIR))} files)")