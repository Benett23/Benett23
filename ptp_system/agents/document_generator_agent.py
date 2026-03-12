"""
Agent de génération de documents (lettres de motivation, tableaux Excel).
Utilise Claude pour valider et personnaliser les documents générés.
"""

import json
import os
from datetime import datetime
import anthropic

from ptp_system.config import CANDIDAT
from ptp_system.tools.document_tools import (
    generer_lettre_transitions_pro,
    generer_lettre_iut,
    generer_planning_ptp,
    generer_liste_iut_contacts,
    generer_tous_documents,
)


OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs/dossier_ptp")


class DocumentGeneratorAgent:
    """
    Sous-agent spécialisé dans la génération des documents du dossier PTP.

    Documents générés :
    - lettre_motivation_transitions_pro.docx
    - lettre_motivation_iut.docx
    - planning_demarches_ptp.xlsx
    - liste_iut_contacts.xlsx
    """

    SYSTEM_PROMPT = f"""Tu es un assistant spécialisé dans la constitution de dossiers
de reconversion professionnelle (PTP — Projet de Transition Professionnelle).

Tu génères les documents nécessaires pour {CANDIDAT['nom_complet']},
technicien ascensoriste de 4 ans qui souhaite intégrer une Licence Pro
en Automatismes / IoT / Énergie industrielle à la rentrée septembre 2026.

Ton rôle est de :
1. Générer les documents demandés via les outils disponibles
2. Vérifier que les documents correspondent au profil
3. Rapporter un résumé des documents créés avec leur emplacement

Sois efficace et génère tous les documents demandés sans hésitation."""

    TOOLS = [
        {
            "name": "generer_lettre_transitions_pro",
            "description": (
                "Génère la lettre de motivation pour le dossier Transitions Pro (CPIR). "
                "Crée un fichier .docx professionnel."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "output_path": {
                        "type": "string",
                        "description": "Chemin de sortie (optionnel, utilise le chemin par défaut si absent)",
                    }
                },
                "required": [],
            },
        },
        {
            "name": "generer_lettre_iut",
            "description": (
                "Génère la lettre de motivation pour candidater dans les IUT. "
                "Peut être personnalisée pour un établissement spécifique."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "formation_nom": {
                        "type": "string",
                        "description": "Nom de la formation (optionnel)",
                    },
                    "etablissement_nom": {
                        "type": "string",
                        "description": "Nom de l'établissement (optionnel)",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Chemin de sortie (optionnel)",
                    },
                },
                "required": [],
            },
        },
        {
            "name": "generer_planning_ptp",
            "description": "Génère le tableau Excel de suivi des démarches PTP avec mise en forme conditionnelle.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "output_path": {
                        "type": "string",
                        "description": "Chemin de sortie (optionnel)",
                    }
                },
                "required": [],
            },
        },
        {
            "name": "generer_liste_iut_contacts",
            "description": "Génère le tableau Excel des établissements à contacter avec tous les IUT cibles.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "output_path": {
                        "type": "string",
                        "description": "Chemin de sortie (optionnel)",
                    }
                },
                "required": [],
            },
        },
        {
            "name": "generer_tous_documents",
            "description": "Génère l'ensemble des 4 documents en une seule opération.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    ]

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.conversations: list[dict] = []
        self.documents_generes: list[dict] = []

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Exécute un outil de génération de document."""
        try:
            if tool_name == "generer_lettre_transitions_pro":
                path = generer_lettre_transitions_pro(
                    output_path=tool_input.get("output_path")
                )
                result = {"success": True, "path": path, "type": "lettre_transitions_pro"}

            elif tool_name == "generer_lettre_iut":
                path = generer_lettre_iut(
                    formation_nom=tool_input.get("formation_nom"),
                    etablissement_nom=tool_input.get("etablissement_nom"),
                    output_path=tool_input.get("output_path"),
                )
                result = {"success": True, "path": path, "type": "lettre_iut"}

            elif tool_name == "generer_planning_ptp":
                path = generer_planning_ptp(output_path=tool_input.get("output_path"))
                result = {"success": True, "path": path, "type": "planning_ptp"}

            elif tool_name == "generer_liste_iut_contacts":
                path = generer_liste_iut_contacts(output_path=tool_input.get("output_path"))
                result = {"success": True, "path": path, "type": "liste_contacts"}

            elif tool_name == "generer_tous_documents":
                paths = generer_tous_documents()
                result = {"success": True, "paths": paths, "type": "tous_documents"}

            else:
                result = {"success": False, "erreur": f"Outil inconnu : {tool_name}"}

            # Tracker les documents créés
            if result.get("success"):
                if "path" in result:
                    self.documents_generes.append({
                        "type": result.get("type"),
                        "path": result["path"],
                        "timestamp": datetime.now().isoformat(),
                    })
                elif "paths" in result:
                    for doc_type, path in result["paths"].items():
                        self.documents_generes.append({
                            "type": doc_type,
                            "path": path,
                            "timestamp": datetime.now().isoformat(),
                        })

        except Exception as e:
            result = {"success": False, "erreur": str(e)}

        return json.dumps(result, ensure_ascii=False)

    def _log_conversation(self, messages: list, result: str):
        self.conversations.append({
            "agent": "document_generator",
            "timestamp": datetime.now().isoformat(),
            "messages": messages,
            "result": result,
        })

    def generer_dossier_complet(self) -> dict:
        """
        Génère l'ensemble du dossier PTP via Claude.
        Retourne un résumé des documents créés.
        """
        user_prompt = f"""Génère l'ensemble des documents du dossier PTP pour {CANDIDAT['nom_complet']} :

1. Lettre de motivation pour Transitions Pro
2. Lettre de motivation pour les IUT (formation : Licence Pro Automatismes AII)
3. Planning des démarches PTP (tableau Excel)
4. Liste des IUT à contacter (tableau Excel avec contacts)

Utilise l'outil generer_tous_documents pour générer tout d'un coup,
puis confirme les 4 documents créés avec leurs chemins."""

        messages = [{"role": "user", "content": user_prompt}]

        while True:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2000,
                system=self.SYSTEM_PROMPT,
                tools=self.TOOLS,
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                result_text = " ".join(
                    block.text for block in response.content if hasattr(block, "text")
                )
                self._log_conversation(messages, result_text)

                return {
                    "success": True,
                    "documents": self.documents_generes,
                    "message": result_text,
                    "nb_documents": len(self.documents_generes),
                }

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

    def get_conversations(self) -> list[dict]:
        return self.conversations

    def get_documents(self) -> list[dict]:
        return self.documents_generes
