#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║   INITIALISATION SUPABASE — Système PTP Chris Gnabroyou      ║
╚══════════════════════════════════════════════════════════════╝

Envoie DIRECTEMENT toutes les écoles depuis la config vers Supabase
pour que l'application mobile affiche les données.

Utilisation :
  python initialiser_supabase.py
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

import requests
from ptp_system.config import FORMATIONS_CIBLES, CANDIDAT

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

SEP = "─" * 62


def _headers():
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }


def construire_payload() -> list[dict]:
    """Construit le payload complet depuis la config — 14 établissements."""
    payload = []
    for formation in FORMATIONS_CIBLES:
        for etab in formation["etablissements"]:
            payload.append({
                "id": f"{formation['id']}_{etab['nom'].replace(' ', '_').lower()[:20]}",
                "etablissement": etab["nom"],
                "ville": etab["ville"],
                "formation": formation["nom"],
                "formation_id": formation["id"],
                "formation_priorite": formation["priorite"],
                "statut": "À contacter",
                "email_contact": etab.get("email_contact", ""),
                "lien_candidature": etab.get("lien_candidature", etab["url"]),
                "date_limite": etab.get("date_limite", ""),
                "score_adequation": None,
                "notes": "",
                "date_premier_contact": None,
                "date_derniere_action": None,
                "nb_emails_envoyes": 0,
                "data_full": json.dumps({
                    "universite": etab.get("universite", ""),
                    "region": etab.get("region", ""),
                    "url": etab.get("url", ""),
                    "competences_visees": formation.get("competences_visees", []),
                }, ensure_ascii=False),
                "updated_at": datetime.utcnow().isoformat() + "Z",
            })
    return payload


def sync_schools(payload: list[dict]) -> bool:
    try:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/schools_tracking",
            headers=_headers(),
            json=payload,
            timeout=20,
        )
        if resp.status_code in (200, 201):
            return True
        print(f"  ❌ Erreur Supabase {resp.status_code} : {resp.text[:400]}")
        return False
    except requests.exceptions.ConnectionError:
        print("  ❌ Impossible de joindre Supabase (vérifiez votre connexion internet)")
        return False
    except Exception as e:
        print(f"  ❌ Erreur : {e}")
        return False


def sync_session_initiale():
    try:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/sessions",
            headers=_headers(),
            json={
                "session_date": datetime.utcnow().isoformat() + "Z",
                "stats": json.dumps({"total": 14, "a_contacter": 14}),
                "summary": "Initialisation — 14 établissements chargés depuis la config",
            },
            timeout=10,
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


def main():
    print(f"\n{SEP}")
    print(f"  INITIALISATION SUPABASE — {CANDIDAT['nom_complet']}")
    print(SEP)

    # Vérification config
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("\n  ❌ Supabase non configuré dans .env")
        print("     Vérifiez SUPABASE_URL et SUPABASE_SERVICE_KEY")
        sys.exit(1)

    print(f"\n  📡 URL Supabase : {SUPABASE_URL}")
    print(f"  🔑 Clé service  : {SUPABASE_SERVICE_KEY[:20]}…\n")

    # Construction du payload
    payload = construire_payload()
    print(f"  📋 {len(payload)} établissements à envoyer :\n")
    for p in payload:
        print(f"     • {p['etablissement']} ({p['ville']}) — {p['formation_id']}")

    print(f"\n  Envoi vers Supabase...")

    if sync_schools(payload):
        print(f"  ✅ {len(payload)} établissements synchronisés dans Supabase !")
        sync_session_initiale()
        print(f"\n  📱 L'application mobile affiche maintenant les données.")
        print(f"  🌐 Ouvrez l'application pour vérifier.")
    else:
        print("\n  ❌ La synchronisation a échoué.")
        print("     Vérifiez que :")
        print("     1. Vous avez une connexion internet")
        print("     2. La table 'schools_tracking' existe dans Supabase")
        print("        → Exécutez le script SQL : scripts/supabase_schema.sql")
        print("        → Dashboard Supabase : https://supabase.com/dashboard")

    print(f"\n{SEP}\n")


if __name__ == "__main__":
    main()
