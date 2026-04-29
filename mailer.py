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
TENANT_ID     = os.environ["MS_TENANT_ID"]       # Azure AD Tenant ID
CLIENT_ID     = os.environ["MS_CLIENT_ID"]        # App registration Client ID
CLIENT_SECRET = os.environ["MS_CLIENT_SECRET"]    # App registration Client Secret
SENDER_EMAIL  = os.environ["MS_SENDER_EMAIL"]     # Cuenta desde la que se envía
REVIEWER_EMAIL = os.environ["REVIEWER_EMAIL"]     # Tu email para recibir el borrador
EDITION_NUMBER = os.environ.get("EDITION_NUMBER", "01")


def get_access_token() -> str:
    """Obtiene el token de acceso de Microsoft Graph."""
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    token = response.json()["access_token"]
    print("  ✅ Token de acceso obtenido")
    return token


def send_draft(html_content: str) -> bool:
    """
    Envía el borrador del NextLetter al revisor (Miguel).
    El asunto incluye [BORRADOR] para que sea fácil de identificar.
    """
    token = get_access_token()
    mes = datetime.now().strftime("%B %Y").capitalize()

    payload = {
        "message": {
            "subject": f"[BORRADOR PARA REVISIÓN] NextLetter #{EDITION_NUMBER} — {mes}",
            "body": {
                "contentType": "HTML",
                "content": f"""
                <div style="background:#fffbe6;border:2px solid #FA3C0F;padding:16px 24px;font-family:Arial,sans-serif;margin-bottom:0;">
                  <strong style="color:#FA3C0F;">⚠️ BORRADOR PARA TU REVISIÓN</strong><br>
                  <span style="font-size:13px;color:#333;">
                    Este es el NextLetter #{EDITION_NUMBER} generado automáticamente. 
                    Revísalo, edita lo que necesites y envíalo manualmente desde Outlook cuando esté listo.<br><br>
                    <strong>Generado el:</strong> {datetime.now().strftime("%d/%m/%Y a las %H:%M")}
                  </span>
                </div>
                {html_content}
                """
            },
            "toRecipients": [
                {"emailAddress": {"address": REVIEWER_EMAIL}}
            ],
            "importance": "normal"
        },
        "saveToSentItems": "true"
    }

    url = f"https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/sendMail"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 202:
        print(f"  ✅ Borrador enviado a {REVIEWER_EMAIL}")
        return True
    else:
        print(f"  ❌ Error al enviar: {response.status_code} — {response.text}")
        return False


if __name__ == "__main__":
    # Test: envía un HTML de prueba
    test_html = "<h1 style='color:#FA3C0F'>Test NextLetter</h1><p>Esto es un test del sistema de envío.</p>"
    send_draft(test_html)
