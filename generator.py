"""
generator.py — NextLetter
Usa Claude API para seleccionar noticias, redactar el contenido
y montar el HTML final del correo.
"""

import os
import json
import anthropic
from datetime import datetime
from typing import List, Dict

# ─── CONFIGURACIÓN ─────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
EDITION_NUMBER    = os.environ.get("EDITION_NUMBER", "01")  # Se puede pasar como variable

# ─── COLORES LOGNEXT ───────────────────────────────────────────────────────────
NAVY   = "#000029"
RED    = "#FA3C0F"
CYAN   = "#3CE6E6"
YELLOW = "#FFFA96"
GREEN  = "#64F07D"
GREY   = "#E1E1E8"
WHITE  = "#FFFFFF"


def select_and_draft(articles: List[Dict]) -> Dict:
    """
    Llama a Claude para:
    1. Seleccionar las noticias más relevantes del mes
    2. Redactar cada sección del NextLetter
    Devuelve un dict con todas las secciones.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Preparar el contexto de artículos para Claude
    articles_text = "\n\n".join([
        f"[{i+1}] FUENTE: {a['source']} | CATEGORÍA: {a['category']}\n"
        f"TÍTULO: {a['title']}\n"
        f"FECHA: {a['date']}\n"
        f"RESUMEN: {a['summary']}\n"
        f"URL: {a['url']}"
        for i, a in enumerate(articles[:40])  # Máximo 40 artículos al modelo
    ])

    mes_actual = datetime.now().strftime("%B %Y").capitalize()

    prompt = f"""Eres el redactor de NextLetter, la newsletter mensual de ciberseguridad y tecnología de LOGNEXT.

TONO: Cercano, con humor sutil, sin tecnicismos innecesarios. Como si lo escribiera un compañero que sabe mucho pero no lo hace pesado. Nada de lenguaje corporativo aburrido.

ESTRUCTURA DEL NEXTLETTER (debes rellenar cada sección):

1. ESTO_PASO: Selecciona LA noticia más impactante del mes en ciberseguridad o tecnología. Cuéntala en 3-4 líneas como si se lo contaras a un amigo. Incluye el dato más llamativo. Incluye la URL de la noticia.

2. CASO_REAL: Elige UN caso real de ataque, brecha o incidente de seguridad. Cuéntalo como si fuera un episodio de serie: qué pasó, cómo, qué consecuencias tuvo. Máximo 5 líneas. Incluye la URL.

3. CONSEJO: UN solo consejo práctico de seguridad que cualquier empleado pueda aplicar hoy mismo. Que sea concreto, útil y con un toque de humor. Máximo 3 líneas.

4. RETO: Una pequeña acción que proponemos hacer este mes. Sencilla, medible. Ej: "Activa el doble factor en tu cuenta personal esta semana". Máximo 2 líneas.

5. ENLACES: 2 enlaces de interés (artículo, vídeo, quiz de seguridad...). Con una línea explicando por qué merece la pena.

6. INTRO: Una introducción de 2-3 líneas para abrir el correo. Cálida, directa, que enganche. Menciona que es la edición #{EDITION_NUMBER} de NextLetter.

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
  "intro": "...",
  "esto_paso": {{"titulo": "...", "texto": "...", "url": "..."}},
  "caso_real": {{"titulo": "...", "texto": "...", "url": "..."}},
  "consejo": {{"titulo": "...", "texto": "..."}},
  "reto": {{"titulo": "...", "texto": "..."}},
  "enlaces": [
    {{"titulo": "...", "descripcion": "...", "url": "..."}},
    {{"titulo": "...", "descripcion": "...", "url": "..."}}
  ]
}}

ARTÍCULOS DISPONIBLES ESTE MES:
{articles_text}
"""

    print("  🤖 Llamando a Claude API para redactar el NextLetter...")
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    # Limpiar posibles backticks si Claude los añade
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    content = json.loads(raw)
    print("  ✅ Contenido generado correctamente")
    return content


def build_html(content: Dict, edition: str) -> str:
    """
    Monta el HTML del correo con el branding de LOGNEXT.
    """
    mes = datetime.now().strftime("%B %Y").capitalize()
    year = datetime.now().year

    enlaces_html = ""
    for e in content.get("enlaces", []):
        enlaces_html += f"""
        <tr>
          <td style="padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.07);">
            <a href="{e['url']}" style="color:{CYAN}; font-weight:600; text-decoration:none;">→ {e['titulo']}</a>
            <div style="color:{GREY}; font-size:13px; margin-top:3px; opacity:0.7;">{e['descripcion']}</div>
          </td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<title>NextLetter #{edition}</title>
</head>
<body style="margin:0;padding:0;background:#0a0a1a;font-family:'Space Grotesk',Arial,sans-serif;">

  <div style="max-width:620px;margin:0 auto;padding:32px 16px;">

    <!-- CABECERA -->
    <div style="background:{NAVY};border-top:5px solid {RED};padding:32px 40px 24px;margin-bottom:4px;">
      <div style="display:flex;align-items:baseline;gap:0;">
        <span style="font-size:52px;font-weight:700;color:{WHITE};letter-spacing:-2px;line-height:1;">NEXT</span>
        <span style="font-size:52px;font-weight:300;color:{RED};letter-spacing:-2px;line-height:1;">LETTER</span>
      </div>
      <div style="border-top:1px solid rgba(255,255,255,0.1);margin-top:12px;padding-top:10px;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:11px;color:{GREY};letter-spacing:2px;text-transform:uppercase;opacity:0.6;">La carta de los que van un paso por delante</span>
        <span style="font-size:11px;color:{RED};font-weight:600;letter-spacing:2px;">#{edition} · {mes}</span>
      </div>
    </div>

    <!-- INTRO -->
    <div style="background:{NAVY};padding:24px 40px;border-top:1px solid rgba(255,255,255,0.06);">
      <p style="color:{GREY};font-size:15px;line-height:1.7;margin:0;">{content['intro']}</p>
    </div>

    <!-- SEPARADOR -->
    <div style="height:4px;background:linear-gradient(90deg,{RED} 0%,{RED} 40%,{CYAN} 40%,{CYAN} 70%,{YELLOW} 70%);"></div>

    <!-- ESTO PASÓ -->
    <div style="background:{NAVY};padding:28px 40px;margin-top:4px;">
      <div style="font-size:10px;color:{RED};letter-spacing:4px;text-transform:uppercase;font-weight:600;margin-bottom:10px;">🗞️ ESTO PASÓ</div>
      <div style="font-size:18px;font-weight:700;color:{WHITE};margin-bottom:12px;line-height:1.3;">{content['esto_paso']['titulo']}</div>
      <p style="color:{GREY};font-size:14px;line-height:1.8;margin:0 0 14px;">{content['esto_paso']['texto']}</p>
      <a href="{content['esto_paso']['url']}" style="color:{CYAN};font-size:13px;font-weight:600;text-decoration:none;">Leer más →</a>
    </div>

    <!-- CASO REAL -->
    <div style="background:#050520;padding:28px 40px;margin-top:4px;border-left:4px solid {RED};">
      <div style="font-size:10px;color:{YELLOW};letter-spacing:4px;text-transform:uppercase;font-weight:600;margin-bottom:10px;">😱 EL CASO DEL MES</div>
      <div style="font-size:18px;font-weight:700;color:{WHITE};margin-bottom:12px;line-height:1.3;">{content['caso_real']['titulo']}</div>
      <p style="color:{GREY};font-size:14px;line-height:1.8;margin:0 0 14px;">{content['caso_real']['texto']}</p>
      <a href="{content['caso_real']['url']}" style="color:{YELLOW};font-size:13px;font-weight:600;text-decoration:none;">Ver la historia completa →</a>
    </div>

    <!-- CONSEJO -->
    <div style="background:{NAVY};padding:28px 40px;margin-top:4px;">
      <div style="font-size:10px;color:{GREEN};letter-spacing:4px;text-transform:uppercase;font-weight:600;margin-bottom:10px;">💡 EL CONSEJO DEL MES</div>
      <div style="font-size:18px;font-weight:700;color:{WHITE};margin-bottom:12px;line-height:1.3;">{content['consejo']['titulo']}</div>
      <p style="color:{GREY};font-size:14px;line-height:1.8;margin:0;">{content['consejo']['texto']}</p>
    </div>

    <!-- RETO -->
    <div style="background:#0a1a0a;padding:24px 40px;margin-top:4px;border:1px solid rgba(100,240,125,0.2);">
      <div style="font-size:10px;color:{GREEN};letter-spacing:4px;text-transform:uppercase;font-weight:600;margin-bottom:10px;">🎯 EL RETO DE ESTE MES</div>
      <div style="font-size:16px;font-weight:600;color:{WHITE};margin-bottom:8px;">{content['reto']['titulo']}</div>
      <p style="color:{GREY};font-size:14px;line-height:1.7;margin:0;">{content['reto']['texto']}</p>
    </div>

    <!-- ENLACES -->
    <div style="background:{NAVY};padding:28px 40px;margin-top:4px;">
      <div style="font-size:10px;color:{CYAN};letter-spacing:4px;text-transform:uppercase;font-weight:600;margin-bottom:16px;">🔗 POR SI QUERÉIS CAER EN EL AGUJERO</div>
      <table style="width:100%;border-collapse:collapse;">
        {enlaces_html}
      </table>
    </div>

    <!-- FOOTER -->
    <div style="background:#000015;padding:24px 40px;margin-top:4px;text-align:center;">
      <div style="font-size:22px;font-weight:700;color:{WHITE};letter-spacing:-1px;">NEXT<span style="color:{RED};font-weight:300;">LETTER</span></div>
      <div style="font-size:11px;color:{GREY};opacity:0.4;margin-top:8px;letter-spacing:1px;">
        by LOGNEXT · Equipo IT · {year}<br>
        ¿Dudas? Escríbenos o llama al +34 636 668 059
      </div>
    </div>

  </div>
</body>
</html>"""

    return html


def generate(articles: List[Dict]) -> str:
    """Función principal: genera el HTML del NextLetter."""
    content = select_and_draft(articles)
    html = build_html(content, EDITION_NUMBER)
    return html


if __name__ == "__main__":
    # Test local con artículos de ejemplo
    from scraper import fetch_articles
    print("\n📰 Obteniendo artículos...\n")
    arts = fetch_articles()
    print("\n✍️  Generando NextLetter...\n")
    html = generate(arts)
    with open("preview.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("\n✅ Preview guardado en preview.html")
