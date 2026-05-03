"""
mailer.py — NextLetter
Envía el borrador del NextLetter via Microsoft Graph API (M365/Outlook).
El correo va SOLO al revisor (Miguel) para su aprobación antes del envío final.
Usa email_template.html — layout de tabla, estilos inline, sin JS ni animaciones.
"""

import os
import requests
from datetime import datetime


# ─── CONFIGURACIÓN (via GitHub Secrets) ────────────────────────────────────────
TENANT_ID      = os.environ["MS_TENANT_ID"]
CLIENT_ID      = os.environ["MS_CLIENT_ID"]
CLIENT_SECRET  = os.environ["MS_CLIENT_SECRET"]
SENDER_EMAIL   = os.environ["MS_SENDER_EMAIL"]     # sistemas@lognext.com
REVIEWER_EMAIL = os.environ["REVIEWER_EMAIL"]       # miguel.aparicio@lognext.com
EDITION_NUMBER = os.environ.get("EDITION_NUMBER", "01")

WEB_URL = f"https://nextletter.lognext.com/{EDITION_NUMBER}/"

_RADAR_DOT_COLORS = ["#FA3C0F", "#FFFA96", "#3CE6E6", "#C896FF"]
_TIPO_LABELS      = {"articulo": "ARTÍCULO", "video": "VÍDEO", "quiz": "QUIZ"}
_TIPO_COLORS      = {"articulo": "#FA3C0F", "video": "#3CE6E6", "quiz": "#FFFA96"}


def get_access_token() -> str:
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    print("  ✅ Token de acceso obtenido")
    return response.json()["access_token"]


def _build_radar_html(radar_items: list) -> str:
    rows = ""
    for i, item in enumerate(radar_items):
        dot_color = _RADAR_DOT_COLORS[i % len(_RADAR_DOT_COLORS)]
        titulo    = item.get("titulo", "")
        org       = item.get("org", "")
        url       = item.get("url", "#")
        fecha     = item.get("fecha", "")
        border    = "" if i == len(radar_items) - 1 else "border-bottom:1px solid rgba(255,255,255,0.06);"
        rows += f"""
    <tr>
      <td style="{border}padding:12px 0;">
        <table cellpadding="0" cellspacing="0" border="0" width="100%"><tr>
          <td style="vertical-align:top;padding-right:10px;width:14px;">
            <div style="width:6px;height:6px;border-radius:50%;background-color:{dot_color};margin-top:5px;"></div>
          </td>
          <td style="vertical-align:top;">
            <p style="margin:0 0 3px 0;font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#E1E1E8;font-family:'Courier New',Courier,monospace;opacity:0.55;">{org}</p>
            <a href="{url}" target="_blank" style="display:block;font-size:13px;font-weight:600;color:#ffffff;text-decoration:none;line-height:1.4;font-family:Arial,sans-serif;">{titulo}</a>
            <p style="margin:4px 0 0 0;font-size:10px;color:#E1E1E8;font-family:'Courier New',Courier,monospace;opacity:0.35;">{fecha}</p>
          </td>
        </tr></table>
      </td>
    </tr>"""
    return f'<table width="100%" cellpadding="0" cellspacing="0" border="0">{rows}\n</table>'


def _build_enlaces_html(enlaces_items: list) -> str:
    blocks = ""
    for i, e in enumerate(enlaces_items):
        tipo    = e.get("tipo", "articulo")
        label   = _TIPO_LABELS.get(tipo, "ENLACE")
        color   = _TIPO_COLORS.get(tipo, "#FA3C0F")
        titulo  = e.get("titulo", "")
        desc    = e.get("descripcion", "")
        url     = e.get("url", "#")
        fuente  = e.get("fuente", "")
        margin  = "" if i == len(enlaces_items) - 1 else "margin-bottom:12px;"
        blocks += f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="{margin}border-left:3px solid {color};background-color:#080820;">
<tr><td style="padding:16px 20px;">
  <p style="margin:0 0 6px 0;font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:{color};font-family:'Courier New',Courier,monospace;">{label}</p>
  <a href="{url}" target="_blank" style="display:block;font-size:14px;font-weight:600;color:#ffffff;text-decoration:none;line-height:1.4;margin-bottom:6px;font-family:Arial,sans-serif;">{titulo}</a>
  <p style="margin:0 0 8px 0;font-size:12px;color:#E1E1E8;line-height:1.6;font-family:Arial,sans-serif;opacity:0.7;">{desc}</p>
  <p style="margin:0;font-size:10px;color:#E1E1E8;font-family:'Courier New',Courier,monospace;opacity:0.4;">{fuente}</p>
</td></tr>
</table>"""
    return blocks


def build_email_html(content: dict, edition: str, web_url: str, timestamp: str) -> str:
    """Carga email_template.html y sustituye todos los [[PLACEHOLDERS]]."""
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    now = datetime.now()
    mes       = now.strftime("%B %Y").capitalize()
    mes_upper = now.strftime("%B %Y").upper()

    replacements = {
        "[[EDITION]]":        edition,
        "[[MES]]":            mes,
        "[[MES_UPPER]]":      mes_upper,
        "[[YEAR]]":           str(now.year),
        "[[TIMESTAMP]]":      timestamp,
        "[[WEB_URL]]":        web_url,
        "[[PREHEADER]]":      "IA, ciberseguridad y el reto del mes — todo lo que necesitas saber",
        "[[INTRO]]":          content.get("intro", ""),
        "[[IA_TITULO]]":      content.get("ia_dia",    {}).get("titulo", ""),
        "[[IA_TEXTO]]":       content.get("ia_dia",    {}).get("texto",  ""),
        "[[IA_URL]]":         content.get("ia_dia",    {}).get("url",    "#"),
        "[[ESTO_TITULO]]":    content.get("esto_paso", {}).get("titulo", ""),
        "[[ESTO_TEXTO]]":     content.get("esto_paso", {}).get("texto",  ""),
        "[[ESTO_URL]]":       content.get("esto_paso", {}).get("url",    "#"),
        "[[CASO_TITULO]]":    content.get("caso_real", {}).get("titulo", ""),
        "[[CASO_TEXTO]]":     content.get("caso_real", {}).get("texto",  ""),
        "[[CASO_URL]]":       content.get("caso_real", {}).get("url",    "#"),
        "[[CONSEJO_TITULO]]": content.get("consejo",   {}).get("titulo", ""),
        "[[CONSEJO_TEXTO]]":  content.get("consejo",   {}).get("texto",  ""),
        "[[RETO_TITULO]]":    content.get("reto",      {}).get("titulo", ""),
        "[[RETO_TEXTO]]":     content.get("reto",      {}).get("texto",  ""),
        "[[RADAR_ITEMS]]":    _build_radar_html(content.get("radar", [])),
        "[[ENLACES_ITEMS]]":  _build_enlaces_html(content.get("enlaces", [])),
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, str(value))

    return html


def send_draft(content: dict) -> bool:
    """
    Construye el email con email_template.html y lo envía al revisor.
    Workflow: Miguel revisa → edita si necesario → reenvía a los Nexters.
    """
    token = get_access_token()
    now   = datetime.now()
    mes   = now.strftime("%B %Y").capitalize()
    ts    = now.strftime("%d/%m/%Y a las %H:%M")

    email_html = build_email_html(content, EDITION_NUMBER, WEB_URL, ts)
    subject    = f"[REVISAR] NextLetter #{EDITION_NUMBER} — {mes} | Lista para envío a las 10:00h"

    payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": email_html,
            },
            "toRecipients": [
                {"emailAddress": {"address": REVIEWER_EMAIL}}
            ],
            "importance": "high",
        },
        "saveToSentItems": "false",
    }

    url = f"https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/sendMail"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 202:
        print(f"  ✅ Borrador enviado a {REVIEWER_EMAIL}")
        print(f"  🌐 Versión web: {WEB_URL}")
        return True
    else:
        print(f"  ❌ Error al enviar: {response.status_code} — {response.text}")
        return False


if __name__ == "__main__":
    test_content = {
        "intro": "Test del sistema de envío. Todo funciona correctamente.",
        "ia_dia":    {"titulo": "Test IA al día",       "texto": "Texto de prueba para IA.",    "url": "https://example.com"},
        "esto_paso": {"titulo": "Test Esto pasó",       "texto": "Texto de prueba. 42% afectados.", "url": "https://example.com"},
        "caso_real": {"titulo": "Test Amenaza del mes", "texto": "Texto de prueba para caso.", "url": "https://example.com"},
        "consejo":   {"titulo": "Test Consejo",         "texto": "Texto de prueba para consejo."},
        "reto":      {"titulo": "Test Reto activo",     "texto": "Texto de prueba para reto."},
        "radar": [
            {"titulo": "Titular 1 de prueba", "org": "INCIBE",   "url": "https://incibe.es",   "fecha": "01/05/2026"},
            {"titulo": "Titular 2 de prueba", "org": "CCN-CERT", "url": "https://ccn-cert.cni.es", "fecha": "02/05/2026"},
            {"titulo": "Titular 3 de prueba", "org": "Xataka",   "url": "https://xataka.com",  "fecha": "03/05/2026"},
            {"titulo": "Titular 4 de prueba", "org": "El País",  "url": "https://elpais.com",  "fecha": "04/05/2026"},
        ],
        "enlaces": [
            {"tipo": "articulo", "titulo": "Test Artículo",  "descripcion": "Descripción del artículo.", "url": "https://example.com", "fuente": "Fuente A"},
            {"tipo": "video",    "titulo": "Test Vídeo",     "descripcion": "Descripción del vídeo.",    "url": "https://example.com", "fuente": "YouTube"},
            {"tipo": "quiz",     "titulo": "Test Quiz",      "descripcion": "Descripción del quiz.",     "url": "https://example.com", "fuente": "Fuente B"},
        ],
    }
    send_draft(test_content)
