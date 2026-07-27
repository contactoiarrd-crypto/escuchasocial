import urllib.parse
import feedparser
import pandas as pd


def obtener_noticias_y_redes(query, rango_tiempo="1d"):
  """Captura noticias y publicaciones abiertas en redes desde fuentes RSS públicas en español."""
  query_encoded = urllib.parse.quote(query)

  # Mapeo de tiempo para Google News RSS
  tiempo_map = {"1d": "when:1d", "7d": "when:7d", "30d": "when:30d"}
  time_filter = tiempo_map.get(rango_tiempo, "when:1d")

  # Feed de Google News filtrado en español para América Latina
  url_news = f"https://news.google.com/rss/search?q={query_encoded}+{time_filter}&hl=es-419&gl=US&ceid=US:es"

  feed = feedparser.parse(url_news)
  noticias = []

  for entry in feed.entries:
    # Identificar si proviene de redes o prensa tradicional
    fuente_nombre = (
        entry.source.title if hasattr(entry, "source") else "Medio Digital"
    )

    if any(
        red in entry.link.lower()
        for red in ["x.com", "twitter.com", "facebook.com", "instagram.com"]
    ):
      fuente_tipo = "Redes Sociales (X / Prensa)"
    else:
      fuente_tipo = f"Prensa ({fuente_nombre})"

    noticias.append({
        "titulo": entry.title,
        "resumen": (
            entry.summary if hasattr(entry, "summary") else entry.title
        ),
        "link": entry.link,
        "fecha": entry.published,
        "fuente": fuente_tipo,
    })

  return pd.DataFrame(noticias)