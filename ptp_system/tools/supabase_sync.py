"""
Synchronisation des données PTP vers Supabase + notifications OneSignal.

Variables d'environnement requises (.env) :
  SUPABASE_URL          ex: https://xxxx.supabase.co
  SUPABASE_SERVICE_KEY  clé service_role (écriture, jamais dans le navigateur)
  SUPABASE_ANON_KEY     clé anon (lecture, utilisée dans le PWA)
  ONESIGNAL_APP_ID      ID de l'app OneSignal
  ONESIGNAL_REST_API_KEY  clé REST OneSignal (serveur)
  VERCEL_URL            ex: https://ptp-chris.vercel.app
"""

import json
import os
from datetime import datetime

import requests


# ── Config ──────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID", "")
ONESIGNAL_REST_KEY = os.getenv("ONESIGNAL_REST_API_KEY", "")
VERCEL_URL = os.getenv("VERCEL_URL", "https://ptp.vercel.app")


def _headers_write() -> dict:
    """En-têtes Supabase avec clé service (écriture autorisée)."""
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }


def _configured() -> bool:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("  ⚠️  Supabase non configuré → données non synchronisées sur mobile")
        print("      Ajoutez SUPABASE_URL et SUPABASE_SERVICE_KEY dans .env")
        return False
    return True


# ── Écoles ──────────────────────────────────────────────────────────────────

def sync_ecoles(ecoles: list[dict]) -> bool:
    """Upsert de toutes les écoles dans la table `schools_tracking`."""
    if not _configured():
        return False
    try:
        payload = [
            {
                "id": e.get("id", e["etablissement"].replace(" ", "_").lower()[:20]),
                "etablissement": e["etablissement"],
                "ville": e["ville"],
                "formation": e["formation"],
                "formation_id": e.get("formation_id", ""),
                "formation_priorite": e.get("formation_priorite", 0),
                "statut": e.get("statut", "À contacter"),
                "email_contact": e.get("email_contact", ""),
                "lien_candidature": e.get("lien_candidature", e.get("url", "")),
                "date_limite": e.get("date_limite", ""),
                "score_adequation": e.get("score_adequation"),
                "notes": e.get("notes", ""),
                "date_premier_contact": e.get("date_premier_contact"),
                "date_derniere_action": e.get("date_derniere_action"),
                "nb_emails_envoyes": e.get("nb_emails_envoyes", 0),
                "data_full": json.dumps(e, ensure_ascii=False),
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }
            for e in ecoles
        ]
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/schools_tracking",
            headers=_headers_write(),
            json=payload,
            timeout=20,
        )
        if resp.status_code in (200, 201):
            print(f"  ✅ Supabase : {len(ecoles)} écoles synchronisées")
            return True
        print(f"  ⚠️  Supabase écoles erreur {resp.status_code}: {resp.text[:300]}")
        return False
    except Exception as exc:
        print(f"  ⚠️  Supabase sync écoles : {exc}")
        return False


# ── Sessions ─────────────────────────────────────────────────────────────────

def sync_session(stats: dict, summary: str = "") -> bool:
    """Insère une entrée de session dans la table `sessions`."""
    if not _configured():
        return False
    try:
        payload = {
            "session_date": datetime.utcnow().isoformat() + "Z",
            "stats": json.dumps(stats, ensure_ascii=False),
            "summary": summary,
        }
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/sessions",
            headers=_headers_write(),
            json=payload,
            timeout=10,
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


# ── OneSignal push notification ──────────────────────────────────────────────

def envoyer_notification_push(
    titre: str,
    message: str,
    url_cible: str = "",
    segment: str = "All",
    bouton_label: str = "",
    bouton_url: str = "",
) -> bool:
    """Envoie une notification push iOS via OneSignal (gratuit)."""
    if not ONESIGNAL_APP_ID or not ONESIGNAL_REST_KEY:
        print("  ⚠️  OneSignal non configuré → pas de notification push")
        print("      Ajoutez ONESIGNAL_APP_ID et ONESIGNAL_REST_API_KEY dans .env")
        return False
    try:
        payload: dict = {
            "app_id": ONESIGNAL_APP_ID,
            "included_segments": [segment],
            "headings": {"fr": titre, "en": titre},
            "contents": {"fr": message, "en": message},
            "url": url_cible or VERCEL_URL,
            "ios_badgeType": "Increase",
            "ios_badgeCount": 1,
            "ios_sound": "default",
            "priority": 10,
        }
        if bouton_label and bouton_url:
            payload["buttons"] = [
                {"id": "action1", "text": bouton_label, "url": bouton_url}
            ]
        resp = requests.post(
            "https://onesignal.com/api/v1/notifications",
            headers={
                "Authorization": f"Basic {ONESIGNAL_REST_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            nb = data.get("recipients", "?")
            print(f"  ✅ Notification push envoyée à {nb} appareil(s) : {titre}")
            return True
        print(f"  ⚠️  OneSignal erreur {resp.status_code}: {resp.text[:300]}")
        return False
    except Exception as exc:
        print(f"  ⚠️  Notification push : {exc}")
        return False


# ── Sync complète ─────────────────────────────────────────────────────────────

def sync_complet(
    ecoles: list[dict],
    stats: dict,
    notifier: bool = True,
    titre_notif: str = "",
    message_notif: str = "",
) -> dict:
    """
    Synchronise tout en une fois :
    - Écoles vers Supabase
    - Session enregistrée
    - Notification push si demandée

    Retourne un dict résumant les opérations.
    """
    resultats: dict = {
        "ecoles_sync": False,
        "session_sync": False,
        "notification": False,
    }

    resultats["ecoles_sync"] = sync_ecoles(ecoles)

    nb_brouillons = stats.get("brouillon_pret", 0)
    nb_contactes = stats.get("contacte", 0)
    summary = (
        f"{nb_contactes} établissements contactés, "
        f"{nb_brouillons} brouillons en attente d'envoi"
    )
    resultats["session_sync"] = sync_session(stats, summary)

    if notifier:
        titre = titre_notif or "☀️ Brief PTP"
        if nb_brouillons > 0:
            message = message_notif or (
                f"📨 {nb_brouillons} email(s) prêt(s) à envoyer — "
                f"✅ {nb_contactes} contacté(s)"
            )
            bouton_label = f"Voir {nb_brouillons} brouillon(s)"
            bouton_url = f"{VERCEL_URL}/ecoles.html"
        else:
            message = message_notif or (
                f"✅ {nb_contactes} contacté(s) · "
                f"📬 {stats.get('reponse_recue', 0)} réponse(s)"
            )
            bouton_label = "Tableau de bord"
            bouton_url = VERCEL_URL

        resultats["notification"] = envoyer_notification_push(
            titre=titre,
            message=message,
            url_cible=VERCEL_URL,
            bouton_label=bouton_label,
            bouton_url=bouton_url,
        )

    return resultats
