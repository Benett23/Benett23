"""
Outils de recherche et scraping web pour trouver les informations
de contact et de candidature des établissements.
"""

import re
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
TIMEOUT = 15


def _get_page(url: str) -> BeautifulSoup | None:
    """Télécharge une page et retourne son contenu BeautifulSoup."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return BeautifulSoup(resp.text, "lxml")
    except Exception:
        try:
            return BeautifulSoup(resp.text, "html.parser")
        except Exception:
            return None


def extraire_emails_page(url: str) -> list[str]:
    """
    Extrait toutes les adresses email présentes sur une page web.
    """
    soup = _get_page(url)
    if not soup:
        return []

    # Recherche dans le texte
    texte = soup.get_text(separator=" ")
    emails = re.findall(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        texte
    )
    # Recherche dans les liens mailto:
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("mailto:"):
            mail = href[7:].split("?")[0].strip()
            if mail:
                emails.append(mail)

    # Dédupliquer et filtrer les adresses génériques
    seen = set()
    result = []
    for em in emails:
        em_lower = em.lower()
        if em_lower not in seen and not any(
            skip in em_lower for skip in ["example", "noreply", "no-reply", "test@"]
        ):
            seen.add(em_lower)
            result.append(em)

    return result[:10]  # Limiter


def chercher_informations_formation(url_etablissement: str, nom_formation: str) -> dict:
    """
    Scrape le site d'un établissement pour trouver :
    - Emails de contact
    - Lien de candidature
    - Date limite de dépôt
    - Responsable de la formation

    Retourne un dict avec les informations trouvées.
    """
    info = {
        "url": url_etablissement,
        "nom_formation": nom_formation,
        "emails": [],
        "lien_candidature": None,
        "date_limite": None,
        "responsable": None,
        "texte_pertinent": "",
        "erreur": None,
    }

    soup = _get_page(url_etablissement)
    if not soup:
        info["erreur"] = f"Impossible d'accéder à {url_etablissement}"
        return info

    # Extraire emails de la page principale
    info["emails"] = extraire_emails_page(url_etablissement)

    # Chercher liens vers la formation
    formation_keywords = _mots_cles_formation(nom_formation)
    candidature_keywords = ["candidat", "inscription", "ecandidat", "postuler", "dossier"]

    liens_formation = []
    liens_candidature = []

    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        texte_lien = a.get_text(strip=True).lower()
        full_url = urljoin(url_etablissement, a["href"])

        if any(kw in href or kw in texte_lien for kw in formation_keywords):
            liens_formation.append(full_url)
        if any(kw in href or kw in texte_lien for kw in candidature_keywords):
            liens_candidature.append(full_url)

    # Tenter de visiter la première page formation trouvée
    if liens_formation:
        page_form = _get_page(liens_formation[0])
        if page_form:
            # Chercher emails supplémentaires
            emails_page = extraire_emails_page(liens_formation[0])
            info["emails"].extend(emails_page)

            # Chercher dates limites
            texte = page_form.get_text(separator=" ")
            info["texte_pertinent"] = texte[:2000]

            date_patterns = [
                r"avant le (\d{1,2}\s+\w+\s+20\d{2})",
                r"jusqu'au (\d{1,2}\s+\w+\s+20\d{2})",
                r"date limite[^:]*:\s*(\d{1,2}[/\-]\d{1,2}[/\-]20\d{2})",
                r"(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+20\d{2})",
            ]
            for pattern in date_patterns:
                match = re.search(pattern, texte, re.IGNORECASE)
                if match:
                    info["date_limite"] = match.group(1)
                    break

            # Chercher lien de candidature dans la page formation
            for a in page_form.find_all("a", href=True):
                if any(kw in a["href"].lower() for kw in candidature_keywords):
                    info["lien_candidature"] = urljoin(liens_formation[0], a["href"])
                    break

    if liens_candidature and not info["lien_candidature"]:
        info["lien_candidature"] = liens_candidature[0]

    # Dédupliquer emails
    info["emails"] = list(dict.fromkeys(info["emails"]))

    return info


def _mots_cles_formation(nom_formation: str) -> list[str]:
    """Génère les mots-clés de recherche depuis le nom de la formation."""
    keywords = ["licence-pro", "licence_pro", "lp-", "geii", "automatisme", "aii",
                "sarii", "industriel", "informatique-industrielle"]
    # Ajouter les mots du nom de la formation
    mots = re.sub(r"[^a-zA-Z\s]", "", nom_formation.lower()).split()
    keywords.extend([m for m in mots if len(m) > 4])
    return keywords


def rechercher_contact_secretariat(nom_iut: str, ville: str, nom_formation: str) -> dict:
    """
    Construit un résultat de contact structuré à partir des informations connues.
    Utilisé comme fallback si le scraping échoue.
    """
    domaine_suggestions = {
        "IUT de Nantes": "univ-nantes.fr",
        "IUT Grenoble": "univ-grenoble-alpes.fr",
        "IUT Lyon": "univ-lyon1.fr",
        "IUT Paris-Saclay": "universite-paris-saclay.fr",
        "IUT de Bordeaux": "u-bordeaux.fr",
        "IUT Cachan": "universite-paris-saclay.fr",
        "IUT de Valenciennes": "uphf.fr",
        "IUT de Rennes": "univ-rennes1.fr",
        "IMT Nord Europe": "imt-nord-europe.fr",
        "CESI": "cesi.fr",
    }

    domaine = None
    for key, val in domaine_suggestions.items():
        if key.lower() in nom_iut.lower():
            domaine = val
            break

    return {
        "nom_iut": nom_iut,
        "ville": ville,
        "nom_formation": nom_formation,
        "email_suggestion": f"secretariat-lp@{domaine}" if domaine else "À rechercher manuellement",
        "lien_candidature_suggestion": "https://ecandidat.univ-xx.fr (à adapter)",
        "note": "Informations à confirmer directement sur le site de l'établissement",
    }
