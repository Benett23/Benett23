#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║         SYSTÈME PTP MULTI-AGENTS — Chris Gnabroyou           ║
║         Projet de Transition Professionnelle                  ║
║         Automatismes | IoT | Énergie industrielle             ║
╚══════════════════════════════════════════════════════════════╝

Utilisation :
  python main_ptp.py                        → Workflow complet
  python main_ptp.py --mode docs            → Génération documents uniquement
  python main_ptp.py --mode contact         → Recherche + emails uniquement
  python main_ptp.py --mode brief           → Brief journalier
  python main_ptp.py --mode dashboard       → Régénérer dashboard uniquement
  python main_ptp.py --formations lpaii     → Filtrer par formation
  python main_ptp.py --max-etab 3           → Limiter à N établissements

Prérequis :
  pip install -r requirements.txt
  cp .env.example .env
  # Pas de clé API requise — utilise claude CLI (abonnement Claude Code)
"""

import argparse
import os
import sys
from pathlib import Path

# Vérifier que le fichier .env existe
env_file = Path(".env")
if not env_file.exists():
    env_example = Path(".env.example")
    if env_example.exists():
        print("⚠️  Fichier .env manquant. Création depuis .env.example...")
        env_file.write_text(env_example.read_text())
        print("   → Éditez .env si nécessaire, puis relancez.\n")
        sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

# Vérifier que claude CLI est disponible (pas de clé API requise)
from ptp_system.core.claude_cli import verifier_cli_disponible
if not verifier_cli_disponible():
    print("\n❌ La commande `claude` est introuvable ou non authentifiée.")
    print("   1. Installez Claude Code : npm install -g @anthropic-ai/claude-code")
    print("   2. Authentifiez-vous     : claude auth login")
    print("   (Aucune clé API nécessaire — utilise votre abonnement Claude Code)")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Système PTP Multi-Agents — Chris Gnabroyou",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode",
        choices=["full", "docs", "contact", "brief", "dashboard"],
        default="full",
        help="Mode d'exécution (défaut: full)",
    )
    parser.add_argument(
        "--formations",
        nargs="+",
        choices=["lpaii", "sarii", "ia_industrie", "cyber_ot", "elec_puissance"],
        help="Filtrer par ID(s) de formation (défaut: toutes)",
    )
    parser.add_argument(
        "--max-etab",
        type=int,
        default=None,
        help="Limiter le nombre d'établissements traités (utile pour les tests)",
    )
    parser.add_argument(
        "--liste-formations",
        action="store_true",
        help="Afficher la liste des formations et établissements configurés",
    )

    args = parser.parse_args()

    if args.liste_formations:
        _afficher_formations()
        return

    # Import ici pour éviter les imports inutiles si --liste-formations
    from ptp_system.agents.orchestrator import PTPOrchestrator

    orchestrator = PTPOrchestrator()

    if args.mode == "docs":
        orchestrator.run_document_generation()

    elif args.mode == "contact":
        orchestrator.run_school_contact(
            formations_ids=args.formations,
            max_etablissements=args.max_etab,
        )

    elif args.mode == "brief":
        orchestrator.run_daily_brief()

    elif args.mode == "dashboard":
        # Régénère uniquement le dashboard sans appeler Claude
        from ptp_system.agents.school_tracker_agent import SchoolTrackerAgent
        from ptp_system.tools.dashboard_tools import generer_tout_dashboard
        tracker = SchoolTrackerAgent()
        paths = generer_tout_dashboard(
            ecoles=tracker.ecoles,
            stats_ecoles=tracker.get_stats(),
        )
        print(f"✅ Dashboard mis à jour :")
        print(f"   🏠 {paths['index']}")
        print(f"   🏫 {paths['ecoles']}")

    else:  # full
        orchestrator.run_full(
            formations_ids=args.formations,
            max_etablissements=args.max_etab,
        )


def _afficher_formations():
    """Affiche la liste des formations et établissements configurés."""
    from ptp_system.config import FORMATIONS_CIBLES, CANDIDAT

    print(f"\n{'='*65}")
    print(f"  Formations configurées pour {CANDIDAT['nom_complet']}")
    print(f"{'='*65}")

    for f in FORMATIONS_CIBLES:
        print(f"\n  [{f['id']}] ⭐ Priorité {f['priorite']} — {f['nom']}")
        print(f"       Niveau : {f['niveau']} | Durée : {f['duree']}")
        print(f"       Établissements ({len(f['etablissements'])}) :")
        for etab in f["etablissements"]:
            print(f"         • {etab['nom']} ({etab['ville']}) — limite : {etab.get('date_limite', 'N/A')}")

    print(f"\n{'='*65}\n")


if __name__ == "__main__":
    main()
