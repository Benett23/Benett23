# Déploiement PWA iOS — Gratuit (Vercel + Supabase + OneSignal)

> Temps estimé : 30 minutes · Coût : 0 €

## Architecture

```
iPhone (PWA installée)
    ↕ temps réel
Vercel (hébergement statique gratuit)
    ↕ données
Supabase (base de données gratuite)
    ↑ synchronisation après chaque run
Script Python local (votre ordinateur)
    ↕ notifications push
OneSignal (push gratuit)
```

---

## Étape 1 — Supabase (base de données)

1. Créez un compte sur **https://supabase.com** (gratuit, pas de CB)
2. Créez un nouveau projet (choisissez une région proche : EU West)
3. Allez dans **SQL Editor** et exécutez ce script :

```sql
-- Table des écoles
CREATE TABLE schools_tracking (
  id TEXT PRIMARY KEY,
  etablissement TEXT NOT NULL,
  ville TEXT,
  formation TEXT,
  formation_id TEXT,
  formation_priorite INTEGER DEFAULT 0,
  statut TEXT DEFAULT 'À contacter',
  email_contact TEXT,
  lien_candidature TEXT,
  date_limite TEXT,
  score_adequation NUMERIC,
  notes TEXT,
  date_premier_contact TIMESTAMPTZ,
  date_derniere_action TIMESTAMPTZ,
  nb_emails_envoyes INTEGER DEFAULT 0,
  data_full JSONB,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table des sessions
CREATE TABLE sessions (
  id SERIAL PRIMARY KEY,
  session_date TIMESTAMPTZ DEFAULT NOW(),
  stats JSONB,
  summary TEXT
);

-- Sécurité : lecture publique (anon), écriture via service_role uniquement
ALTER TABLE schools_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Lecture publique" ON schools_tracking
  FOR SELECT USING (true);

CREATE POLICY "Lecture publique" ON sessions
  FOR SELECT USING (true);

-- Activer les mises à jour en temps réel
ALTER PUBLICATION supabase_realtime ADD TABLE schools_tracking;
```

4. Allez dans **Project Settings > API** et copiez :
   - `Project URL` → `SUPABASE_URL`
   - `anon / public` key → `SUPABASE_ANON_KEY` (pour le navigateur)
   - `service_role / secret` key → `SUPABASE_SERVICE_KEY` (pour Python uniquement)

5. Ajoutez ces valeurs dans votre fichier `.env` local.

---

## Étape 2 — OneSignal (notifications push)

1. Créez un compte sur **https://onesignal.com** (gratuit)
2. Créez une nouvelle application : **Web Push**
3. Choisissez **Custom Code** comme intégration
4. Renseignez l'URL de votre site Vercel (ex: `https://ptp-chris.vercel.app`)
5. Copiez :
   - **App ID** → `ONESIGNAL_APP_ID`
   - **REST API Key** → `ONESIGNAL_REST_API_KEY`
6. Ajoutez ces valeurs dans votre `.env` local.

> **iOS :** Les notifications push web fonctionnent sur iOS 16.4+ via Safari.
> L'utilisateur doit accepter les notifications lors de la première visite.

---

## Étape 3 — Vercel (hébergement)

### Option A : Via l'interface web (recommandée)

1. Créez un compte sur **https://vercel.com** (gratuit, login avec GitHub)
2. Importez votre dépôt GitHub
3. Configurez les variables d'environnement dans **Settings > Environment Variables** :
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `ONESIGNAL_APP_ID`
4. Déployez → Vercel lance `python scripts/build_pwa.py` automatiquement

### Option B : Via la CLI Vercel

```bash
npm install -g vercel
vercel login
vercel --prod
```

Puis renseignez les secrets :
```bash
vercel env add SUPABASE_URL
vercel env add SUPABASE_ANON_KEY
vercel env add ONESIGNAL_APP_ID
```

---

## Étape 4 — Installer l'app sur iPhone

1. Ouvrez **Safari** sur votre iPhone (pas Chrome)
2. Allez sur votre URL Vercel (ex: `https://ptp-chris.vercel.app`)
3. Appuyez sur l'icône **Partager** (rectangle avec flèche vers le haut)
4. Sélectionnez **"Sur l'écran d'accueil"**
5. Nommez l'app `PTP` et appuyez **Ajouter**
6. L'app apparaît sur votre écran d'accueil comme une vraie app !
7. Acceptez les notifications push quand la bannière apparaît

---

## Étape 5 — Synchronisation automatique

Après chaque run Python, les données sont poussées vers Supabase :

```bash
# Le système synchronise automatiquement :
python main_ptp.py          # → sync après chaque exécution

# Ou forcer une sync manuelle :
python -c "
from ptp_system.agents.school_tracker_agent import SchoolTrackerAgent
from ptp_system.tools.supabase_sync import sync_complet
t = SchoolTrackerAgent()
sync_complet(t.ecoles, t.get_stats(), notifier=True)
"
```

---

## Brief journalier automatique (cron)

Pour recevoir un email + notification push chaque matin :

**Linux/Mac (crontab) :**
```bash
crontab -e
# Ajouter cette ligne :
0 8 * * * cd /chemin/vers/Benett23 && python main_ptp.py --mode brief
```

**Windows (Planificateur de tâches) :**
1. Recherchez "Planificateur de tâches" dans le menu Démarrer
2. Créez une tâche > Déclencheur : Quotidien à 8h00
3. Action : `python C:\chemin\vers\Benett23\main_ptp.py --mode brief`

---

## Icônes PNG pour iOS (optionnel, améliore la qualité)

```bash
pip install Pillow
python scripts/generate_pwa_icons.py
# Puis redéployez sur Vercel
```

---

## Résumé des coûts

| Service    | Plan      | Limites gratuites         | Coût  |
|------------|-----------|---------------------------|-------|
| Vercel     | Hobby     | 100GB bande passante/mois  | 0 €   |
| Supabase   | Free      | 500MB BDD, 1GB storage     | 0 €   |
| OneSignal  | Free      | Notifications illimitées   | 0 €   |
| Claude CLI | Pro/Max   | Via votre abonnement       | 0 €   |
| **Total**  |           |                            | **0 €** |
