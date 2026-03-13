"""
Génération des pages HTML du tableau de bord PTP :
- outputs/dashboard/index.html  : vue d'ensemble du projet avec coches
- outputs/dashboard/ecoles.html : tableau interactif des écoles contactées
"""

import json
import os
from datetime import datetime

from ptp_system.config import CANDIDAT, FORMATIONS_CIBLES, ETAPES_PTP, INFO_PTP


DASHBOARD_DIR = "outputs/dashboard"


def _ensure_dir():
    os.makedirs(DASHBOARD_DIR, exist_ok=True)


# ============================================================================
# PAGE 1 — index.html : Tableau de bord général
# ============================================================================

def generer_dashboard(
    documents_generes: list[dict] = None,
    nb_emails_rediges: int = 0,
    nb_etab_analyses: int = 0,
    derniere_session: str = None,
    stats_ecoles: dict = None,
) -> str:
    """
    Génère le tableau de bord principal HTML.
    Les coches auto sont basées sur les données passées.
    Les coches manuelles (étapes PTP) sont sauvegardées en localStorage.
    Retourne le chemin du fichier créé.
    """
    _ensure_dir()
    output_path = os.path.join(DASHBOARD_DIR, "index.html")

    docs = {d["type"]: d for d in (documents_generes or [])}
    has_lettre_tp = "lettre_transitions_pro" in docs
    has_lettre_iut = "lettre_iut" in docs
    has_planning = "planning_ptp" in docs
    has_contacts = "liste_contacts" in docs

    stats = stats_ecoles or {}
    total_ecoles = stats.get("total", sum(len(f["etablissements"]) for f in FORMATIONS_CIBLES))
    brouillons = stats.get("brouillon_pret", nb_emails_rediges)
    contactes = stats.get("contacte", 0)
    en_attente = stats.get("en_attente", 0)
    reponses = stats.get("reponse_recue", 0)
    admis = stats.get("admis", 0)

    session_str = derniere_session or "Aucune session"
    now_str = datetime.now().strftime("%d/%m/%Y à %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tableau de bord PTP — {CANDIDAT['nom_complet']}</title>
<style>
  :root {{
    --blue: #1F497D; --blue-light: #4472C4; --blue-pale: #EBF3FB;
    --green: #107c10; --green-bg: #dff0d8; --green-check: #28a745;
    --orange: #d67f20; --orange-bg: #fff3cd;
    --red: #c00; --red-bg: #fce4d6;
    --grey: #666; --grey-bg: #f5f5f5; --border: #ddd;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f0f4f8; color: #333; }}

  /* Header */
  .header {{ background: var(--blue); color: white; padding: 24px 32px; }}
  .header h1 {{ font-size: 1.6em; font-weight: 700; }}
  .header .meta {{ opacity: .8; font-size: .9em; margin-top: 6px; }}

  /* Navigation */
  .nav {{ background: var(--blue-light); padding: 0 32px; display: flex; gap: 4px; }}
  .nav a {{
    color: white; text-decoration: none; padding: 12px 20px; font-size: .9em;
    border-bottom: 3px solid transparent; transition: all .2s;
  }}
  .nav a:hover, .nav a.active {{ border-bottom-color: white; background: rgba(255,255,255,.1); }}

  /* Layout */
  .container {{ max-width: 1100px; margin: 0 auto; padding: 24px 20px; }}

  /* Cards */
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 28px; }}
  .card {{
    background: white; border-radius: 10px; padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,.08); text-align: center;
  }}
  .card .num {{ font-size: 2.2em; font-weight: 700; color: var(--blue); }}
  .card .label {{ color: var(--grey); font-size: .85em; margin-top: 4px; }}
  .card.green .num {{ color: var(--green); }}
  .card.orange .num {{ color: var(--orange); }}

  /* Sections */
  .section {{ background: white; border-radius: 10px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
  .section h2 {{ color: var(--blue); font-size: 1.15em; margin-bottom: 18px; padding-bottom: 10px; border-bottom: 2px solid var(--blue-pale); display: flex; align-items: center; gap: 8px; }}

  /* Checklist */
  .checklist {{ list-style: none; }}
  .checklist li {{
    display: flex; align-items: flex-start; gap: 12px;
    padding: 10px 12px; border-radius: 8px; margin-bottom: 6px;
    transition: background .15s;
  }}
  .checklist li:hover {{ background: var(--grey-bg); }}
  .checklist li.done {{ background: var(--green-bg); }}
  .checklist li.pending {{ background: var(--orange-bg); }}
  .checklist li.todo {{ background: #fff; border: 1px solid var(--border); }}

  /* Checkbox styles */
  .check-wrap {{ position: relative; width: 22px; height: 22px; flex-shrink: 0; margin-top: 1px; }}
  .check-wrap input[type=checkbox] {{ position: absolute; opacity: 0; width: 100%; height: 100%; cursor: pointer; z-index: 2; margin: 0; }}
  .check-box {{
    width: 22px; height: 22px; border-radius: 5px; border: 2px solid #ccc;
    background: white; display: flex; align-items: center; justify-content: center;
    transition: all .2s; font-size: 14px;
  }}
  .check-wrap input:checked + .check-box {{ background: var(--green-check); border-color: var(--green-check); color: white; }}
  .check-wrap input:checked + .check-box::after {{ content: '✓'; font-weight: bold; color: white; }}

  .auto-check {{ color: var(--green-check); font-size: 1.3em; flex-shrink: 0; }}
  .auto-cross {{ color: var(--grey); font-size: 1.3em; flex-shrink: 0; }}

  .item-text {{ flex: 1; }}
  .item-title {{ font-weight: 600; font-size: .95em; }}
  .item-desc {{ color: var(--grey); font-size: .82em; margin-top: 3px; }}
  .badge {{
    display: inline-block; padding: 2px 8px; border-radius: 12px;
    font-size: .75em; font-weight: 600; flex-shrink: 0; align-self: center;
  }}
  .badge.auto {{ background: var(--green-bg); color: var(--green); }}
  .badge.manual {{ background: var(--orange-bg); color: var(--orange); }}
  .badge.todo {{ background: #eee; color: #888; }}

  /* Progress bar */
  .progress-wrap {{ background: #eee; border-radius: 10px; height: 12px; margin: 8px 0 4px; overflow: hidden; }}
  .progress-bar {{ height: 100%; border-radius: 10px; background: linear-gradient(90deg, var(--blue-light), var(--blue)); transition: width .6s ease; }}

  /* Table formations */
  .form-grid {{ display: grid; gap: 12px; }}
  .form-row {{ border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
  .form-header {{
    background: var(--blue-pale); padding: 10px 14px;
    font-weight: 600; font-size: .9em; color: var(--blue);
    display: flex; align-items: center; justify-content: space-between; cursor: pointer;
  }}
  .form-body {{ padding: 12px 14px; display: none; }}
  .form-body.open {{ display: block; }}
  .prio-badge {{ background: var(--blue); color: white; border-radius: 12px; padding: 2px 10px; font-size: .75em; }}

  /* Footer */
  .footer {{ text-align: center; color: var(--grey); font-size: .8em; padding: 20px; }}

  /* Alerte dates */
  .alert {{ background: var(--orange-bg); border-left: 4px solid var(--orange); padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 16px; font-size: .9em; }}
  .alert strong {{ color: var(--orange); }}
</style>
</head>
<body>

<div class="header">
  <h1>📋 Tableau de bord PTP — {CANDIDAT['nom_complet']}</h1>
  <div class="meta">
    Technicien ascensoriste → Licence Pro Automatismes/IoT | Rentrée {INFO_PTP['rentree_cible']} |
    Dernière mise à jour : {now_str}
  </div>
</div>

<div class="nav">
  <a href="index.html" class="active">🏠 Vue d'ensemble</a>
  <a href="ecoles.html">🏫 Écoles contactées</a>
</div>

<div class="container">

  <!-- Alertes dates limites -->
  <div class="alert">
    <strong>⚡ Action prioritaire :</strong>
    Dépôt dossier PTP minimum 3 mois avant la rentrée → avant juin 2026.
    Candidatures IUT : mars–mai 2026. <a href="ecoles.html">Voir le tableau des écoles →</a>
  </div>

  <!-- KPIs -->
  <div class="cards">
    <div class="card">
      <div class="num">{total_ecoles}</div>
      <div class="label">Établissements ciblés</div>
    </div>
    <div class="card {'green' if brouillons > 0 else ''}">
      <div class="num">{brouillons}</div>
      <div class="label">Brouillons prêts</div>
    </div>
    <div class="card {'green' if contactes > 0 else 'orange'}">
      <div class="num">{contactes}</div>
      <div class="label">Écoles contactées</div>
    </div>
    <div class="card {'green' if reponses > 0 else ''}">
      <div class="num">{reponses}</div>
      <div class="label">Réponses reçues</div>
    </div>
    <div class="card {'green' if admis > 0 else ''}">
      <div class="num">{admis}</div>
      <div class="label">Admissions</div>
    </div>
  </div>

  <!-- Section 1 : Documents -->
  <div class="section">
    <h2>📄 Documents du dossier PTP</h2>
    <ul class="checklist">
      <li class="{'done' if has_lettre_tp else 'todo'}">
        {'<span class="auto-check">✅</span>' if has_lettre_tp else '<span class="auto-cross">○</span>'}
        <div class="item-text">
          <div class="item-title">Lettre de motivation — Transitions Pro (CPIR)</div>
          <div class="item-desc">
            {'Générée : ' + docs.get('lettre_transitions_pro', {}).get('path', '') if has_lettre_tp else 'À générer : python main_ptp.py --mode docs'}
          </div>
        </div>
        <span class="badge {'auto' if has_lettre_tp else 'todo'}">{'✓ Auto' if has_lettre_tp else 'À faire'}</span>
      </li>
      <li class="{'done' if has_lettre_iut else 'todo'}">
        {'<span class="auto-check">✅</span>' if has_lettre_iut else '<span class="auto-cross">○</span>'}
        <div class="item-text">
          <div class="item-title">Lettre de motivation — IUT (admissions)</div>
          <div class="item-desc">
            {'Générée : ' + docs.get('lettre_iut', {}).get('path', '') if has_lettre_iut else 'À générer avec --mode docs'}
          </div>
        </div>
        <span class="badge {'auto' if has_lettre_iut else 'todo'}">{'✓ Auto' if has_lettre_iut else 'À faire'}</span>
      </li>
      <li class="{'done' if has_planning else 'todo'}">
        {'<span class="auto-check">✅</span>' if has_planning else '<span class="auto-cross">○</span>'}
        <div class="item-text">
          <div class="item-title">Planning démarches PTP (.xlsx)</div>
          <div class="item-desc">
            {'Généré : ' + docs.get('planning_ptp', {}).get('path', '') if has_planning else 'À générer'}
          </div>
        </div>
        <span class="badge {'auto' if has_planning else 'todo'}">{'✓ Auto' if has_planning else 'À faire'}</span>
      </li>
      <li class="{'done' if has_contacts else 'todo'}">
        {'<span class="auto-check">✅</span>' if has_contacts else '<span class="auto-cross">○</span>'}
        <div class="item-text">
          <div class="item-title">Liste IUT contacts (.xlsx)</div>
          <div class="item-desc">
            {'Générée : ' + docs.get('liste_contacts', {}).get('path', '') if has_contacts else 'À générer'}
          </div>
        </div>
        <span class="badge {'auto' if has_contacts else 'todo'}">{'✓ Auto' if has_contacts else 'À faire'}</span>
      </li>
      <li class="todo" id="li-cv">
        <div class="check-wrap">
          <input type="checkbox" id="cb-cv" onchange="saveCheck('cv', this.checked)">
          <div class="check-box"></div>
        </div>
        <div class="item-text">
          <div class="item-title">CV actualisé (orienté reconversion tech)</div>
          <div class="item-desc">Vous avez déjà un CV — vérifiez qu'il mentionne : variateurs, API, NF EN 81, diagnostic</div>
        </div>
        <span class="badge manual">Manuel</span>
      </li>
    </ul>
  </div>

  <!-- Section 2 : Démarches PTP -->
  <div class="section">
    <h2>🔁 Étapes du dossier PTP</h2>
    <ul class="checklist">
{_generer_etapes_html()}
    </ul>
  </div>

  <!-- Section 3 : Candidatures par formation -->
  <div class="section">
    <h2>🏫 Candidatures par formation</h2>
    <div class="progress-wrap">
      <div class="progress-bar" id="prog-bar" style="width: {min(100, (contactes + brouillons) * 100 // max(total_ecoles, 1))}%"></div>
    </div>
    <p style="font-size:.82em;color:var(--grey);margin-bottom:16px">
      {contactes + brouillons} / {total_ecoles} établissements contactés ou en cours
      — <a href="ecoles.html">Voir le détail complet →</a>
    </p>
    <div class="form-grid" id="formations-grid">
{_generer_formations_html()}
    </div>
  </div>

  <!-- Section 4 : Financement PTP -->
  <div class="section">
    <h2>💰 Financement PTP — Transitions Pro</h2>
    <ul class="checklist">
      <li class="done">
        <span class="auto-check">✅</span>
        <div class="item-text">
          <div class="item-title">Vérification éligibilité PTP</div>
          <div class="item-desc">CDI/CDD + 24 mois d'expérience dont 12 chez l'employeur actuel ✓</div>
        </div>
        <span class="badge auto">✓ Fait</span>
      </li>
      <li class="todo" id="li-rdv-tp">
        <div class="check-wrap">
          <input type="checkbox" id="cb-rdv-tp" onchange="saveCheck('rdv-tp', this.checked)">
          <div class="check-box"></div>
        </div>
        <div class="item-text">
          <div class="item-title">Prendre RDV avec Transitions Pro de votre région</div>
          <div class="item-desc">
            Site : <a href="https://www.transitionspro.fr" target="_blank">www.transitionspro.fr</a>
            — Accompagnement gratuit pour monter le dossier
          </div>
        </div>
        <span class="badge manual">Manuel</span>
      </li>
      <li class="todo" id="li-dossier-tp">
        <div class="check-wrap">
          <input type="checkbox" id="cb-dossier-tp" onchange="saveCheck('dossier-tp', this.checked)">
          <div class="check-box"></div>
        </div>
        <div class="item-text">
          <div class="item-title">Dépôt dossier PTP</div>
          <div class="item-desc">Avant juin 2026 (3 mois avant rentrée septembre 2026)</div>
        </div>
        <span class="badge manual">Manuel</span>
      </li>
      <li class="todo" id="li-info-employeur">
        <div class="check-wrap">
          <input type="checkbox" id="cb-info-employeur" onchange="saveCheck('info-employeur', this.checked)">
          <div class="check-box"></div>
        </div>
        <div class="item-text">
          <div class="item-title">Informer l'employeur (lettre recommandée)</div>
          <div class="item-desc">Demande de congé formation — à envoyer après accord Transitions Pro</div>
        </div>
        <span class="badge manual">Manuel</span>
      </li>
      <li class="todo" id="li-financement-ok">
        <div class="check-wrap">
          <input type="checkbox" id="cb-financement-ok" onchange="saveCheck('financement-ok', this.checked)">
          <div class="check-box"></div>
        </div>
        <div class="item-text">
          <div class="item-title">Confirmation financement reçue</div>
          <div class="item-desc">Réponse ~2 mois après dépôt dossier. Couvre frais pédagogiques + salaire maintenu</div>
        </div>
        <span class="badge manual">Manuel</span>
      </li>
    </ul>
  </div>

</div>

<div class="footer">
  Système PTP Multi-Agents — {CANDIDAT['nom_complet']} |
  Généré le {now_str} |
  <a href="ecoles.html">Tableau des écoles →</a>
</div>

<script>
// --- Persistance des coches manuelles ---
const KEY = 'ptp_checks_{CANDIDAT["nom_complet"].replace(" ", "_")}';

function saveCheck(id, checked) {{
  const data = JSON.parse(localStorage.getItem(KEY) || '{{}}');
  data[id] = checked;
  localStorage.setItem(KEY, JSON.stringify(data));
  updateStyle(id, checked);
}}

function updateStyle(id, checked) {{
  const li = document.getElementById('li-' + id);
  if (!li) return;
  li.classList.remove('done', 'pending', 'todo');
  li.classList.add(checked ? 'done' : 'todo');
}}

function loadChecks() {{
  const data = JSON.parse(localStorage.getItem(KEY) || '{{}}');
  for (const [id, checked] of Object.entries(data)) {{
    const cb = document.getElementById('cb-' + id);
    if (cb) {{
      cb.checked = checked;
      updateStyle(id, checked);
    }}
  }}
}}

// --- Accordéon formations ---
document.querySelectorAll('.form-header').forEach(h => {{
  h.addEventListener('click', () => {{
    const body = h.nextElementSibling;
    body.classList.toggle('open');
    h.querySelector('.toggle-icon').textContent = body.classList.contains('open') ? '▲' : '▼';
  }});
}});

// Ouvrir la première formation par défaut
const firstBody = document.querySelector('.form-body');
const firstIcon = document.querySelector('.toggle-icon');
if (firstBody) {{ firstBody.classList.add('open'); }}
if (firstIcon) {{ firstIcon.textContent = '▲'; }}

loadChecks();
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def _generer_etapes_html() -> str:
    """Génère les lignes HTML des étapes PTP."""
    items = []
    for etape in ETAPES_PTP:
        statut = etape["statut"]
        is_done = "✅" in statut or "fait" in statut.lower()
        is_doing = "🔄" in statut or "cours" in statut.lower()
        css_class = "done" if is_done else ("pending" if is_doing else "todo")
        badge_class = "auto" if is_done else ("manual" if not is_doing else "manual")
        badge_text = "✓ Fait" if is_done else ("🔄 En cours" if is_doing else "À faire")
        check_id = f"etape-{etape['num']}"

        if is_done:
            icon = '<span class="auto-check">✅</span>'
        elif is_doing:
            icon = '<span style="font-size:1.3em">🔄</span>'
        else:
            icon = f'''<div class="check-wrap">
              <input type="checkbox" id="cb-{check_id}" onchange="saveCheck('{check_id}', this.checked)">
              <div class="check-box"></div>
            </div>'''

        items.append(f"""      <li class="{css_class}" id="li-{check_id}">
        {icon}
        <div class="item-text">
          <div class="item-title">{etape['num']}. {etape['action']}</div>
          <div class="item-desc"><strong>{etape['organisme']}</strong> — {etape['delai']} — {etape['notes']}</div>
        </div>
        <span class="badge {badge_class}">{badge_text}</span>
      </li>""")

    return "\n".join(items)


def _generer_formations_html() -> str:
    """Génère les accordéons de formations."""
    items = []
    for f in FORMATIONS_CIBLES:
        etab_rows = ""
        for etab in f["etablissements"]:
            etab_rows += f"""          <tr>
            <td>{etab['nom']}</td>
            <td>{etab['ville']}</td>
            <td>{etab.get('date_limite', 'N/A')}</td>
            <td><a href="ecoles.html">Voir →</a></td>
          </tr>
"""
        items.append(f"""    <div class="form-row">
      <div class="form-header">
        <span>⭐ Priorité {f['priorite']} — {f['nom']}</span>
        <div style="display:flex;align-items:center;gap:10px">
          <span class="prio-badge">{len(f['etablissements'])} établissements</span>
          <span class="toggle-icon">▼</span>
        </div>
      </div>
      <div class="form-body">
        <p style="color:var(--grey);font-size:.85em;margin-bottom:10px">
          Compétences visées : {' · '.join(f['competences_visees'][:3])}
        </p>
        <table style="width:100%;border-collapse:collapse;font-size:.88em">
          <thead>
            <tr style="background:var(--blue-pale)">
              <th style="padding:6px 10px;text-align:left">Établissement</th>
              <th style="padding:6px 10px;text-align:left">Ville</th>
              <th style="padding:6px 10px;text-align:left">Date limite</th>
              <th style="padding:6px 10px;text-align:left">Détail</th>
            </tr>
          </thead>
          <tbody>
{etab_rows}          </tbody>
        </table>
      </div>
    </div>""")

    return "\n".join(items)


# ============================================================================
# PAGE 2 — ecoles.html : Tableau des écoles contactées
# ============================================================================

def generer_page_ecoles(ecoles: list[dict] = None) -> str:
    """
    Génère le tableau interactif des écoles avec boutons de confirmation d'envoi.
    Retourne le chemin du fichier créé.
    """
    _ensure_dir()
    output_path = os.path.join(DASHBOARD_DIR, "ecoles.html")

    if ecoles is None:
        from ptp_system.agents.school_tracker_agent import charger_tracking
        ecoles = charger_tracking()

    now_str = datetime.now().strftime("%d/%m/%Y à %H:%M")

    # Calculer stats pour le résumé
    stats = {s: 0 for s in ["À contacter", "Brouillon prêt", "Contacté",
                              "En attente", "Réponse reçue", "Dossier déposé", "Admis", "Refusé"]}
    for e in ecoles:
        if e["statut"] in stats:
            stats[e["statut"]] += 1

    rows = _generer_lignes_ecoles(ecoles)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Écoles contactées — PTP {CANDIDAT['nom_complet']}</title>
<style>
  :root {{
    --blue: #1F497D; --blue-light: #4472C4; --blue-pale: #EBF3FB;
    --green: #107c10; --green-bg: #dff0d8;
    --orange: #d67f20; --orange-bg: #fff3cd;
    --red: #c00; --red-bg: #fce4d6;
    --grey: #666; --border: #ddd;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f0f4f8; color: #333; }}

  .header {{ background: var(--blue); color: white; padding: 24px 32px; }}
  .header h1 {{ font-size: 1.5em; font-weight: 700; }}
  .header .meta {{ opacity: .8; font-size: .88em; margin-top: 5px; }}

  .nav {{ background: var(--blue-light); padding: 0 32px; display: flex; gap: 4px; }}
  .nav a {{
    color: white; text-decoration: none; padding: 12px 20px; font-size: .9em;
    border-bottom: 3px solid transparent; transition: all .2s;
  }}
  .nav a:hover, .nav a.active {{ border-bottom-color: white; background: rgba(255,255,255,.1); }}

  .container {{ max-width: 1300px; margin: 0 auto; padding: 24px 20px; }}

  /* Stats bar */
  .stats-bar {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }}
  .stat-chip {{
    display: flex; align-items: center; gap: 6px; padding: 8px 14px;
    background: white; border-radius: 20px; font-size: .85em; font-weight: 600;
    box-shadow: 0 1px 4px rgba(0,0,0,.1); cursor: pointer; transition: all .2s;
    border: 2px solid transparent;
  }}
  .stat-chip:hover {{ transform: translateY(-1px); box-shadow: 0 3px 10px rgba(0,0,0,.15); }}
  .stat-chip.active {{ border-color: var(--blue); }}
  .stat-chip .dot {{ width: 10px; height: 10px; border-radius: 50%; }}

  /* Table */
  .table-wrap {{ background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,.08); overflow: hidden; }}
  .table-controls {{
    padding: 16px 20px; border-bottom: 1px solid var(--border);
    display: flex; gap: 12px; align-items: center; flex-wrap: wrap;
  }}
  .table-controls input {{
    flex: 1; min-width: 200px; padding: 8px 14px; border: 1px solid var(--border);
    border-radius: 20px; font-size: .9em; outline: none;
  }}
  .table-controls input:focus {{ border-color: var(--blue-light); }}
  .table-controls select {{
    padding: 8px 12px; border: 1px solid var(--border); border-radius: 20px;
    font-size: .85em; background: white; cursor: pointer;
  }}

  table {{ width: 100%; border-collapse: collapse; font-size: .87em; }}
  thead tr {{ background: var(--blue-pale); }}
  th {{
    padding: 11px 12px; text-align: left; font-weight: 600; color: var(--blue);
    border-bottom: 2px solid var(--blue-light); cursor: pointer; white-space: nowrap;
    user-select: none;
  }}
  th:hover {{ background: #d6e8f8; }}
  th .sort-icon {{ margin-left: 4px; opacity: .5; font-size: .8em; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #eee; vertical-align: middle; }}
  tr:hover td {{ background: #fafafa; }}

  /* Badges statut */
  .badge {{
    display: inline-block; padding: 3px 10px; border-radius: 12px;
    font-size: .78em; font-weight: 600; white-space: nowrap;
  }}
  .badge-a-contacter {{ background: #eee; color: #666; }}
  .badge-brouillon {{ background: var(--orange-bg); color: var(--orange); }}
  .badge-contacte {{ background: #d0f0ff; color: #0066aa; }}
  .badge-attente {{ background: #e8d4f8; color: #6a0dad; }}
  .badge-reponse {{ background: var(--green-bg); color: var(--green); }}
  .badge-admis {{ background: #c6efce; color: #276221; font-size:.85em; }}
  .badge-refuse {{ background: var(--red-bg); color: var(--red); }}
  .badge-dossier {{ background: #cce5ff; color: #004085; }}

  /* Boutons */
  .btn {{
    display: inline-flex; align-items: center; gap: 5px;
    padding: 5px 12px; border-radius: 6px; font-size: .8em;
    font-weight: 600; cursor: pointer; border: none; transition: all .15s;
    text-decoration: none;
  }}
  .btn-confirm {{ background: var(--green); color: white; }}
  .btn-confirm:hover {{ background: #0d6b0d; }}
  .btn-relance {{ background: var(--blue-light); color: white; }}
  .btn-relance:hover {{ background: var(--blue); }}
  .btn-view {{ background: #eee; color: #333; }}
  .btn-view:hover {{ background: #ddd; }}

  /* Score */
  .score {{ font-weight: 700; }}
  .score-high {{ color: var(--green); }}
  .score-med {{ color: var(--orange); }}
  .score-low {{ color: var(--red); }}

  /* Empty state */
  .empty {{ text-align: center; padding: 40px; color: var(--grey); }}

  /* Modal */
  .modal-overlay {{
    display: none; position: fixed; inset: 0; background: rgba(0,0,0,.5);
    z-index: 100; align-items: center; justify-content: center;
  }}
  .modal-overlay.open {{ display: flex; }}
  .modal {{
    background: white; border-radius: 12px; padding: 28px; max-width: 520px;
    width: 90%; box-shadow: 0 10px 40px rgba(0,0,0,.3);
  }}
  .modal h3 {{ color: var(--blue); margin-bottom: 16px; }}
  .modal label {{ display: block; font-size: .9em; font-weight: 600; margin-bottom: 6px; color: var(--blue); }}
  .modal select, .modal textarea {{
    width: 100%; padding: 10px; border: 1px solid var(--border); border-radius: 8px;
    font-size: .9em; font-family: inherit; margin-bottom: 14px;
  }}
  .modal textarea {{ min-height: 80px; resize: vertical; }}
  .modal-actions {{ display: flex; gap: 10px; justify-content: flex-end; margin-top: 6px; }}
  .btn-cancel {{ background: #eee; color: #333; }}
  .btn-cancel:hover {{ background: #ddd; }}
  .btn-save {{ background: var(--blue); color: white; padding: 8px 20px; }}
  .btn-save:hover {{ background: var(--blue-light); }}

  .footer {{ text-align: center; color: var(--grey); font-size: .8em; padding: 20px; }}
</style>
</head>
<body>

<div class="header">
  <h1>🏫 Écoles contactées — Dossier PTP</h1>
  <div class="meta">
    {CANDIDAT['nom_complet']} | {len(ecoles)} établissements ciblés | Mis à jour : {now_str}
  </div>
</div>

<div class="nav">
  <a href="index.html">🏠 Vue d'ensemble</a>
  <a href="ecoles.html" class="active">🏫 Écoles contactées</a>
</div>

<div class="container">

  <!-- Stats chips -->
  <div class="stats-bar">
    <div class="stat-chip active" onclick="filterByStatus('all')" id="chip-all">
      <div class="dot" style="background:#aaa"></div>
      Tous ({len(ecoles)})
    </div>
    <div class="stat-chip" onclick="filterByStatus('Brouillon prêt')" id="chip-brouillon">
      <div class="dot" style="background:var(--orange)"></div>
      Brouillon prêt ({stats.get('Brouillon prêt', 0)})
    </div>
    <div class="stat-chip" onclick="filterByStatus('Contacté')" id="chip-contacte">
      <div class="dot" style="background:#0099dd"></div>
      Contacté ({stats.get('Contacté', 0)})
    </div>
    <div class="stat-chip" onclick="filterByStatus('En attente')" id="chip-attente">
      <div class="dot" style="background:#9b59b6"></div>
      En attente ({stats.get('En attente', 0)})
    </div>
    <div class="stat-chip" onclick="filterByStatus('Réponse reçue')" id="chip-reponse">
      <div class="dot" style="background:var(--green)"></div>
      Réponse ({stats.get('Réponse reçue', 0)})
    </div>
    <div class="stat-chip" onclick="filterByStatus('À contacter')" id="chip-a-contacter">
      <div class="dot" style="background:#ccc"></div>
      À contacter ({stats.get('À contacter', 0)})
    </div>
  </div>

  <!-- Table -->
  <div class="table-wrap">
    <div class="table-controls">
      <input type="text" id="search-input" placeholder="🔍 Rechercher un établissement, ville, formation..." oninput="filterTable()">
      <select id="filter-formation" onchange="filterTable()">
        <option value="">Toutes les formations</option>
        {''.join(f'<option value="{f["id"]}">{f["nom"][:45]}...</option>' for f in FORMATIONS_CIBLES)}
      </select>
      <select id="filter-priorite" onchange="filterTable()">
        <option value="">Toutes priorités</option>
        {''.join(f'<option value="{i}">Priorité {i}</option>' for i in range(1, 6))}
      </select>
    </div>

    <table id="ecoles-table">
      <thead>
        <tr>
          <th onclick="sortTable(0)">Établissement <span class="sort-icon">↕</span></th>
          <th onclick="sortTable(1)">Ville <span class="sort-icon">↕</span></th>
          <th onclick="sortTable(2)">Formation <span class="sort-icon">↕</span></th>
          <th onclick="sortTable(3)">Prio <span class="sort-icon">↕</span></th>
          <th onclick="sortTable(4)">Email contact <span class="sort-icon">↕</span></th>
          <th onclick="sortTable(5)">Date limite <span class="sort-icon">↕</span></th>
          <th onclick="sortTable(6)">Score <span class="sort-icon">↕</span></th>
          <th onclick="sortTable(7)">Statut <span class="sort-icon">↕</span></th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="ecoles-tbody">
{rows}
      </tbody>
    </table>
    <div class="empty" id="empty-msg" style="display:none">
      Aucun établissement ne correspond aux filtres sélectionnés.
    </div>
  </div>

</div>

<!-- Modal confirmation envoi -->
<div class="modal-overlay" id="modal-overlay">
  <div class="modal">
    <h3>✅ Confirmer l'action</h3>
    <input type="hidden" id="modal-id">
    <label>Établissement</label>
    <div id="modal-etab" style="font-weight:600;margin-bottom:14px;color:var(--blue)"></div>
    <label>Nouveau statut</label>
    <select id="modal-statut">
      <option value="Contacté">✉️ Contacté (email envoyé)</option>
      <option value="En attente">⏳ En attente de réponse</option>
      <option value="Réponse reçue">📬 Réponse reçue</option>
      <option value="Dossier déposé">📁 Dossier déposé</option>
      <option value="Admis">🎉 Admis</option>
      <option value="Refusé">❌ Refusé</option>
      <option value="Sans suite">🚫 Sans suite</option>
    </select>
    <label>Notes (optionnel)</label>
    <textarea id="modal-notes" placeholder="Ex: Réponse positive, entretien prévu le 15/03..."></textarea>
    <div class="modal-actions">
      <button class="btn btn-cancel" onclick="closeModal()">Annuler</button>
      <button class="btn btn-save" onclick="saveAction()">💾 Enregistrer</button>
    </div>
  </div>
</div>

<div class="footer">
  Système PTP Multi-Agents — {CANDIDAT['nom_complet']} |
  <a href="index.html">← Retour au tableau de bord</a>
</div>

<script>
// ── Données des écoles (persistance localStorage) ──────────────────────────
const ECOLES_KEY = 'ptp_ecoles_{CANDIDAT["nom_complet"].replace(" ", "_")}';

function getEcolesData() {{
  return JSON.parse(localStorage.getItem(ECOLES_KEY) || '{{}}');
}}

function setEcoleData(id, data) {{
  const all = getEcolesData();
  all[id] = {{ ...all[id], ...data }};
  localStorage.setItem(ECOLES_KEY, JSON.stringify(all));
}}

// ── Filtres & Recherche ─────────────────────────────────────────────────────
let currentStatusFilter = 'all';

function filterByStatus(status) {{
  currentStatusFilter = status;
  document.querySelectorAll('.stat-chip').forEach(c => c.classList.remove('active'));
  const chipId = status === 'all' ? 'chip-all'
    : status === 'Brouillon prêt' ? 'chip-brouillon'
    : status === 'Contacté' ? 'chip-contacte'
    : status === 'En attente' ? 'chip-attente'
    : status === 'Réponse reçue' ? 'chip-reponse'
    : status === 'À contacter' ? 'chip-a-contacter' : 'chip-all';
  const chip = document.getElementById(chipId);
  if (chip) chip.classList.add('active');
  filterTable();
}}

function filterTable() {{
  const search = document.getElementById('search-input').value.toLowerCase();
  const formFilter = document.getElementById('filter-formation').value;
  const prioFilter = document.getElementById('filter-priorite').value;
  const rows = document.querySelectorAll('#ecoles-tbody tr');
  let visible = 0;

  rows.forEach(row => {{
    const text = row.textContent.toLowerCase();
    const statut = row.dataset.statut || '';
    const formId = row.dataset.formid || '';
    const prio = row.dataset.prio || '';

    const matchSearch = !search || text.includes(search);
    const matchStatus = currentStatusFilter === 'all' || statut === currentStatusFilter;
    const matchForm = !formFilter || formId === formFilter;
    const matchPrio = !prioFilter || prio === prioFilter;

    const show = matchSearch && matchStatus && matchForm && matchPrio;
    row.style.display = show ? '' : 'none';
    if (show) visible++;
  }});

  document.getElementById('empty-msg').style.display = visible === 0 ? 'block' : 'none';
}}

// ── Tri des colonnes ────────────────────────────────────────────────────────
let sortCol = -1, sortAsc = true;

function sortTable(col) {{
  const tbody = document.getElementById('ecoles-tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  sortAsc = sortCol === col ? !sortAsc : true;
  sortCol = col;

  rows.sort((a, b) => {{
    const aVal = a.cells[col]?.textContent.trim() || '';
    const bVal = b.cells[col]?.textContent.trim() || '';
    return sortAsc ? aVal.localeCompare(bVal, 'fr') : bVal.localeCompare(aVal, 'fr');
  }});
  rows.forEach(r => tbody.appendChild(r));

  document.querySelectorAll('th .sort-icon').forEach((el, i) => {{
    el.textContent = i === col ? (sortAsc ? '↑' : '↓') : '↕';
  }});
}}

// ── Modal confirmation ──────────────────────────────────────────────────────
function openModal(id, nom, defaultStatus) {{
  document.getElementById('modal-id').value = id;
  document.getElementById('modal-etab').textContent = nom;
  document.getElementById('modal-statut').value = defaultStatus || 'Contacté';
  document.getElementById('modal-notes').value = (getEcolesData()[id] || {{}}).notes || '';
  document.getElementById('modal-overlay').classList.add('open');
}}

function closeModal() {{
  document.getElementById('modal-overlay').classList.remove('open');
}}

function saveAction() {{
  const id = document.getElementById('modal-id').value;
  const statut = document.getElementById('modal-statut').value;
  const notes = document.getElementById('modal-notes').value;

  setEcoleData(id, {{ statut, notes, date_action: new Date().toLocaleDateString('fr-FR') }});

  // Mettre à jour l'affichage de la ligne
  const row = document.querySelector(`tr[data-id="${{id}}"]`);
  if (row) {{
    row.dataset.statut = statut;
    const badgeCell = row.querySelector('.statut-cell');
    if (badgeCell) badgeCell.innerHTML = getBadgeHTML(statut);
    const actionsCell = row.querySelector('.actions-cell');
    if (actionsCell) actionsCell.innerHTML = getActionsHTML(id, row.querySelector('td').textContent, statut);
  }}
  closeModal();
}}

function getBadgeHTML(statut) {{
  const map = {{
    'À contacter': 'badge-a-contacter',
    'Brouillon prêt': 'badge-brouillon',
    'Contacté': 'badge-contacte',
    'En attente': 'badge-attente',
    'Réponse reçue': 'badge-reponse',
    'Dossier déposé': 'badge-dossier',
    'Admis': 'badge-admis',
    'Refusé': 'badge-refuse',
  }};
  return `<span class="badge ${{map[statut] || 'badge-a-contacter'}}">${{statut}}</span>`;
}}

function getActionsHTML(id, nom, statut) {{
  const nextStatus = statut === 'Brouillon prêt' ? 'Contacté'
    : statut === 'Contacté' ? 'En attente'
    : statut === 'En attente' ? 'Réponse reçue'
    : 'Mise à jour';
  const btnLabel = statut === 'Brouillon prêt' ? '✅ Confirmer envoi'
    : statut === 'Contacté' ? '⏳ Marquer en attente'
    : statut === 'En attente' ? '📬 Réponse reçue'
    : '✏️ Mettre à jour';
  const safeNom = nom.replace(/'/g, "\\'");
  return `<button class="btn btn-confirm" onclick="openModal('${{id}}', '${{safeNom}}', '${{nextStatus}}')">${{btnLabel}}</button>`;
}}

// ── Restaurer les statuts depuis localStorage ───────────────────────────────
function restoreStatuts() {{
  const data = getEcolesData();
  for (const [id, info] of Object.entries(data)) {{
    const row = document.querySelector(`tr[data-id="${{id}}"]`);
    if (!row || !info.statut) continue;
    row.dataset.statut = info.statut;
    const badgeCell = row.querySelector('.statut-cell');
    if (badgeCell) badgeCell.innerHTML = getBadgeHTML(info.statut);
    const nomCell = row.cells[0]?.textContent || '';
    const actionsCell = row.querySelector('.actions-cell');
    if (actionsCell) actionsCell.innerHTML = getActionsHTML(id, nomCell, info.statut);
  }}
}}

// Fermer modal en cliquant à l'extérieur
document.getElementById('modal-overlay').addEventListener('click', (e) => {{
  if (e.target === e.currentTarget) closeModal();
}});

restoreStatuts();
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def _generer_lignes_ecoles(ecoles: list[dict]) -> str:
    """Génère les lignes TR du tableau des écoles."""
    status_badge = {
        "À contacter": "badge-a-contacter",
        "Brouillon prêt": "badge-brouillon",
        "Contacté": "badge-contacte",
        "En attente": "badge-attente",
        "Réponse reçue": "badge-reponse",
        "Dossier déposé": "badge-dossier",
        "Admis": "badge-admis",
        "Refusé": "badge-refuse",
    }

    rows = []
    for e in ecoles:
        statut = e.get("statut", "À contacter")
        badge_cls = status_badge.get(statut, "badge-a-contacter")
        ecole_id = e.get("id", e["etablissement"].replace(" ", "_").lower()[:20])
        score = e.get("score_adequation", "")
        score_html = ""
        if score:
            try:
                s = float(str(score).split("/")[0])
                css = "score-high" if s >= 7 else "score-med" if s >= 5 else "score-low"
                score_html = f'<span class="score {css}">{score}/10</span>'
            except Exception:
                score_html = str(score)

        # Email contact : lien cliquable
        email = e.get("email_contact", "")
        email_html = f'<a href="mailto:{email}">{email}</a>' if email else '<span style="color:#aaa">N/A</span>'

        # Lien candidature
        lien = e.get("lien_candidature", e.get("url", "#"))
        lien_html = f'<a href="{lien}" target="_blank" class="btn btn-view">🔗 Postuler</a>'

        # Bouton action selon statut (pré-calculer le nom échappé hors f-string)
        nom_js = e["etablissement"].replace("'", "\\'")
        if statut == "Brouillon prêt":
            action_html = (
                f'<button class="btn btn-confirm actions-cell"'
                f' onclick="openModal(\'{ecole_id}\', \'{nom_js}\', \'Contacté\')">'
                f'✅ Confirmer envoi</button>'
            )
        elif statut in ("Contacté", "En attente"):
            next_s = "En attente" if statut == "Contacté" else "Réponse reçue"
            label = "⏳ Marquer en attente" if statut == "Contacté" else "📬 Réponse reçue"
            action_html = (
                f'<button class="btn btn-relance actions-cell"'
                f' onclick="openModal(\'{ecole_id}\', \'{nom_js}\', \'{next_s}\')">'
                f'{label}</button>'
            )
        else:
            action_html = (
                f'<button class="btn btn-view actions-cell"'
                f' onclick="openModal(\'{ecole_id}\', \'{nom_js}\', \'{statut}\')">'
                f'✏️ Mettre à jour</button>'
            )

        nom_court = e["etablissement"][:28]

        rows.append(f"""        <tr data-id="{ecole_id}" data-statut="{statut}"
            data-formid="{e.get('formation_id', '')}" data-prio="{e.get('formation_priorite', '')}">
          <td><strong>{nom_cout_html(nom_court)}</strong><br><small style="color:#888">{e.get('universite', '')[:30]}</small></td>
          <td>{e['ville']}</td>
          <td style="max-width:200px;font-size:.82em">{e['formation'][:60]}…</td>
          <td style="text-align:center"><strong style="color:var(--blue)">⭐{e.get('formation_priorite', '')}</strong></td>
          <td style="font-size:.85em">{email_html}</td>
          <td style="font-size:.85em;white-space:nowrap">{e.get('date_limite', 'N/A')}</td>
          <td style="text-align:center">{score_html}</td>
          <td class="statut-cell"><span class="badge {badge_cls}">{statut}</span></td>
          <td style="white-space:nowrap;display:flex;gap:6px;flex-wrap:wrap;align-items:center">
            {action_html}
            {lien_html}
          </td>
        </tr>""")

    return "\n".join(rows)


def nom_cout_html(nom: str) -> str:
    return nom


def generer_tout_dashboard(
    ecoles: list[dict] = None,
    documents_generes: list[dict] = None,
    nb_emails_rediges: int = 0,
    nb_etab_analyses: int = 0,
    derniere_session: str = None,
    stats_ecoles: dict = None,
) -> dict[str, str]:
    """
    Génère les deux pages du dashboard.
    Retourne {"index": chemin, "ecoles": chemin}.
    """
    if ecoles is None:
        from ptp_system.agents.school_tracker_agent import charger_tracking
        ecoles = charger_tracking()

    index_path = generer_dashboard(
        documents_generes=documents_generes,
        nb_emails_rediges=nb_emails_rediges,
        nb_etab_analyses=nb_etab_analyses,
        derniere_session=derniere_session,
        stats_ecoles=stats_ecoles,
    )
    ecoles_path = generer_page_ecoles(ecoles)

    return {"index": index_path, "ecoles": ecoles_path}
