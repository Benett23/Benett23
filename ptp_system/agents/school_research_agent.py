"""
Agent de recherche d'informations sur les établissements.
Utilise Claude pour analyser et enrichir les données de contact des IUT.
"""

import json
from datetime import datetime
from ptp_system.core.claude_cli import ClaudeCliClient

from ptp_system.config import CANDIDAT, FORMATIONS_CIBLES
from ptp_system.tools.web_tools import chercher_informations_formation, rechercher_contact_secretariat


class SchoolResearchAgent:
    """
    Sous-agent spécialisé dans la recherche d'informations sur les établissements.

    Tâches :
    - Identifier les contacts pertinents (email secrétariat, responsable formation)
    - Vérifier les dates limites de candidature
    - Trouver les liens de candidature officiels
    - Évaluer l'adéquation formation/profil
    """

    SYSTEM_PROMPT = """Tu es un assistant spécialisé dans la recherche d'informations
sur les IUT et universités françaises pour les candidatures en Licence Professionnelle.

Ton rôle est d'analyser les informations disponibles sur les établissements et de :
1. Identifier les contacts les plus pertinents (secrétariat pédagogique, responsable LP)
2. Confirmer les dates limites de candidature
3. Évaluer l'adéquation entre le profil du candidat et la formation
4. Rédiger un résumé structuré de chaque établissement

Profil du candidat :
- Nom : Chris Gnabroyou
- Diplômes : BTS Électrotechnique + Bac STI2D
- Expérience : 4 ans technicien ascensoriste
- Objectif : Spécialisation automatismes, IoT, énergie industrielle
- Mobilité : France entière | Rentrée souhaitée : Septembre 2026

Sois factuel, précis et structure tes réponses en JSON valide quand demandé."""

    TOOLS = [
        {
            "name": "scraper_site_etablissement",
            "description": (
                "Scrape le site web d'un établissement pour trouver les informations "
                "de contact, lien de candidature et dates limites de la formation."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "url_etablissement": {
                        "type": "string",
                        "description": "URL du site officiel de l'établissement",
                    },
                    "nom_formation": {
                        "type": "string",
                        "description": "Nom exact de la formation recherchée",
                    },
                },
                "required": ["url_etablissement", "nom_formation"],
            },
        },
        {
            "name": "obtenir_contact_fallback",
            "description": "Génère des suggestions de contact si le scraping échoue.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "nom_iut": {"type": "string", "description": "Nom de l'IUT"},
                    "ville": {"type": "string", "description": "Ville de l'IUT"},
                    "nom_formation": {"type": "string", "description": "Nom de la formation"},
                },
                "required": ["nom_iut", "ville", "nom_formation"],
            },
        },
    ]

    def __init__(self):
        self.client = ClaudeCliClient()
        self.conversations: list[dict] = []

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Exécute un outil et retourne le résultat en JSON."""
        if tool_name == "scraper_site_etablissement":
            result = chercher_informations_formation(
                url_etablissement=tool_input["url_etablissement"],
                nom_formation=tool_input["nom_formation"],
            )
        elif tool_name == "obtenir_contact_fallback":
            result = rechercher_contact_secretariat(
                nom_iut=tool_input["nom_iut"],
                ville=tool_input["ville"],
                nom_formation=tool_input["nom_formation"],
            )
        else:
            result = {"erreur": f"Outil inconnu : {tool_name}"}

        return json.dumps(result, ensure_ascii=False)

    def _log_conversation(self, agent_name: str, messages: list, result: str):
        self.conversations.append({
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "messages": messages,
            "result": result,
        })

    def analyser_etablissement(self, formation: dict, etablissement: dict) -> dict:
        """
        Analyse un établissement spécifique pour une formation donnée.
        Retourne un dict avec les informations enrichies.
        """
        user_prompt = f"""Analyse l'établissement suivant pour le candidat Chris Gnabroyou :

Formation : {formation['nom']}
Établissement : {etablissement['nom']}
Ville : {etablissement['ville']}
URL : {etablissement['url']}
Email de contact connu : {etablissement.get('email_contact', 'Non renseigné')}
Date limite connue : {etablissement.get('date_limite', 'Non renseignée')}

1. Scrape le site de l'établissement pour trouver des informations à jour
2. Évalue l'adéquation entre le profil de Chris et cette formation
3. Retourne un JSON structuré avec :
   - contact_email : meilleur email de contact trouvé
   - lien_candidature : URL de candidature officielle
   - date_limite : date limite confirmée
   - score_adequation : note /10 avec justification
   - points_forts : liste des atouts du candidat pour cette formation
   - conseils : conseils pour maximiser les chances d'admission"""

        messages = [{"role": "user", "content": user_prompt}]

        while True:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2000,
                system=self.SYSTEM_PROMPT,
                tools=self.TOOLS,
                messages=messages,
                thinking={"type": "adaptive"},
            )

            # Ajouter la réponse à l'historique
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                # Extraire le texte final
                result_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        result_text += block.text
                self._log_conversation(
                    f"school_research_{etablissement['nom']}", messages, result_text
                )

                # Tenter de parser le JSON de la réponse
                try:
                    json_match = __import__("re").search(
                        r"\{.*\}", result_text, __import__("re").DOTALL
                    )
                    if json_match:
                        parsed = json.loads(json_match.group())
                    else:
                        parsed = {"analyse_texte": result_text}
                except json.JSONDecodeError:
                    parsed = {"analyse_texte": result_text}

                # Enrichir avec les données de base
                parsed.update({
                    "etablissement": etablissement["nom"],
                    "ville": etablissement["ville"],
                    "formation": formation["nom"],
                    "url": etablissement["url"],
                    "email_base": etablissement.get("email_contact", ""),
                    "date_limite_base": etablissement.get("date_limite", ""),
                })
                return parsed

            # Traitement des appels d'outils
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_output = self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_output,
                        })
                messages.append({"role": "user", "content": tool_results})

    def rechercher_toutes_formations(
        self, formations_ids: list[str] = None
    ) -> list[dict]:
        """
        Analyse tous les établissements de toutes les formations cibles.
        Retourne une liste de résultats enrichis.
        """
        formations = FORMATIONS_CIBLES
        if formations_ids:
            formations = [f for f in formations if f["id"] in formations_ids]

        resultats = []
        for formation in formations:
            for etablissement in formation["etablissements"]:
                print(f"  🔍 Analyse : {etablissement['nom']} — {formation['nom'][:40]}...")
                try:
                    result = self.analyser_etablissement(formation, etablissement)
                    resultats.append(result)
                except Exception as e:
                    resultats.append({
                        "etablissement": etablissement["nom"],
                        "ville": etablissement["ville"],
                        "formation": formation["nom"],
                        "erreur": str(e),
                    })

        return resultats

    def get_conversations(self) -> list[dict]:
        return self.conversations
