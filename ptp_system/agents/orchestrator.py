"""
Orchestrateur principal du système PTP multi-agents.
Coordonne tous les sous-agents et gère le flux de travail.
"""

import json
import os
from datetime import datetime
import anthropic

from ptp_system.config import CANDIDAT, FORMATIONS_CIBLES
from ptp_system.agents.school_research_agent import SchoolResearchAgent
from ptp_system.agents.email_draft_agent import EmailDraftAgent
from ptp_system.agents.document_generator_agent import DocumentGeneratorAgent
from ptp_system.agents.debrief_agent import DebriefAgent


class PTPOrchestrator:
    """
    Orchestrateur principal qui coordonne les 4 sous-agents :
    1. SchoolResearchAgent    — Recherche infos établissements
    2. EmailDraftAgent        — Rédige les emails de contact
    3. DocumentGeneratorAgent — Génère les documents du dossier
    4. DebriefAgent           — Compile et envoie le débrief

    Modes d'exécution :
    - run_full()             : Exécute tout le workflow
    - run_school_contact()   : Recherche + emails uniquement
    - run_document_generation() : Documents uniquement
    """

    SYSTEM_PROMPT = f"""Tu es l'orchestrateur du système PTP pour {CANDIDAT['nom_complet']}.

Tu coordonnes les sous-agents suivants :
- school_research  : Recherche les contacts et infos des établissements
- email_draft      : Rédige les emails personnalisés
- document_generator : Génère les documents du dossier
- debrief          : Compile et envoie le rapport de débrief

Ta mission : optimiser les démarches PTP de Chris pour maximiser ses chances
d'admission en Licence Pro Automatismes / IoT à la rentrée septembre 2026.

Sois stratégique : priorise les établissements avec les meilleures adéquations
et les dates limites les plus proches."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.session_start = datetime.now().isoformat()
        self.all_conversations: list[dict] = []
        self.all_errors: list[str] = []

        # Initialiser les sous-agents
        self.school_agent = SchoolResearchAgent()
        self.email_agent = EmailDraftAgent()
        self.doc_agent = DocumentGeneratorAgent()
        self.debrief_agent = DebriefAgent()

    def _collect_conversations(self):
        """Collecte toutes les conversations de tous les agents."""
        self.all_conversations.extend(self.school_agent.get_conversations())
        self.all_conversations.extend(self.email_agent.get_conversations())
        self.all_conversations.extend(self.doc_agent.get_conversations())

    def run_document_generation(self) -> dict:
        """
        Lance uniquement la génération des documents du dossier PTP.
        """
        print(f"\n{'='*60}")
        print(f"  📄 GÉNÉRATION DES DOCUMENTS — {CANDIDAT['nom_complet']}")
        print(f"{'='*60}\n")

        resultats_documents = []
        erreurs = []

        try:
            print("📝 Génération du dossier PTP complet...")
            result = self.doc_agent.generer_dossier_complet()
            resultats_documents = result.get("documents", [])
            print(f"  ✅ {len(resultats_documents)} documents générés")
            for doc in resultats_documents:
                print(f"     📄 {doc['type']} : {doc['path']}")
        except Exception as e:
            erreurs.append(f"DocumentGeneratorAgent: {str(e)}")
            print(f"  ❌ Erreur génération documents : {e}")

        self._collect_conversations()

        # Débrief
        print("\n📊 Envoi du débrief...")
        debrief_result = self.debrief_agent.envoyer_debrief_session(
            resultats_recherche=[],
            resultats_emails=[],
            resultats_documents=resultats_documents,
            session_start=self.session_start,
            toutes_conversations=self.all_conversations,
            erreurs=erreurs,
        )

        self._print_summary(
            nb_etab=0,
            nb_emails=0,
            nb_docs=len(resultats_documents),
            debrief_result=debrief_result,
        )

        return {
            "documents": resultats_documents,
            "debrief": debrief_result,
            "erreurs": erreurs,
        }

    def run_school_contact(
        self,
        formations_ids: list[str] = None,
        max_etablissements: int = None,
    ) -> dict:
        """
        Lance la recherche d'informations + rédaction des emails de contact.

        Args:
            formations_ids: IDs des formations à traiter (None = toutes)
            max_etablissements: Limiter le nombre d'établissements traités
        """
        print(f"\n{'='*60}")
        print(f"  🎓 CONTACT ÉTABLISSEMENTS — {CANDIDAT['nom_complet']}")
        print(f"{'='*60}\n")

        resultats_recherche = []
        resultats_emails = []
        erreurs = []

        # Phase 1 : Recherche d'informations
        print("🔍 Phase 1 : Recherche d'informations sur les établissements...")
        try:
            resultats_recherche = self.school_agent.rechercher_toutes_formations(
                formations_ids=formations_ids
            )
            if max_etablissements:
                resultats_recherche = resultats_recherche[:max_etablissements]
            print(f"  ✅ {len(resultats_recherche)} établissements analysés")
        except Exception as e:
            erreurs.append(f"SchoolResearchAgent: {str(e)}")
            print(f"  ❌ Erreur recherche : {e}")
            # Fallback : utiliser les données de config directement
            resultats_recherche = self._get_fallback_etablissements(formations_ids)

        # Phase 2 : Rédaction des emails
        print("\n✉️  Phase 2 : Rédaction des emails de contact...")
        try:
            resultats_emails = self.email_agent.rediger_emails_batch(
                etablissements_info=resultats_recherche
            )
            nb_ok = len([r for r in resultats_emails if r.get("success")])
            print(f"  ✅ {nb_ok}/{len(resultats_emails)} emails rédigés")
        except Exception as e:
            erreurs.append(f"EmailDraftAgent: {str(e)}")
            print(f"  ❌ Erreur emails : {e}")

        self._collect_conversations()

        # Phase 3 : Débrief
        print("\n📊 Phase 3 : Envoi du débrief...")
        debrief_result = self.debrief_agent.envoyer_debrief_session(
            resultats_recherche=resultats_recherche,
            resultats_emails=resultats_emails,
            resultats_documents=[],
            session_start=self.session_start,
            toutes_conversations=self.all_conversations,
            erreurs=erreurs,
        )

        self._print_summary(
            nb_etab=len(resultats_recherche),
            nb_emails=len([r for r in resultats_emails if r.get("success")]),
            nb_docs=0,
            debrief_result=debrief_result,
        )

        return {
            "etablissements": resultats_recherche,
            "emails": resultats_emails,
            "debrief": debrief_result,
            "erreurs": erreurs,
        }

    def run_full(
        self,
        formations_ids: list[str] = None,
        max_etablissements: int = None,
    ) -> dict:
        """
        Lance le workflow complet :
        1. Génération des documents
        2. Recherche d'informations sur les établissements
        3. Rédaction des emails de contact
        4. Envoi du débrief
        """
        print(f"\n{'='*60}")
        print(f"  🚀 SYSTÈME PTP MULTI-AGENTS — {CANDIDAT['nom_complet']}")
        print(f"  📅 Démarrage : {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
        print(f"{'='*60}\n")

        resultats_recherche = []
        resultats_emails = []
        resultats_documents = []
        erreurs = []

        # ── Étape 1 : Documents ──────────────────────────────────────
        print("📄 Étape 1/3 : Génération des documents PTP...")
        try:
            doc_result = self.doc_agent.generer_dossier_complet()
            resultats_documents = doc_result.get("documents", [])
            print(f"  ✅ {len(resultats_documents)} documents créés")
        except Exception as e:
            erreurs.append(f"DocumentGeneratorAgent: {str(e)}")
            print(f"  ⚠️  Documents : {e}")

        # ── Étape 2 : Recherche établissements ───────────────────────
        print("\n🔍 Étape 2/3 : Analyse des établissements...")
        try:
            resultats_recherche = self.school_agent.rechercher_toutes_formations(
                formations_ids=formations_ids
            )
            if max_etablissements:
                resultats_recherche = resultats_recherche[:max_etablissements]
            print(f"  ✅ {len(resultats_recherche)} établissements analysés")
        except Exception as e:
            erreurs.append(f"SchoolResearchAgent: {str(e)}")
            print(f"  ⚠️  Recherche : {e}")
            resultats_recherche = self._get_fallback_etablissements(formations_ids)

        # ── Étape 3 : Emails ─────────────────────────────────────────
        print("\n✉️  Étape 3/3 : Rédaction des emails de contact...")
        try:
            resultats_emails = self.email_agent.rediger_emails_batch(
                etablissements_info=resultats_recherche
            )
            nb_ok = len([r for r in resultats_emails if r.get("success")])
            print(f"  ✅ {nb_ok}/{len(resultats_emails)} brouillons créés")
        except Exception as e:
            erreurs.append(f"EmailDraftAgent: {str(e)}")
            print(f"  ⚠️  Emails : {e}")

        self._collect_conversations()

        # ── Débrief ──────────────────────────────────────────────────
        print("\n📊 Débrief : Compilation et envoi du rapport...")
        debrief_result = self.debrief_agent.envoyer_debrief_session(
            resultats_recherche=resultats_recherche,
            resultats_emails=resultats_emails,
            resultats_documents=resultats_documents,
            session_start=self.session_start,
            toutes_conversations=self.all_conversations,
            erreurs=erreurs,
        )

        self._print_summary(
            nb_etab=len(resultats_recherche),
            nb_emails=len([r for r in resultats_emails if r.get("success")]),
            nb_docs=len(resultats_documents),
            debrief_result=debrief_result,
        )

        return {
            "documents": resultats_documents,
            "etablissements": resultats_recherche,
            "emails": resultats_emails,
            "debrief": debrief_result,
            "erreurs": erreurs,
        }

    def _get_fallback_etablissements(self, formations_ids: list[str] = None) -> list[dict]:
        """Retourne les données de config comme fallback si le scraping échoue."""
        formations = FORMATIONS_CIBLES
        if formations_ids:
            formations = [f for f in formations if f["id"] in formations_ids]

        resultats = []
        for formation in formations:
            for etab in formation["etablissements"]:
                resultats.append({
                    "etablissement": etab["nom"],
                    "ville": etab["ville"],
                    "formation": formation["nom"],
                    "email_base": etab.get("email_contact", ""),
                    "url": etab["url"],
                    "date_limite_base": etab.get("date_limite", ""),
                    "lien_candidature": etab.get("lien_candidature", etab["url"]),
                })
        return resultats

    def _print_summary(
        self,
        nb_etab: int,
        nb_emails: int,
        nb_docs: int,
        debrief_result: dict,
    ):
        """Affiche le résumé final de la session."""
        print(f"\n{'='*60}")
        print("  ✅ SESSION TERMINÉE")
        print(f"{'='*60}")
        print(f"  📊 Établissements analysés : {nb_etab}")
        print(f"  ✉️  Brouillons emails créés : {nb_emails}")
        print(f"  📄 Documents générés       : {nb_docs}")

        if debrief_result.get("debrief_path"):
            print(f"  💾 Débrief HTML           : {debrief_result['debrief_path']}")

        email_result = debrief_result.get("email_result", {})
        if email_result.get("success"):
            print(f"  📧 Débrief email          : ✅ Envoyé")
        else:
            msg = email_result.get("message", "Non envoyé (Gmail non configuré)")
            print(f"  📧 Débrief email          : ⚠️  {msg}")

        print(f"\n  📁 Fichiers dans : outputs/")
        print(f"{'='*60}\n")
