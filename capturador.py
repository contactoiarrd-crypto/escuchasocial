import urllib.parse
import feedparser
import pandas as pd


def obtener_noticias_y_redes(query, rango_tiempo="1d"):
  """Rastrea medios de comunicación y publicaciones de redes sociales recientes.

  rango_tiempo: '1d' (últimas 24hs), '7d' (última semana), '30d' (último mes)
  """
  noticias = []

  # 1. Búsqueda en Medios Digitales (Google News con filtro de tiempo)
  query_medios = f"{query} when:{rango_tiempo}"
  query_encoded = urllib.parse.quote(query_medios)
  url_medios = f"https://news.google.com/rss/search?q={query_encoded}&hl=es-419&gl=AR&ceid=AR:es-419"

  feed_medios = feedparser.parse(url_medios)
  for entry in feed_medios.entries:
    noticias.append({
        "fuente": "Medio Digital",
        "titulo": getattr(entry, "title", "Sin título"),
        "resumen": getattr(entry, "summary", getattr(entry, "title", "")),
        "link": getattr(entry, "link", "#"),
        "fecha": getattr(entry, "published", "Reciente"),
    })

  # 2. Búsqueda en Redes Sociales (Menciones en X / Twitter y plataformas digitales)
  query_redes = f"{query} site:x.com OR site:twitter.com when:{rango_tiempo}"
  query_redes_encoded = urllib.parse.quote(query_redes)
  url_redes = f"https://news.google.com/rss/search?q={query_redes_encoded}&hl=es-419&gl=AR&ceid=AR:es-419"

  feed_redes = feedparser.parse(url_redes)
  for entry in feed_redes.entries:
    noticias.append({
        "fuente": "Redes Sociales (X / Prensa)",
        "titulo": getattr(entry, "title", "Publicación en Redes"),
        "resumen": getattr(entry, "summary", getattr(entry, "title", "")),
        "link": getattr(entry, "link", "#"),
        "fecha": getattr(entry, "published", "Reciente"),
    })

  return pd.DataFrame(noticias)