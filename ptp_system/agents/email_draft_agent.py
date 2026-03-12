"""
Agent de rédaction de brouillons d'emails pour contacter les établissements.
Utilise Claude pour personnaliser chaque email selon l'établissement.
"""

import json
from datetime import datetime
import anthropic

from ptp_system.config import CANDIDAT, INFO_PTP
from ptp_system.tools.gmail_tools import sauvegarder_brouillon


class EmailDraftAgent:
    """
    Sous-agent spécialisé dans la rédaction d'emails personnalisés.

    Tâches :
    - Rédiger un email de prise de contact pour chaque établissement
    - Personnaliser le contenu selon la formation et l'établissement
    - Sauvegarder les brouillons (local + Gmail si configuré)
    - Gérer les emails de relance
    """

    SYSTEM_PROMPT = """Tu es un assistant expert en communication professionnelle,
spécialisé dans la rédaction d'emails de candidature pour des formations universitaires.

Tu dois rédiger des emails en français, professionnels et personnalisés pour
Chris Gnabroyou qui candidate en Licence Professionnelle dans le cadre d'un PTP.

Profil du candidat :
- Prénom : Chris | Nom : Gnabroyou
- Diplômes : BTS Électrotechnique + Bac STI2D
- Métier actuel : Technicien ascensoriste (4 ans d'expérience)
- Objectif : Spécialisation automatismes, IoT, énergie industrielle
- Financement : PTP (Projet de Transition Professionnelle) via Transitions Pro
- Rentrée souhaitée : Septembre 2026

Règles pour les emails :
- Ton professionnel mais accessible
- Mentionner le contexte PTP (financement externe, démarche sérieuse)
- Mettre en avant la maturité professionnelle (4 ans terrain)
- Cohérence BTS Électrotechnique → Licence Pro visée
- Longueur : 200-350 mots pour un premier contact
- Toujours terminer par les coordonnées
- Indiquer la disponibilité pour un entretien

Retourne les emails en HTML bien formaté."""

    TOOLS = [
        {
            "name": "sauvegarder_brouillon_email",
            "description": (
                "Sauvegarde l'email rédigé en brouillon (fichier local .html/.eml "
                "et dans Gmail si configuré). Retourne le chemin du fichier sauvegardé."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "destinataire": {
                        "type": "string",
                        "description": "Adresse email du destinataire",
                    },
                    "sujet": {
                        "type": "string",
                        "description": "Objet de l'email",
                    },
                    "corps_html": {
                        "type": "string",
                        "description": "Corps de l'email en HTML",
                    },
                    "corps_texte": {
                        "type": "string",
                        "description": "Version texte de l'email (fallback)",
                    },
                    "nom_fichier": {
                        "type": "string",
                        "description": "Nom du fichier brouillon (sans extension)",
                    },
                },
                "required": ["destinataire", "sujet", "corps_html"],
            },
        },
    ]

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.conversations: list[dict] = []
        self.brouillons_crees: list[dict] = []

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "sauvegarder_brouillon_email":
            result = sauvegarder_brouillon(
                destinataire=tool_input["destinataire"],
                sujet=tool_input["sujet"],
                corps_html=tool_input["corps_html"],
                corps_texte=tool_input.get("corps_texte", ""),
                nom_fichier=tool_input.get("nom_fichier"),
            )
            # Tracker les brouillons créés
            self.brouillons_crees.append({
                "destinataire": tool_input["destinataire"],
                "sujet": tool_input["sujet"],
                "timestamp": datetime.now().isoformat(),
                "paths": result.get("paths", []),
            })
            return json.dumps(result, ensure_ascii=False)

        return json.dumps({"erreur": f"Outil inconnu : {tool_name}"})

    def _log_conversation(self, label: str, messages: list, result: str):
        self.conversations.append({
            "agent": "email_draft",
            "label": label,
            "timestamp": datetime.now().isoformat(),
            "messages": messages,
            "result": result,
        })

    def rediger_email_contact(
        self,
        etablissement_info: dict,
        type_email: str = "premier_contact",
    ) -> dict:
        """
        Rédige et sauvegarde un email personnalisé pour un établissement.

        Args:
            etablissement_info: Dict avec nom, ville, formation, email_contact, etc.
            type_email: 'premier_contact', 'relance', 'demande_info'

        Retourne: {"success": bool, "sujet": str, "paths": list, "message": str}
        """
        nom_etab = etablissement_info.get("etablissement", "l'établissement")
        ville = etablissement_info.get("ville", "")
        formation = etablissement_info.get("formation", "Licence Professionnelle")
        email_dest = (
            etablissement_info.get("contact_email")
            or etablissement_info.get("email_base")
            or etablissement_info.get("email_contact")
            or f"secretariat@{nom_etab.lower().replace(' ', '-')}.fr"
        )
        date_limite = (
            etablissement_info.get("date_limite")
            or etablissement_info.get("date_limite_base")
            or "non précisée"
        )
        score = etablissement_info.get("score_adequation", "")
        points_forts = etablissement_info.get("points_forts", [])

        type_labels = {
            "premier_contact": "prise de contact et demande d'information",
            "relance": "relance suite à un premier contact sans réponse",
            "demande_info": "demande d'informations sur les modalités d'admission",
        }
        type_desc = type_labels.get(type_email, type_email)

        nom_fichier = (
            f"email_{nom_etab.replace(' ', '_')[:25]}_{type_email}"
        )

        user_prompt = f"""Rédige un email de {type_desc} pour :

Établissement : {nom_etab} ({ville})
Formation visée : {formation}
Email destinataire : {email_dest}
Date limite candidature : {date_limite}
Adéquation profil/formation : {score}
Points forts identifiés : {', '.join(points_forts) if points_forts else 'Expérience électrotechnique terrain'}

Contexte supplémentaire :
- Chris candidate dans le cadre d'un PTP (financement Transitions Pro)
- Son expérience ascensoriste (variateurs, API, maintenance) est directement liée à la formation
- Il est mobile sur toute la France
- Rentrée souhaitée : Septembre 2026

Instructions :
1. Rédige l'email complet en HTML professionnel
2. Sujet accrocheur mentionnant la formation et le contexte PTP
3. Corps : introduction, contexte PTP, atouts du profil, demande précise, formule de politesse
4. Signature complète avec nom et coordonnées (à remplir)
5. Sauvegarde le brouillon avec l'outil sauvegarder_brouillon_email
   - Nom fichier : {nom_fichier}
6. Confirme la sauvegarde et donne un résumé"""

        messages = [{"role": "user", "content": user_prompt}]

        while True:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=3000,
                system=self.SYSTEM_PROMPT,
                tools=self.TOOLS,
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                result_text = " ".join(
                    block.text for block in response.content if hasattr(block, "text")
                )
                self._log_conversation(nom_etab, messages, result_text)

                # Trouver le dernier brouillon créé pour cet email
                brouillon = next(
                    (b for b in reversed(self.brouillons_crees)
                     if b["destinataire"] == email_dest),
                    None,
                )

                return {
                    "success": True,
                    "etablissement": nom_etab,
                    "destinataire": email_dest,
                    "sujet": brouillon["sujet"] if brouillon else "Email PTP",
                    "paths": brouillon["paths"] if brouillon else [],
                    "message": result_text,
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

    def rediger_emails_batch(
        self, etablissements_info: list[dict], type_email: str = "premier_contact"
    ) -> list[dict]:
        """
        Rédige les emails pour une liste d'établissements.
        Retourne la liste des résultats.
        """
        resultats = []
        for etab in etablissements_info:
            nom = etab.get("etablissement", etab.get("nom", "Établissement"))
            print(f"  ✉️  Rédaction email pour : {nom}...")
            try:
                result = self.rediger_email_contact(etab, type_email)
                resultats.append(result)
            except Exception as e:
                resultats.append({
                    "success": False,
                    "etablissement": nom,
                    "erreur": str(e),
                })

        return resultats

    def get_conversations(self) -> list[dict]:
        return self.conversations

    def get_brouillons(self) -> list[dict]:
        return self.brouillons_crees
