# 🚀 Guide de démarrage — Système PTP Multi-Agents

**Pour Chris Gnabroyou | Projet de Transition Professionnelle**

---

## 1. Installation

```bash
# Installer les dépendances Python
pip install -r requirements.txt

# Copier le fichier de configuration
cp .env.example .env
```

---

## 2. Configuration (`.env`)

Éditez le fichier `.env` et renseignez :

### Obligatoire
```env
ANTHROPIC_API_KEY=sk-ant-...
```
→ Créer une clé sur : https://console.anthropic.com/settings/keys

### Optionnel (pour l'envoi des débriefs par email)
```env
GMAIL_USER=votre.email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
DEBRIEF_EMAIL_TO=votre.email@gmail.com
```

**Pour obtenir un mot de passe d'application Gmail :**
1. Activez la double authentification sur votre compte Google
2. Allez sur : https://myaccount.google.com/apppasswords
3. Créez un mot de passe pour "Mail"

---

## 3. Utilisation

### Workflow complet (recommandé)
```bash
python main_ptp.py
```
Exécute : Génération documents → Recherche établissements → Rédaction emails → Débrief

### Générer uniquement les documents
```bash
python main_ptp.py --mode docs
```
Génère les 4 fichiers dans `outputs/dossier_ptp/`

### Contacter les établissements (recherche + emails)
```bash
python main_ptp.py --mode contact
```

### Filtrer par formation
```bash
python main_ptp.py --formations lpaii sarii
```

### Tester avec peu d'établissements
```bash
python main_ptp.py --max-etab 3
```

### Voir toutes les formations configurées
```bash
python main_ptp.py --liste-formations
```

---

## 4. Structure des fichiers générés

```
outputs/
├── dossier_ptp/
│   ├── lettre_motivation_transitions_pro.docx
│   ├── lettre_motivation_iut.docx
│   ├── planning_demarches_ptp.xlsx
│   └── liste_iut_contacts.xlsx
├── drafts/
│   ├── email_IUT_Nantes_premier_contact.html   ← Brouillons emails
│   ├── email_IUT_Nantes_premier_contact.eml    ← Importable dans Gmail
│   └── ...
└── logs/
    ├── debrief_20260312_143022.html            ← Rapport débrief
    └── session_20260312_143022.json            ← Données brutes
```

---

## 5. Architecture des agents

```
PTPOrchestrator (main_ptp.py)
├── 🔍 SchoolResearchAgent
│   → Analyse les sites des IUT
│   → Trouve contacts, dates limites, liens candidature
│   → Évalue l'adéquation profil/formation
│
├── ✉️  EmailDraftAgent
│   → Rédige des emails personnalisés pour chaque établissement
│   → Sauvegarde en .html et .eml (brouillons locaux)
│   → Envoie dans Gmail Drafts si configuré
│
├── 📄 DocumentGeneratorAgent
│   → Lettre motivation Transitions Pro (.docx)
│   → Lettre motivation IUT (.docx)
│   → Planning démarches PTP (.xlsx)
│   → Liste contacts IUT (.xlsx)
│
└── 📊 DebriefAgent
    → Compile tous les résultats
    → Génère rapport HTML détaillé
    → Envoie par email (si Gmail configuré)
    → Sauvegarde localement
```

---

## 6. IDs des formations disponibles

| ID | Formation | Priorité |
|----|-----------|---------|
| `lpaii` | Licence Pro Automatismes et Informatique Industrielle | ⭐ 1 |
| `sarii` | Licence Pro SARII (Systèmes Automatisés...) | ⭐ 2 |
| `ia_industrie` | Licence Pro IA pour l'Industrie | ⭐ 3 |
| `cyber_ot` | Licence Pro Cybersécurité des Systèmes Industriels | ⭐ 4 |
| `elec_puissance` | Licence Pro Électronique de Puissance | ⭐ 5 |

---

## 7. Réviser les brouillons emails avant envoi

Les emails générés sont des **brouillons à valider** avant envoi.

1. Ouvrez les fichiers `.html` dans `outputs/drafts/`
2. Vérifiez et ajustez le contenu si nécessaire
3. Pour envoyer depuis Gmail : importez les `.eml` ou copiez-collez depuis le `.html`

> ⚠️ **Le système ne peut pas envoyer automatiquement des emails aux établissements.**
> Les brouillons sont préparés pour votre validation.
