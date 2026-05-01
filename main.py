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
    html = generate(articles, warnings=freshness["warnings"])

    # 3. Guardar preview local
    preview_path = "nextletter_preview.html"
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  💾 Preview guardado en {preview_path}")

    # 4. Enviar borrador al revisor
    print("\n📧 PASO 3: Enviando borrador para revisión...\n")
    success = send_draft(html)

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
