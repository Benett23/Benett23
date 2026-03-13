#!/usr/bin/env python3
"""
Tableau de bord web pour le générateur de clips chrétiens.

Routes :
  GET  /              → page d'accueil avec formulaire
  POST /generate      → génère un clip et le retourne
  GET  /clips         → liste des clips générés
  GET  /clips/<name>  → télécharge un clip
  GET  /health        → status API

Lancer : python app.py  (ou flask run)
"""

import os
import threading
from pathlib import Path
from datetime import datetime

from flask import (
    Flask,
    jsonify,
    render_template_string,
    request,
    send_file,
    url_for,
)

from content_library import THEMES, get_random_prayer, get_random_verse
from clip_generator import generate_image_clip, generate_video_clip, OUTPUT_DIR

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB upload max

# ---------------------------------------------------------------------------
# Templates HTML intégrés (pas besoin de dossier templates séparé)
# ---------------------------------------------------------------------------

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>✝ Générateur de Clips Chrétiens</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      min-height: 100vh;
      color: #e0e0e0;
    }
    header {
      background: rgba(255,255,255,0.05);
      border-bottom: 1px solid rgba(255,215,0,0.3);
      padding: 20px 40px;
      display: flex;
      align-items: center;
      gap: 16px;
    }
    header h1 { font-size: 1.8rem; color: #ffd700; }
    header p  { color: #aaa; font-size: 0.9rem; }
    .container { max-width: 900px; margin: 40px auto; padding: 0 20px; }
    .card {
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 16px;
      padding: 32px;
      margin-bottom: 24px;
    }
    .card h2 { font-size: 1.2rem; color: #ffd700; margin-bottom: 20px; }
    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    label { font-size: 0.85rem; color: #aaa; display: block; margin-bottom: 6px; }
    select, input[type=number], input[type=text] {
      width: 100%;
      background: rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 8px;
      padding: 10px 14px;
      color: #fff;
      font-size: 0.95rem;
    }
    select option { background: #1a1a2e; }
    .checkbox-row { display: flex; align-items: center; gap: 10px; margin-top: 4px; }
    .checkbox-row input { width: auto; }
    .btn {
      display: inline-block;
      padding: 14px 32px;
      border-radius: 10px;
      border: none;
      cursor: pointer;
      font-size: 1rem;
      font-weight: bold;
      transition: opacity 0.2s;
    }
    .btn:hover { opacity: 0.85; }
    .btn-primary { background: linear-gradient(135deg, #ffd700, #ff8c00); color: #1a1a2e; }
    .btn-secondary { background: rgba(255,255,255,0.1); color: #fff; border: 1px solid rgba(255,255,255,0.2); }
    .result-box {
      background: rgba(0,255,100,0.07);
      border: 1px solid rgba(0,255,100,0.2);
      border-radius: 12px;
      padding: 20px;
      margin-top: 20px;
      display: none;
    }
    .result-box.error {
      background: rgba(255,50,50,0.1);
      border-color: rgba(255,50,50,0.3);
    }
    .result-box a { color: #ffd700; text-decoration: none; font-weight: bold; }
    .clips-list { list-style: none; }
    .clips-list li {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid rgba(255,255,255,0.07);
    }
    .clips-list li:last-child { border-bottom: none; }
    .clip-name { font-size: 0.9rem; color: #ccc; }
    .clip-size { font-size: 0.8rem; color: #888; margin-left: 12px; }
    .spinner { display: none; margin-left: 10px; }
    .loading .spinner { display: inline-block; }
    .loading .btn-text { display: none; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .spinner-icon {
      display: inline-block;
      width: 18px; height: 18px;
      border: 3px solid rgba(26,26,46,0.4);
      border-top-color: #1a1a2e;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      vertical-align: middle;
    }
    .verse-preview {
      background: rgba(255,215,0,0.06);
      border-left: 3px solid #ffd700;
      padding: 12px 16px;
      border-radius: 0 8px 8px 0;
      font-style: italic;
      color: #ddd;
      font-size: 0.9rem;
      margin-top: 16px;
    }
    .verse-preview strong { color: #ffd700; font-style: normal; }
  </style>
</head>
<body>

<header>
  <div>
    <h1>✝ Générateur de Clips Chrétiens</h1>
    <p>Créez des clips inspirants avec versets, prières et visuels automatiquement</p>
  </div>
</header>

<div class="container">

  <!-- Aperçu aléatoire d'un verset -->
  <div class="card">
    <h2>📖 Verset du moment</h2>
    <div class="verse-preview">
      « {{ verse.text }} »
      <br><strong>— {{ verse.reference }}</strong>
      <span style="float:right; font-size:0.8rem; color:#888;">Thème : {{ verse.theme }}</span>
    </div>
  </div>

  <!-- Formulaire de génération -->
  <div class="card">
    <h2>🎬 Générer un clip</h2>
    <form id="genForm" onsubmit="generateClip(event)">
      <div class="form-grid">

        <div>
          <label>Format de sortie</label>
          <select name="format" id="format">
            <option value="image">Image (PNG)</option>
            <option value="video">Vidéo (MP4)</option>
          </select>
        </div>

        <div>
          <label>Thème</label>
          <select name="theme">
            <option value="">Aléatoire (IA choisit)</option>
            {% for t in themes %}
            <option value="{{ t }}">{{ t|capitalize }}</option>
            {% endfor %}
          </select>
        </div>

        <div id="durationField" style="display:none;">
          <label>Durée (secondes)</label>
          <input type="number" name="duration" value="15" min="5" max="60"/>
        </div>

        <div style="display:flex; align-items:flex-end;">
          <div>
            <label>Options</label>
            <div class="checkbox-row">
              <input type="checkbox" name="include_prayer" id="include_prayer" checked/>
              <label for="include_prayer" style="margin:0;">Inclure une prière</label>
            </div>
          </div>
        </div>

      </div>

      <div style="margin-top:24px; display:flex; gap:12px; align-items:center;">
        <button type="submit" class="btn btn-primary" id="generateBtn">
          <span class="btn-text">✨ Générer le clip</span>
          <span class="spinner"><span class="spinner-icon"></span> Génération…</span>
        </button>
        <a href="/clips" class="btn btn-secondary">📁 Mes clips</a>
      </div>
    </form>

    <div class="result-box" id="resultBox">
      <span id="resultMsg"></span>
    </div>
  </div>

  <!-- Liste des derniers clips -->
  {% if clips %}
  <div class="card">
    <h2>📁 Derniers clips générés</h2>
    <ul class="clips-list">
      {% for c in clips %}
      <li>
        <span>
          <span class="clip-name">{{ c.name }}</span>
          <span class="clip-size">{{ c.size }}</span>
        </span>
        <a href="/clips/{{ c.name }}" class="btn btn-secondary" style="padding:6px 16px; font-size:0.85rem;">
          ⬇ Télécharger
        </a>
      </li>
      {% endfor %}
    </ul>
  </div>
  {% endif %}

</div>

<script>
  // Affiche/masque le champ durée selon le format
  document.getElementById('format').addEventListener('change', function() {
    document.getElementById('durationField').style.display =
      this.value === 'video' ? 'block' : 'none';
  });

  async function generateClip(e) {
    e.preventDefault();
    const form = e.target;
    const btn = document.getElementById('generateBtn');
    const resultBox = document.getElementById('resultBox');
    const resultMsg = document.getElementById('resultMsg');

    btn.classList.add('loading');
    resultBox.style.display = 'none';
    resultBox.classList.remove('error');

    const data = {
      format: form.format.value,
      theme: form.theme.value || null,
      include_prayer: form.include_prayer.checked,
      duration: parseInt(form.duration?.value || 15),
    };

    try {
      const resp = await fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const json = await resp.json();

      if (json.success) {
        resultMsg.innerHTML = `✅ Clip créé : <a href="/clips/${json.filename}">⬇ ${json.filename}</a>`;
      } else {
        resultBox.classList.add('error');
        resultMsg.textContent = '❌ Erreur : ' + json.error;
      }
    } catch (err) {
      resultBox.classList.add('error');
      resultMsg.textContent = '❌ Erreur réseau : ' + err.message;
    }

    btn.classList.remove('loading');
    resultBox.style.display = 'block';
  }
</script>
</body>
</html>
"""

CLIPS_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8"/>
  <title>Mes Clips</title>
  <style>
    body { font-family: Arial, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 40px; }
    h1 { color: #ffd700; margin-bottom: 24px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.1); }
    th { color: #ffd700; font-size: 0.85rem; text-transform: uppercase; }
    a { color: #ffd700; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .back { display: inline-block; margin-bottom: 20px; color: #aaa; font-size: 0.9rem; }
  </style>
</head>
<body>
  <a href="/" class="back">← Retour au tableau de bord</a>
  <h1>📁 Clips générés</h1>
  {% if clips %}
  <table>
    <tr><th>Fichier</th><th>Taille</th><th>Date</th><th>Action</th></tr>
    {% for c in clips %}
    <tr>
      <td>{{ c.name }}</td>
      <td>{{ c.size }}</td>
      <td>{{ c.date }}</td>
      <td><a href="/clips/{{ c.name }}">⬇ Télécharger</a></td>
    </tr>
    {% endfor %}
  </table>
  {% else %}
  <p style="color:#888;">Aucun clip généré pour l'instant.</p>
  {% endif %}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _list_clips(limit: int = 10) -> list[dict]:
    """Retourne les derniers clips du dossier output/."""
    if not OUTPUT_DIR.exists():
        return []
    files = sorted(
        [f for f in OUTPUT_DIR.iterdir() if f.suffix in (".png", ".mp4")],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:limit]
    result = []
    for f in files:
        size_kb = f.stat().st_size / 1024
        size_str = f"{size_kb:.0f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
        date_str = datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
        result.append({"name": f.name, "size": size_str, "date": date_str})
    return result


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    verse = get_random_verse()
    clips = _list_clips(5)
    return render_template_string(DASHBOARD_HTML, verse=verse, themes=THEMES, clips=clips)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    fmt = data.get("format", "image")
    theme = data.get("theme") or None
    include_prayer = bool(data.get("include_prayer", True))
    duration = int(data.get("duration", 15))

    try:
        if fmt == "video":
            path = generate_video_clip(
                theme=theme,
                include_prayer=include_prayer,
                duration=duration,
            )
        else:
            path = generate_image_clip(
                theme=theme,
                include_prayer=include_prayer,
            )
        filename = Path(path).name
        return jsonify({"success": True, "filename": filename, "path": path})
    except Exception as exc:
        app.logger.error("Erreur de génération : %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/clips")
def list_clips():
    clips = _list_clips(50)
    return render_template_string(CLIPS_HTML, clips=clips)


@app.route("/clips/<filename>")
def download_clip(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        return jsonify({"error": "Fichier introuvable"}), 404
    return send_file(str(file_path.resolve()), as_attachment=True)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "output_dir": str(OUTPUT_DIR),
        "clips_count": len(list(OUTPUT_DIR.glob("*"))) if OUTPUT_DIR.exists() else 0,
        "timestamp": datetime.now().isoformat(),
    })


# ---------------------------------------------------------------------------
# Entrée principale
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    print(f"[INFO] Tableau de bord lancé sur http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
