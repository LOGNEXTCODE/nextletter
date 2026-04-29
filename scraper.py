"""
scraper.py — NextLetter
Extrae noticias de ciberseguridad y tecnología desde feeds RSS oficiales.
"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict

# ─── FUENTES RSS ───────────────────────────────────────────────────────────────
SOURCES = [
    {
        "name": "INCIBE",
        "url": "https://www.incibe.es/feed",
        "category": "seguridad",
        "priority": 1,
    },
    {
        "name": "CCN-CERT",
        "url": "https://www.ccn-cert.cni.es/rss.html",
        "category": "seguridad",
        "priority": 1,
    },
    {
        "name": "El País Tecnología",
        "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/tecnologia/portada",
        "category": "tecnologia",
        "priority": 2,
    },
    {
        "name": "Xataka",
        "url": "https://www.xataka.com/index.xml",
        "category": "tecnologia",
        "priority": 2,
    },
    {
        "name": "El Mundo Tecnología",
        "url": "https://e00-elmundo.uecdn.es/elmundo/rss/tecnologia.xml",
        "category": "tecnologia",
        "priority": 2,
    },
    {
        "name": "Bleeping Computer",
        "url": "https://www.bleepingcomputer.com/feed/",
        "category": "seguridad",
        "priority": 1,
    },
]

# Cuántos días hacia atrás buscar noticias
DAYS_LOOKBACK = 35


def fetch_articles(max_per_source: int = 10) -> List[Dict]:
    """
    Descarga artículos de todas las fuentes RSS.
    Filtra por fecha (últimos DAYS_LOOKBACK días).
    Devuelve lista de artículos ordenados por fuente y fecha.
    """
    cutoff = datetime.now() - timedelta(days=DAYS_LOOKBACK)
    articles = []

    for source in SOURCES:
        print(f"  📡 Leyendo: {source['name']}...")
        try:
            feed = feedparser.parse(source["url"])
            count = 0

            for entry in feed.entries:
                if count >= max_per_source:
                    break

                # Parsear fecha
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])

                # Filtrar por fecha
                if pub_date and pub_date < cutoff:
                    continue

                # Extraer resumen limpio
                summary = ""
                if hasattr(entry, "summary"):
                    summary = entry.summary
                elif hasattr(entry, "description"):
                    summary = entry.description

                # Limpiar HTML básico del resumen
                import re
                summary = re.sub(r"<[^>]+>", "", summary).strip()
                summary = summary[:500] + "..." if len(summary) > 500 else summary

                articles.append({
                    "source": source["name"],
                    "category": source["category"],
                    "priority": source["priority"],
                    "title": entry.get("title", "Sin título"),
                    "url": entry.get("link", ""),
                    "summary": summary,
                    "date": pub_date.strftime("%d/%m/%Y") if pub_date else "Fecha desconocida",
                    "date_raw": pub_date,
                })
                count += 1

        except Exception as e:
            print(f"  ⚠️  Error en {source['name']}: {e}")
            continue

    # Ordenar: primero por prioridad, luego por fecha descendente
    articles.sort(
        key=lambda x: (x["priority"], -(x["date_raw"].timestamp() if x["date_raw"] else 0))
    )

    print(f"\n  ✅ Total artículos recopilados: {len(articles)}")
    return articles


if __name__ == "__main__":
    print("\n🔍 Iniciando scraping de fuentes...\n")
    arts = fetch_articles()
    for a in arts[:5]:
        print(f"  [{a['source']}] {a['title']} — {a['date']}")
