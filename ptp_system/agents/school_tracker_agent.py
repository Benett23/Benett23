"""
Agent de recensement des écoles contactées.
Maintient une base de données JSON persistante et génère un tableau HTML.
"""

import json
import os
from datetime import datetime
from pathlib import Path
import anthropic

from ptp_system.config import CANDIDAT, FORMATIONS_CIBLES


TRACKER_FILE = os.path.join(os.getenv("LOGS_DIR", "outputs/logs"), "schools_tracking.json")
DASHBOARD_DIR = "outputs/dashboard"


# ---------------------------------------------------------------------------
# Structure d'une entrée école
# ---------------------------------------------------------------------------
def _entree_ecole_vide(etab: dict, formation: dict) -> dict:
    return {
        "id": f"{formation['id']}_{etab['nom'].replace(' ', '_').lower()[:20]}",
        "etablissement": etab["nom"],
        "universite": etab.get("universite", ""),
        "ville": etab["ville"],
        "region": etab["region"],
        "formation": formation["nom"],
        "formation_id": formation["id"],
        "formation_priorite": formation["priorite"],
        "url": etab["url"],
        "email_contact": etab.get("email_contact", ""),
        "lien_candidature": etab.get("lien_candidature", etab["url"]),
        "date_limite": etab.get("date_limite", ""),
        # Suivi des contacts
        "statut": "À contacter",
        "date_premier_contact": None,
        "date_derniere_action": None,
        "nb_emails_envoyes": 0,
        "email_sujet": "",
        "email_path": "",
        "reponse_recue": False,
        "date_reponse": None,
        "contenu_reponse": "",
        "decision": "",  # admis | refusé | en attente | sans suite
        "notes": "",
        # Scores (remplis par SchoolResearchAgent)
        "score_adequation": None,
        "points_forts": [],
    }


# ---------------------------------------------------------------------------
# Persistance JSON
# ---------------------------------------------------------------------------

def charger_tracking() -> list[dict]:
    """Charge le fichier de tracking existant ou initialise depuis la config."""
    if os.path.isfile(TRACKER_FILE):
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return _initialiser_tracking()


def _initialiser_tracking() -> list[dict]:
    """Crée les entrées initiales depuis la config des formations."""
    ecoles = []
    for formation in FORMATIONS_CIBLES:
        for etab in formation["etablissements"]:
            ecoles.append(_entree_ecole_vide(etab, formation))
    return ecoles


def sauvegarder_tracking(ecoles: list[dict]) -> None:
    os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(ecoles, f, ensure_ascii=False, indent=2)


def _trouver_ecole(ecoles: list[dict], etablissement: str, formation: str) -> dict | None:
    """Retrouve une école par son nom et sa formation (matching partiel)."""
    etab_lower = etablissement.lower()
    form_lower = formation.lower()
    for e in ecoles:
        if etab_lower in e["etablissement"].lower() or e["etablissement"].lower() in etab_lower:
            if not formation or form_lower[:20] in e["formation"].lower():
                return e
    # Fallback : matching sur le nom seulement
    for e in ecoles:
        if etab_lower in e["etablissement"].lower() or e["etablissement"].lower() in etab_lower:
            return e
    return None


# ---------------------------------------------------------------------------
# SchoolTrackerAgent
# ---------------------------------------------------------------------------

class SchoolTrackerAgent:
    """
    Sous-agent de recensement et suivi des écoles contactées.

    Maintient un fichier JSON persistant entre les sessions et génère :
    - outputs/dashboard/ecoles.html : tableau interactif des écoles
    - outputs/logs/schools_tracking.json : données brutes
    """

    SYSTEM_PROMPT = """Tu es un assistant chargé de maintenir à jour le tableau
de suivi des candidatures PTP de Chris Gnabroyou.

Tu mets à jour les statuts des établissements après chaque action
(email rédigé, réponse reçue, etc.) et génères un rapport de progression.

Statuts possibles :
- "À contacter" : aucun contact encore
- "Brouillon prêt" : email rédigé, pas encore envoyé
- "Contacté" : email envoyé
- "En attente" : email envoyé, pas de réponse
- "Réponse reçue" : l'établissement a répondu
- "Dossier déposé" : dossier de candidature soumis
- "Admis" : admission confirmée
- "Refusé" : refus reçu
- "Sans suite" : candidature abandonnée"""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.ecoles = charger_tracking()
        self.conversations: list[dict] = []

    # ── Mise à jour depuis les résultats des autres agents ───────────────

    def maj_depuis_emails(self, resultats_emails: list[dict]) -> int:
        """
        Met à jour le statut des écoles pour lesquelles un email a été rédigé.
        Retourne le nombre d'entrées mises à jour.
        """
        count = 0
        for res in resultats_emails:
            if not res.get("success"):
                continue
            nom = res.get("etablissement", "")
            ecole = _trouver_ecole(self.ecoles, nom, res.get("formation", ""))
            if ecole:
                ecole["statut"] = "Brouillon prêt"
                ecole["date_premiere_action"] = datetime.now().isoformat()
                ecole["date_derniere_action"] = datetime.now().isoformat()
                ecole["email_sujet"] = res.get("sujet", "")
                ecole["email_path"] = (
                    res.get("paths", [""])[0] if res.get("paths") else ""
                )
                count += 1
        return count

    def maj_depuis_recherche(self, resultats_recherche: list[dict]) -> int:
        """
        Enrichit les données des écoles avec les résultats du SchoolResearchAgent.
        """
        count = 0
        for res in resultats_recherche:
            if res.get("erreur"):
                continue
            nom = res.get("etablissement", "")
            ecole = _trouver_ecole(self.ecoles, nom, res.get("formation", ""))
            if ecole:
                if res.get("contact_email"):
                    ecole["email_contact"] = res["contact_email"]
                if res.get("lien_candidature"):
                    ecole["lien_candidature"] = res["lien_candidature"]
                if res.get("date_limite"):
                    ecole["date_limite"] = res["date_limite"]
                if res.get("score_adequation"):
                    ecole["score_adequation"] = res["score_adequation"]
                if res.get("points_forts"):
                    ecole["points_forts"] = res["points_forts"]
                count += 1
        return count

    def marquer_contacte(
        self, etablissement: str, formation: str = "", notes: str = ""
    ) -> bool:
        """Marque manuellement une école comme 'Contacté'."""
        ecole = _trouver_ecole(self.ecoles, etablissement, formation)
        if ecole:
            ecole["statut"] = "Contacté"
            ecole["date_premier_contact"] = datetime.now().isoformat()
            ecole["date_derniere_action"] = datetime.now().isoformat()
            ecole["nb_emails_envoyes"] += 1
            if notes:
                ecole["notes"] = notes
            return True
        return False

    def enregistrer_reponse(
        self, etablissement: str, contenu: str, decision: str = ""
    ) -> bool:
        """Enregistre une réponse reçue d'un établissement."""
        ecole = _trouver_ecole(self.ecoles, etablissement, "")
        if ecole:
            ecole["statut"] = "Réponse reçue"
            ecole["reponse_recue"] = True
            ecole["date_reponse"] = datetime.now().isoformat()
            ecole["contenu_reponse"] = contenu
            ecole["date_derniere_action"] = datetime.now().isoformat()
            if decision:
                ecole["decision"] = decision
                ecole["statut"] = decision.capitalize()
            return True
        return False

    def sauvegarder(self) -> None:
        sauvegarder_tracking(self.ecoles)

    def get_stats(self) -> dict:
        """Retourne les statistiques de progression."""
        stats = {
            "total": len(self.ecoles),
            "a_contacter": 0,
            "brouillon_pret": 0,
            "contacte": 0,
            "en_attente": 0,
            "reponse_recue": 0,
            "dossier_depose": 0,
            "admis": 0,
            "refuse": 0,
        }
        mapping = {
            "À contacter": "a_contacter",
            "Brouillon prêt": "brouillon_pret",
            "Contacté": "contacte",
            "En attente": "en_attente",
            "Réponse reçue": "reponse_recue",
            "Dossier déposé": "dossier_depose",
            "Admis": "admis",
            "Refusé": "refuse",
        }
        for e in self.ecoles:
            key = mapping.get(e["statut"])
            if key:
                stats[key] += 1
        return stats

    def get_conversations(self) -> list[dict]:
        return self.conversations
