"""
Script de build exécuté par Vercel avant le déploiement.
- Injecte les variables d'environnement (Supabase, OneSignal) dans le PWA
- Génère les icônes PNG si Pillow est disponible

Variables d'environnement requises dans Vercel :
  SUPABASE_URL
  SUPABASE_ANON_KEY
  ONESIGNAL_APP_ID
"""

import os
import re
import sys

PWA_DIR = os.path.join(os.path.dirname(__file__), "..", "pwa")


def remplacer_placeholders(filepath: str, replacements: dict) -> None:
    """Remplace les placeholders __VAR__ dans un fichier HTML/JS."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    for placeholder, value in replacements.items():
        content = content.replace(f"__{placeholder}__", value or "")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ {os.path.basename(filepath)} — placeholders injectés")


def main():
    print("🔨 Build PWA — injection des variables d'environnement")

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")
    onesignal_app_id = os.getenv("ONESIGNAL_APP_ID", "")

    if not supabase_url:
        print("  ⚠️  SUPABASE_URL non défini — le PWA tournera en mode offline uniquement")
    if not supabase_anon_key:
        print("  ⚠️  SUPABASE_ANON_KEY non défini")
    if not onesignal_app_id:
        print("  ⚠️  ONESIGNAL_APP_ID non défini — pas de notifications push")

    replacements = {
        "SUPABASE_URL": supabase_url,
        "SUPABASE_ANON_KEY": supabase_anon_key,
        "ONESIGNAL_APP_ID": onesignal_app_id,
    }

    # Injecter dans tous les fichiers HTML et JS du PWA
    for fname in ["index.html", "ecoles.html", "sw.js"]:
        fpath = os.path.join(PWA_DIR, fname)
        if os.path.isfile(fpath):
            remplacer_placeholders(fpath, replacements)

    # Générer les icônes PNG si Pillow disponible
    print("\n🎨 Génération des icônes…")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from scripts.generate_pwa_icons import generer_avec_pillow
        generer_avec_pillow()
    except ImportError:
        print("  ℹ️  Pillow absent — icônes SVG utilisées (fonctionnel sur Android/Chrome)")
        from scripts.generate_pwa_icons import generer_svg_fallback
        generer_svg_fallback()

        # Mettre à jour le manifest pour pointer vers les SVG
        manifest_path = os.path.join(PWA_DIR, "manifest.json")
        with open(manifest_path, "r") as f:
            content = f.read()
        content = content.replace(".png", ".svg")
        with open(manifest_path, "w") as f:
            f.write(content)
        print("  ℹ️  manifest.json mis à jour pour utiliser les SVG")

    print("\n✅ Build PWA terminé")


if __name__ == "__main__":
    main()
