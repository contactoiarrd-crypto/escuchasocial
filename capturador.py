import re
import urllib.parse
import feedparser
import pandas as pd


def obtener_noticias_y_redes(query, rango_tiempo="1d"):
  """Captura publicaciones de prensa y redes sociales (Instagram, X, Facebook, Threads, etc.) en tiempo real."""
  query_encoded = urllib.parse.quote(query)

  tiempo_map = {
      "1h": "when:1h",
      "1d": "when:1d",
      "7d": "when:7d",
      "30d": "when:30d",
  }
  time_filter = tiempo_map.get(rango_tiempo, "when:1d")

  url_news = f"https://news.google.com/rss/search?q={query_encoded}+{time_filter}&hl=es-419&gl=AR&ceid=AR:es"

  feed = feedparser.parse(url_news)
  noticias = []

  for entry in feed.entries:
    fuente_nombre = (
        entry.source.title if hasattr(entry, "source") else "Medio Digital"
    )
    link_lower = entry.link.lower()

    # Identificación detallada de Redes Sociales
    if "instagram.com" in link_lower:
      fuente_tipo = f"Redes - Instagram 📸 ({fuente_nombre})"
    elif "threads.net" in link_lower:
      fuente_tipo = f"Redes - Threads 🧵 ({fuente_nombre})"
    elif "x.com" in link_lower or "twitter.com" in link_lower:
      fuente_tipo = f"Redes - X / Twitter 🐦 ({fuente_nombre})"
    elif "facebook.com" in link_lower:
      fuente_tipo = f"Redes - Facebook 📘 ({fuente_nombre})"
    elif "youtube.com" in link_lower or "youtu.be" in link_lower:
      fuente_tipo = f"Redes - YouTube 🔴 ({fuente_nombre})"
    elif "tiktok.com" in link_lower:
      fuente_tipo = f"Redes - TikTok 🎵 ({fuente_nombre})"
    elif "t.me" in link_lower or "telegram" in link_lower:
      fuente_tipo = f"Redes - Telegram ✈️ ({fuente_nombre})"
    elif "instagram" in entry.title.lower():
      fuente_tipo = f"Redes - Instagram 📸 ({fuente_nombre})"
    else:
      fuente_tipo = f"Prensa ({fuente_nombre})"

    resumen_texto = entry.summary if hasattr(entry, "summary") else entry.title
    if "<" in resumen_texto and ">" in resumen_texto:
      resumen_texto = re.sub("<[^<]+?>", "", resumen_texto)

    noticias.append({
        "titulo": entry.title,
        "resumen": resumen_texto,
        "link": entry.link,
        "fecha": entry.published,
        "fuente": fuente_tipo,
    })

  return pd.DataFrame(noticias)