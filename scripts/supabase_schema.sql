-- ============================================================
-- Schéma Supabase — Système PTP Multi-Agents
-- Projet : bgfzucxocpwjjvimxsbk
-- ============================================================

-- Table principale : suivi des écoles
CREATE TABLE IF NOT EXISTS public.schools_tracking (
  id                   TEXT PRIMARY KEY,
  etablissement        TEXT NOT NULL,
  universite           TEXT,
  ville                TEXT,
  region               TEXT,
  formation            TEXT,
  formation_id         TEXT,
  formation_priorite   INTEGER DEFAULT 99,
  url                  TEXT,
  email_contact        TEXT,
  lien_candidature     TEXT,
  date_limite          TEXT,
  statut               TEXT NOT NULL DEFAULT 'À contacter',
  date_premier_contact TEXT,
  date_derniere_action TEXT,
  nb_emails_envoyes    INTEGER DEFAULT 0,
  email_sujet          TEXT DEFAULT '',
  email_path           TEXT DEFAULT '',
  reponse_recue        BOOLEAN DEFAULT FALSE,
  date_reponse         TEXT,
  contenu_reponse      TEXT DEFAULT '',
  decision             TEXT DEFAULT '',
  notes                TEXT DEFAULT '',
  score_adequation     NUMERIC,
  points_forts         JSONB DEFAULT '[]'::JSONB,
  created_at           TIMESTAMPTZ DEFAULT NOW(),
  updated_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Mise à jour automatique du champ updated_at
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_schools_updated_at ON public.schools_tracking;
CREATE TRIGGER trg_schools_updated_at
  BEFORE UPDATE ON public.schools_tracking
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Activer Row Level Security (accès public en lecture, service_role en écriture)
ALTER TABLE public.schools_tracking ENABLE ROW LEVEL SECURITY;

-- Politique : lecture publique (anon key)
DROP POLICY IF EXISTS "Lecture publique" ON public.schools_tracking;
CREATE POLICY "Lecture publique"
  ON public.schools_tracking
  FOR SELECT
  USING (true);

-- Politique : écriture via service_role (Python backend)
DROP POLICY IF EXISTS "Ecriture service role" ON public.schools_tracking;
CREATE POLICY "Ecriture service role"
  ON public.schools_tracking
  FOR ALL
  USING (auth.role() = 'service_role');

-- Activer Realtime pour les mises à jour en temps réel (PWA)
ALTER PUBLICATION supabase_realtime ADD TABLE public.schools_tracking;

-- Index pour performances
CREATE INDEX IF NOT EXISTS idx_schools_statut ON public.schools_tracking(statut);
CREATE INDEX IF NOT EXISTS idx_schools_formation_priorite ON public.schools_tracking(formation_priorite);
