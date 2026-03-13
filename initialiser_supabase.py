#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║   SYNCHRONISATION SUPABASE — Système PTP Chris Gnabroyou     ║
╚══════════════════════════════════════════════════════════════╝

Synchronise l'état RÉEL du PC (documents générés, emails rédigés)
vers Supabase pour que l'application mobile soit à jour.

Utilisation :
  python initialiser_supabase.py
  ou double-cliquer INITIALISER_APPLI_MOBILE.bat
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

SUPABASE_URL         = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
DRAFTS_DIR           = Path(os.getenv("DRAFTS_DIR", "outputs/drafts"))
OUTPUT_DIR           = Path(os.getenv("OUTPUT_DIR", "outputs/dossier_ptp"))
SEP = "─" * 62


def _headers():
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }


# ── Détection de l'état réel sur le PC ────────────────────────────────────────

def detecter_docs_generes() -> list[str]:
    """Retourne la liste des types de documents déjà générés sur le PC."""
    mapping = {
        "lettre_transitions_pro": "lettre_motivation_transitions_pro.docx",
        "lettre_iut":             "lettre_motivation_iut.docx",
        "planning_ptp":           "planning_demarches_ptp.xlsx",
        "liste_contacts":         "liste_iut_contacts.xlsx",
    }
    return [typ for typ, fichier in mapping.items() if (OUTPUT_DIR / fichier).exists()]


def detecter_brouillon_email(nom_etab: str) -> bool:
    """Vérifie si un brouillon email existe pour cet établissement."""
    safe = nom_etab.replace(" ", "_")[:25]
    return (DRAFTS_DIR / f"email_{safe}_contact.html").exists()


# ── Construction du payload ────────────────────────────────────────────────────

def construire_payload() -> list[dict]:
    """Construit le payload avec le STATUT RÉEL basé sur les fichiers présents."""
    payload = []
    for formation in FORMATIONS_CIBLES:
        for etab in formation["etablissements"]:
            a_brouillon = detecter_brouillon_email(etab["nom"])
            statut = "Brouillon prêt" if a_brouillon else "À contacter"

            payload.append({
                "id": f"{formation['id']}_{etab['nom'].replace(' ', '_').lower()[:20]}",
                "etablissement": etab["nom"],
                "ville": etab["ville"],
                "formation": formation["nom"],
                "formation_id": formation["id"],
                "formation_priorite": formation["priorite"],
                "statut": statut,
                "email_contact": etab.get("email_contact", ""),
                "lien_candidature": etab.get("lien_candidature", etab["url"]),
                "date_limite": etab.get("date_limite", ""),
                "score_adequation": None,
                "notes": "",
                "date_premier_contact": None,
                "date_derniere_action": datetime.utcnow().isoformat() + "Z" if a_brouillon else None,
                "nb_emails_envoyes": 0,
                "telephone": etab.get("telephone", ""),
                "data_full": json.dumps({
                    "universite": etab.get("universite", ""),
                    "region": etab.get("region", ""),
                    "url": etab.get("url", ""),
                    "telephone": etab.get("telephone", ""),
                    "competences_visees": formation.get("competences_visees", []),
                }, ensure_ascii=False),
                "updated_at": datetime.utcnow().isoformat() + "Z",
            })
    return payload


# ── Envoi vers Supabase ────────────────────────────────────────────────────────

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


def sync_session(docs_generes: list[str], nb_brouillons: int) -> bool:
    stats = {
        "total": 14,
        "a_contacter": 14 - nb_brouillons,
        "brouillon_pret": nb_brouillons,
        "contacte": 0,
        "docs_generes": docs_generes,
    }
    try:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/sessions",
            headers=_headers(),
            json={
                "session_date": datetime.utcnow().isoformat() + "Z",
                "stats": json.dumps(stats, ensure_ascii=False),
                "summary": (
                    f"{nb_brouillons} brouillons prêts, "
                    f"{len(docs_generes)} documents générés"
                ),
            },
            timeout=10,
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{SEP}")
    print(f"  SYNCHRONISATION APPLI MOBILE — {CANDIDAT['nom_complet']}")
    print(SEP)

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("\n  ❌ Supabase non configuré dans .env")
        print("     Vérifiez SUPABASE_URL et SUPABASE_SERVICE_KEY")
        sys.exit(1)

    # ── Analyse de l'état réel sur le PC ──────────────────────────────────────
    print("\n  🔍 Analyse des fichiers présents sur le PC...\n")

    docs_generes = detecter_docs_generes()
    payload = construire_payload()
    nb_brouillons = sum(1 for p in payload if p["statut"] == "Brouillon prêt")

    print(f"  📄 Documents générés ({len(docs_generes)}/4) :")
    for d in docs_generes:
        print(f"     ✅ {d}")
    if len(docs_generes) < 4:
        manquants = {"lettre_transitions_pro", "lettre_iut", "planning_ptp", "liste_contacts"} - set(docs_generes)
        for m in manquants:
            print(f"     ⏳ {m}  ← lancez DEMARRER.bat → option 1")

    print(f"\n  ✉️  Brouillons emails ({nb_brouillons}/14) :")
    for p in payload:
        icon = "✅" if p["statut"] == "Brouillon prêt" else "⏳"
        print(f"     {icon} {p['etablissement']} ({p['ville']})")

    # ── Synchronisation ────────────────────────────────────────────────────────
    print(f"\n  📡 Envoi vers Supabase...")

    if sync_schools(payload):
        print(f"  ✅ {len(payload)} établissements synchronisés")
        print(f"     → {nb_brouillons} avec statut 'Brouillon prêt'")
        sync_session(docs_generes, nb_brouillons)
        print(f"  ✅ Session enregistrée")
        print(f"\n  📱 Rafraîchissez l'application mobile pour voir les données à jour.")
    else:
        print("\n  ❌ La synchronisation a échoué.")
        print("     1. Vérifiez votre connexion internet")
        print("     2. Vérifiez que la table 'schools_tracking' existe dans Supabase")

    print(f"\n{SEP}\n")


if __name__ == "__main__":
    main()
