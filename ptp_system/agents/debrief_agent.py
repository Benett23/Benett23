"""
Agent de débrief — compile toutes les activités de la session et envoie un email récapitulatif.
"""

import json
import os
from datetime import datetime
from ptp_system.core.claude_cli import ClaudeCliClient

from ptp_system.config import CANDIDAT
from ptp_system.tools.gmail_tools import envoyer_debrief


class DebriefAgent:
    """
    Sous-agent de synthèse et débrief.

    Tâches :
    - Compiler les résultats de tous les autres agents
    - Générer un rapport HTML structuré
    - Envoyer le débrief par email
    - Sauvegarder le débrief localement
    """

    SYSTEM_PROMPT = """Tu es un assistant chargé de rédiger des rapports de synthèse
clairs et utiles pour Chris Gnabroyou dans le cadre de son projet PTP.

Tu dois transformer des données brutes (résultats d'agents, logs de conversations)
en un rapport HTML lisible, structuré et actionnable.

Le rapport doit être :
- En français
- Format HTML propre avec styles inline
- Organisé en sections claires
- Avec des tableaux pour les données structurées
- Avec des liens cliquables
- Avec des indicateurs visuels (✅ ⚠️ ❌ 🔄)
- Actionnable : dire clairement ce que Chris doit faire ensuite"""

    LOGS_DIR = os.getenv("LOGS_DIR", "outputs/logs")

    def __init__(self):
        self.client = ClaudeCliClient()
        self.conversations: list[dict] = []

    def _generer_html_debrief(
        self,
        resultats_recherche: list[dict],
        resultats_emails: list[dict],
        resultats_documents: list[dict],
        session_start: str,
        erreurs: list[str] = None,
    ) -> str:
        """
        Demande à Claude de générer un rapport HTML complet.
        """
        data = {
            "session_start": session_start,
            "session_end": datetime.now().isoformat(),
            "candidat": CANDIDAT["nom_complet"],
            "recherche_etablissements": resultats_recherche,
            "emails_rediges": resultats_emails,
            "documents_generes": resultats_documents,
            "erreurs": erreurs or [],
        }

        user_prompt = f"""Génère un rapport HTML de débrief complet pour la session PTP.

Données de la session :
```json
{json.dumps(data, ensure_ascii=False, indent=2)[:6000]}
```

Le rapport HTML doit inclure :
1. **En-tête** : titre, date/heure, nom du candidat
2. **Résumé exécutif** : nb établissements analysés, emails rédigés, documents créés
3. **Tableau des établissements** : nom, formation, email contact, date limite, score adéquation, statut
4. **Emails rédigés** : liste des brouillons créés avec destinataire et sujet
5. **Documents générés** : liste avec chemin de chaque fichier
6. **⚡ Actions prioritaires** : ce que Chris doit faire dans les 7 prochains jours
7. **⚠️ Alertes** : dates limites proches, erreurs rencontrées

Utilise des styles CSS inline, une palette de couleurs professionnelle (bleu #1F497D, blanc, gris).
Rends le HTML complet et lisible dans un client email."""

        messages = [{"role": "user", "content": user_prompt}]

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8000,
            system=self.SYSTEM_PROMPT,
            messages=messages,
        )

        html_content = ""
        for block in response.content:
            if hasattr(block, "text"):
                html_content += block.text

        # Extraire le HTML si Claude a mis du texte avant/après
        import re
        html_match = re.search(r"<!DOCTYPE html>.*</html>", html_content, re.DOTALL | re.IGNORECASE)
        if html_match:
            html_content = html_match.group()
        elif "<html" in html_content.lower():
            start = html_content.lower().find("<html")
            html_content = html_content[start:]

        return html_content

    def _sauvegarder_debrief_local(self, html_content: str, session_id: str) -> str:
        """Sauvegarde le débrief en HTML localement."""
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        filename = f"debrief_{session_id}.html"
        path = os.path.join(self.LOGS_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return path

    def _sauvegarder_log_json(self, session_data: dict, session_id: str) -> str:
        """Sauvegarde les données brutes de session en JSON."""
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        filename = f"session_{session_id}.json"
        path = os.path.join(self.LOGS_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        return path

    def envoyer_debrief_session(
        self,
        resultats_recherche: list[dict] = None,
        resultats_emails: list[dict] = None,
        resultats_documents: list[dict] = None,
        session_start: str = None,
        toutes_conversations: list[dict] = None,
        erreurs: list[str] = None,
    ) -> dict:
        """
        Compile les résultats et envoie le débrief par email.

        Retourne : {"success": bool, "debrief_path": str, "email_result": dict}
        """
        if session_start is None:
            session_start = datetime.now().isoformat()

        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        resultats_recherche = resultats_recherche or []
        resultats_emails = resultats_emails or []
        resultats_documents = resultats_documents or []
        erreurs = erreurs or []

        print("  📊 Génération du rapport de débrief...")

        # Générer le HTML
        html_content = self._generer_html_debrief(
            resultats_recherche=resultats_recherche,
            resultats_emails=resultats_emails,
            resultats_documents=resultats_documents,
            session_start=session_start,
            erreurs=erreurs,
        )

        # Sauvegarder localement
        debrief_path = self._sauvegarder_debrief_local(html_content, session_id)
        print(f"  💾 Débrief sauvegardé : {debrief_path}")

        # Sauvegarder les données JSON brutes
        session_data = {
            "session_id": session_id,
            "candidat": CANDIDAT["nom_complet"],
            "session_start": session_start,
            "session_end": datetime.now().isoformat(),
            "resultats_recherche": resultats_recherche,
            "resultats_emails": resultats_emails,
            "resultats_documents": resultats_documents,
            "conversations": toutes_conversations or [],
            "erreurs": erreurs,
        }
        json_path = self._sauvegarder_log_json(session_data, session_id)

        # Compter les actions
        nb_etab = len(resultats_recherche)
        nb_emails = len([r for r in resultats_emails if r.get("success")])
        nb_docs = len(resultats_documents)

        # Envoyer par email
        sujet = (
            f"[PTP] Débrief session du {datetime.now().strftime('%d/%m/%Y %H:%M')} — "
            f"{nb_etab} établissements | {nb_emails} emails | {nb_docs} documents"
        )

        print("  📧 Envoi du débrief par email...")
        email_result = envoyer_debrief(
            sujet=sujet,
            corps_html=html_content,
            corps_texte=(
                f"Débrief PTP — {CANDIDAT['nom_complet']}\n"
                f"Session : {session_start}\n"
                f"Établissements analysés : {nb_etab}\n"
                f"Emails rédigés : {nb_emails}\n"
                f"Documents générés : {nb_docs}\n"
                f"Rapport complet : {debrief_path}"
            ),
        )

        return {
            "success": True,
            "session_id": session_id,
            "debrief_path": debrief_path,
            "json_path": json_path,
            "email_result": email_result,
            "stats": {
                "etablissements": nb_etab,
                "emails": nb_emails,
                "documents": nb_docs,
                "erreurs": len(erreurs),
            },
        }

    def get_conversations(self) -> list[dict]:
        return self.conversations
