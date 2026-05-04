"""
generator.py — NextLetter
Usa Claude API para seleccionar noticias y redactar el contenido de cada sección.
Rellena web_template.html con los datos generados — no genera HTML desde cero.
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
    "cybersecurity": "1550751827-4bd374c3f58b",
    "data-breach":   "1555963879-ea7c5a52a1e0",
    "hacker":        "1614064641938-3bbee52942c7",
    "network":       "1544197150-b99a580bb7be",
    "server":        "1558618742-b04c9b8c5ee5",
    "cloud":         "1451187580459-43490279c0fa",
    "code":          "1517694712202-14dd9538aa97",
    "ai":            "1676299081847-824916de030a",
    "robot":         "1485827404703-89b55fcc595e",
    "phishing":      "1526374965328-7f61d4dc18c5",
    "privacy":       "1610337673044-720471f83677",
    "energy":        "1473341304170-971dccb5ac1e",
    "business":      "1573497019236-17f8177b81e8",
    "mobile":        "1512941937669-90a1b58e7e9c",
    "spain":         "1539037116277-4db20889f2d4",
    "technology":    "1518770660439-4636190af475",
}


def _unsplash_url(keyword: str, w: int = 1200, h: int = 220) -> str:
    key = keyword.lower().split(",")[0].replace(" ", "-").strip()
    photo_id = _UNSPLASH_PHOTOS.get(key, _UNSPLASH_PHOTOS["technology"])
    return f"https://images.unsplash.com/photo-{photo_id}?auto=format&fit=crop&w={w}&h={h}&q=80"


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

AUDIENCIA: El equipo IT de LOGNEXT en España (los "Nexters"). Nivel técnico medio-alto.
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


def render_template(content: Dict, edition: str) -> str:
    """Lee web_template.html y sustituye todos los {{PLACEHOLDERS}} con el contenido generado."""
    now       = datetime.now()
    mes_upper = now.strftime("%B %Y").upper()
    year      = now.year
    month     = now.month

    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Imágenes Unsplash
    ia_img_url      = _unsplash_url(content.get("ia_dia",   {}).get("imagen", "ai"),             1200, 180)
    esto_img_url    = _unsplash_url(content.get("esto_paso", {}).get("imagen", "cybersecurity"), 1200, 220)
    caso_img_url    = _unsplash_url(content.get("caso_real", {}).get("imagen", "hacker"),         800, 160)
    consejo_img_url = _unsplash_url(content.get("consejo",  {}).get("imagen", "code"),            800, 160)

    # Radar (4 items fijos)
    radar = content.get("radar", [])
    for i in range(1, 5):
        item = radar[i - 1] if i - 1 < len(radar) else {}
        html = html.replace(f"{{{{RADAR_{i}_ORG}}}}", item.get("org", ""))
        html = html.replace(f"{{{{RADAR_{i}_TITULO}}}}", item.get("titulo", ""))
        html = html.replace(f"{{{{RADAR_{i}_URL}}}}", item.get("url", "#"))
        html = html.replace(f"{{{{RADAR_{i}_META}}}}", item.get("fecha", ""))

    # Recursos (3 items fijos: artículo, vídeo, quiz)
    enlaces = content.get("enlaces", [])
    for i in range(1, 4):
        e = enlaces[i - 1] if i - 1 < len(enlaces) else {}
        html = html.replace(f"{{{{RECURSOS_{i}_TITULO}}}}", e.get("titulo", ""))
        html = html.replace(f"{{{{RECURSOS_{i}_URL}}}}", e.get("url", "#"))
        html = html.replace(f"{{{{RECURSOS_{i}_DESC}}}}", e.get("descripcion", ""))
        html = html.replace(f"{{{{RECURSOS_{i}_FUENTE}}}}", e.get("fuente", ""))

    # Footer: lista de ediciones (actual + 2 próximas)
    edition_int = int(edition)
    now_badge = (
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

    # Sustituciones simples
    replacements = {
        "{{EDICION_NUM}}":     edition,
        "{{EDICION_MES}}":     mes_upper,
        "{{EDICION_AÑO}}":     str(year),
        "{{INTRO_TEXTO}}":     content.get("intro", ""),
        "{{IA_IMG_URL}}":      ia_img_url,
        "{{IA_TITULO}}":       content.get("ia_dia",    {}).get("titulo", ""),
        "{{IA_TEXTO}}":        content.get("ia_dia",    {}).get("texto",  ""),
        "{{IA_URL}}":          content.get("ia_dia",    {}).get("url",    "#"),
        "{{NOTICIA_IMG_URL}}": esto_img_url,
        "{{NOTICIA_TITULO}}":  content.get("esto_paso", {}).get("titulo", ""),
        "{{NOTICIA_TEXTO}}":   content.get("esto_paso", {}).get("texto",  ""),
        "{{NOTICIA_URL}}":     content.get("esto_paso", {}).get("url",    "#"),
        "{{AMENAZA_IMG_URL}}": caso_img_url,
        "{{AMENAZA_TITULO}}":  content.get("caso_real", {}).get("titulo", ""),
        "{{AMENAZA_TEXTO}}":   content.get("caso_real", {}).get("texto",  ""),
        "{{AMENAZA_URL}}":     content.get("caso_real", {}).get("url",    "#"),
        "{{CONSEJO_IMG_URL}}": consejo_img_url,
        "{{CONSEJO_TITULO}}":  content.get("consejo",   {}).get("titulo", ""),
        "{{CONSEJO_TEXTO}}":   content.get("consejo",   {}).get("texto",  ""),
        "{{RETO_TITULO}}":     content.get("reto",      {}).get("titulo", ""),
        "{{RETO_TEXTO}}":      content.get("reto",      {}).get("texto",  ""),
        "{{FOOTER_EDICIONES}}": footer_editions,
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, str(value))

    return html


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

    html = render_template(content, EDITION_NUMBER)
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
