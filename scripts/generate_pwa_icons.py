"""
Génère les icônes PNG pour la PWA (192×192, 512×512, 180×180).
Utilise Pillow si disponible, sinon génère un SVG converti en PNG via cairosvg.

Usage :
  pip install Pillow
  python scripts/generate_pwa_icons.py
"""

import os
import sys

ICONS_DIR = os.path.join(os.path.dirname(__file__), "..", "pwa", "icons")


def generer_avec_pillow():
    from PIL import Image, ImageDraw, ImageFont

    os.makedirs(ICONS_DIR, exist_ok=True)

    for size in (192, 512, 180):
        img = Image.new("RGBA", (size, size), (31, 73, 125, 255))  # Bleu PTP
        draw = ImageDraw.Draw(img)

        # Rond intérieur légèrement plus clair
        margin = int(size * 0.08)
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=int(size * 0.2),
            fill=(68, 114, 196, 255),
        )

        # Emoji / texte au centre
        emoji = "📋"
        try:
            # Essayer une police système
            font_size = int(size * 0.45)
            font = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", font_size)
        except Exception:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", int(size * 0.4))
            except Exception:
                font = ImageFont.load_default()
                emoji = "PTP"

        # Centrer
        bbox = draw.textbbox((0, 0), emoji, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (size - text_w) // 2 - bbox[0]
        y = (size - text_h) // 2 - bbox[1]
        draw.text((x, y), emoji, font=font, embedded_color=True)

        path = os.path.join(ICONS_DIR, f"icon-{size}.png")
        img.save(path, "PNG", optimize=True)
        print(f"  ✅ {path}")


def generer_svg_fallback():
    """Génère des icônes SVG simples (sans Pillow)."""
    os.makedirs(ICONS_DIR, exist_ok=True)

    # SVG bleu PTP avec texte "PTP"
    svg_template = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s} {s}" width="{s}" height="{s}">
  <rect width="{s}" height="{s}" rx="{r}" fill="#1F497D"/>
  <rect x="{m}" y="{m}" width="{inner}" height="{inner}" rx="{ri}" fill="#4472C4"/>
  <text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle"
    font-family="-apple-system,BlinkMacSystemFont,sans-serif"
    font-size="{fs}" font-weight="800" fill="white">PTP</text>
</svg>"""

    for size in (192, 512, 180):
        margin = int(size * 0.08)
        inner = size - 2 * margin
        svg = svg_template.format(
            s=size,
            r=int(size * 0.22),
            m=margin,
            inner=inner,
            ri=int(size * 0.15),
            fs=int(size * 0.28),
        )
        path = os.path.join(ICONS_DIR, f"icon-{size}.svg")
        with open(path, "w") as f:
            f.write(svg)
        print(f"  ✅ {path} (SVG — renommez en .png si besoin)")

    print("\n  ℹ️  Pour des PNG, installez Pillow : pip install Pillow")
    print("  ℹ️  Ou convertissez les SVG en ligne : https://cloudconvert.com/svg-to-png")


if __name__ == "__main__":
    print("🎨 Génération des icônes PWA…")
    try:
        import PIL
        generer_avec_pillow()
        print("\n✅ Icônes PNG générées dans pwa/icons/")
    except ImportError:
        print("  ⚠️  Pillow non installé → génération SVG")
        generer_svg_fallback()
