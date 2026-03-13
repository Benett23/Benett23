#!/usr/bin/env python3
"""
Générateur de clips chrétiens.

Assemble automatiquement :
  - Un verset biblique (sélection aléatoire ou thématique)
  - Une prière chrétienne
  - Une image de fond (couleur dégradée ou fichier)
  - Une musique de fond (optionnelle)

Sortie :
  - Image PNG (Pillow)
  - Vidéo MP4 via Remotion (Node.js)

Dépendances :
  Python : Pillow, python-dotenv
  Node   : remotion, @remotion/cli (dans ./remotion/)
"""

import json
import os
import random
import subprocess
import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from content_library import Prayer, Verse, get_content_by_theme, get_random_prayer, get_random_verse

# ---------------------------------------------------------------------------
# Constantes de rendu
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 1080, 1920   # Format portrait 9:16 (Reels / Shorts)
CLIP_DURATION = 15           # secondes (utilisé si vidéo)
FPS = 24

# Palettes de couleurs par thème (dégradés linéaires simulés)
THEME_GRADIENTS: dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]] = {
    "foi":      ((30, 60, 114),   (42, 82, 152)),
    "espoir":   ((20, 130, 80),   (10, 80, 50)),
    "amour":    ((180, 30, 60),   (120, 10, 30)),
    "paix":     ((30, 100, 170),  (10, 60, 120)),
    "force":    ((80, 40, 10),    (140, 80, 20)),
    "grâce":    ((100, 20, 140),  (60, 10, 100)),
    "louange":  ((200, 140, 10),  (180, 100, 0)),
    "guérison": ((10, 150, 150),  (0, 100, 120)),
}

OUTPUT_DIR = Path("output")
ASSETS_DIR = Path("assets")
FONTS_DIR = ASSETS_DIR / "fonts"
MUSIC_DIR = ASSETS_DIR / "music"
IMAGES_DIR = ASSETS_DIR / "images"

# Polices de secours (Pillow utilise la police par défaut si introuvable)
FONT_TITLE = str(FONTS_DIR / "title.ttf") if (FONTS_DIR / "title.ttf").exists() else None
FONT_BODY = str(FONTS_DIR / "body.ttf") if (FONTS_DIR / "body.ttf").exists() else None


# ---------------------------------------------------------------------------
# Utilitaires image
# ---------------------------------------------------------------------------

def _load_font(path: str | None, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if path and Path(path).exists():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _gradient_background(
    color_top: tuple[int, int, int],
    color_bottom: tuple[int, int, int],
) -> Image.Image:
    """Crée une image avec un dégradé vertical."""
    img = Image.new("RGB", (WIDTH, HEIGHT))
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
        for x in range(WIDTH):
            img.putpixel((x, y), (r, g, b))
    return img


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y_start: int,
    max_width: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, int, int, int],
    line_spacing: int = 10,
) -> int:
    """Dessine du texte centré, avec retour à la ligne automatique. Retourne le y final."""
    avg_char_width = 18
    chars_per_line = max(1, max_width // avg_char_width)
    lines = textwrap.wrap(text, width=chars_per_line)
    y = y_start
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (WIDTH - text_w) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += (bbox[3] - bbox[1]) + line_spacing
    return y


def _overlay_background_image(base: Image.Image, image_path: str) -> Image.Image:
    """Superpose une image de fond redimensionnée avec transparence."""
    try:
        bg = Image.open(image_path).convert("RGBA").resize((WIDTH, HEIGHT))
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 160))
        bg = Image.alpha_composite(bg, overlay)
        return Image.alpha_composite(base.convert("RGBA"), bg).convert("RGB")
    except Exception:
        return base


# ---------------------------------------------------------------------------
# Composition de la frame principale
# ---------------------------------------------------------------------------

def compose_frame(
    verse: Verse,
    prayer: Prayer,
    bg_image_path: str | None = None,
    include_prayer: bool = True,
) -> Image.Image:
    """
    Génère l'image (frame) principale du clip.
    """
    colors = THEME_GRADIENTS.get(verse.theme, ((30, 60, 114), (10, 30, 80)))
    img = _gradient_background(colors[0], colors[1])

    if bg_image_path:
        img = _overlay_background_image(img, bg_image_path)

    draw = ImageDraw.Draw(img)

    # --- Croix / symbole décoratif ---
    cross_color = (255, 255, 255, 60)
    cx, cy = WIDTH // 2, 200
    draw.rectangle([cx - 8, cy - 60, cx + 8, cy + 60], fill=(255, 255, 255, 40))
    draw.rectangle([cx - 40, cy - 10, cx + 40, cy + 10], fill=(255, 255, 255, 40))

    # --- Titre du thème ---
    font_theme = _load_font(FONT_TITLE, 42)
    theme_label = verse.theme.upper()
    bbox = draw.textbbox((0, 0), theme_label, font=font_theme)
    draw.text(
        ((WIDTH - (bbox[2] - bbox[0])) // 2, 310),
        theme_label,
        font=font_theme,
        fill=(255, 215, 0, 220),
    )

    # --- Ligne séparatrice ---
    draw.line([(120, 390), (WIDTH - 120, 390)], fill=(255, 255, 255, 80), width=2)

    # --- Verset ---
    font_verse = _load_font(FONT_BODY, 48)
    y = _draw_centered_text(
        draw,
        f'« {verse.text} »',
        y_start=430,
        max_width=WIDTH - 140,
        font=font_verse,
        fill=(255, 255, 255, 240),
        line_spacing=14,
    )

    # Référence du verset
    font_ref = _load_font(FONT_TITLE, 38)
    y += 20
    ref_bbox = draw.textbbox((0, 0), verse.reference, font=font_ref)
    draw.text(
        ((WIDTH - (ref_bbox[2] - ref_bbox[0])) // 2, y),
        verse.reference,
        font=font_ref,
        fill=(255, 215, 0, 200),
    )
    y += (ref_bbox[3] - ref_bbox[1]) + 60

    if include_prayer:
        # --- Ligne séparatrice ---
        draw.line([(120, y), (WIDTH - 120, y)], fill=(255, 255, 255, 60), width=1)
        y += 40

        # Titre de la prière
        font_prayer_title = _load_font(FONT_TITLE, 40)
        title_bbox = draw.textbbox((0, 0), prayer.title, font=font_prayer_title)
        draw.text(
            ((WIDTH - (title_bbox[2] - title_bbox[0])) // 2, y),
            prayer.title,
            font=font_prayer_title,
            fill=(200, 230, 255, 220),
        )
        y += (title_bbox[3] - title_bbox[1]) + 24

        # Texte de la prière
        font_prayer = _load_font(FONT_BODY, 38)
        _draw_centered_text(
            draw,
            prayer.text,
            y_start=y,
            max_width=WIDTH - 160,
            font=font_prayer,
            fill=(220, 220, 255, 200),
            line_spacing=12,
        )

    # --- Filigrane / signature ---
    font_wm = _load_font(FONT_BODY, 30)
    wm_text = "✝  Parole de Vie"
    wm_bbox = draw.textbbox((0, 0), wm_text, font=font_wm)
    draw.text(
        ((WIDTH - (wm_bbox[2] - wm_bbox[0])) // 2, HEIGHT - 80),
        wm_text,
        font=font_wm,
        fill=(255, 255, 255, 120),
    )

    return img


# ---------------------------------------------------------------------------
# Export PNG
# ---------------------------------------------------------------------------

def generate_image_clip(
    theme: str | None = None,
    bg_image_path: str | None = None,
    include_prayer: bool = True,
    output_path: str | None = None,
) -> str:
    """
    Génère un clip image (PNG) et le sauvegarde.
    Retourne le chemin du fichier généré.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    verse = get_random_verse(theme)
    prayer = get_random_prayer(verse.theme)

    # Cherche une image de fond dans assets/images si disponible et non fournie
    if not bg_image_path and IMAGES_DIR.exists():
        candidates = list(IMAGES_DIR.glob("*.jpg")) + list(IMAGES_DIR.glob("*.png"))
        theme_candidates = [p for p in candidates if verse.theme in p.stem.lower()]
        if theme_candidates:
            bg_image_path = str(random.choice(theme_candidates))
        elif candidates:
            bg_image_path = str(random.choice(candidates))

    frame = compose_frame(verse, prayer, bg_image_path, include_prayer)

    if not output_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(OUTPUT_DIR / f"clip_{verse.theme}_{ts}.png")

    frame.save(output_path, "PNG")
    print(f"[OK] Image générée : {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Export MP4 via Remotion
# ---------------------------------------------------------------------------

REMOTION_DIR = Path(__file__).parent / "remotion"


def _pick_music(theme: str) -> str | None:
    """Cherche un fichier musical dans remotion/public/music/."""
    music_dir = REMOTION_DIR / "public" / "music"
    if not music_dir.exists():
        return None
    files = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav"))
    themed = [f for f in files if theme in f.stem.lower()]
    chosen = random.choice(themed) if themed else (random.choice(files) if files else None)
    return chosen.name if chosen else None


def _pick_bg_image(theme: str) -> str | None:
    """Cherche une image de fond dans remotion/public/images/."""
    img_dir = REMOTION_DIR / "public" / "images"
    if not img_dir.exists():
        return None
    files = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))
    themed = [f for f in files if theme in f.stem.lower()]
    chosen = random.choice(themed) if themed else (random.choice(files) if files else None)
    return chosen.name if chosen else None


def generate_video_clip(
    theme: str | None = None,
    bg_image_path: str | None = None,
    include_prayer: bool = True,
    duration: int = CLIP_DURATION,
    output_path: str | None = None,
    composition_id: str = "ChristianClip",
) -> str:
    """
    Génère un clip vidéo MP4 via Remotion (Node.js).
    Nécessite : cd remotion && npm install
    Retourne le chemin du fichier généré.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    verse = get_random_verse(theme)
    prayer = get_random_prayer(verse.theme)

    music_file = _pick_music(verse.theme)
    bg_image = _pick_bg_image(verse.theme) if not bg_image_path else Path(bg_image_path).name

    if not output_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(OUTPUT_DIR / f"clip_{verse.theme}_{ts}.mp4")

    # Paramètres transmis au composant Remotion
    props = {
        "verse": verse.text,
        "reference": verse.reference,
        "theme": verse.theme,
        "prayerTitle": prayer.title,
        "prayer": prayer.text,
        "includePrayer": include_prayer,
        "musicFile": music_file,
        "bgImage": bg_image,
    }

    script = str(REMOTION_DIR / "scripts" / "render-single.mjs")
    rel_output = os.path.relpath(output_path, REMOTION_DIR)

    cmd = [
        "node",
        script,
        json.dumps(props),
        rel_output,
        composition_id,
    ]

    print(f"[INFO] Remotion render : {composition_id} → {output_path}")
    result = subprocess.run(cmd, cwd=str(REMOTION_DIR), capture_output=False, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Remotion render a échoué (code {result.returncode}).")

    print(f"[OK] Vidéo générée : {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# CLI rapide
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Générateur de clips chrétiens")
    parser.add_argument("--theme", choices=["foi", "espoir", "amour", "paix", "force", "grâce", "louange", "guérison"], help="Thème du clip")
    parser.add_argument("--format", choices=["image", "video"], default="image", help="Format de sortie")
    parser.add_argument("--no-prayer", action="store_true", help="Ne pas inclure de prière")
    parser.add_argument("--bg", help="Chemin vers une image de fond")
    parser.add_argument("--duration", type=int, default=15, help="Durée en secondes (vidéo uniquement)")
    parser.add_argument("--output", help="Chemin de sortie du fichier")
    args = parser.parse_args()

    if args.format == "video":
        generate_video_clip(
            theme=args.theme,
            bg_image_path=args.bg,
            include_prayer=not args.no_prayer,
            duration=args.duration,
            output_path=args.output,
        )
    else:
        generate_image_clip(
            theme=args.theme,
            bg_image_path=args.bg,
            include_prayer=not args.no_prayer,
            output_path=args.output,
        )
