"""
main.py — NextLetter
Orquestador principal. Ejecutado mensualmente por GitHub Actions.
"""

import os
import sys
from datetime import datetime

from scraper import fetch_articles, validate_freshness
from generator import generate
from mailer import send_draft


def run():
    print("\n" + "="*55)
    print(f"  🚀 NEXTLETTER — Generación automática")
    print(f"  📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*55 + "\n")

    # Protección: nunca sobreescribir una edición ya publicada
    edition = os.environ.get("EDITION_NUMBER", "01")
    output_path = f"{edition}/index.html"
    if os.path.exists(output_path):
        raise FileExistsError(
            f"❌ ERROR: {output_path} ya existe. No se sobreescribe una edición publicada.\n"
            f"   Si quieres regenerar la edición {edition}, elimina {output_path} manualmente primero."
        )

    # 1. Scraping de fuentes
    print("📡 PASO 1: Recopilando noticias del mes...\n")
    articles = fetch_articles(max_per_source=8)

    if not articles:
        print("❌ No se encontraron artículos. Abortando.")
        sys.exit(1)

    # Validar frescura y cobertura antes de llamar a la API
    freshness = validate_freshness(articles)

    # 2. Generar el NextLetter con Claude (+ verificación editorial automática)
    print("\n✍️  PASO 2: Generando NextLetter con Claude API...\n")
    web_html, content = generate(articles, warnings=freshness["warnings"])

    # 3. Guardar HTML — index.html para GitHub Pages
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(web_html)
    print(f"\n  💾 HTML guardado como index.html")

    # 4. Enviar borrador al revisor (email compatible con Outlook/Gmail)
    print("\n📧 PASO 3: Enviando borrador para revisión...\n")
    success = send_draft(content)

    if success:
        print("\n" + "="*55)
        print("  ✅ PROCESO COMPLETADO")
        print(f"  El borrador está en tu bandeja de entrada.")
        print(f"  Revísalo y envíalo cuando estés listo.")
        print("="*55 + "\n")
    else:
        print("\n❌ Error en el envío. Revisa los logs.")
        sys.exit(1)


if __name__ == "__main__":
    run()
