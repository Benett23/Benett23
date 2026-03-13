#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║         LANCEUR RAPIDE — Système PTP Chris Gnabroyou         ║
╚══════════════════════════════════════════════════════════════╝

Utilisation :
  python lancer.py          → Menu interactif
  python lancer.py docs     → Générer les documents (rapide, sans Claude)
  python lancer.py emails   → Générer les brouillons d'emails (rapide, sans Claude)
  python lancer.py sync     → Synchroniser l'appli mobile
  python lancer.py full     → Workflow complet (avec Claude, ~20 min)
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# ── Setup ──────────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

from ptp_system.config import CANDIDAT, FORMATIONS_CIBLES
from ptp_system.tools.document_tools import generer_tous_documents
from ptp_system.tools.gmail_tools import sauvegarder_brouillon_local


# ── Génération emails sans Claude ──────────────────────────────────────────────

def _template_email_html(etab: str, ville: str, formation: str, email_dest: str, date_limite: str) -> tuple[str, str]:
    """Génère un email de prise de contact professionnel depuis un template."""
    formation_courte = formation[:50] + ("…" if len(formation) > 50 else "")

    sujet = f"Candidature LP {formation_courte} — Rentrée septembre 2026 (PTP)"

    corps_html = f"""<p>Madame, Monsieur,</p>

<p>Technicien ascensoriste depuis 4 ans, titulaire d'un <strong>BTS Électrotechnique</strong> et
d'un Bac STI2D, je me permets de vous contacter dans le cadre d'un <strong>Projet de Transition
Professionnelle (PTP)</strong> financé par <em>Transitions Pro</em>.</p>

<p>Je souhaite intégrer la <strong>{formation}</strong> à <strong>{etab}</strong> ({ville})
pour la rentrée de <strong>septembre 2026</strong>, afin de me spécialiser en automatismes
industriels, IoT et réseaux industriels.</p>

<p>Mon expérience terrain (câblage, variateurs de fréquence, schémas électriques, API,
diagnostic électrotechnique) me permettrait d'aborder cette formation avec une maturité
professionnelle concrète, valorisant à la fois les aspects théoriques et pratiques.</p>

<p>Dans ce cadre, je souhaiterais :</p>
<ul>
  <li>Confirmer la recevabilité de mon dossier (BTS Électrotechnique → LP visée)</li>
  <li>Obtenir les modalités et critères de candidature pour la rentrée 2026</li>
  <li>Connaître les éventuelles dates d'entretien ou d'examen d'entrée</li>
</ul>

<p>Le financement PTP couvre les frais pédagogiques et maintient mon salaire — ma démarche est
donc solide et sécurisée sur le plan financier.
{f'<br><em>(Date limite candidature indiquée : {date_limite})</em>' if date_limite and date_limite != 'N/A' else ''}</p>

<p>Je reste disponible pour un entretien téléphonique ou présentiel à votre convenance,
et me tiens à disposition pour tout document complémentaire.</p>

<p>Dans l'attente de votre retour, je vous adresse mes meilleures salutations.</p>

<p><br><strong>Chris Gnabroyou</strong><br>
Technicien ascensoriste | Candidat {formation_courte}<br>
Email : Gnabroyouchris.étudiant@gmail.com<br>
Tél : [à compléter]<br>
Localisation : France (mobilité nationale)
</p>"""

    corps_texte = (
        f"Madame, Monsieur,\n\n"
        f"Technicien ascensoriste depuis 4 ans (BTS Électrotechnique + Bac STI2D), "
        f"je candidate en {formation} à {etab} dans le cadre d'un PTP.\n\n"
        f"Mon expérience terrain en électrotechnique me permettrait d'aborder cette formation "
        f"avec maturité. Le financement PTP couvre les frais pédagogiques et maintient mon salaire.\n\n"
        f"Pourriez-vous me confirmer les modalités de candidature pour la rentrée 2026 ?\n\n"
        f"Cordialement,\nChris Gnabroyou\nGnabroyouchris.étudiant@gmail.com"
    )

    return sujet, corps_html, corps_texte


def generer_emails_direct():
    """Génère les brouillons d'emails sans Claude — utilise un template professionnel."""
    print("\n✉️  Génération des brouillons d'emails...")
    print("   (Mode direct — aucune IA requise)\n")

    resultats = []
    total = sum(len(f["etablissements"]) for f in FORMATIONS_CIBLES)
    n = 0

    for formation in FORMATIONS_CIBLES:
        for etab in formation["etablissements"]:
            n += 1
            nom = etab["nom"]
            ville = etab["ville"]
            email_dest = etab.get("email_contact", f"secretariat@{nom.lower().replace(' ', '-')}.fr")
            date_limite = etab.get("date_limite", "")

            sujet, corps_html, corps_texte = _template_email_html(
                etab=nom, ville=ville,
                formation=formation["nom"],
                email_dest=email_dest,
                date_limite=date_limite,
            )

            nom_fichier = f"email_{nom.replace(' ', '_')[:25]}_contact"
            result = sauvegarder_brouillon_local(
                destinataire=email_dest,
                sujet=sujet,
                corps_html=corps_html,
                corps_texte=corps_texte,
                nom_fichier=nom_fichier,
            )

            status = "✅" if result["success"] else "❌"
            print(f"  {status} [{n}/{total}] {nom} ({ville})")
            if result["success"]:
                for p in result.get("paths", []):
                    print(f"       → {p}")
            resultats.append(result)

    ok = sum(1 for r in resultats if r["success"])
    print(f"\n  📂 {ok}/{total} brouillons créés dans : outputs/drafts/")
    print("  💡 Ouvrez les fichiers .html pour relire et personnaliser avant envoi.\n")
    return resultats


def generer_documents_direct():
    """Génère tous les documents sans Claude."""
    print("\n📄 Génération des documents...")
    print("   (Mode direct — aucune IA requise)\n")
    try:
        paths = generer_tous_documents()
        print("  ✅ Documents créés :")
        for nom, path in paths.items():
            print(f"     📄 {path}")
        print()
        return paths
    except Exception as e:
        print(f"  ❌ Erreur : {e}")
        return {}


def synchroniser_mobile():
    """Synchronise les données avec l'app mobile (Supabase)."""
    print("\n📡 Synchronisation avec l'application mobile...")
    try:
        from ptp_system.tools.supabase_sync import sync_complet
        from ptp_system.agents.school_tracker_agent import SchoolTrackerAgent
        tracker = SchoolTrackerAgent()
        stats = tracker.get_stats()
        sync_complet(ecoles=tracker.ecoles, stats=stats, notifier=False)
        print("  ✅ Synchronisation terminée\n")
    except Exception as e:
        print(f"  ❌ Erreur sync : {e}\n")


def lancer_complet():
    """Lance le workflow complet avec Claude (long)."""
    print("\n🚀 Lancement du workflow complet avec Claude AI...")
    print("   ⚠️  Cette opération peut prendre 20-40 minutes.")
    print("   Le programme génère les documents + rédige les emails avec l'IA.\n")
    confirm = input("   Confirmer ? (o/N) : ").strip().lower()
    if confirm != 'o':
        print("  Annulé.\n")
        return
    os.system(f"{sys.executable} main_ptp.py --mode full")


def menu():
    """Menu interactif principal."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║         SYSTÈME PTP — {CANDIDAT['nom_complet']:<35}║
║         {datetime.now().strftime('%d/%m/%Y à %H:%M'):<51}║
╚══════════════════════════════════════════════════════════════╝

  Que souhaitez-vous faire ?

  [1] 📄  Générer les documents  (lettres, tableaux Excel)       ~30 sec
  [2] ✉️   Rédiger les brouillons d'emails pour tous les IUT      ~1 min
  [3] 📡  Synchroniser l'application mobile                      ~10 sec
  [4] 🚀  Workflow complet avec Claude AI (tous les modes)       ~30 min
  [Q] 🚪  Quitter
""")

    choix = input("  Votre choix : ").strip().lower()

    if choix == '1':
        generer_documents_direct()
    elif choix == '2':
        generer_emails_direct()
    elif choix == '3':
        synchroniser_mobile()
    elif choix == '4':
        lancer_complet()
    elif choix == 'q':
        print("\n  Au revoir !\n")
        sys.exit(0)
    else:
        print(f"\n  ❓ Choix '{choix}' non reconnu.\n")

    # Retour au menu après l'action
    input("  Appuyez sur Entrée pour revenir au menu...")
    menu()


# ── Point d'entrée ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "docs":
            generer_documents_direct()
        elif cmd == "emails":
            generer_emails_direct()
        elif cmd == "sync":
            synchroniser_mobile()
        elif cmd == "full":
            lancer_complet()
        else:
            print(f"Commande inconnue : {cmd}")
            print("Utilisation : python lancer.py [docs|emails|sync|full]")
    else:
        menu()
