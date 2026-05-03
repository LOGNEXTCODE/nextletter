"""
generator.py — NextLetter
Usa Claude API para seleccionar noticias, redactar el contenido
y montar el HTML final del correo.
"""

import os
import json
import re
import anthropic
from datetime import datetime
from typing import List, Dict

# ─── CONFIGURACIÓN ─────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
EDITION_NUMBER    = os.environ.get("EDITION_NUMBER", "01")

# ─── COLORES LOGNEXT ───────────────────────────────────────────────────────────
NAVY   = "#000029"
RED    = "#FA3C0F"
CYAN   = "#3CE6E6"
YELLOW = "#FFFA96"
GREEN  = "#64F07D"
VIOLET = "#C896FF"
BLUE   = "#3791F5"
GREY   = "#E1E1E8"
WHITE  = "#FFFFFF"

FORBIDDEN_WORDS = [
    "disruptivo", "disrupción", "ecosistema", "sinergia",
    "innovador", "innovación", "paradigma", "disruptive"
]

_MONTHS_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


def _next_month_label(year: int, month: int, delta: int) -> str:
    idx = (month - 1 + delta) % 12
    y   = year + (month - 1 + delta) // 12
    return f"{_MONTHS_ES[idx]} {y}"


# ─── IMÁGENES UNSPLASH (IDs verificados, CDN directo sin API key) ───────────────
_UNSPLASH_PHOTOS = {
    "cybersecurity": "1550751827-4bd374c3f58b",   # blue digital lock
    "data-breach":   "1555963879-ea7c5a52a1e0",   # red warning / alert
    "hacker":        "1614064641938-3bbee52942c7", # dark hooded figure (confirmed)
    "network":       "1544197150-b99a580bb7be",    # fiber optic cables
    "server":        "1558618742-b04c9b8c5ee5",    # dark server rack room
    "cloud":         "1451187580459-43490279c0fa", # data center aerial
    "code":          "1517694712202-14dd9538aa97", # dark terminal / code screen
    "ai":            "1676299081847-824916de030a", # AI abstract (confirmed)
    "robot":         "1485827404703-89b55fcc595e", # robot / automation
    "phishing":      "1526374965328-7f61d4dc18c5", # email phishing hook
    "privacy":       "1610337673044-720471f83677", # privacy / lock
    "energy":        "1473341304170-971dccb5ac1e", # energy / power grid
    "business":      "1573497019236-17f8177b81e8", # IT professional at desk
    "mobile":        "1512941937669-90a1b58e7e9c", # mobile / smartphone
    "spain":         "1539037116277-4db20889f2d4", # Spain / city
    "technology":    "1518770660439-4636190af475", # tech abstract
}


def _unsplash_url(keyword: str, w: int = 1200, h: int = 220) -> str:
    key = keyword.lower().split(",")[0].replace(" ", "-").strip()
    photo_id = _UNSPLASH_PHOTOS.get(key, _UNSPLASH_PHOTOS["technology"])
    return f"https://images.unsplash.com/photo-{photo_id}?auto=format&fit=crop&w={w}&h={h}&q=80"


# ─── CONSTANTES DE DISEÑO (strings planos — sin f-string) ──────────────────────

_FAVICON_SVG = (
    "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 521 438'>"
    "<polygon fill='%23000029' points='175,119 116,119 201,219 115,320 175,320 243,243 243,196'/>"
    "<polygon fill='%23000029' points='344,119 403,119 318,219 404,320 344,320 276,243 276,196'/>"
    "<polygon fill='%23FA3C0F' points='92,348 27,408 86,408 149,348'/>"
    "<polygon fill='%23FA3C0F' points='425,90 489,30 430,30 369,90'/></svg>"
)

_LOGNEXT_WORDMARK_SVG = (
    '<svg height="22" viewBox="0 0 1920 437.9" xmlns="http://www.w3.org/2000/svg"'
    ' style="margin-right:20px;flex-shrink:0;">'
    '<polygon fill="#FFFFFF" points="1417.7,117.4 1358.3,117.4 1443,218 1357.9,318.7 1417.7,318.7 1485.6,241.8 1485.6,194.3"/>'
    '<polygon fill="#FFFFFF" points="1585.9,117.4 1645.3,117.4 1560.5,218 1645.7,318.7 1585.9,318.7 1518,241.8 1518,194.3"/>'
    '<polygon fill="#FA3C0F" points="1334.7,346.7 1269.7,406.4 1328.5,406.4 1391,346.7"/>'
    '<polygon fill="#FA3C0F" points="1667.5,88.6 1730.6,28.9 1671.8,28.9 1611.2,88.6"/>'
    '<path fill="#FFFFFF" d="M230.7,271.4v47.4H43.3V117.4h52.3v154H230.7z"/>'
    '<path fill="#FFFFFF" d="M1175.7,161.1v38.3h161.1v37.4h-161.1v40.8h161.1v41.1h-212.9V117.4h212.9v43.7H1175.7z"/>'
    '<path fill="#FFFFFF" d="M1032.6,117.6v195.7h-1.5l-96.8-195.7H826.5v201.2h52.3V123h1.5l96.5,195.7h108.1V117.6H1032.6z"/>'
    '<polygon fill="#FFFFFF" points="1685,117.3 1645.5,163.2 1733.8,163.2 1733.8,318.7 1786,318.7 1786,163.2 1876.7,163.2 1876.7,117.3"/>'
    '<path fill="#FFFFFF" d="M245.6,217.8c0-68.7,39.1-106.4,130.4-106.4c91,0,130.4,37.9,130.4,106.4'
    'c0,68.7-39.4,107-130.4,107C284.7,324.8,245.6,286.8,245.6,217.8z M454,217.8c0-42.1-22.4-62.6-78.1-62.6'
    'c-55.7,0-78,20.3-78,62.6c0,42.7,22.5,63.3,78,63.3C431.4,281.1,454,260.2,454,217.8z"/>'
    '<path fill="#FFFFFF" d="M791.7,200.8H658.1v36.7h78.4c-6.4,28.8-28.3,43.9-74.3,43.9'
    'c-55.4,0-78.6-21-78.6-63.7c0-42.4,22.9-63.2,78.6-63.2c35,0,55.5,9.3,66.6,25.5h58.8'
    'c-13.1-44.5-52.8-68.7-125.4-68.7c-91.3,0-130.4,37.6-130.4,106.4c0,69,42.3,107,130.4,107'
    'c88.2,0,130.4-38.2,130.4-107C792.6,211.9,792.3,206.3,791.7,200.8z"/>'
    '</svg>'
)

_CURSOR_SVG = (
    '<svg class="cursor-logo" id="cursorLogo" viewBox="0 0 521 437.9" xmlns="http://www.w3.org/2000/svg">'
    '<polygon fill="#FFFFFF" points="175.2,118.7 115.8,118.7 200.5,219.4 115.4,320 175.2,320 243.1,243.1 243.1,195.6"/>'
    '<polygon fill="#FFFFFF" points="343.4,118.7 402.8,118.7 318,219.4 403.2,320 343.4,320 275.5,243.1 275.5,195.6"/>'
    '<polygon fill="#FA3C0F" points="92.2,348.1 27.2,407.7 86,407.7 148.5,348.1"/>'
    '<polygon fill="#FA3C0F" points="425,89.9 488.1,30.3 429.3,30.3 368.7,89.9"/>'
    '</svg>'
)

# GA4 script — __EDITION__ se sustituye en build_html()
_GA4_SCRIPT = """<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
  function trackSection(section) {
    gtag('event', 'section_read', { section_name: section, edition: '__EDITION__' });
  }
  function trackLink(label, url) {
    gtag('event', 'outbound_click', { link_label: label, link_url: url, edition: '__EDITION__' });
    return true;
  }
  function trackPhishing(action) {
    gtag('event', 'phishing_test', { action: action, edition: '__EDITION__' });
  }
</script>"""

# CSS completo — string plano sin f-string para evitar conflictos con {}
_CSS = """
:root {
  --navy:   #000029;
  --red:    #FA3C0F;
  --cyan:   #3CE6E6;
  --yellow: #FFFA96;
  --green:  #64F07D;
  --violet: #C896FF;
  --blue:   #3791F5;
  --grey:   #E1E1E8;
  --dark:   #080820;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  background: linear-gradient(160deg, #0e0e35 0%, #080820 60%, #0a0a2a 100%);
  font-family: 'Space Grotesk', sans-serif;
  color: var(--grey);
  min-height: 100vh;
  overflow-x: hidden;
  cursor: none;
}
.cursor-logo, .cursor-ring { display: none; }
@media (pointer: fine) {
  .cursor-logo {
    display: block; position: fixed;
    width: 28px; height: 24px;
    pointer-events: none; z-index: 9999;
    transform: translate(-50%, -50%);
    transition: transform 0.15s ease;
    filter: drop-shadow(0 0 5px rgba(250,60,15,0.7));
  }
  .cursor-logo.hover {
    transform: translate(-50%, -50%) scale(1.5);
    filter: drop-shadow(0 0 10px rgba(250,60,15,1));
  }
  .cursor-ring {
    display: block; position: fixed;
    width: 44px; height: 44px;
    border: 1px solid rgba(60,230,230,0.5);
    border-radius: 50%; pointer-events: none; z-index: 9998;
    transform: translate(-50%, -50%);
    transition: all 0.15s ease;
  }
  .cursor-ring.hover { width: 58px; height: 58px; border-color: rgba(250,60,15,0.5); }
  body { cursor: none; }
}
#nebula-canvas { position: fixed; inset: 0; pointer-events: none; z-index: 0; }
.bg-grid {
  position: fixed; inset: 0;
  background-image: radial-gradient(circle, rgba(250,60,15,0.08) 1px, transparent 1px);
  background-size: 50px 50px;
  pointer-events: none; z-index: 0;
}
.topbar {
  background: rgba(0,0,20,0.95);
  border-bottom: 1px solid rgba(250,60,15,0.15);
  padding: 12px 24px;
  position: sticky; top: 0; z-index: 100;
  backdrop-filter: blur(10px);
}
.topbar-inner { max-width: 1100px; margin: 0 auto; width: 100%; padding: 0 24px; display: flex; align-items: center; }
.topbar-name { flex: 1; font-size: 14px; font-weight: 700; color: #fff; letter-spacing: -0.5px; }
.topbar-name span { color: var(--red); font-weight: 300; }
.topbar-center { flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
.topbar-right { flex: 1; text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.topbar-edition-num { font-size: 10px; color: var(--red); font-family: 'JetBrains Mono', monospace; letter-spacing: 2px; font-weight: 700; }
.topbar-edition-date { font-size: 9px; color: rgba(255,255,255,0.4); font-family: 'JetBrains Mono', monospace; letter-spacing: 1px; font-weight: 400; }
.wrapper { max-width: 1100px; margin: 0 auto; padding: 0 24px 80px; position: relative; z-index: 1; }
.header {
  background: var(--navy); border-top: 5px solid var(--red);
  padding: 56px 64px 40px; position: relative; overflow: hidden;
  animation: fadeDown 0.6s ease both;
}
.header::before {
  content: ''; position: absolute; inset: 0;
  background: repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(255,255,255,0.01) 2px,rgba(255,255,255,0.01) 4px);
  pointer-events: none;
}
.header-scan {
  position: absolute; top: 0; left: 0; width: 100%; height: 3px;
  background: linear-gradient(90deg, transparent, var(--red), transparent);
  animation: scan 3s linear infinite; opacity: 0.5;
}
@keyframes scan { from{top:0} to{top:100%} }
.header-inner { display: grid; grid-template-columns: 1fr auto; gap: 40px; align-items: end; }
.logo-row { display: flex; align-items: baseline; gap: 0; margin-bottom: 8px; }
.logo-next { font-size: 88px; font-weight: 700; color: #fff; letter-spacing: -4px; line-height: 1; }
.logo-letter { font-size: 88px; font-weight: 300; color: var(--red); letter-spacing: -4px; line-height: 1; }
.header-tagline-big {
  font-size: 13px; letter-spacing: 2px; text-transform: uppercase; opacity: 0.4;
  font-family: 'JetBrains Mono', monospace; margin-bottom: 20px;
}
.header-dots { display: flex; gap: 8px; }
.hdot { width: 8px; height: 8px; border-radius: 50%; animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.7)} }
.header-stats { display: flex; flex-direction: row; gap: 32px; align-items: center; border-left: 1px solid rgba(255,255,255,0.08); padding-left: 40px; }
.stat-item { text-align: center; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.stat-number { font-size: 32px; font-weight: 700; color: var(--red); line-height: 1; font-family: 'JetBrains Mono', monospace; }
.stat-label { font-size: 10px; letter-spacing: 2px; text-transform: uppercase; opacity: 0.4; font-family: 'JetBrains Mono', monospace; }
.header-meta { border-top: 1px solid rgba(255,255,255,0.08); margin-top: 24px; padding-top: 16px; display: flex; justify-content: space-between; align-items: center; }
.header-issue { font-size: 11px; color: var(--red); font-weight: 700; letter-spacing: 3px; font-family: 'JetBrains Mono', monospace; }
.intro { background: rgba(250,60,15,0.06); border-left: 4px solid var(--red); padding: 24px 40px; margin-top: 4px; font-size: 15px; line-height: 1.9; color: var(--grey); animation: fadeDown 0.6s 0.1s ease both; }
.sep { height: 4px; background: linear-gradient(90deg, var(--red) 0%, var(--red) 33%, var(--cyan) 33%, var(--cyan) 66%, var(--yellow) 66%); margin-top: 4px; }
.main-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin-top: 4px; }
.full-width { grid-column: 1 / -1; }
.card { background: var(--navy); padding: 36px 44px; position: relative; overflow: hidden; transition: all 0.3s ease; cursor: pointer; animation: fadeUp 0.5s ease both; }
.card::after { content: ''; position: absolute; inset: 0; opacity: 0; transition: opacity 0.3s ease; pointer-events: none; }
.card:hover { transform: translateY(-3px); box-shadow: 0 8px 32px rgba(0,0,0,0.4); }
.card:hover::after { opacity: 1; }
.card-esto::after  { background: radial-gradient(ellipse at 50% 0%, rgba(250,60,15,0.1), transparent 70%); }
.card-caso::after  { background: radial-gradient(ellipse at 50% 0%, rgba(255,250,150,0.08), transparent 70%); }
.card-consejo::after { background: radial-gradient(ellipse at 50% 0%, rgba(100,240,125,0.08), transparent 70%); }
.card-reto::after  { background: radial-gradient(ellipse at 50% 0%, rgba(60,230,230,0.08), transparent 70%); }
.card-phishing::after { background: radial-gradient(ellipse at 50% 0%, rgba(200,150,255,0.1), transparent 70%); }
.card-esto   { box-shadow: inset 0 1px 0 rgba(250,60,15,0.3); }
.card-caso   { background: #05051f; border-left: 4px solid var(--yellow); }
.card-consejo { box-shadow: inset 0 1px 0 rgba(100,240,125,0.2); }
.card-reto   { background: #001a05; border: 1px solid rgba(100,240,125,0.2); }
.card-phishing { background: #0a0020; border: 1px solid rgba(200,150,255,0.2); }
.card-links  { background: #000029; box-shadow: inset 0 1px 0 rgba(200,150,255,0.2); }
.card-ia     { background: #000e22; border-left: 4px solid var(--blue); box-shadow: inset 0 1px 0 rgba(55,145,245,0.25); }
.card-ia::after { background: radial-gradient(ellipse at 50% 0%, rgba(55,145,245,0.1), transparent 70%); }
.section-tag { font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 4px; text-transform: uppercase; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
.section-tag::after { content: ''; flex: 1; height: 1px; background: currentColor; opacity: 0.12; }
.card-title { font-size: 22px; font-weight: 700; color: #fff; line-height: 1.3; margin-bottom: 16px; }
.card-text  { font-size: 14px; line-height: 1.9; color: var(--grey); opacity: 0.85; margin-bottom: 20px; }
.card-link { display: inline-flex; align-items: center; gap: 8px; font-size: 11px; font-weight: 600; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px; text-decoration: none; padding: 10px 20px; border: 1px solid currentColor; transition: all 0.25s ease; }
.card-link:hover { opacity: 0.95; }
.card-esto .card-link:hover    { background: var(--red);    color: #fff !important; }
.card-caso .card-link:hover    { background: var(--yellow); color: var(--navy) !important; }
.card-consejo .card-link:hover { background: var(--green);  color: var(--navy) !important; }
.card-reto .card-link:hover    { background: var(--cyan);   color: var(--navy) !important; }
.card-link .arrow { transition: transform 0.2s ease; }
.card-link:hover .arrow { transform: translateX(4px); }
.reto-badge { display: inline-block; background: var(--green); color: var(--navy); font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; letter-spacing: 2px; padding: 4px 14px; margin-bottom: 16px; }
.reto-progress { margin-top: 24px; height: 3px; background: rgba(100,240,125,0.15); border-radius: 2px; overflow: hidden; }
.reto-progress-bar { height: 100%; width: 0%; background: var(--green); border-radius: 2px; animation: progressFill 2s 1s ease forwards; }
@keyframes progressFill { to { width: 65%; } }
.reto-label { display: flex; justify-content: space-between; font-size: 11px; font-family: 'JetBrains Mono', monospace; margin-top: 8px; opacity: 0.5; }
.phishing-inner { background: rgba(200,150,255,0.05); border: 1px solid rgba(200,150,255,0.1); border-radius: 4px; padding: 24px; margin-top: 16px; }
.phishing-email-preview { background: #fff; border-radius: 4px; padding: 16px; margin-bottom: 16px; font-family: Arial, sans-serif; color: #333; }
.phishing-email-header { border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 10px; font-size: 12px; color: #666; }
.phishing-email-subject { font-weight: bold; font-size: 14px; color: #111; margin-bottom: 4px; }
.phishing-email-body { font-size: 13px; line-height: 1.6; color: #444; }
.phishing-email-body a { color: #1a73e8; text-decoration: underline; }
.phishing-question { font-size: 15px; font-weight: 600; color: #fff; margin-bottom: 16px; line-height: 1.5; }
.phishing-buttons { display: flex; gap: 12px; flex-wrap: wrap; }
.phishing-btn { padding: 12px 24px; font-size: 13px; font-weight: 600; font-family: 'Space Grotesk', sans-serif; border: none; cursor: pointer; transition: all 0.25s ease; letter-spacing: 0.5px; flex: 1; min-width: 120px; }
.phishing-btn-yes { background: rgba(250,60,15,0.15); color: var(--red); border: 1px solid var(--red); }
.phishing-btn-yes:hover { background: var(--red); color: #fff; }
.phishing-btn-no  { background: rgba(100,240,125,0.1); color: var(--green); border: 1px solid var(--green); }
.phishing-btn-no:hover  { background: var(--green); color: var(--navy); }
.phishing-result { display: none; padding: 16px; border-radius: 4px; font-size: 14px; line-height: 1.7; margin-top: 12px; }
.phishing-result.show { display: block; }
.phishing-result.correct { background: rgba(100,240,125,0.1); border: 1px solid rgba(100,240,125,0.3); color: var(--green); }
.phishing-result.wrong   { background: rgba(250,60,15,0.1);  border: 1px solid rgba(250,60,15,0.3);  color: var(--red); }
.phishing-clues { margin-top: 12px; padding: 12px; background: rgba(0,0,0,0.3); border-radius: 4px; }
.phishing-clue { font-size: 12px; font-family: 'JetBrains Mono', monospace; color: var(--grey); opacity: 0.8; margin-bottom: 4px; display: flex; gap: 8px; align-items: flex-start; }
.card-radar { box-shadow: inset 0 1px 0 rgba(60,230,230,0.2); }
.card-radar::after { background: radial-gradient(ellipse at 50% 0%, rgba(60,230,230,0.07), transparent 70%); }
.radar-list { display: flex; flex-direction: column; gap: 0; margin-top: 4px; }
.radar-item { display: block; text-decoration: none; color: var(--grey); padding: 14px 0; border-bottom: 1px solid rgba(255,255,255,0.05); transition: all 0.2s ease; }
.radar-item:last-child { border-bottom: none; padding-bottom: 0; }
.radar-item:hover { padding-left: 8px; }
.radar-source { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.radar-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; animation: pulse 2s ease-in-out infinite; }
.radar-org { font-size: 9px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; font-family: 'JetBrains Mono', monospace; opacity: 0.6; }
.radar-headline { font-size: 13px; font-weight: 600; color: #fff; line-height: 1.4; margin-bottom: 4px; }
.radar-item:hover .radar-headline { color: var(--cyan); }
.radar-meta { font-size: 10px; opacity: 0.35; font-family: 'JetBrains Mono', monospace; }
.radar-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 16px; }
.radar-grid-item { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 16px 20px; text-decoration: none; color: var(--grey); transition: all 0.2s ease; display: block; backdrop-filter: blur(4px); }
.radar-grid-item:hover { background: rgba(255,255,255,0.04); padding-left: 26px; }
.links-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 4px; }
.link-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); padding: 24px; text-decoration: none; color: var(--grey); transition: all 0.25s ease; display: flex; flex-direction: column; gap: 8px; position: relative; overflow: hidden; }
.link-card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px; transform: scaleX(0); transform-origin: left; transition: transform 0.3s ease; }
.link-card:hover { transform: translateY(-4px); background: rgba(255,255,255,0.05); }
.link-card:hover::before { transform: scaleX(1); }
.lc-news::before  { background: var(--red); }
.lc-video::before { background: var(--cyan); }
.lc-quiz::before  { background: var(--yellow); }
.link-icon  { width: 28px; height: 28px; display: block; color: currentColor; }
.link-label { font-size: 10px; font-family: 'JetBrains Mono', monospace; letter-spacing: 2px; text-transform: uppercase; opacity: 0.4; }
.link-title { font-size: 14px; font-weight: 600; color: #fff; line-height: 1.4; }
.link-desc  { font-size: 12px; opacity: 0.55; line-height: 1.6; }
.link-source { font-size: 11px; opacity: 0.4; font-family: 'JetBrains Mono', monospace; margin-top: auto; }
.footer { background: #000015; border-top: 1px solid rgba(250,60,15,0.15); padding: 56px 64px 40px; margin-top: 4px; animation: fadeUp 0.5s 0.6s ease both; }
.footer-inner { display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 48px; max-width: 1100px; margin: 0 auto 40px; }
.footer-col-title { font-size: 11px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; font-family: 'JetBrains Mono', monospace; color: var(--red); margin-bottom: 6px; }
.footer-col-rule { width: 32px; height: 2px; background: var(--red); margin-bottom: 20px; }
.footer-brand-name { font-size: 28px; font-weight: 700; letter-spacing: -1px; color: #fff; margin-bottom: 12px; }
.footer-brand-name span { color: var(--red); font-weight: 300; }
.footer-brand-text { font-size: 13px; line-height: 1.8; opacity: 0.45; max-width: 260px; }
.footer-links-list { list-style: none; display: flex; flex-direction: column; gap: 10px; }
.footer-links-list li a { font-size: 13px; color: var(--grey); text-decoration: none; opacity: 0.55; transition: opacity 0.2s ease, padding-left 0.2s ease; display: flex; align-items: center; gap: 8px; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.5px; }
.footer-links-list li a:hover { opacity: 1; padding-left: 6px; }
.footer-links-list li a::before { content: '→'; color: var(--red); font-size: 10px; }
.footer-contact-item { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 12px; font-size: 13px; }
.footer-contact-icon { color: var(--red); flex-shrink: 0; font-family: 'JetBrains Mono', monospace; font-size: 11px; margin-top: 2px; opacity: 0.7; }
.footer-contact-text { opacity: 0.55; line-height: 1.5; font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.footer-contact-text a { color: var(--grey); text-decoration: none; transition: color 0.2s ease; }
.footer-contact-text a:hover { color: var(--red); }
.footer-bottom { border-top: 1px solid rgba(255,255,255,0.06); padding-top: 24px; display: flex; justify-content: center; align-items: center; max-width: 1100px; margin: 0 auto; }
.footer-copy { font-size: 11px; opacity: 0.3; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px; }
@keyframes fadeDown { from{opacity:0;transform:translateY(-20px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeUp   { from{opacity:0;transform:translateY(20px)}  to{opacity:1;transform:translateY(0)} }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: linear-gradient(160deg, #0e0e35 0%, #080820 60%, #0a0a2a 100%); }
::-webkit-scrollbar-thumb { background: var(--red); border-radius: 2px; }
@media (max-width: 900px) {
  .main-grid { grid-template-columns: 1fr; }
  .header-inner { grid-template-columns: 1fr; }
  .header-stats { flex-direction: row; gap: 20px; border-left: none; border-top: 1px solid rgba(255,255,255,0.08); padding-left: 0; padding-top: 20px; align-items: center; justify-content: space-around; }
  .logo-next, .logo-letter { font-size: 64px; }
  .links-grid { grid-template-columns: 1fr; }
  .header { padding: 36px 28px 28px; }
  .card { padding: 28px 28px; }
  .topbar { padding: 12px 0; }
  .wrapper { padding: 0 12px 60px; }
  .footer-inner { grid-template-columns: 1fr; gap: 32px; }
  .footer { padding: 40px 28px 28px; }
  .footer-bottom { flex-direction: column; align-items: flex-start; }
  .radar-grid { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
  .logo-next, .logo-letter { font-size: 48px; letter-spacing: -2px; }
  .card-title { font-size: 18px; }
  .header { padding: 28px 20px 24px; }
  .card { padding: 24px 20px; }
  .topbar { padding: 6px 0; }
  .topbar-inner { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; align-items: center; padding: 0 8px; gap: 2px; }
  .topbar-name { flex: 1; font-size: 8px; letter-spacing: -0.5px; min-width: 0; white-space: nowrap; }
  .topbar-center { flex-shrink: 0; }
  .topbar-center svg { height: 10px !important; margin-right: 4px !important; }
  .topbar-right { flex: 1; }
  .topbar-edition-num { font-size: 7px; letter-spacing: 0.3px; }
  .topbar-edition-date { font-size: 6px; letter-spacing: 0.3px; }
  .phishing-buttons { flex-direction: column; }
  .stat-number { font-size: 24px; }
}
"""

# JS — string plano (contiene template literals JS con ${} que no son Python f-string)
_JS = r"""
const cursorLogo = document.getElementById('cursorLogo');
const ring = document.getElementById('cursorRing');
if (cursorLogo && ring) {
  let mx = -200, my = -200, rx = -200, ry = -200, hasMoved = false;
  cursorLogo.style.opacity = '0';
  ring.style.opacity = '0';
  document.addEventListener('mousemove', e => {
    mx = e.clientX; my = e.clientY;
    cursorLogo.style.left = mx + 'px';
    cursorLogo.style.top  = my + 'px';
    if (!hasMoved) {
      hasMoved = true; rx = mx; ry = my;
      cursorLogo.style.opacity = '1';
      ring.style.opacity = '1';
    }
  });
  function animateRing() {
    rx += (mx - rx) * 0.1; ry += (my - ry) * 0.1;
    ring.style.left = rx + 'px'; ring.style.top = ry + 'px';
    requestAnimationFrame(animateRing);
  }
  animateRing();
  document.querySelectorAll('.card, .link-card, .card-link, .phishing-btn, .topbar, .footer-links-list a, .footer-contact-text a').forEach(el => {
    el.addEventListener('mouseenter', () => { cursorLogo.classList.add('hover'); ring.classList.add('hover'); });
    el.addEventListener('mouseleave', () => { cursorLogo.classList.remove('hover'); ring.classList.remove('hover'); });
  });
}
const nc = document.getElementById('nebula-canvas');
const nx = nc.getContext('2d');
function resizeNebula() { nc.width = window.innerWidth; nc.height = window.innerHeight; }
resizeNebula();
window.addEventListener('resize', resizeNebula);
const stars = Array.from({length: 150}, () => ({
  x: Math.random() * window.innerWidth, y: Math.random() * window.innerHeight,
  r: Math.random() * 1.2, a: Math.random() * 0.5 + 0.1, tw: Math.random() * Math.PI * 2,
}));
const shooters = Array.from({length: 3}, () => newShooter());
function newShooter() {
  return { x: Math.random() * window.innerWidth * 1.5, y: -10,
    len: Math.random() * 90 + 50, speed: Math.random() * 6 + 3,
    angle: Math.PI / 4 + (Math.random()-0.5)*0.2, alpha: 0, fading: true };
}
function drawNebula() {
  nx.fillStyle = 'rgba(8,8,32,0.18)';
  nx.fillRect(0, 0, nc.width, nc.height);
  stars.forEach(s => {
    s.tw += 0.018;
    const a = s.a * (0.5 + Math.sin(s.tw) * 0.5);
    nx.fillStyle = `rgba(255,255,255,${a})`; nx.beginPath(); nx.arc(s.x, s.y, s.r, 0, Math.PI*2); nx.fill();
  });
  shooters.forEach((s, i) => {
    if (s.fading) { s.alpha += 0.04; if (s.alpha >= 1) s.fading = false; }
    else { s.alpha -= 0.025; }
    if (s.alpha <= 0) { shooters[i] = newShooter(); return; }
    s.x += Math.cos(s.angle) * s.speed; s.y += Math.sin(s.angle) * s.speed;
    const gr = nx.createLinearGradient(s.x, s.y, s.x - Math.cos(s.angle)*s.len, s.y - Math.sin(s.angle)*s.len);
    gr.addColorStop(0, `rgba(255,255,255,${s.alpha})`);
    gr.addColorStop(0.4, `rgba(250,60,15,${s.alpha*0.4})`);
    gr.addColorStop(1, 'rgba(255,255,255,0)');
    nx.strokeStyle = gr; nx.lineWidth = 1.2;
    nx.beginPath(); nx.moveTo(s.x, s.y); nx.lineTo(s.x - Math.cos(s.angle)*s.len, s.y - Math.sin(s.angle)*s.len); nx.stroke();
    if (s.x > nc.width + 100 || s.y > nc.height + 100) shooters[i] = newShooter();
  });
  requestAnimationFrame(drawNebula);
}
drawNebula();
function answerPhishing(clickedYes) {
  const result = document.getElementById('phishing-result');
  if (!clickedYes) {
    trackPhishing('correct');
    result.className = 'phishing-result show correct';
    result.innerHTML = '<strong>✅ ¡Correcto! Este email es phishing.</strong><br><br>Buen ojo. Aquí tienes las pistas que lo delatan:<div class="phishing-clues"><div class="phishing-clue">⚠️ <span>El dominio del remitente es <strong>microsoft-365security.com</strong>, no microsoft.com</span></div><div class="phishing-clue">⚠️ <span>Microsoft nunca os pedirá verificación por email con <strong>urgencia de 24h</strong></span></div><div class="phishing-clue">⚠️ <span>El enlace "Verificar mi cuenta" lleva a un dominio desconocido, no a microsoft.com</span></div><div class="phishing-clue">✅ <span>Ante la duda: <strong>llamad a IT</strong> antes de hacer clic en cualquier enlace urgente</span></div></div>';
  } else {
    trackPhishing('incorrect');
    result.className = 'phishing-result show wrong';
    result.innerHTML = '<strong>❌ ¡Cuidado! Este email es phishing.</strong><br><br>Habrías caído. Estas son las señales de alarma que pasaste por alto:<div class="phishing-clues"><div class="phishing-clue">🚨 <span>El dominio del remitente es <strong>microsoft-365security.com</strong> — NO es Microsoft</span></div><div class="phishing-clue">🚨 <span>La urgencia artificial ("24h") es la táctica más usada para que no pienses</span></div><div class="phishing-clue">🚨 <span>Microsoft nunca suspende cuentas por email sin avisos previos en el portal</span></div><div class="phishing-clue">✅ <span>Regla de oro: <strong>ante la duda, llama a IT</strong> antes de hacer clic</span></div></div>';
  }
  document.querySelectorAll('.phishing-btn').forEach(b => { b.disabled = true; b.style.opacity = '0.5'; b.style.cursor = 'default'; });
}
"""

# ─── SECCIÓN PHISHING ESTÁTICA ─────────────────────────────────────────────────
_PHISHING_HTML = """
    <div class="card card-phishing full-width" onmouseenter="trackSection('phishing_test')">
      <div class="section-tag" style="color:var(--violet)">&#127919; Pon a prueba tu ojo &#8212; Test del mes</div>
      <div class="card-title">&#191;Detectar&#237;as este email antes de hacer clic?</div>
      <div class="card-text">Este es el tipo de correo que usan los atacantes. Tiene todos los ingredientes: urgencia, remitente aparentemente leg&#237;timo y un enlace tentador. &#191;Sabr&#237;as que es falso?</div>
      <div class="phishing-inner">
        <div class="phishing-email-preview">
          <div class="phishing-email-header">
            <div><strong>De:</strong> soporte@microsoft-365security.com</div>
            <div><strong>Para:</strong> tu@lognext.com</div>
            <div class="phishing-email-subject">&#9888;&#65039; URGENTE: Tu cuenta de Microsoft 365 ser&#225; suspendida en 24h</div>
          </div>
          <div class="phishing-email-body">
            Hola,<br><br>
            Hemos detectado actividad sospechosa en tu cuenta corporativa. Para evitar la suspensi&#243;n inmediata de tu acceso, debes verificar tu identidad en las pr&#243;ximas <strong>24 horas</strong>.<br><br>
            <a href="javascript:void(0)" onclick="return false;" style="color:#1a73e8;text-decoration:underline;cursor:not-allowed;">&#8594; Verificar mi cuenta ahora</a><br><br>
            Si no realizas esta verificaci&#243;n, tu acceso quedar&#225; bloqueado y deber&#225;s contactar con el departamento de IT para restaurarlo.<br><br>
            Atentamente,<br>
            Equipo de Seguridad de Microsoft
          </div>
        </div>
        <div class="phishing-question">&#191;Es este email leg&#237;timo o un intento de phishing?</div>
        <div class="phishing-buttons">
          <button class="phishing-btn phishing-btn-yes" onclick="answerPhishing(false)">&#9888;&#65039; Es phishing &#8212; No har&#237;a clic</button>
          <button class="phishing-btn phishing-btn-no"  onclick="answerPhishing(true)">&#9989; Parece leg&#237;timo &#8212; Har&#237;a clic</button>
        </div>
        <div class="phishing-result" id="phishing-result"></div>
      </div>
    </div>"""


# ─── SELECCIÓN Y REDACCIÓN ─────────────────────────────────────────────────────

def select_and_draft(articles: List[Dict], warnings: List[str] = None) -> Dict:
    """
    Dos fases integradas en una llamada:
      Fase 1 — Razonamiento editorial: Claude justifica qué artículos elige y por qué.
      Fase 2 — Redacción: escribe el contenido con restricciones editoriales explícitas.
    Devuelve dict con todas las secciones + campo 'razonamiento'.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    articles_text = "\n\n".join([
        f"[{i+1}] FUENTE: {a['source']} | CATEGORÍA: {a['category']}\n"
        f"TÍTULO: {a['title']}\n"
        f"FECHA: {a['date']}\n"
        f"RESUMEN: {a['summary']}\n"
        f"URL: {a['url']}"
        for i, a in enumerate(articles[:40])
    ])

    mes_actual = datetime.now().strftime("%B %Y").capitalize()

    aviso_scraping = ""
    if warnings:
        aviso_scraping = f"""
⚠️ AVISO EDITORIAL (no ignorar):
{chr(10).join(f'  - {w}' for w in warnings)}
Si la cobertura es insuficiente en alguna sección, indícalo con [COBERTURA LIMITADA ESTE MES]
en el campo 'texto' correspondiente. NUNCA inventes noticias ni URLs.
"""

    prompt = f"""Eres el editor jefe de NextLetter, la newsletter mensual de LOGNEXT.

AUDIENCIA: ~222 empleados IT de LOGNEXT en España (los "Nexters"). Nivel técnico medio-alto.
Contexto clave: LOGNEXT está en proceso de certificación ENS. Las noticias de ciberseguridad
en España tienen relevancia directa para ellos.
Tono: cercano, directo, con humor sutil. Nada corporativo ni frío. Como un compañero que sabe mucho.
{aviso_scraping}
══════════════════════════════════════════════════════
PASO 1 — SELECCIÓN RAZONADA (hazlo antes de escribir)
══════════════════════════════════════════════════════
Antes de redactar, decide qué artículos usar. Para cada sección indica en UNA línea
por qué es la mejor opción para los Nexters. Esto va en el campo "razonamiento" del JSON.

══════════════════════════════════════════════════════
PASO 2 — REDACCIÓN (con estas restricciones obligatorias)
══════════════════════════════════════════════════════
• consejo.texto: MÁXIMO 3 frases. Cuando hayas dado el consejo, para.
• esto_paso.texto: DEBE incluir al menos 1 dato numérico o porcentaje.
• Palabras PROHIBIDAS (reescribe si aparecen): {', '.join(FORBIDDEN_WORDS)}
• URLs: siempre de los artículos proporcionados. NUNCA inventadas.
• ESTO_PASO, CASO_REAL y CONSEJO: campo "imagen" — elige UNA palabra exacta: cybersecurity, data-breach, hacker, network, server, cloud, code, ai, robot, phishing, privacy, energy, business, mobile, spain, technology
• intro: 2-3 líneas. Cálida, directa. Mencionar edición #{EDITION_NUMBER}.
• radar: EXACTAMENTE 4 ítems, de fuentes distintas.
• enlaces: EXACTAMENTE 3 recursos (1 artículo, 1 vídeo, 1 quiz/herramienta).

══════════════════════════════════════════════════════
SECCIONES A GENERAR
══════════════════════════════════════════════════════
1. ESTO_PASO: La noticia más impactante del mes en ciberseguridad/tecnología.
   3-4 líneas. Dato numérico obligatorio. URL de la noticia.

2. CASO_REAL: Un incidente real de seguridad narrado como episodio de serie.
   Qué pasó, cómo, consecuencias. Máx 5 líneas. URL.

3. CONSEJO: UN consejo práctico que cualquier empleado puede aplicar hoy.
   Concreto, útil, con toque de humor. Máx 3 frases.

4. RETO: Una acción concreta que los Nexters pueden completar este mes.
   Específica, medible, motivadora. Máx 2 frases. No es una recomendación — es un reto activo.

5. RADAR: 4 titulares relevantes de fuentes distintas. Breve y directo.
   Incluir org (nombre corto de la fuente) y fecha.

6. IA_DIA: Tendencia o incidente relevante sobre IA en ciberseguridad.
   3-4 líneas. Cómo afecta a equipos IT. URL del artículo fuente.

7. ENLACES: 3 recursos:
   - tipo "articulo": lectura recomendada
   - tipo "video": vídeo educativo o demostrativo (YouTube u otro)
   - tipo "quiz": herramienta interactiva, test o quiz de seguridad
   Cada uno con descripcion (1 línea de por qué merece la pena) y fuente.

8. INTRO: 2-3 líneas de apertura. Cálida, directa, que enganche.

Responde ÚNICAMENTE con JSON válido con esta estructura exacta:
{{
  "razonamiento": {{
    "esto_paso": "Elegí [título] porque [motivo concreto para Nexters]",
    "caso_real": "Elegí [título] porque...",
    "radar": "Elegí estos 4 porque..."
  }},
  "intro": "...",
  "esto_paso": {{"titulo": "...", "texto": "...", "url": "...", "imagen": "ONE keyword from: cybersecurity, data-breach, hacker, network, server, cloud, code, ai, robot, phishing, privacy, energy, business, mobile, spain, technology"}},
  "caso_real": {{"titulo": "...", "texto": "...", "url": "...", "imagen": "ONE keyword from: cybersecurity, data-breach, hacker, network, server, cloud, code, ai, robot, phishing, privacy, energy, business, mobile, spain, technology"}},
  "consejo":   {{"titulo": "...", "texto": "...", "imagen": "ONE keyword from the same list"}},
  "reto":      {{"titulo": "...", "texto": "..."}},
  "ia_dia":    {{"titulo": "...", "texto": "...", "url": "...", "imagen": "ONE keyword from the same list"}},
  "radar": [
    {{"titulo": "...", "org": "...", "url": "...", "fecha": "..."}},
    {{"titulo": "...", "org": "...", "url": "...", "fecha": "..."}},
    {{"titulo": "...", "org": "...", "url": "...", "fecha": "..."}},
    {{"titulo": "...", "org": "...", "url": "...", "fecha": "..."}}
  ],
  "enlaces": [
    {{"tipo": "articulo", "titulo": "...", "descripcion": "...", "url": "...", "fuente": "..."}},
    {{"tipo": "video",    "titulo": "...", "descripcion": "...", "url": "...", "fuente": "..."}},
    {{"tipo": "quiz",     "titulo": "...", "descripcion": "...", "url": "...", "fuente": "..."}}
  ]
}}

═══════════════════════════════════════════════
ARTÍCULOS DISPONIBLES — {mes_actual}
═══════════════════════════════════════════════
{articles_text}
"""

    print("  🤖 Llamando a Claude API (selección razonada + redacción)...")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    content = json.loads(raw)

    if "razonamiento" in content:
        print("\n  📝 Razonamiento editorial:")
        for k, v in content["razonamiento"].items():
            print(f"     {k}: {v}")

    print("  ✅ Contenido generado correctamente")
    return content


def verify_content(content: Dict, edition: str) -> List[str]:
    """
    Verifica criterios editoriales antes del envío.
    Devuelve lista de issues; lista vacía = todo OK.
    """
    issues = []
    mes = datetime.now().strftime("%B %Y").capitalize()

    subject = f"NextLetter #{edition} — {mes}"
    if len(subject) > 45:
        issues.append(f"Subject demasiado largo: {len(subject)} chars (máx 45)")

    texto_esto = content.get("esto_paso", {}).get("texto", "")
    if not any(c.isdigit() for c in texto_esto):
        issues.append("esto_paso sin dato numérico — añadir cifra de impacto")

    for seccion in ["esto_paso", "caso_real", "ia_dia"]:
        url = content.get(seccion, {}).get("url", "")
        if not url.startswith("http"):
            issues.append(f"{seccion} sin URL válida (tiene: '{url}')")

    radar = content.get("radar", [])
    if len(radar) != 4:
        issues.append(f"Radar con {len(radar)} ítems — necesita exactamente 4")

    all_text = json.dumps(content, ensure_ascii=False).lower()
    found = [w for w in FORBIDDEN_WORDS if w in all_text]
    if found:
        issues.append(f"Palabras prohibidas encontradas: {', '.join(found)}")

    consejo_text = content.get("consejo", {}).get("texto", "")
    frases = [f for f in re.split(r'[.!?]', consejo_text) if f.strip()]
    if len(frases) > 3:
        issues.append(f"consejo.texto con {len(frases)} frases — máx 3")

    reto_text = content.get("reto", {}).get("texto", "")
    reto_frases = [f for f in re.split(r'[.!?]', reto_text) if f.strip()]
    if len(reto_frases) > 2:
        issues.append(f"reto.texto con {len(reto_frases)} frases — máx 2")

    enlaces = content.get("enlaces", [])
    if len(enlaces) != 3:
        issues.append(f"enlaces con {len(enlaces)} ítems — necesita exactamente 3")

    return issues


def build_html(content: Dict, edition: str) -> str:
    """Monta el HTML del NextLetter replicando exactamente el diseño oficial."""
    now       = datetime.now()
    mes       = now.strftime("%B %Y").capitalize()
    mes_upper = now.strftime("%B %Y").upper()
    year      = now.year
    month     = now.month

    # ── Extraer contenido en variables locales ──────────────────────────────
    intro          = content.get("intro", "")
    esto_titulo    = content.get("esto_paso", {}).get("titulo", "")
    esto_texto     = content.get("esto_paso", {}).get("texto", "")
    esto_url       = content.get("esto_paso", {}).get("url", "#")
    caso_titulo    = content.get("caso_real", {}).get("titulo", "")
    caso_texto     = content.get("caso_real", {}).get("texto", "")
    caso_url       = content.get("caso_real", {}).get("url", "#")
    consejo_titulo = content.get("consejo",  {}).get("titulo", "")
    consejo_texto  = content.get("consejo",  {}).get("texto", "")
    reto_titulo    = content.get("reto",     {}).get("titulo", "")
    reto_texto     = content.get("reto",     {}).get("texto", "")
    ia_titulo      = content.get("ia_dia",   {}).get("titulo", "")
    ia_texto       = content.get("ia_dia",   {}).get("texto", "")
    ia_url         = content.get("ia_dia",   {}).get("url", "#")

    # URLs de imágenes Unsplash (IDs curados, CDN directo)
    esto_img_url    = _unsplash_url(content.get("esto_paso", {}).get("imagen", "cybersecurity"), 1200, 220)
    caso_img_url    = _unsplash_url(content.get("caso_real", {}).get("imagen", "hacker"),         800, 160)
    consejo_img_url = _unsplash_url(content.get("consejo",  {}).get("imagen", "code"),            800, 160)
    ia_img_url      = _unsplash_url(content.get("ia_dia",   {}).get("imagen", "ai"),             1200, 180)

    # ── Radar HTML ──────────────────────────────────────────────────────────
    radar_dot_colors = [RED, YELLOW, CYAN, VIOLET]
    radar_html = ""
    for i, item in enumerate(content.get("radar", [])):
        dot_color = radar_dot_colors[i % len(radar_dot_colors)]
        r_titulo = item.get("titulo", "")
        r_org    = item.get("org", "")
        r_url    = item.get("url", "#")
        r_fecha  = item.get("fecha", "")
        radar_html += (
            f'<a href="{r_url}" target="_blank" class="radar-grid-item"'
            f' onclick="trackLink(\'radar_{i}\', this.href)">\n'
            f'  <div class="radar-source">'
            f'<span class="radar-dot" style="background:{dot_color}"></span>'
            f'<span class="radar-org">{r_org}</span></div>\n'
            f'  <div class="radar-headline">{r_titulo}</div>\n'
            f'  <div class="radar-meta">{r_fecha}</div>\n'
            f'</a>\n'
        )

    # ── Enlaces HTML ────────────────────────────────────────────────────────
    tipo_icons  = {
        "articulo": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>',
        "video":    '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>',
        "quiz":     '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    }
    _LINK_ICON_FALLBACK = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>'
    tipo_labels = {"articulo": "Artículo", "video": "Vídeo", "quiz": "Quiz interactivo"}
    tipo_class  = {"articulo": "lc-news", "video": "lc-video", "quiz": "lc-quiz"}
    enlaces_html = ""
    for e in content.get("enlaces", []):
        tipo    = e.get("tipo", "articulo")
        icon    = tipo_icons.get(tipo, _LINK_ICON_FALLBACK)
        label   = tipo_labels.get(tipo, "Enlace")
        lc_cls  = tipo_class.get(tipo, "lc-news")
        e_titulo = e.get("titulo", "")
        e_desc   = e.get("descripcion", "")
        e_url    = e.get("url", "#")
        e_fuente = e.get("fuente", "")
        enlaces_html += (
            f'<a href="{e_url}" class="link-card {lc_cls}" target="_blank"'
            f' onclick="trackLink(\'{tipo}\', this.href)">\n'
            f'  <span class="link-icon">{icon}</span>\n'
            f'  <span class="link-label">{label}</span>\n'
            f'  <span class="link-title">{e_titulo}</span>\n'
            f'  <span class="link-desc">{e_desc}</span>\n'
            f'  <span class="link-source">{e_fuente}</span>\n'
            f'</a>\n'
        )

    # ── Footer: lista de ediciones (actual + 2 próximas) ────────────────────
    edition_int   = int(edition)
    now_badge     = (
        '<span style="display:inline-flex;align-items:center;gap:5px;margin-left:6px;'
        'background:rgba(250,60,15,0.15);border:1px solid rgba(250,60,15,0.4);'
        'padding:1px 7px;font-size:9px;letter-spacing:1.5px;color:var(--red);vertical-align:middle;">'
        '<span style="width:5px;height:5px;border-radius:50%;background:var(--red);'
        'display:inline-block;animation:pulse 1.5s ease-in-out infinite;"></span>NOW</span>'
    )
    footer_editions = ""
    for delta in range(3):
        ed_num = edition_int + delta
        ed_str = f"{ed_num:02d}"
        ed_mes = _next_month_label(year, month, delta)
        if delta == 0:
            footer_editions += f'<li><a href="/{ed_str}/">#{ed_str} — {ed_mes} {now_badge}</a></li>\n'
        else:
            footer_editions += (
                f'<li><a href="#" style="opacity:0.25;pointer-events:none;">'
                f'#{ed_str} — {ed_mes}</a></li>\n'
            )

    # ── GA4 script con edición sustituida ───────────────────────────────────
    ga4_script = _GA4_SCRIPT.replace("__EDITION__", edition)

    # ── HTML completo ────────────────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NextLetter #{edition} — LOGNEXT</title>
<link rel="icon" type="image/svg+xml" href="{_FAVICON_SVG}">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
{ga4_script}
<style>
{_CSS}
</style>
</head>
<body>

{_CURSOR_SVG}
<div class="cursor-ring" id="cursorRing"></div>

<canvas id="nebula-canvas"></canvas>
<div class="bg-grid"></div>

<!-- TOPBAR -->
<div class="topbar">
  <div class="topbar-inner">
    <span class="topbar-name">NEXT<span>LETTER</span></span>
    <div class="topbar-center">
      {_LOGNEXT_WORDMARK_SVG}
    </div>
    <div class="topbar-right">
      <span class="topbar-edition-num">EDICIÓN #{edition}</span>
      <span class="topbar-edition-date">{mes_upper}</span>
    </div>
  </div>
</div>

<div class="wrapper">

  <!-- HEADER -->
  <div class="header">
    <div class="header-scan"></div>
    <div class="header-inner">
      <div>
        <div class="logo-row">
          <span class="logo-next">NEXT</span><span class="logo-letter">LETTER</span>
        </div>
        <div class="header-tagline-big">Intel real. Sin ruido. Cada mes.</div>
        <div class="header-dots">
          <div class="hdot" style="background:var(--red);animation-delay:0s"></div>
          <div class="hdot" style="background:var(--cyan);animation-delay:0.3s"></div>
          <div class="hdot" style="background:var(--yellow);animation-delay:0.6s"></div>
          <div class="hdot" style="background:var(--green);animation-delay:0.9s"></div>
          <div class="hdot" style="background:var(--violet);animation-delay:1.2s"></div>
        </div>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <div class="stat-number">#{edition}</div>
          <div class="stat-label">Edición</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">6</div>
          <div class="stat-label">Secciones</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">~5'</div>
          <div class="stat-label">Lectura</div>
        </div>
      </div>
    </div>
    <div class="header-meta">
      <span style="font-size:11px;opacity:0.4;font-family:'JetBrains Mono',monospace;letter-spacing:2px;">BY LOGNEXT · DEPARTAMENTO IT</span>
      <span class="header-issue">{mes_upper}</span>
    </div>
  </div>

  <!-- INTRO -->
  <div class="intro" onmouseenter="trackSection('intro')">
    {intro}
  </div>

  <!-- SEPARADOR -->
  <div class="sep"></div>

  <!-- GRID PRINCIPAL -->
  <div class="main-grid">

    <!-- 1. IA AL DÍA — primera sección, ancho completo -->
    <div class="card card-ia full-width" onmouseenter="trackSection('ia_dia')">
      <div style="height:200px;overflow:hidden;margin:-36px -44px 28px;position:relative;">
        <img src="{ia_img_url}" loading="lazy" alt="" style="width:100%;height:100%;object-fit:cover;opacity:0.35;">
        <div style="position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,14,34,0) 30%,#000e22 100%);"></div>
      </div>
      <div class="section-tag" style="color:var(--blue)"><svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg> IA al día</div>
      <div class="card-title">{ia_titulo}</div>
      <div class="card-text">{ia_texto}</div>
      <a href="{ia_url}" target="_blank" class="card-link" style="color:var(--blue)" onclick="trackLink('ia_dia', this.href)">Leer el análisis completo <span class="arrow">→</span></a>
    </div>

    <!-- 2a. ESTO PASÓ — columna izquierda -->
    <div class="card card-esto" onmouseenter="trackSection('esto_paso')">
      <div style="height:180px;overflow:hidden;margin:-36px -44px 24px;position:relative;">
        <img src="{esto_img_url}" loading="lazy" alt="" style="width:100%;height:100%;object-fit:cover;opacity:0.45;">
        <div style="position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,41,0) 30%,#000029 100%);"></div>
      </div>
      <div class="section-tag" style="color:var(--red)"><svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><rect x="2" y="3" width="20" height="18" rx="2"/><line x1="7" y1="8" x2="17" y2="8"/><line x1="7" y1="12" x2="17" y2="12"/><line x1="7" y1="16" x2="13" y2="16"/></svg> Esto pasó</div>
      <div class="card-title">{esto_titulo}</div>
      <div class="card-text">{esto_texto}</div>
      <a href="{esto_url}" target="_blank" class="card-link" style="color:var(--red)" onclick="trackLink('esto_paso', this.href)">Leer la historia completa <span class="arrow">→</span></a>
    </div>

    <!-- 2b. CASO DEL MES — columna derecha -->
    <div class="card card-caso" onmouseenter="trackSection('caso_mes')">
      <div style="height:180px;overflow:hidden;margin:-36px -44px 24px;position:relative;">
        <img src="{caso_img_url}" loading="lazy" alt="" style="width:100%;height:100%;object-fit:cover;opacity:0.4;">
        <div style="position:absolute;inset:0;background:linear-gradient(to bottom,rgba(5,5,31,0) 30%,#05051f 100%);"></div>
      </div>
      <div class="section-tag" style="color:var(--yellow)"><svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> Amenaza del mes</div>
      <div class="card-title">{caso_titulo}</div>
      <div class="card-text">{caso_texto}</div>
      <a href="{caso_url}" target="_blank" class="card-link" style="color:var(--yellow)" onclick="trackLink('caso_mes', this.href)">Ver el caso completo <span class="arrow">→</span></a>
    </div>

    <!-- 3. EN EL RADAR — ancho completo, grid 2×2 -->
    <div class="card card-radar full-width" onmouseenter="trackSection('radar')">
      <div class="section-tag" style="color:var(--cyan)"><svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><path d="M4 11a9 9 0 0 1 9 9"/><path d="M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1" fill="currentColor" stroke="none"/></svg> En el radar</div>
      <div class="card-title">Lo que no puedes perderte este mes</div>
      <div class="radar-grid">
        {radar_html}
      </div>
    </div>

    <!-- 4a. CONSEJO — columna izquierda -->
    <div class="card card-consejo" onmouseenter="trackSection('consejo')">
      <div style="height:160px;overflow:hidden;margin:-36px -44px 24px;position:relative;">
        <img src="{consejo_img_url}" loading="lazy" alt="" style="width:100%;height:100%;object-fit:cover;opacity:0.3;">
        <div style="position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,41,0) 30%,#000029 100%);"></div>
      </div>
      <div class="section-tag" style="color:var(--green)"><svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14z"/></svg> Consejo del mes</div>
      <div class="card-title">{consejo_titulo}</div>
      <div class="card-text">{consejo_texto}</div>
    </div>

    <!-- 4b. RETO — columna derecha -->
    <div class="card card-reto" onmouseenter="trackSection('reto')">
      <div class="section-tag" style="color:var(--green)"><svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> El reto de {mes}</div>
      <div class="reto-badge">RETO ACTIVO</div>
      <div class="card-title">{reto_titulo}</div>
      <div class="card-text">{reto_texto}</div>
      <div class="reto-progress"><div class="reto-progress-bar"></div></div>
      <div class="reto-label">
        <span>{mes_upper}</span>
        <span>¿Lo has hecho ya? ✓</span>
      </div>
    </div>

    <!-- 5. PHISHING TEST — estático, ancho completo -->
    {_PHISHING_HTML}

    <!-- 6. ENLACES — ancho completo -->
    <div class="card card-links full-width" style="padding-bottom:36px;" onmouseenter="trackSection('enlaces')">
      <div class="section-tag" style="color:var(--violet)"><svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg> Por si queréis caer en el agujero</div>
      <div class="links-grid">
        {enlaces_html}
      </div>
    </div>

  </div><!-- /main-grid -->

  <!-- FOOTER -->
  <div class="footer">
    <div class="footer-inner">

      <div>
        <div class="footer-col-title">Somos Nexters</div>
        <div class="footer-col-rule"></div>
        <div class="footer-brand-name">NEXT<span>LETTER</span></div>
        <div class="footer-brand-text">La newsletter de LOGNEXT para todos los Nexters. Sin tecnicismos aburridos, sin correos genéricos. Solo lo que importa, cada mes.</div>
      </div>

      <div>
        <div class="footer-col-title">Ediciones</div>
        <div class="footer-col-rule"></div>
        <ul class="footer-links-list">
          {footer_editions}
        </ul>
      </div>

      <div>
        <div class="footer-col-title">Contacto IT</div>
        <div class="footer-col-rule"></div>
        <div class="footer-contact-item">
          <span class="footer-contact-icon">✉</span>
          <span class="footer-contact-text"><a href="mailto:sistemas@lognext.com">sistemas@lognext.com</a></span>
        </div>
        <div class="footer-contact-item">
          <span class="footer-contact-icon">☎</span>
          <span class="footer-contact-text"><a href="tel:+34636668059">+34 636 668 059</a></span>
        </div>
        <div class="footer-contact-item">
          <span class="footer-contact-icon">◎</span>
          <span class="footer-contact-text"><a href="https://lognext.com" target="_blank">lognext.com</a></span>
        </div>
      </div>

    </div>
    <div class="footer-bottom">
      <span class="footer-copy">© {year} LOGNEXT · Todos los derechos reservados.</span>
    </div>
  </div>

</div><!-- /wrapper -->

<script>
{_JS}
</script>
</body>
</html>"""


def generate(articles: List[Dict], warnings: List[str] = None) -> tuple:
    """Función principal: devuelve (web_html, content) para web y email."""
    content = select_and_draft(articles, warnings=warnings)

    issues = verify_content(content, EDITION_NUMBER)
    if issues:
        print(f"\n  ⚠️  {len(issues)} issue(s) editorial(es) detectado(s):")
        for issue in issues:
            print(f"     • {issue}")
        print("  ↩️  Regenerando con correcciones...\n")
        content = select_and_draft(articles, warnings=warnings)
        issues_retry = verify_content(content, EDITION_NUMBER)
        if issues_retry:
            print(f"  ⚠️  Tras reintento quedan {len(issues_retry)} issue(s) — continuando con advertencia")
            for issue in issues_retry:
                print(f"     • {issue}")
    else:
        print("  ✅ Verificación editorial: OK")

    html = build_html(content, EDITION_NUMBER)
    return html, content


if __name__ == "__main__":
    from scraper import fetch_articles, validate_freshness
    print("\n📰 Obteniendo artículos...\n")
    arts = fetch_articles()
    freshness = validate_freshness(arts)
    print("\n✍️  Generando NextLetter...\n")
    web_html, content = generate(arts, warnings=freshness["warnings"])
    with open("preview.html", "w", encoding="utf-8") as f:
        f.write(web_html)
    print("\n✅ Preview guardado en preview.html")
