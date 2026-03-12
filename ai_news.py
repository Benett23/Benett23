#!/usr/bin/env python3
"""
Actualités IA quotidiennes - Envoi par email chaque matin.
Sources: flux RSS de sites spécialisés en IA.
"""

import os
import smtplib
import ssl
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from dotenv import load_dotenv

load_dotenv()

# Flux RSS de sources IA (en français et anglais traduits)
RSS_FEEDS = [
    {"url": "https://www.lemondeinformatique.fr/flux-rss/thematique/intelligence-artificielle/rss.xml", "source": "Le Monde Informatique"},
    {"url": "https://www.01net.com/rss/actualites/", "source": "01net"},
    {"url": "https://www.journaldunet.com/intelligence-artificielle/rss/", "source": "Journal du Net"},
    {"url": "https://www.zdnet.fr/feeds/rss/actualites/", "source": "ZDNet FR"},
    {"url": "https://www.numerama.com/feed/", "source": "Numerama"},
]

AI_KEYWORDS = [
    "intelligence artificielle", "ia", "machine learning", "deep learning",
    "chatgpt", "gpt", "llm", "openai", "google gemini", "mistral",
    "algorithme", "neural", "modèle", "anthropic", "claude", "robot",
    "automation", "automatisation", "génératif", "generative ai",
]

MAX_ARTICLES = 10


def fetch_rss(feed_info: dict) -> list[dict]:
    """Récupère et parse un flux RSS, filtre les articles IA."""
    articles = []
    try:
        resp = requests.get(feed_info["url"], timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        namespace = {"atom": "http://www.w3.org/2005/Atom"}

        # Support RSS 2.0 et Atom
        items = root.findall(".//item") or root.findall(".//atom:entry", namespace)

        yesterday = datetime.now(timezone.utc) - timedelta(hours=36)

        for item in items:
            title = (item.findtext("title") or item.findtext("atom:title", namespaces=namespace) or "").strip()
            link = (item.findtext("link") or item.findtext("atom:link", namespaces=namespace) or "").strip()
            description = (
                item.findtext("description")
                or item.findtext("atom:summary", namespaces=namespace)
                or ""
            ).strip()

            # Filtre par mot-clé IA
            text = (title + " " + description).lower()
            if not any(kw in text for kw in AI_KEYWORDS):
                continue

            articles.append({
                "title": title,
                "link": link,
                "description": description[:300] + ("..." if len(description) > 300 else ""),
                "source": feed_info["source"],
            })

    except Exception as e:
        print(f"[WARN] Impossible de récupérer {feed_info['source']}: {e}")

    return articles


def build_html(articles: list[dict]) -> str:
    """Génère le corps HTML de l'email."""
    date_str = datetime.now().strftime("%A %d %B %Y").capitalize()

    items_html = ""
    for art in articles:
        items_html += f"""
        <div style="margin-bottom:24px; border-left:4px solid #4A90E2; padding-left:12px;">
            <a href="{art['link']}" style="font-size:16px; font-weight:bold; color:#1a1a1a; text-decoration:none;">
                {art['title']}
            </a>
            <p style="font-size:12px; color:#888; margin:4px 0;">Source : {art['source']}</p>
            <p style="font-size:14px; color:#444; margin:6px 0;">{art['description']}</p>
        </div>
        """

    if not items_html:
        items_html = "<p>Aucun article IA trouvé aujourd'hui. Vérifiez les flux RSS configurés.</p>"

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width:700px; margin:auto; padding:20px; background:#f9f9f9;">
        <div style="background:#4A90E2; padding:20px; border-radius:8px 8px 0 0;">
            <h1 style="color:white; margin:0; font-size:22px;">Actualités IA du {date_str}</h1>
            <p style="color:#d0e8ff; margin:6px 0 0 0; font-size:14px;">{len(articles)} article(s) sélectionné(s)</p>
        </div>
        <div style="background:white; padding:24px; border-radius:0 0 8px 8px; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            {items_html}
        </div>
        <p style="text-align:center; color:#aaa; font-size:12px; margin-top:16px;">
            Envoyé automatiquement par ai_news.py · {datetime.now().strftime("%H:%M")}
        </p>
    </body>
    </html>
    """


def send_email(subject: str, html_body: str) -> None:
    """Envoie l'email via SMTP."""
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    email_from = os.environ["EMAIL_FROM"]
    email_to = os.environ["EMAIL_TO"]
    use_tls = os.environ.get("SMTP_TLS", "true").lower() == "true"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = email_to
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if use_tls:
            server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.sendmail(email_from, email_to, msg.as_string())

    print(f"[OK] Email envoyé à {email_to}")


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Récupération des actualités IA...")

    all_articles = []
    for feed in RSS_FEEDS:
        articles = fetch_rss(feed)
        all_articles.extend(articles)
        print(f"  {feed['source']}: {len(articles)} article(s) IA trouvé(s)")

    # Déduplique par titre
    seen = set()
    unique_articles = []
    for art in all_articles:
        if art["title"] not in seen:
            seen.add(art["title"])
            unique_articles.append(art)

    unique_articles = unique_articles[:MAX_ARTICLES]

    date_str = datetime.now().strftime("%d/%m/%Y")
    subject = f"Actualités IA du {date_str} ({len(unique_articles)} articles)"
    html = build_html(unique_articles)

    send_email(subject, html)


if __name__ == "__main__":
    main()
