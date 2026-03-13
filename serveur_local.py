#!/usr/bin/env python3
"""
Serveur local pour la PWA PTP.
Lance un serveur HTTP sur http://localhost:8080

Usage :
  python serveur_local.py
"""

import http.server
import os
import socketserver
import webbrowser
from pathlib import Path

PORT = 8080
PWA_DIR = Path(__file__).parent / "pwa"


class PWAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PWA_DIR), **kwargs)

    def end_headers(self):
        # Headers requis pour le Service Worker
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Service-Worker-Allowed", "/")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # Silencieux


if __name__ == "__main__":
    os.chdir(PWA_DIR)
    url = f"http://localhost:{PORT}"

    print(f"\n🖥️  Serveur local PTP démarré")
    print(f"   → {url}")
    print(f"   → {url}/ecoles.html")
    print(f"\n   (Ctrl+C pour arrêter)\n")

    webbrowser.open(url)

    with socketserver.TCPServer(("", PORT), PWAHandler) as httpd:
        httpd.serve_forever()
