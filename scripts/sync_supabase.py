#!/usr/bin/env python3
"""
Synchronise le fichier schools_tracking.json vers Supabase.
Usage : python scripts/sync_supabase.py
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Charger .env depuis la racine du projet
ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
TRACKING_FILE = ROOT / "outputs" / "logs" / "schools_tracking.json"

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ SUPABASE_URL ou SUPABASE_SERVICE_KEY manquant dans .env")
    sys.exit(1)

try:
    from supabase import create_client
except ImportError:
    print("❌ Paquet 'supabase' manquant. Lancez : pip install supabase>=2.0.0")
    sys.exit(1)

def main():
    if not TRACKING_FILE.exists():
        print(f"❌ Fichier introuvable : {TRACKING_FILE}")
        sys.exit(1)

    with open(TRACKING_FILE, "r", encoding="utf-8") as f:
        ecoles = json.load(f)

    print(f"📤 {len(ecoles)} établissements à synchroniser…")

    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Upsert (insert ou update si l'id existe déjà)
    result = client.table("schools_tracking").upsert(ecoles).execute()

    if hasattr(result, "data") and result.data is not None:
        print(f"✅ {len(result.data)} enregistrements synchronisés avec succès.")
    else:
        print("⚠️  Réponse inattendue de Supabase :", result)

if __name__ == "__main__":
    main()
