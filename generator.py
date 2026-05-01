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

# Palabras que destrozan el tono de NextLetter
FORBIDDEN_WORDS = [
    "disruptivo", "disrupción", "ecosistema", "sinergia",
    "innovador", "innovación", "paradigma", "disruptive"
]


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

    # Contexto de alerta editorial si el scraping fue débil
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
• reto.texto: MÁXIMO 2 frases (la acción + el tiempo estimado).
• esto_paso.texto: DEBE incluir al menos 1 dato numérico o porcentaje.
• Palabras PROHIBIDAS (reescribe si aparecen): {', '.join(FORBIDDEN_WORDS)}
• URLs: siempre de los artículos proporcionados. NUNCA inventadas.
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

4. RETO: Acción concreta que proponemos este mes. Sencilla, medible.
   Máx 2 frases: la acción + el tiempo estimado.

5. RADAR: 4 titulares relevantes de fuentes distintas. Breve y directo.
   Incluir org (nombre corto de la fuente) y fecha.

6. IA_DIA: Tendencia IA del mes más relevante para empresas IT españolas.
   4-5 líneas. Con perspectiva editorial, no solo descripción. URL.

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
    "radar": "Elegí estos 4 porque...",
    "ia_dia": "Elegí [título] porque..."
  }},
  "intro": "...",
  "esto_paso": {{"titulo": "...", "texto": "...", "url": "..."}},
  "caso_real": {{"titulo": "...", "texto": "...", "url": "..."}},
  "consejo": {{"titulo": "...", "texto": "..."}},
  "reto": {{"titulo": "...", "texto": "..."}},
  "radar": [
    {{"titulo": "...", "org": "...", "url": "...", "fecha": "..."}},
    {{"titulo": "...", "org": "...", "url": "...", "fecha": "..."}},
    {{"titulo": "...", "org": "...", "url": "...", "fecha": "..."}},
    {{"titulo": "...", "org": "...", "url": "...", "fecha": "..."}}
  ],
  "ia_dia": {{"titulo": "...", "texto": "...", "url": "..."}},
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

    # Mostrar razonamiento editorial en logs
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

    # Subject line del CLAUDE.md: máx 45 caracteres
    subject = f"NextLetter #{edition} — {mes}"
    if len(subject) > 45:
        issues.append(f"Subject demasiado largo: {len(subject)} chars (máx 45)")

    # esto_paso debe tener dato numérico
    texto_esto = content.get("esto_paso", {}).get("texto", "")
    if not any(c.isdigit() for c in texto_esto):
        issues.append("esto_paso sin dato numérico — añadir cifra de impacto")

    # URLs válidas en secciones dinámicas clave
    for seccion in ["esto_paso", "caso_real", "ia_dia"]:
        url = content.get(seccion, {}).get("url", "")
        if not url.startswith("http"):
            issues.append(f"{seccion} sin URL válida (tiene: '{url}')")

    # Radar: exactamente 4 ítems
    radar = content.get("radar", [])
    if len(radar) != 4:
        issues.append(f"Radar con {len(radar)} ítems — necesita exactamente 4")

    # Palabras prohibidas en cualquier campo de texto
    all_text = json.dumps(content, ensure_ascii=False).lower()
    found = [w for w in FORBIDDEN_WORDS if w in all_text]
    if found:
        issues.append(f"Palabras prohibidas encontradas: {', '.join(found)}")

    # consejo: máx 3 frases
    consejo_text = content.get("consejo", {}).get("texto", "")
    frases = [f for f in re.split(r'[.!?]', consejo_text) if f.strip()]
    if len(frases) > 3:
        issues.append(f"consejo.texto con {len(frases)} frases — máx 3")

    # reto: máx 2 frases
    reto_text = content.get("reto", {}).get("texto", "")
    frases_reto = [f for f in re.split(r'[.!?]', reto_text) if f.strip()]
    if len(frases_reto) > 2:
        issues.append(f"reto.texto con {len(frases_reto)} frases — máx 2")

    # enlaces: exactamente 3
    enlaces = content.get("enlaces", [])
    if len(enlaces) != 3:
        issues.append(f"enlaces con {len(enlaces)} ítems — necesita exactamente 3")

    return issues


def build_html(content: Dict, edition: str) -> str:
    """Monta el HTML del correo con el branding oficial de LOGNEXT."""
    mes = datetime.now().strftime("%B %Y").capitalize()
    year = datetime.now().year

    # ── Radar HTML ──
    radar_colors = [RED, YELLOW, CYAN, VIOLET]
    radar_html = ""
    for i, item in enumerate(content.get("radar", [])):
        color = radar_colors[i % len(radar_colors)]
        radar_html += f"""
        <tr>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
              <span style="width:6px;height:6px;border-radius:50%;background:{color};display:inline-block;flex-shrink:0;"></span>
              <span style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;opacity:0.6;color:{GREY};">{item.get('org', '')}</span>
            </div>
            <a href="{item.get('url', '#')}" style="color:{WHITE};font-size:13px;font-weight:600;text-decoration:none;line-height:1.4;display:block;margin-bottom:3px;">{item.get('titulo', '')}</a>
            <div style="font-size:10px;opacity:0.35;color:{GREY};">{item.get('fecha', '')}</div>
          </td>
        </tr>"""

    # ── Enlaces HTML (3 recursos tipo artículo / vídeo / quiz) ──
    tipo_icons  = {"articulo": "📰", "video": "▶️", "quiz": "🎮"}
    tipo_labels = {"articulo": "ARTÍCULO", "video": "VÍDEO", "quiz": "QUIZ INTERACTIVO"}
    tipo_colors = {"articulo": RED, "video": CYAN, "quiz": YELLOW}
    enlaces_html = ""
    for e in content.get("enlaces", []):
        tipo  = e.get("tipo", "articulo")
        icon  = tipo_icons.get(tipo, "🔗")
        label = tipo_labels.get(tipo, "ENLACE")
        color = tipo_colors.get(tipo, CYAN)
        enlaces_html += f"""
        <tr>
          <td style="padding:16px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);vertical-align:top;width:33%;">
            <div style="font-size:24px;margin-bottom:8px;">{icon}</div>
            <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;opacity:0.4;margin-bottom:6px;color:{GREY};">{label}</div>
            <a href="{e.get('url', '#')}" style="color:{WHITE};font-size:13px;font-weight:600;text-decoration:none;line-height:1.4;display:block;margin-bottom:8px;">{e.get('titulo', '')}</a>
            <div style="color:{GREY};font-size:12px;opacity:0.55;margin-bottom:8px;">{e.get('descripcion', '')}</div>
            <div style="font-size:10px;opacity:0.35;color:{GREY};">{e.get('fuente', '')}</div>
          </td>
          <td style="width:4px;"></td>"""
    # Cerrar última fila correctamente
    enlaces_html = f"<tr>{enlaces_html}</tr>"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<title>NextLetter #{edition}</title>
</head>
<body style="margin:0;padding:0;background:#080820;font-family:'Space Grotesk',Arial,sans-serif;">

  <div style="max-width:680px;margin:0 auto;padding:32px 16px;">

    <!-- CABECERA -->
    <div style="background:{NAVY};border-top:5px solid {RED};padding:32px 40px 24px;margin-bottom:4px;">
      <div>
        <span style="font-size:52px;font-weight:700;color:{WHITE};letter-spacing:-2px;line-height:1;">NEXT</span><span style="font-size:52px;font-weight:300;color:{RED};letter-spacing:-2px;line-height:1;">LETTER</span>
      </div>
      <div style="border-top:1px solid rgba(255,255,255,0.1);margin-top:12px;padding-top:10px;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:11px;color:{GREY};letter-spacing:2px;text-transform:uppercase;opacity:0.6;">La carta de los que van un paso por delante</span>
        <span style="font-size:11px;color:{RED};font-weight:600;letter-spacing:2px;">#{edition} · {mes}</span>
      </div>
    </div>

    <!-- INTRO -->
    <div style="background:{NAVY};padding:24px 40px;border-top:1px solid rgba(255,255,255,0.06);margin-bottom:4px;">
      <p style="color:{GREY};font-size:15px;line-height:1.7;margin:0;">{content.get('intro', '')}</p>
    </div>

    <!-- SEPARADOR -->
    <div style="height:4px;background:linear-gradient(90deg,{RED} 0%,{RED} 33%,{CYAN} 33%,{CYAN} 66%,{YELLOW} 66%);margin-bottom:4px;"></div>

    <!-- ESTO PASÓ -->
    <div style="background:{NAVY};padding:28px 40px;margin-bottom:4px;box-shadow:inset 0 1px 0 rgba(250,60,15,0.3);">
      <div style="font-size:10px;color:{RED};letter-spacing:4px;text-transform:uppercase;font-weight:600;margin-bottom:10px;">🗞️ ESTO PASÓ</div>
      <div style="font-size:20px;font-weight:700;color:{WHITE};margin-bottom:12px;line-height:1.3;">{content.get('esto_paso', {{}}).get('titulo', '')}</div>
      <p style="color:{GREY};font-size:14px;line-height:1.8;margin:0 0 14px;">{content.get('esto_paso', {{}}).get('texto', '')}</p>
      <a href="{content.get('esto_paso', {{}}).get('url', '#')}" style="color:{CYAN};font-size:12px;font-weight:600;text-decoration:none;padding:8px 16px;border:1px solid {CYAN};display:inline-block;">Leer la historia completa →</a>
    </div>

    <!-- CASO DEL MES -->
    <div style="background:#05051f;padding:28px 40px;margin-bottom:4px;border-left:4px solid {YELLOW};">
      <div style="font-size:10px;color:{YELLOW};letter-spacing:4px;text-transform:uppercase;font-weight:600;margin-bottom:10px;">😱 EL CASO DEL MES</div>
      <div style="font-size:20px;font-weight:700;color:{WHITE};margin-bottom:12px;line-height:1.3;">{content.get('caso_real', {{}}).get('titulo', '')}</div>
      <p style="color:{GREY};font-size:14px;line-height:1.8;margin:0 0 14px;">{content.get('caso_real', {{}}).get('texto', '')}</p>
      <a href="{content.get('caso_real', {{}}).get('url', '#')}" style="color:{YELLOW};font-size:12px;font-weight:600;text-decoration:none;padding:8px 16px;border:1px solid {YELLOW};display:inline-block;">Ver el caso completo →</a>
    </div>

    <!-- CONSEJO -->
    <div style="background:{NAVY};padding:28px 40px;margin-bottom:4px;box-shadow:inset 0 1px 0 rgba(100,240,125,0.2);">
      <div style="font-size:10px;color:{GREEN};letter-spacing:4px;text-transform:uppercase;font-weight:600;margin-bottom:10px;">💡 EL CONSEJO DEL MES</div>
      <div style="font-size:20px;font-weight:700;color:{WHITE};margin-bottom:12px;line-height:1.3;">{content.get('consejo', {{}}).get('titulo', '')}</div>
      <p style="color:{GREY};font-size:14px;line-height:1.8;margin:0;">{content.get('consejo', {{}}).get('texto', '')}</p>
    </div>

    <!-- RETO -->
    <div style="background:#001a05;padding:24px 40px;margin-bottom:4px;border:1px solid rgba(100,240,125,0.2);">
      <div style="font-size:10px;color:{GREEN};letter-spacing:4px;text-transform:uppercase;font-weight:600;margin-bottom:10px;">🎯 EL RETO DE ESTE MES</div>
      <div style="display:inline-block;background:{GREEN};color:{NAVY};font-size:10px;font-weight:700;letter-spacing:2px;padding:3px 12px;margin-bottom:12px;">RETO ACTIVO</div>
      <div style="font-size:17px;font-weight:600;color:{WHITE};margin-bottom:8px;">{content.get('reto', {{}}).get('titulo', '')}</div>
      <p style="color:{GREY};font-size:14px;line-height:1.7;margin:0;">{content.get('reto', {{}}).get('texto', '')}</p>
    </div>

    <!-- EN EL RADAR -->
    <div style="background:{NAVY};padding:28px 40px;margin-bottom:4px;box-shadow:inset 0 1px 0 rgba(60,230,230,0.2);">
      <div style="font-size:10px;color:{CYAN};letter-spacing:4px;text-transform:uppercase;font-weight:600;margin-bottom:12px;">📡 EN EL RADAR</div>
      <div style="font-size:20px;font-weight:700;color:{WHITE};margin-bottom:16px;">Lo que no puedes perderte este mes</div>
      <table style="width:100%;border-collapse:collapse;">
        {radar_html}
      </table>
    </div>

    <!-- IA AL DÍA -->
    <div style="background:#000e22;padding:28px 40px;margin-bottom:4px;border-left:4px solid {BLUE};">
      <div style="font-size:10px;color:{BLUE};letter-spacing:4px;text-transform:uppercase;font-weight:600;margin-bottom:10px;">🤖 IA AL DÍA</div>
      <div style="font-size:20px;font-weight:700;color:{WHITE};margin-bottom:12px;line-height:1.3;">{content.get('ia_dia', {{}}).get('titulo', '')}</div>
      <p style="color:{GREY};font-size:14px;line-height:1.8;margin:0 0 14px;">{content.get('ia_dia', {{}}).get('texto', '')}</p>
      <a href="{content.get('ia_dia', {{}}).get('url', '#')}" style="color:{BLUE};font-size:12px;font-weight:600;text-decoration:none;padding:8px 16px;border:1px solid {BLUE};display:inline-block;">Leer el análisis completo →</a>
    </div>

    <!-- AGUJERO / ENLACES -->
    <div style="background:{NAVY};padding:28px 40px;margin-bottom:4px;box-shadow:inset 0 1px 0 rgba(200,150,255,0.2);">
      <div style="font-size:10px;color:{VIOLET};letter-spacing:4px;text-transform:uppercase;font-weight:600;margin-bottom:16px;">🔗 POR SI QUERÉIS CAER EN EL AGUJERO</div>
      <table style="width:100%;border-collapse:collapse;">
        {enlaces_html}
      </table>
    </div>

    <!-- FOOTER -->
    <div style="background:#000015;padding:28px 40px;margin-top:4px;text-align:center;">
      <div style="font-size:22px;font-weight:700;color:{WHITE};letter-spacing:-1px;">NEXT<span style="color:{RED};font-weight:300;">LETTER</span></div>
      <div style="height:2px;width:32px;background:{RED};margin:10px auto;"></div>
      <div style="font-size:11px;color:{GREY};opacity:0.4;letter-spacing:1px;line-height:1.8;">
        by LOGNEXT · Departamento IT · {year}<br>
        ¿Dudas? <a href="mailto:sistemas@lognext.com" style="color:{GREY};opacity:0.6;">sistemas@lognext.com</a>
      </div>
    </div>

  </div>
</body>
</html>"""

    return html


def generate(articles: List[Dict], warnings: List[str] = None) -> str:
    """Función principal: genera el HTML del NextLetter."""
    content = select_and_draft(articles, warnings=warnings)

    # Verificar criterios editoriales
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
    return html


if __name__ == "__main__":
    from scraper import fetch_articles, validate_freshness
    print("\n📰 Obteniendo artículos...\n")
    arts = fetch_articles()
    freshness = validate_freshness(arts)
    print("\n✍️  Generando NextLetter...\n")
    html = generate(arts, warnings=freshness["warnings"])
    with open("preview.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("\n✅ Preview guardado en preview.html")
