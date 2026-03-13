"""
Configuration centrale du système PTP.
Profil candidat, formations cibles et données des établissements.
"""

# ---------------------------------------------------------------------------
# Profil du candidat
# ---------------------------------------------------------------------------
CANDIDAT = {
    "prenom": "Chris",
    "nom": "Gnabroyou",
    "nom_complet": "Chris Gnabroyou",
    "diplomes": ["BTS Électrotechnique", "Bac STI2D"],
    "metier_actuel": "Technicien ascensoriste",
    "experience_annees": 4,
    "objectif_court": "Spécialisation automatismes, IoT et énergie industrielle",
    "objectif_long": (
        "Évoluer vers un poste d'ingénieur/technicien expert en automatismes industriels, "
        "IoT ou cybersécurité OT, en capitalisant sur 4 ans d'expérience terrain en "
        "électrotechnique et maintenance ascensoriste."
    ),
    "modalite": "Présentiel à temps plein",
    "mobilite": "France entière",
    "rentree_cible": "Septembre 2026",
    "competences_techniques": [
        "Électrotechnique (câblage, appareillage, variateurs de fréquence)",
        "Maintenance préventive et corrective d'ascenseurs",
        "Lecture et interprétation de schémas électriques",
        "Diagnostic et dépannage électrotechnique",
        "Installation et mise en service d'équipements ascensoristes",
        "Respect des réglementations NF EN 81 et normes de sécurité",
        "Outils de mesure : multimètre, oscilloscope, valise de diagnostic",
        "Gestion des interventions et reporting client",
    ],
    "soft_skills": [
        "Rigueur et méthode",
        "Autonomie sur chantier",
        "Sens du service client",
        "Capacité d'adaptation",
        "Travail en équipe",
    ],
}

# ---------------------------------------------------------------------------
# Formations cibles (par ordre de priorité)
# ---------------------------------------------------------------------------
FORMATIONS_CIBLES = [
    {
        "id": "lpaii",
        "nom": "Licence Pro Automatismes et Informatique Industrielle",
        "niveau": "Bac+3",
        "duree": "1 an",
        "priorite": 1,
        "competences_visees": [
            "Automatismes (API Siemens, Schneider)",
            "Réseaux industriels (Profibus, Ethernet industriel)",
            "Supervision SCADA",
            "IoT industriel",
        ],
        "etablissements": [
            {
                "nom": "IUT de Nantes",
                "universite": "Université de Nantes",
                "ville": "Nantes",
                "region": "Pays de la Loire",
                "telephone": "02 40 30 60 00",
                "url": "https://iutnantes.univ-nantes.fr",
                "email_contact": "secretariat.lp@iutnantes.univ-nantes.fr",
                "lien_candidature": "https://candidatures.iutnantes.univ-nantes.fr",
                "date_limite": "Mai 2026",
            },
            {
                "nom": "IUT Grenoble Alpes",
                "universite": "Université Grenoble Alpes",
                "ville": "Grenoble",
                "region": "Auvergne-Rhône-Alpes",
                "telephone": "04 76 82 53 00",
                "url": "https://iut.univ-grenoble-alpes.fr",
                "email_contact": "lp-aii@iut.univ-grenoble-alpes.fr",
                "lien_candidature": "https://ecandidat.univ-grenoble-alpes.fr",
                "date_limite": "Avril 2026",
            },
            {
                "nom": "IUT Lyon 1",
                "universite": "Université Claude Bernard Lyon 1",
                "ville": "Lyon",
                "region": "Auvergne-Rhône-Alpes",
                "telephone": "04 72 69 20 00",
                "url": "https://iut.univ-lyon1.fr",
                "email_contact": "lp-geii@iut.univ-lyon1.fr",
                "lien_candidature": "https://iut.univ-lyon1.fr/candidature",
                "date_limite": "Mai 2026",
            },
            {
                "nom": "IUT Paris-Saclay (Orsay)",
                "universite": "Université Paris-Saclay",
                "ville": "Orsay",
                "region": "Île-de-France",
                "telephone": "01 69 15 60 00",
                "url": "https://www.iut-orsay.universite-paris-saclay.fr",
                "email_contact": "geii@iut-orsay.universite-paris-saclay.fr",
                "lien_candidature": "https://ecandidat.universite-paris-saclay.fr",
                "date_limite": "Avril 2026",
            },
            {
                "nom": "IUT de Bordeaux",
                "universite": "Université de Bordeaux",
                "ville": "Bordeaux",
                "region": "Nouvelle-Aquitaine",
                "telephone": "05 57 12 20 00",
                "url": "https://www.iut.u-bordeaux.fr",
                "email_contact": "lp-geii@iut.u-bordeaux.fr",
                "lien_candidature": "https://ecandidat.u-bordeaux.fr",
                "date_limite": "Mai 2026",
            },
        ],
    },
    {
        "id": "sarii",
        "nom": "Licence Pro SARII (Systèmes Automatisés, Réseaux et Informatique Industrielle)",
        "niveau": "Bac+3",
        "duree": "1 an",
        "priorite": 2,
        "competences_visees": [
            "IoT industriel",
            "Systèmes embarqués",
            "Télémaintenance",
            "Réseaux industriels",
        ],
        "etablissements": [
            {
                "nom": "IUT Cachan (Paris-Saclay)",
                "universite": "Université Paris-Saclay",
                "ville": "Cachan",
                "region": "Île-de-France",
                "telephone": "01 41 24 11 00",
                "url": "https://www.iut-cachan.universite-paris-saclay.fr",
                "email_contact": "sarii@iut-cachan.universite-paris-saclay.fr",
                "lien_candidature": "https://ecandidat.universite-paris-saclay.fr",
                "date_limite": "Avril 2026",
            },
            {
                "nom": "IUT de Valenciennes",
                "universite": "Université Polytechnique Hauts-de-France",
                "ville": "Valenciennes",
                "region": "Hauts-de-France",
                "telephone": "03 27 51 73 10",
                "url": "https://www.iut-valenciennes.fr",
                "email_contact": "lp-sarii@uphf.fr",
                "lien_candidature": "https://ecandidat.uphf.fr",
                "date_limite": "Mai 2026",
            },
            {
                "nom": "IUT de Rennes",
                "universite": "Université de Rennes 1",
                "ville": "Rennes",
                "region": "Bretagne",
                "telephone": "02 23 23 38 23",
                "url": "https://iut-rennes.univ-rennes1.fr",
                "email_contact": "lp-sarii@univ-rennes1.fr",
                "lien_candidature": "https://ecandidat.univ-rennes1.fr",
                "date_limite": "Mai 2026",
            },
        ],
    },
    {
        "id": "ia_industrie",
        "nom": "Licence Pro IA pour l'Industrie / Data Industrie 4.0",
        "niveau": "Bac+3",
        "duree": "1 an",
        "priorite": 3,
        "competences_visees": [
            "Python, machine learning appliqué",
            "Traitement de données industrielles",
            "Maintenance prédictive",
            "Capteurs et IoT",
        ],
        "etablissements": [
            {
                "nom": "IUT de Bordeaux",
                "universite": "Université de Bordeaux",
                "ville": "Bordeaux",
                "region": "Nouvelle-Aquitaine",
                "telephone": "05 57 12 20 00",
                "url": "https://www.iut.u-bordeaux.fr",
                "email_contact": "lp-ia@iut.u-bordeaux.fr",
                "lien_candidature": "https://ecandidat.u-bordeaux.fr",
                "date_limite": "Mai 2026",
            },
            {
                "nom": "IUT de Valenciennes",
                "universite": "Université Polytechnique Hauts-de-France",
                "ville": "Valenciennes",
                "region": "Hauts-de-France",
                "telephone": "03 27 51 73 10",
                "url": "https://www.iut-valenciennes.fr",
                "email_contact": "lp-ia@uphf.fr",
                "lien_candidature": "https://ecandidat.uphf.fr",
                "date_limite": "Mai 2026",
            },
        ],
    },
    {
        "id": "cyber_ot",
        "nom": "Licence Pro Cybersécurité des Systèmes Industriels (OT Security)",
        "niveau": "Bac+3",
        "duree": "1 an",
        "priorite": 4,
        "competences_visees": [
            "Sécurité réseaux SCADA",
            "Protocoles industriels (Modbus, Profibus)",
            "Audit de sécurité OT",
            "Cybersécurité industrielle",
        ],
        "etablissements": [
            {
                "nom": "IUT de Valenciennes",
                "universite": "Université Polytechnique Hauts-de-France",
                "ville": "Valenciennes",
                "region": "Hauts-de-France",
                "telephone": "03 27 51 73 10",
                "url": "https://www.iut-valenciennes.fr",
                "email_contact": "lp-cyber@uphf.fr",
                "lien_candidature": "https://ecandidat.uphf.fr",
                "date_limite": "Avril 2026",
            },
            {
                "nom": "IMT Nord Europe",
                "universite": "IMT Nord Europe",
                "ville": "Douai",
                "region": "Hauts-de-France",
                "telephone": "03 27 71 22 22",
                "url": "https://imt-nord-europe.fr",
                "email_contact": "admissions@imt-nord-europe.fr",
                "lien_candidature": "https://imt-nord-europe.fr/formations/candidature",
                "date_limite": "Avril 2026",
            },
        ],
    },
    {
        "id": "elec_puissance",
        "nom": "Licence Pro Électronique de Puissance et Conversion d'Énergie",
        "niveau": "Bac+3",
        "duree": "1 an",
        "priorite": 5,
        "competences_visees": [
            "Variateurs de fréquence",
            "Onduleurs et convertisseurs",
            "Stockage d'énergie",
            "Efficacité énergétique",
        ],
        "etablissements": [
            {
                "nom": "IUT Cachan (Paris-Saclay)",
                "universite": "Université Paris-Saclay",
                "ville": "Cachan",
                "region": "Île-de-France",
                "telephone": "01 41 24 11 00",
                "url": "https://www.iut-cachan.universite-paris-saclay.fr",
                "email_contact": "lp-epce@iut-cachan.universite-paris-saclay.fr",
                "lien_candidature": "https://ecandidat.universite-paris-saclay.fr",
                "date_limite": "Avril 2026",
            },
            {
                "nom": "IUT Grenoble Alpes",
                "universite": "Université Grenoble Alpes",
                "ville": "Grenoble",
                "region": "Auvergne-Rhône-Alpes",
                "telephone": "04 76 82 53 00",
                "url": "https://iut.univ-grenoble-alpes.fr",
                "email_contact": "lp-epce@iut.univ-grenoble-alpes.fr",
                "lien_candidature": "https://ecandidat.univ-grenoble-alpes.fr",
                "date_limite": "Mai 2026",
            },
        ],
    },
]

# ---------------------------------------------------------------------------
# Étapes clés du dossier PTP
# ---------------------------------------------------------------------------
ETAPES_PTP = [
    {
        "num": 1,
        "action": "Vérifier éligibilité PTP",
        "organisme": "Transitions Pro (CPIR)",
        "delai": "Immédiat",
        "statut": "✅ Fait",
        "notes": "CDI/CDD + 24 mois d'expérience dont 12 chez employeur actuel requis",
    },
    {
        "num": 2,
        "action": "Choisir la formation cible",
        "organisme": "Personnel",
        "delai": "Mars 2026",
        "statut": "🔄 En cours",
        "notes": "Priorité : Licence Pro AII. Explorer aussi SARII et IA Industrie 4.0",
    },
    {
        "num": 3,
        "action": "Contacter Transitions Pro de sa région",
        "organisme": "Transitions Pro (CPIR)",
        "delai": "Avril 2026",
        "statut": "À faire",
        "notes": "www.transitionspro.fr — prendre RDV pour accompagnement dossier",
    },
    {
        "num": 4,
        "action": "Déposer le dossier PTP",
        "organisme": "Transitions Pro (CPIR)",
        "delai": "Juin 2026",
        "statut": "À faire",
        "notes": "Minimum 3 mois avant début de formation (rentrée sept. 2026)",
    },
    {
        "num": 5,
        "action": "Informer l'employeur",
        "organisme": "Employeur actuel",
        "delai": "Juin 2026",
        "statut": "À faire",
        "notes": "Lettre recommandée AR de demande de congé formation",
    },
    {
        "num": 6,
        "action": "Candidater auprès des IUT cibles",
        "organisme": "IUT / Universités",
        "delai": "Mars–Mai 2026",
        "statut": "🔄 En cours",
        "notes": "Candidatures sur eCandidat / Parcoursup ou directement via email",
    },
    {
        "num": 7,
        "action": "Confirmer le financement PTP",
        "organisme": "Transitions Pro (CPIR)",
        "delai": "Juillet 2026",
        "statut": "À faire",
        "notes": "Réponse environ 2 mois après dépôt dossier. Couvre frais pédagogiques + salaire",
    },
    {
        "num": 8,
        "action": "Début de formation",
        "organisme": "IUT sélectionné",
        "delai": "Septembre 2026",
        "statut": "À faire",
        "notes": "Rentrée universitaire 2026–2027",
    },
]

# ---------------------------------------------------------------------------
# Informations PTP générales
# ---------------------------------------------------------------------------
INFO_PTP = {
    "organisme_financeur": "Transitions Pro (CPIR)",
    "lien_officiel": "https://www.transitionspro.fr",
    "delai_depot": "Minimum 3 mois avant début de formation",
    "financement": "Frais pédagogiques + maintien de salaire (selon plafond SMIC × 2)",
    "contrat_requis": "CDI ou CDD — 24 mois d'expérience dont 12 chez employeur actuel",
    "rentree_cible": "Septembre 2026",
}
