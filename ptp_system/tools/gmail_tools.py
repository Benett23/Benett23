"""
Outils Gmail/SMTP pour envoyer des emails et sauvegarder des brouillons.
"""

import os
import smtplib
import email.utils
import imaplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
DEBRIEF_EMAIL_TO = os.getenv("DEBRIEF_EMAIL_TO", GMAIL_USER)
DRAFTS_DIR = os.getenv("DRAFTS_DIR", "outputs/drafts")


def _is_gmail_configured() -> bool:
    return bool(GMAIL_USER and GMAIL_APP_PASSWORD)


# ---------------------------------------------------------------------------
# Envoi d'email (SMTP)
# ---------------------------------------------------------------------------

def envoyer_email(
    destinataire: str,
    sujet: str,
    corps_html: str,
    corps_texte: str = "",
    pieces_jointes: list[str] = None,
) -> dict:
    """
    Envoie un email via Gmail SMTP.
    Retourne {"success": bool, "message": str}.
    """
    if not _is_gmail_configured():
        return {
            "success": False,
            "message": "Gmail non configuré. Veuillez renseigner GMAIL_USER et GMAIL_APP_PASSWORD dans .env",
        }

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = GMAIL_USER
        msg["To"] = destinataire
        msg["Subject"] = sujet
        msg["Date"] = email.utils.formatdate(localtime=True)

        if corps_texte:
            msg.attach(MIMEText(corps_texte, "plain", "utf-8"))
        msg.attach(MIMEText(corps_html, "html", "utf-8"))

        # Pièces jointes
        if pieces_jointes:
            for filepath in pieces_jointes:
                if os.path.isfile(filepath):
                    with open(filepath, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{os.path.basename(filepath)}"',
                    )
                    msg.attach(part)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, destinataire, msg.as_string())

        return {"success": True, "message": f"Email envoyé à {destinataire}"}

    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": (
                "Erreur d'authentification Gmail. Vérifiez que :\n"
                "1. La double authentification est activée sur votre compte Google\n"
                "2. Vous utilisez un mot de passe d'application (pas votre vrai mot de passe)\n"
                "   Créer sur : https://myaccount.google.com/apppasswords"
            ),
        }
    except Exception as e:
        return {"success": False, "message": f"Erreur envoi email : {str(e)}"}


# ---------------------------------------------------------------------------
# Sauvegarde de brouillon dans Gmail (IMAP APPEND)
# ---------------------------------------------------------------------------

def sauvegarder_brouillon_gmail(
    destinataire: str,
    sujet: str,
    corps_html: str,
    corps_texte: str = "",
) -> dict:
    """
    Sauvegarde un brouillon directement dans le dossier Brouillons de Gmail via IMAP.
    Retourne {"success": bool, "message": str}.
    """
    if not _is_gmail_configured():
        return {
            "success": False,
            "message": "Gmail non configuré (GMAIL_USER / GMAIL_APP_PASSWORD manquants dans .env)",
        }

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = GMAIL_USER
        msg["To"] = destinataire
        msg["Subject"] = sujet
        msg["Date"] = email.utils.formatdate(localtime=True)

        if corps_texte:
            msg.attach(MIMEText(corps_texte, "plain", "utf-8"))
        msg.attach(MIMEText(corps_html, "html", "utf-8"))

        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(GMAIL_USER, GMAIL_APP_PASSWORD)

        # Chercher le dossier Brouillons (peut s'appeler [Gmail]/Drafts ou [Gmail]/Brouillons)
        result, folders = imap.list()
        drafts_folder = "[Gmail]/Drafts"
        for folder_info in folders:
            decoded = folder_info.decode()
            if "Drafts" in decoded or "Brouillons" in decoded:
                # Extraire le nom du dossier
                parts = decoded.split('"')
                if len(parts) >= 3:
                    drafts_folder = parts[-2]
                break

        imap.append(
            drafts_folder,
            "\\Draft",
            imaplib.Time2Internaldate(datetime.now().timestamp()),
            msg.as_bytes(),
        )
        imap.logout()

        return {
            "success": True,
            "message": f"Brouillon créé dans Gmail pour : {destinataire} | Sujet : {sujet}",
        }

    except imaplib.IMAP4.error as e:
        return {
            "success": False,
            "message": f"Erreur IMAP Gmail : {str(e)}. Vérifiez l'accès IMAP dans les paramètres Gmail.",
        }
    except Exception as e:
        return {"success": False, "message": f"Erreur création brouillon Gmail : {str(e)}"}


# ---------------------------------------------------------------------------
# Sauvegarde locale d'un brouillon (.eml + .html)
# ---------------------------------------------------------------------------

def sauvegarder_brouillon_local(
    destinataire: str,
    sujet: str,
    corps_html: str,
    corps_texte: str = "",
    nom_fichier: str = None,
) -> dict:
    """
    Sauvegarde un brouillon localement en .html et .eml.
    Retourne {"success": bool, "message": str, "paths": list}.
    """
    os.makedirs(DRAFTS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_sujet = "".join(c if c.isalnum() or c in "-_ " else "_" for c in sujet[:40])
    base_name = nom_fichier or f"{timestamp}_{safe_sujet}"

    paths = []

    # Sauvegarde HTML (lisible facilement)
    html_path = os.path.join(DRAFTS_DIR, f"{base_name}.html")
    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{sujet}</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; }}
.header {{ background: #1F497D; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
.meta {{ color: #666; font-size: 0.9em; margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
</style>
</head>
<body>
<div class="header"><h2>📧 Brouillon email PTP</h2></div>
<div class="meta">
  <strong>À :</strong> {destinataire}<br>
  <strong>Sujet :</strong> {sujet}<br>
  <strong>Créé le :</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M')}
</div>
{corps_html}
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    paths.append(html_path)

    # Sauvegarde .eml (importable dans Gmail / Thunderbird)
    eml_path = os.path.join(DRAFTS_DIR, f"{base_name}.eml")
    msg = MIMEMultipart("alternative")
    msg["From"] = GMAIL_USER or "chris.gnabroyou@gmail.com"
    msg["To"] = destinataire
    msg["Subject"] = sujet
    msg["Date"] = email.utils.formatdate(localtime=True)

    if corps_texte:
        msg.attach(MIMEText(corps_texte, "plain", "utf-8"))
    msg.attach(MIMEText(corps_html, "html", "utf-8"))

    with open(eml_path, "w", encoding="utf-8") as f:
        f.write(msg.as_string())
    paths.append(eml_path)

    return {
        "success": True,
        "message": f"Brouillon sauvegardé localement : {html_path}",
        "paths": paths,
    }


# ---------------------------------------------------------------------------
# Sauvegarde brouillon (local + Gmail si configuré)
# ---------------------------------------------------------------------------

def sauvegarder_brouillon(
    destinataire: str,
    sujet: str,
    corps_html: str,
    corps_texte: str = "",
    nom_fichier: str = None,
) -> dict:
    """
    Sauvegarde un brouillon localement ET dans Gmail si configuré.
    """
    # Toujours sauvegarder en local
    local_result = sauvegarder_brouillon_local(
        destinataire, sujet, corps_html, corps_texte, nom_fichier
    )

    # Tenter Gmail si configuré
    gmail_result = None
    if _is_gmail_configured():
        gmail_result = sauvegarder_brouillon_gmail(
            destinataire, sujet, corps_html, corps_texte
        )

    return {
        "success": local_result["success"],
        "local": local_result,
        "gmail": gmail_result,
        "message": (
            f"{local_result['message']}"
            + (f" | Gmail : {gmail_result['message']}" if gmail_result else " | Gmail non configuré")
        ),
    }


# ---------------------------------------------------------------------------
# Envoi du débrief
# ---------------------------------------------------------------------------

def envoyer_debrief(
    sujet: str,
    corps_html: str,
    corps_texte: str = "",
    pieces_jointes: list[str] = None,
) -> dict:
    """
    Envoie l'email de débrief à l'adresse configurée dans DEBRIEF_EMAIL_TO.
    """
    return envoyer_email(
        destinataire=DEBRIEF_EMAIL_TO or GMAIL_USER,
        sujet=sujet,
        corps_html=corps_html,
        corps_texte=corps_texte,
        pieces_jointes=pieces_jointes,
    )
