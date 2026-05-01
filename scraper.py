"""
scraper.py — NextLetter
Extrae noticias de ciberseguridad y tecnología desde feeds RSS oficiales.
"""

import re
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict

# ─── FUENTES RSS ───────────────────────────────────────────────────────────────
SOURCES = [
    # Prioridad alta: fuentes oficiales españolas
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
    # Medios internacionales de seguridad
    {
        "name": "The Hacker News",
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "category": "seguridad",
        "priority": 1,
    },
    {
        "name": "Bleeping Computer",
        "url": "https://www.bleepingcomputer.com/feed/",
        "category": "seguridad",
        "priority": 1,
    },
    {
        "name": "Hispasec / Una al día",
        "url": "https://unaaldia.hispasec.com/feed",
        "category": "seguridad",
        "priority": 1,
    },
    # Medios tecnológicos en español
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
]

DAYS_LOOKBACK = 35


def fetch_articles(max_per_source: int = 10) -> List[Dict]:
    """
    Descarga artículos de todas las fuentes RSS.
    Filtra por fecha (últimos DAYS_LOOKBACK días).
    Devuelve lista ordenada por prioridad y fecha descendente.
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

                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])

                if pub_date and pub_date < cutoff:
                    continue

                summary = ""
                if hasattr(entry, "summary"):
                    summary = entry.summary
                elif hasattr(entry, "description"):
                    summary = entry.description

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

    articles.sort(
        key=lambda x: (x["priority"], -(x["date_raw"].timestamp() if x["date_raw"] else 0))
    )

    print(f"\n  ✅ Total artículos recopilados: {len(articles)}")
    return articles


def validate_freshness(articles: List[Dict]) -> Dict:
    """
    Detecta escasez de contenido antes de llamar a la API.
    Devuelve warnings si hay pocos artículos frescos o de seguridad.
    El generador los pasa a Claude para que no invente cobertura.
    """
    cutoff_fresh = datetime.now() - timedelta(days=7)
    fresh = [a for a in articles if a["date_raw"] and a["date_raw"] > cutoff_fresh]
    security = [a for a in articles if a["category"] == "seguridad"]

    warnings = []
    if len(fresh) < 5:
        warnings.append(
            f"Solo {len(fresh)} artículos de los últimos 7 días — "
            f"posible caída de feeds RSS"
        )
    if len(security) < 3:
        warnings.append(
            f"Solo {len(security)} artículos de seguridad — "
            f"posible caída de INCIBE/CCN-CERT/THN"
        )
    if not articles:
        warnings.append("Sin artículos — scraping completamente fallido")

    if warnings:
        print("\n  ⚠️  ALERTAS DE COBERTURA:")
        for w in warnings:
            print(f"     • {w}")

    return {
        "warnings": warnings,
        "total": len(articles),
        "fresh_count": len(fresh),
        "security_count": len(security),
    }


if __name__ == "__main__":
    print("\n🔍 Iniciando scraping de fuentes...\n")
    arts = fetch_articles()
    stats = validate_freshness(arts)
    print(f"\n  📊 Frescos (7d): {stats['fresh_count']} | Seguridad: {stats['security_count']}")
    for a in arts[:5]:
        print(f"  [{a['source']}] {a['title']} — {a['date']}")
