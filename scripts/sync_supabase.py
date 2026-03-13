#!/usr/bin/env python3
"""
Synchronise le fichier schools_tracking.json vers Supabase.
Usage : python scripts/sync_supabase.py
"""

import json
import os
import sys
from pathlib import Path

# Charger .env manuellement (sans dépendance externe)
ROOT = Path(__file__).parent.parent
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
TRACKING_FILE = ROOT / "outputs" / "logs" / "schools_tracking.json"

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ SUPABASE_URL ou SUPABASE_SERVICE_KEY manquant dans .env")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("❌ Paquet 'requests' manquant. Lancez : pip install requests")
    sys.exit(1)

def main():
    if not TRACKING_FILE.exists():
        print(f"❌ Fichier introuvable : {TRACKING_FILE}")
        sys.exit(1)

    with open(TRACKING_FILE, "r", encoding="utf-8") as f:
        ecoles = json.load(f)

    print(f"📤 {len(ecoles)} établissements à synchroniser…")

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }

    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/schools_tracking",
        headers=headers,
        json=ecoles,
        timeout=30,
    )

    if r.status_code in (200, 201):
        print(f"✅ Synchronisation réussie ({r.status_code})")
    else:
        print(f"❌ Erreur {r.status_code} : {r.text[:300]}")
        sys.exit(1)

if __name__ == "__main__":
    main()
