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

Le système utilise `claude` CLI — **aucune clé API Anthropic n'est requise**.
Assurez-vous d'être authentifié :

```bash
claude auth login
```

### Gmail (débriefs par email)
```env
GMAIL_USER=votre.email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
DEBRIEF_EMAIL_TO=votre.email@gmail.com
```

**Pour obtenir un mot de passe d'application Gmail :**
1. Activez la double authentification sur votre compte Google
2. Allez sur : https://myaccount.google.com/apppasswords
3. Créez un mot de passe (ex: nom "Claude")
4. Copiez les 16 caractères générés (format : `xxxx xxxx xxxx xxxx`)

### Supabase + OneSignal (PWA mobile)
```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=...
SUPABASE_ANON_KEY=...
ONESIGNAL_APP_ID=...
ONESIGNAL_REST_API_KEY=...
```

Voir `DEPLOIEMENT_PWA.md` pour les instructions détaillées.

---

## 3. Utilisation

### Workflow complet (recommandé)
```bash
python main_ptp.py
```
Exécute : Documents → Recherche établissements → Emails → Dashboard → Débrief email

### Générer uniquement les documents
```bash
python main_ptp.py --mode docs
```
Génère les 4 fichiers dans `outputs/dossier_ptp/`

### Contacter les établissements (recherche + emails)
```bash
python main_ptp.py --mode contact
```

### Brief journalier (priorités du jour + email récapitulatif)
```bash
python main_ptp.py --mode brief
```
Régénère le dashboard et envoie un email avec les actions à faire aujourd'hui.
**Idéal à programmer en tâche cron chaque matin.**

### Régénérer le dashboard sans lancer Claude
```bash
python main_ptp.py --mode dashboard
```
Recharge le tracking existant et met à jour les pages HTML.

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

### Programmer le brief journalier (cron)
```bash
# Chaque matin à 8h00
0 8 * * * cd /chemin/vers/projet && python main_ptp.py --mode brief
```
Ajoutez cette ligne avec `crontab -e` sur Linux/Mac.

---

## 4. Structure des fichiers générés

```
outputs/
├── dashboard/
│   ├── index.html       ← Tableau de bord principal (ouvrir dans le nav.)
│   └── ecoles.html      ← Tableau des écoles avec boutons de confirmation
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
    ├── schools_tracking.json                   ← Base de données des écoles
    ├── debrief_20260312_143022.html            ← Rapport débrief
    └── session_20260312_143022.json            ← Données brutes session
```

---

## 5. Architecture des agents

```
PTPOrchestrator (main_ptp.py)
├── 🔍 SchoolResearchAgent
│   → Scrape les sites IUT, trouve contacts, dates limites, liens
│   → Évalue l'adéquation profil/formation (score /10)
│
├── ✉️  EmailDraftAgent
│   → Rédige des emails personnalisés pour chaque établissement
│   → Sauvegarde en .html et .eml (brouillons locaux)
│   → Peut envoyer dans Gmail Drafts si configuré
│
├── 📄 DocumentGeneratorAgent
│   → Lettre motivation Transitions Pro (.docx)
│   → Lettre motivation IUT (.docx)
│   → Planning démarches PTP (.xlsx)
│   → Liste contacts IUT (.xlsx)
│
├── 🏫 SchoolTrackerAgent  ← NOUVEAU
│   → Maintient la base JSON des écoles (schools_tracking.json)
│   → Suit les statuts : À contacter → Brouillon prêt → Contacté → ...
│   → Met à jour après chaque session automatiquement
│
├── 🖥️  DashboardTools  ← NOUVEAU
│   → index.html : vue d'ensemble avec coches automatiques + manuelles
│   → ecoles.html : tableau interactif avec boutons "Confirmer envoi"
│   → Filtres, tri, recherche, persistance localStorage
│
└── 📊 DebriefAgent
    → Compile tous les résultats
    → Génère rapport HTML détaillé
    → Envoie par email (si Gmail configuré)
    → Brief journalier (--mode brief)
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
