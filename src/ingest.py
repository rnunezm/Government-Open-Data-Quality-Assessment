# scripts/ingest.py
import os, glob, shutil
from datetime import datetime
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.profiling import run_profile_from_csv


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_DIR = os.path.join(BASE_DIR,"input")
ARCHIVE_DIR = os.path.join(BASE_DIR,"archive")
os.makedirs(ARCHIVE_DIR,exist_ok=True)

def pick_latest_csv():
    files = sorted(glob.glob(os.path.join(INPUT_DIR,"*.csv")),key=os.path.getmtime)
    return files[-1] if files else None

def process_latest():
    csv = pick_latest_csv()
    if csv is None:
        print("No hay CSV en input/")
        return None
    print("Procesando:",csv)
    profile = run_profile_from_csv(csv)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dest = os.path.join(ARCHIVE_DIR,f"{os.path.basename(csv).rsplit('.',1)[0]}_{ts}.csv")
    shutil.move(csv,dest)
    print(f"CSV movido a archive: {dest}")
    return profile
