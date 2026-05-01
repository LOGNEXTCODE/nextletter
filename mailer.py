"""
mailer.py — NextLetter
Envía el borrador del NextLetter via Microsoft Graph API (M365/Outlook).
El correo va SOLO al revisor (Miguel) para su aprobación antes del envío final.
"""

import os
import json
import requests
from datetime import datetime


# ─── CONFIGURACIÓN (via GitHub Secrets) ────────────────────────────────────────
TENANT_ID      = os.environ["MS_TENANT_ID"]
CLIENT_ID      = os.environ["MS_CLIENT_ID"]
CLIENT_SECRET  = os.environ["MS_CLIENT_SECRET"]
SENDER_EMAIL   = os.environ["MS_SENDER_EMAIL"]     # sistemas@lognext.com
REVIEWER_EMAIL = os.environ["REVIEWER_EMAIL"]       # miguel.aparicio@lognext.com
EDITION_NUMBER = os.environ.get("EDITION_NUMBER", "01")

# URL de la versión web publicada en GitHub Pages
WEB_URL = f"https://nextletter.lognext.com/{EDITION_NUMBER}/"


def get_access_token() -> str:
    """Obtiene el token de acceso de Microsoft Graph."""
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


def send_draft(html_content: str) -> bool:
    """
    Envía el NextLetter al revisor (Miguel) para su aprobación.
    Incluye un banner de revisión con enlace a la versión web publicada.
    Workflow: Miguel revisa → edita si necesario → reenvía a todos los Nexters.
    """
    token = get_access_token()
    mes   = datetime.now().strftime("%B %Y").capitalize()
    ts    = datetime.now().strftime("%d/%m/%Y a las %H:%M")

    banner = f"""
<div style="background:#0a0a1a;border:2px solid #FA3C0F;padding:20px 28px;font-family:'Space Grotesk',Arial,sans-serif;margin-bottom:0;">
  <table style="width:100%;border-collapse:collapse;">
    <tr>
      <td style="vertical-align:top;padding-right:20px;">
        <div style="color:#FA3C0F;font-weight:700;font-size:14px;letter-spacing:1px;margin-bottom:8px;">
          ⚠️ BORRADOR PARA REVISIÓN — NextLetter #{EDITION_NUMBER}
        </div>
        <div style="color:#E1E1E8;font-size:13px;line-height:1.7;opacity:0.8;">
          Generado automáticamente el <strong>{ts}</strong>.<br>
          Revísalo, edita lo que necesites y reenvíalo manualmente a los Nexters cuando esté listo.
        </div>
      </td>
      <td style="vertical-align:top;text-align:right;white-space:nowrap;">
        <a href="{WEB_URL}"
           style="display:inline-block;background:#FA3C0F;color:#fff;font-size:12px;
                  font-weight:700;text-decoration:none;padding:10px 18px;
                  letter-spacing:1px;text-transform:uppercase;">
          Ver versión web →
        </a>
      </td>
    </tr>
  </table>
</div>
<div style="height:4px;background:linear-gradient(90deg,#FA3C0F 0%,#FA3C0F 33%,#3CE6E6 33%,#3CE6E6 66%,#FFFA96 66%);margin-bottom:0;"></div>
"""

    payload = {
        "message": {
            "subject": f"[REVISAR] NextLetter #{EDITION_NUMBER} — {mes}",
            "body": {
                "contentType": "HTML",
                "content": banner + html_content,
            },
            "toRecipients": [
                {"emailAddress": {"address": REVIEWER_EMAIL}}
            ],
            "importance": "high",
        },
        "saveToSentItems": "false",   # No ensuciar el Enviados con borradores de revisión
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
    test_html = "<h1 style='color:#FA3C0F;font-family:Arial'>Test NextLetter</h1><p style='color:#fff;background:#000029;padding:20px'>Esto es un test del sistema de envío.</p>"
    send_draft(test_html)
