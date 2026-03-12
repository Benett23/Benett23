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
from ptp_system.agents.school_tracker_agent import SchoolTrackerAgent
from ptp_system.tools.dashboard_tools import generer_tout_dashboard


class PTPOrchestrator:
    """
    Orchestrateur principal qui coordonne les 5 sous-agents :
    1. SchoolResearchAgent    — Recherche infos établissements
    2. EmailDraftAgent        — Rédige les emails de contact
    3. DocumentGeneratorAgent — Génère les documents du dossier
    4. SchoolTrackerAgent     — Recense et suit les écoles contactées
    5. DebriefAgent           — Compile et envoie le débrief

    Modes d'exécution :
    - run_full()             : Exécute tout le workflow
    - run_school_contact()   : Recherche + emails uniquement
    - run_document_generation() : Documents uniquement
    - run_daily_brief()      : Brief journalier (dashboard + email)
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
        self.tracker_agent = SchoolTrackerAgent()
        self.debrief_agent = DebriefAgent()

    def _collect_conversations(self):
        """Collecte toutes les conversations de tous les agents."""
        self.all_conversations.extend(self.school_agent.get_conversations())
        self.all_conversations.extend(self.email_agent.get_conversations())
        self.all_conversations.extend(self.doc_agent.get_conversations())

    def _generer_dashboard(self, resultats_documents=None, resultats_emails=None,
                           resultats_recherche=None) -> dict:
        """Met à jour le tracker et génère les pages du dashboard."""
        if resultats_recherche:
            self.tracker_agent.maj_depuis_recherche(resultats_recherche)
        if resultats_emails:
            self.tracker_agent.maj_depuis_emails(resultats_emails)
        self.tracker_agent.sauvegarder()

        stats = self.tracker_agent.get_stats()
        paths = generer_tout_dashboard(
            ecoles=self.tracker_agent.ecoles,
            documents_generes=resultats_documents or [],
            nb_emails_rediges=len([r for r in (resultats_emails or []) if r.get("success")]),
            nb_etab_analyses=len(resultats_recherche or []),
            derniere_session=self.session_start,
            stats_ecoles=stats,
        )
        print(f"  🖥️  Dashboard : {paths['index']}")
        print(f"  🏫 Écoles    : {paths['ecoles']}")
        return paths

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

        # Dashboard
        print("\n🖥️  Génération du dashboard...")
        self._generer_dashboard(resultats_documents=resultats_documents)

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

        # Phase 3 : Dashboard
        print("\n🖥️  Phase 3 : Mise à jour du dashboard...")
        self._generer_dashboard(
            resultats_emails=resultats_emails,
            resultats_recherche=resultats_recherche,
        )

        # Phase 4 : Débrief
        print("\n📊 Phase 4 : Envoi du débrief...")
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

        # ── Dashboard ────────────────────────────────────────────────
        print("\n🖥️  Dashboard : Mise à jour des pages...")
        self._generer_dashboard(
            resultats_documents=resultats_documents,
            resultats_emails=resultats_emails,
            resultats_recherche=resultats_recherche,
        )

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

    def run_daily_brief(self) -> dict:
        """
        Brief journalier : régénère le dashboard avec l'état actuel
        et envoie un email de rappel des actions prioritaires du jour.
        """
        from ptp_system.tools.gmail_tools import envoyer_debrief
        from ptp_system.tools.dashboard_tools import generer_tout_dashboard

        print(f"\n{'='*60}")
        print(f"  ☀️  BRIEF JOURNALIER — {CANDIDAT['nom_complet']}")
        print(f"  📅 {datetime.now().strftime('%A %d %B %Y à %H:%M')}")
        print(f"{'='*60}\n")

        # Recharger le tracker
        self.tracker_agent = SchoolTrackerAgent()
        stats = self.tracker_agent.get_stats()

        # Régénérer le dashboard
        print("🖥️  Mise à jour du dashboard...")
        paths = generer_tout_dashboard(
            ecoles=self.tracker_agent.ecoles,
            stats_ecoles=stats,
            derniere_session=datetime.now().isoformat(),
        )

        # Compiler le brief email
        brouillons_en_attente = [
            e for e in self.tracker_agent.ecoles if e["statut"] == "Brouillon prêt"
        ]
        a_contacter = [
            e for e in self.tracker_agent.ecoles if e["statut"] == "À contacter"
        ]
        en_attente = [
            e for e in self.tracker_agent.ecoles if e["statut"] == "En attente"
        ]

        now_fr = datetime.now().strftime("%A %d %B %Y")
        corps_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;max-width:700px;margin:auto;padding:20px;color:#333}}
.header{{background:#1F497D;color:white;padding:20px;border-radius:8px;margin-bottom:20px}}
h2{{color:#1F497D;border-bottom:2px solid #EBF3FB;padding-bottom:8px}}
.card{{background:#EBF3FB;border-radius:8px;padding:14px;margin:10px 0}}
table{{width:100%;border-collapse:collapse;font-size:.9em}}
th{{background:#4472C4;color:white;padding:8px;text-align:left}}
td{{padding:7px 8px;border-bottom:1px solid #eee}}
.badge{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.8em;font-weight:600}}
.b-orange{{background:#fff3cd;color:#d67f20}}
.b-grey{{background:#eee;color:#666}}
.b-purple{{background:#e8d4f8;color:#6a0dad}}
a{{color:#1F497D}}
</style></head>
<body>
<div class="header">
  <h1 style="margin:0;font-size:1.4em">☀️ Brief journalier PTP</h1>
  <div style="opacity:.85;margin-top:5px">{now_fr} — {CANDIDAT['nom_complet']}</div>
</div>

<div class="card">
  <strong>📊 Progression globale</strong><br>
  🏫 {stats['total']} établissements ciblés &nbsp;|&nbsp;
  📨 {stats.get('brouillon_pret', 0)} brouillons prêts &nbsp;|&nbsp;
  ✅ {stats.get('contacte', 0)} contactés &nbsp;|&nbsp;
  📬 {stats.get('reponse_recue', 0)} réponses &nbsp;|&nbsp;
  🎉 {stats.get('admis', 0)} admissions
</div>
"""
        if brouillons_en_attente:
            corps_html += f"""
<h2>⚡ Action requise : {len(brouillons_en_attente)} email(s) prêt(s) à envoyer</h2>
<p>Ces brouillons ont été rédigés par le système et attendent votre validation :</p>
<table>
  <tr><th>Établissement</th><th>Ville</th><th>Formation</th></tr>
  {''.join(f"<tr><td><strong>{e['etablissement']}</strong></td><td>{e['ville']}</td><td style='font-size:.85em'>{e['formation'][:50]}…</td></tr>" for e in brouillons_en_attente)}
</table>
<p style="margin-top:12px">
  👉 Ouvrez <code>outputs/drafts/</code> pour relire et envoyer les emails.<br>
  Confirmez ensuite l'envoi sur : <a href="outputs/dashboard/ecoles.html">la page des écoles</a>
</p>
"""
        if en_attente:
            corps_html += f"""
<h2>⏳ En attente de réponse ({len(en_attente)} école(s))</h2>
<table>
  <tr><th>Établissement</th><th>Ville</th><th>Date limite</th></tr>
  {''.join(f"<tr><td>{e['etablissement']}</td><td>{e['ville']}</td><td>{e.get('date_limite','N/A')}</td></tr>" for e in en_attente[:5])}
</table>
"""
        corps_html += f"""
<p style="margin-top:20px;text-align:center;color:#888;font-size:.85em">
  Dashboard complet : <a href="outputs/dashboard/index.html">outputs/dashboard/index.html</a>
</p>
</body></html>"""

        sujet = (
            f"☀️ Brief PTP du {now_fr} — "
            f"{len(brouillons_en_attente)} brouillon(s) à envoyer"
            if brouillons_en_attente else
            f"☀️ Brief PTP du {now_fr} — {stats.get('contacte', 0)} école(s) contactée(s)"
        )

        print("📧 Envoi du brief journalier...")
        email_result = envoyer_debrief(sujet=sujet, corps_html=corps_html)

        self._print_summary(0, 0, 0, {"email_result": email_result,
                                       "debrief_path": paths["index"]})
        return {"stats": stats, "dashboard": paths, "email_result": email_result}

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
