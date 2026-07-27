import re
import urllib.parse
import feedparser
import pandas as pd


def obtener_noticias_y_redes(query, rango_tiempo="1d"):
  """Captura noticias generales y consulta puentes directos de redes sociales."""
  query_encoded = urllib.parse.quote(query)

  tiempo_map = {
      "1h": "when:1h",
      "1d": "when:1d",
      "7d": "when:7d",
      "30d": "when:30d",
  }
  time_filter = tiempo_map.get(rango_tiempo, "when:1d")

  # 1. FUENTE A: Medios y Web Abierta
  url_news = f"https://news.google.com/rss/search?q={query_encoded}+{time_filter}&hl=es-419&gl=AR&ceid=AR:es"

  # 2. FUENTE B: PUENTES DIRECTOS DE REDES SOCIALES (RSSHub / Puentes Públicos)
  # Lista de puentes RSS de canales públicos de alertas y emergencias en redes
  puentes_redes = [
      # Ejemplo: Puente RSSBridge/RSSHub para canales públicos de alertas en Telegram
      "https://rsshub.app/telegram/channel/alertas_meteorologicas",
  ]

  noticias = []

  # Captura 1: Google News y Menciones Web
  feed_main = feedparser.parse(url_news)
  for entry in feed_main.entries:
    fuente_nombre = (
        entry.source.title if hasattr(entry, "source") else "Medio Digital"
    )
    link_lower = entry.link.lower()

    if "instagram.com" in link_lower or "instagram" in entry.title.lower():
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

  # Captura 2: Procesamiento del Puente Directo de Redes
  for url_puente in puentes_redes:
    try:
      feed_puente = feedparser.parse(url_puente)
      for entry in feed_puente.entries:
        # Filtrar si la publicación del puente coincide con los términos buscados
        texto_completo = f"{entry.title} {entry.summary}".lower()
        if any(
            kw.strip().lower()
            for kw in query.split("OR")
            if kw.strip().lower() in texto_completo
        ):
          resumen_texto = (
              entry.summary if hasattr(entry, "summary") else entry.title
          )
          if "<" in resumen_texto and ">" in resumen_texto:
            resumen_texto = re.sub("<[^<]+?>", "", resumen_texto)

          noticias.append({
              "titulo": f"[PUENTE DIRECTO] {entry.title}",
              "resumen": resumen_texto,
              "link": entry.link,
              "fecha": getattr(entry, "published", "Reciente"),
              "fuente": "Redes - Puente Directo 📡",
          })
    except Exception:
      continue

  return pd.DataFrame(noticias)