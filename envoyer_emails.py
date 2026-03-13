#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║     ENVOI DES EMAILS — Système PTP Chris Gnabroyou           ║
╚══════════════════════════════════════════════════════════════╝

Ce script lit les brouillons dans outputs/drafts/,
affiche la liste des établissements et envoie les emails via Gmail.

Utilisation :
  python envoyer_emails.py          → Menu interactif
  python envoyer_emails.py --liste  → Afficher la liste sans envoyer
  python envoyer_emails.py --tout   → Envoyer tous les emails (avec confirmation)
"""

import os
import sys
import re
import smtplib
import email.utils
from pathlib import Path
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

from ptp_system.config import FORMATIONS_CIBLES, CANDIDAT

# ── Config Gmail ───────────────────────────────────────────────────────────────
GMAIL_USER     = os.getenv("GMAIL_USER", "")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
DRAFTS_DIR     = Path(os.getenv("DRAFTS_DIR", "outputs/drafts"))
LOG_DIR        = Path(os.getenv("LOGS_DIR", "outputs/logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE       = LOG_DIR / "emails_envoyes.log"

SEP = "─" * 62


def _couleur(texte, code):
    return f"\033[{code}m{texte}\033[0m"

def ok(t):  return _couleur(t, "32")
def err(t): return _couleur(t, "31")
def gris(t):return _couleur(t, "90")
def bold(t):return _couleur(t, "1")


# ── Construire la liste complète des établissements ────────────────────────────

def construire_liste() -> list[dict]:
    """Retourne tous les établissements avec leurs infos d'email."""
    etablissements = []
    num = 0
    for formation in FORMATIONS_CIBLES:
        for etab in formation["etablissements"]:
            # Chercher le fichier brouillon correspondant
            safe = etab["nom"].replace(" ", "_")[:25]
            draft_html = DRAFTS_DIR / f"email_{safe}_contact.html"
            draft_eml  = DRAFTS_DIR / f"email_{safe}_contact.eml"

            # Lire le sujet depuis le HTML
            sujet = None
            corps_html = None
            if draft_html.exists():
                contenu = draft_html.read_text(encoding="utf-8")
                m = re.search(r'<strong>Sujet\s*:</strong>\s*(.*?)<br', contenu)
                if m:
                    sujet = m.group(1).strip()
                # Extraire le corps (tout après la balise .meta fermante)
                corps_html = _extraire_corps(contenu)

            num += 1
            etablissements.append({
                "num":        num,
                "nom":        etab["nom"],
                "ville":      etab["ville"],
                "formation":  formation["nom"],
                "email":      etab.get("email_contact", ""),
                "date_limite":etab.get("date_limite", "N/A"),
                "sujet":      sujet or f"Candidature LP {formation['nom'][:40]}… — Rentrée sept. 2026 (PTP)",
                "draft_html": draft_html if draft_html.exists() else None,
                "draft_eml":  draft_eml  if draft_eml.exists()  else None,
                "corps_html": corps_html,
                "envoye":     _deja_envoye(etab["nom"]),
            })
    return etablissements


def _extraire_corps(html_complet: str) -> str:
    """Extrait le corps de l'email depuis le HTML du brouillon."""
    # Supprimer le wrapper header/meta du brouillon, garder juste le corps de l'email
    m = re.search(r'</div>\s*\n(.+)', html_complet, re.DOTALL)
    if m:
        return m.group(1).strip()
    return html_complet


def _deja_envoye(nom_etab: str) -> bool:
    if not LOG_FILE.exists():
        return False
    return nom_etab in LOG_FILE.read_text(encoding="utf-8")


def _logger_envoi(etab: dict):
    ligne = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {etab['nom']} | {etab['email']} | {etab['sujet']}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(ligne)


# ── Affichage ──────────────────────────────────────────────────────────────────

def afficher_liste(etablissements: list[dict]):
    print(f"\n{bold('LISTE DES ÉTABLISSEMENTS À CONTACTER')}")
    print(SEP)
    print(f"  {'N°':>2}  {'Établissement':<28}  {'Ville':<12}  {'Email':30}  {'Statut'}")
    print(SEP)

    for e in etablissements:
        statut = ok("✅ Envoyé") if e["envoye"] else gris("📝 À envoyer")
        draft  = "" if e["draft_html"] else err(" ⚠️ no draft")
        print(f"  {e['num']:>2}  {e['nom']:<28}  {e['ville']:<12}  {e['email']:<30}  {statut}{draft}")

    print(SEP)
    total   = len(etablissements)
    envoyes = sum(1 for e in etablissements if e["envoye"])
    print(f"  Total : {total} établissements | {envoyes} envoyés | {total - envoyes} restants\n")


def apercu_email(e: dict):
    print(f"\n{SEP}")
    print(f"  {bold('APERÇU EMAIL')}")
    print(f"  À      : {e['email']}")
    print(f"  Sujet  : {e['sujet']}")
    print(f"  Brouillon : {e['draft_html'] or 'non trouvé'}")
    print(SEP)
    if e["draft_html"]:
        print(f"  💡 Ouvrez '{e['draft_html']}' dans un navigateur pour relire le contenu.")
    print()


# ── Envoi Gmail ────────────────────────────────────────────────────────────────

def tester_connexion_gmail() -> bool:
    if not GMAIL_USER or not GMAIL_PASSWORD:
        print(err("❌ Gmail non configuré dans .env (GMAIL_USER / GMAIL_APP_PASSWORD)"))
        return False
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as s:
            s.ehlo()
            s.starttls()
            s.login(GMAIL_USER, GMAIL_PASSWORD)
        print(ok(f"✅ Connexion Gmail OK ({GMAIL_USER})"))
        return True
    except Exception as e:
        print(err(f"❌ Impossible de se connecter à Gmail : {e}"))
        print("   → Vérifiez que vous avez internet et que le mot de passe d'application est valide.")
        return False


def envoyer_email(e: dict) -> bool:
    """Envoie un email pour un établissement. Retourne True si succès."""
    if not e["email"]:
        print(err(f"  ❌ Pas d'adresse email pour {e['nom']}"))
        return False

    corps_html = e.get("corps_html") or f"<p>Bonjour,<br>Candidature LP PTP septembre 2026.<br>Chris Gnabroyou</p>"

    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = GMAIL_USER
        msg["To"]      = e["email"]
        msg["Subject"] = e["sujet"]
        msg["Date"]    = email.utils.formatdate(localtime=True)
        msg["Reply-To"]= GMAIL_USER

        corps_texte = re.sub(r'<[^>]+>', '', corps_html).strip()
        msg.attach(MIMEText(corps_texte, "plain", "utf-8"))
        msg.attach(MIMEText(corps_html,  "html",  "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, e["email"], msg.as_string())

        _logger_envoi(e)
        print(ok(f"  ✅ Email envoyé → {e['email']}"))
        return True

    except smtplib.SMTPAuthenticationError:
        print(err("  ❌ Erreur d'authentification Gmail."))
        print("     Vérifiez le mot de passe d'application sur : myaccount.google.com/apppasswords")
        return False
    except Exception as ex:
        print(err(f"  ❌ Erreur : {ex}"))
        return False


# ── Menus ──────────────────────────────────────────────────────────────────────

def menu_envoi_un(etablissements: list[dict]):
    """Choisir un établissement et envoyer l'email."""
    afficher_liste(etablissements)
    choix = input("  Numéro de l'établissement à contacter (ou Q pour annuler) : ").strip()
    if choix.lower() == 'q':
        return

    try:
        num = int(choix)
        e = next(x for x in etablissements if x["num"] == num)
    except (ValueError, StopIteration):
        print(err(f"  Numéro invalide : {choix}"))
        return

    apercu_email(e)
    if e["envoye"]:
        print(f"  ⚠️  Un email a déjà été envoyé à {e['nom']}.")
        confirm = input("  Envoyer quand même ? (o/N) : ").strip().lower()
        if confirm != 'o':
            return

    confirm = input(f"  Confirmer l'envoi à {e['email']} ? (o/N) : ").strip().lower()
    if confirm == 'o':
        envoyer_email(e)
    else:
        print("  Annulé.")


def menu_envoi_tous(etablissements: list[dict]):
    """Envoyer tous les emails non encore envoyés."""
    non_envoyes = [e for e in etablissements if not e["envoye"]]
    if not non_envoyes:
        print(ok("\n  ✅ Tous les emails ont déjà été envoyés !"))
        return

    print(f"\n  {len(non_envoyes)} emails à envoyer :")
    for e in non_envoyes:
        print(f"    • {e['nom']} ({e['ville']}) → {e['email']}")

    print()
    confirm = input(f"  Confirmer l'envoi de {len(non_envoyes)} emails ? (o/N) : ").strip().lower()
    if confirm != 'o':
        print("  Annulé.")
        return

    ok_count = 0
    for i, e in enumerate(non_envoyes, 1):
        print(f"\n  [{i}/{len(non_envoyes)}] {e['nom']}…")
        if envoyer_email(e):
            ok_count += 1

    print(f"\n{SEP}")
    print(f"  Résultat : {ok_count}/{len(non_envoyes)} emails envoyés")
    if ok_count < len(non_envoyes):
        print("  Les emails non envoyés peuvent être retentés en relançant ce script.")
    print(SEP)


def menu():
    etablissements = construire_liste()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     ENVOI DES EMAILS — {CANDIDAT['nom_complet']:<35}║
╚══════════════════════════════════════════════════════════════╝

  [1] 📋  Voir la liste des établissements et leurs emails
  [2] ✉️   Envoyer un email (choisir l'établissement)
  [3] 🚀  Envoyer TOUS les emails non encore envoyés
  [4] 🔌  Tester la connexion Gmail
  [Q] 🚪  Quitter
""")

    choix = input("  Votre choix : ").strip().lower()

    if choix == '1':
        afficher_liste(etablissements)
    elif choix == '2':
        if tester_connexion_gmail():
            menu_envoi_un(etablissements)
    elif choix == '3':
        if tester_connexion_gmail():
            menu_envoi_tous(etablissements)
    elif choix == '4':
        tester_connexion_gmail()
    elif choix == 'q':
        print("\n  Au revoir !\n")
        sys.exit(0)
    else:
        print(f"\n  ❓ Choix non reconnu.\n")
        return

    input("\n  Appuyez sur Entrée pour revenir au menu...")
    menu()


# ── Point d'entrée ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--liste" in sys.argv:
        afficher_liste(construire_liste())
    elif "--tout" in sys.argv:
        if tester_connexion_gmail():
            menu_envoi_tous(construire_liste())
    elif "--test" in sys.argv:
        tester_connexion_gmail()
    else:
        menu()
