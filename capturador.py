import re
import urllib.parse
from datetime import datetime
import feedparser
import pandas as pd
import requests


def obtener_noticias_y_redes(query, rango_tiempo="1d", pais_o_region=""):
  """Motor de captura multicanal para el Monitor Interamericano de Escucha Activa.

  Combina:
    1. Medios Digitales y Prensa vía Google News RSS.
    2. Reddit (Búsqueda nativa vía RSS en tiempo real).
    3. Bluesky (API pública abierta sin restricciones).
    4. Proxy de Redes Sociales (X/Twitter, Instagram, Facebook, TikTok) vía
    Google Social Search.
    5. Puentes RSS Directos (Telegram/Canales de Alertas).
  """
  noticias = []

  # Mapeo de ventana de tiempo para Google News / Proxy
  tiempo_map = {
      "1h": "when:1h",
      "1d": "when:1d",
      "7d": "when:7d",
      "30d": "when:30d",
  }
  time_filter = tiempo_map.get(rango_tiempo, "when:1d")

  # Limpiar y codificar querys
  query_limpia = query.strip()
  query_encoded = urllib.parse.quote(query_limpia)

  # ---------------------------------------------------------
  # 1. PRENSA Y MEDIOS DIGITALES (Google News RSS)
  # ---------------------------------------------------------
  url_news = f"https://news.google.com/rss/search?q={query_encoded}+{time_filter}&hl=es-419&gl=AR&ceid=AR:es-419"
  try:
    feed_main = feedparser.parse(url_news)
    for entry in feed_main.entries:
      fuente_nombre = (
          entry.source.title if hasattr(entry, "source") else "Medio Digital"
      )
      link_lower = entry.link.lower()

      # Clasificación rápida si aparece alguna red social dentro del índice de Google News
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
          "fecha": getattr(entry, "published", "Reciente"),
          "fuente": fuente_tipo,
      })
  except Exception as e:
    print(f"Error cargando Google News: {e}")

  # ---------------------------------------------------------
  # 2. REDDIT (RSS Nativo en Tiempo Real)
  # ---------------------------------------------------------
  try:
    # Extraer palabras clave principales quitando operadores booleanos para Reddit
    terms_reddit = [
        w
        for w in query_limpia.split()
        if w.upper() not in ["OR", "AND", "NOT"]
    ]
    query_reddit_clean = " ".join(terms_reddit[:5])
    url_reddit = f"https://www.reddit.com/search.rss?q={urllib.parse.quote(query_reddit_clean)}&sort=new"
    feed_reddit = feedparser.parse(
        url_reddit,
        agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) MonitorSAT/1.0",
    )

    for entry in feed_reddit.entries[:10]:
      resumen_texto = entry.summary if hasattr(entry, "summary") else entry.title
      if "<" in resumen_texto and ">" in resumen_texto:
        resumen_texto = re.sub("<[^<]+?>", "", resumen_texto)

      noticias.append({
          "titulo": f"💬 [Reddit] {entry.title}",
          "resumen": (
              resumen_texto[:250] + "..."
              if len(resumen_texto) > 250
              else resumen_texto
          ),
          "link": entry.link,
          "fecha": getattr(entry, "published", "Reciente"),
          "fuente": "Redes - Reddit 💬",
      })
  except Exception as e:
    print(f"Error capturando Reddit: {e}")

  # ---------------------------------------------------------
  # 3. BLUESKY (API Pública Abierta)
  # ---------------------------------------------------------
  try:
    terms_bsky = [
        w
        for w in query_limpia.split()
        if w.upper() not in ["OR", "AND", "NOT"]
    ]
    query_bsky_clean = " ".join(terms_bsky[:5])
    url_bsky = f"https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q={urllib.parse.quote(query_bsky_clean)}&limit=10"
    resp = requests.get(url_bsky, timeout=4)
    if resp.status_code == 200:
      posts = resp.json().get("posts", [])
      for p in posts:
        author_handle = p.get("author", {}).get("handle", "anon")
        record = p.get("record", {})
        texto = record.get("text", "")
        post_id = p.get("uri", "").split("/")[-1]

        noticias.append({
            "titulo": f"🦋 [Bluesky @{author_handle}]: {texto[:100]}...",
            "resumen": texto,
            "link": f"https://bsky.app/profile/{author_handle}/post/{post_id}",
            "fecha": (
                record.get("createdAt", "Reciente")[:19].replace("T", " ")
            ),
            "fuente": "Redes - Bluesky 🦋",
        })
  except Exception as e:
    print(f"Error capturando Bluesky: {e}")

  # ---------------------------------------------------------
  # 4. PROXY DE REDES SOCIALES (Google Search `site:`)
  # ---------------------------------------------------------
  try:
    terms_social = [
        w
        for w in query_limpia.split()
        if w.upper() not in ["OR", "AND", "NOT"]
    ]
    query_social_clean = " ".join(terms_social[:6])
    query_social = f"(site:x.com OR site:twitter.com OR site:instagram.com OR site:facebook.com OR site:tiktok.com) {query_social_clean}"
    url_social_proxy = f"https://news.google.com/rss/search?q={urllib.parse.quote(query_social)}+{time_filter}&hl=es-419&gl=AR&ceid=AR:es-419"

    feed_social = feedparser.parse(url_social_proxy)
    for entry in feed_social.entries[:10]:
      link_lower = entry.link.lower()
      if "x.com" in link_lower or "twitter.com" in link_lower:
        red_nombre = "Redes - X / Twitter 🐦 (Proxy)"
      elif "instagram.com" in link_lower:
        red_nombre = "Redes - Instagram 📸 (Proxy)"
      elif "facebook.com" in link_lower:
        red_nombre = "Redes - Facebook 📘 (Proxy)"
      elif "tiktok.com" in link_lower:
        red_nombre = "Redes - TikTok 🎵 (Proxy)"
      else:
        red_nombre = "Redes - Social Proxy 🌐"

      resumen_texto = entry.summary if hasattr(entry, "summary") else entry.title
      if "<" in resumen_texto and ">" in resumen_texto:
        resumen_texto = re.sub("<[^<]+?>", "", resumen_texto)

      noticias.append({
          "titulo": entry.title,
          "resumen": resumen_texto,
          "link": entry.link,
          "fecha": getattr(entry, "published", "Reciente"),
          "fuente": red_nombre,
      })
  except Exception as e:
    print(f"Error en Proxy de Redes: {e}")

  # ---------------------------------------------------------
  # 5. PUENTES DIRECTOS RSS (Telegram / Canales Especializados)
  # ---------------------------------------------------------
  puentes_redes = [
      # Ejemplo de puente RSSHub para canales o cuentas públicas
      "https://rsshub.app/telegram/channel/alertas_meteorologicas",
  ]

  for url_puente in puentes_redes:
    try:
      feed_puente = feedparser.parse(url_puente)
      for entry in feed_puente.entries[:5]:
        texto_completo = f"{entry.title} {entry.summary}".lower()
        # Verificar coincidencia básica
        if any(
            kw.strip().lower()
            for kw in query_limpia.split("OR")
            if kw.strip().lower() in texto_completo
        ):
          resumen_texto = (
              entry.summary if hasattr(entry, "summary") else entry.title
          )
          if "<" in resumen_texto and ">" in resumen_texto:
            resumen_texto = re.sub("<[^<]+?>", "", resumen_texto)

          noticias.append({
              "titulo": f"✈️ [Telegram] {entry.title}",
              "resumen": resumen_texto,
              "link": entry.link,
              "fecha": getattr(entry, "published", "Reciente"),
              "fuente": "Redes - Telegram ✈️ (Puente Directo)",
          })
    except Exception:
      continue

  # Convertir a DataFrame y eliminar duplicados exactos por título
  df = pd.DataFrame(noticias)
  if not df.empty:
    df = df.drop_duplicates(subset=["titulo"]).reset_index(drop=True)

  return df