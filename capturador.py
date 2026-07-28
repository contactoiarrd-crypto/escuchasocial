import html
import re
import urllib.parse
import feedparser
import pandas as pd
import requests

CATEGORIAS_RIESGO = {
    "🔴 Pedido de Auxilio / Evacuación": [
        "rescate", "evacua", "atrapad", "sos", "auxilio", "urgente", "pedir ayuda", 
        "techo", "aislados", "comida", "agua potable", "salvamento", "emergencia vital"
    ],
    "🟡 Infraestructura y Servicios": [
        "corte", "sin luz", "sin agua", "intransitable", "caida", "postes", "ruta", 
        "puente", "anegad", "desborde", "camino", "cable", "energia", "comunicaciones"
    ],
    "🔵 Vacío de Información / Rumor": [
        "es verdad", "dicen que", "alguien sabe", "confirmado", "fake", "rumor", 
        "compuertas", "abrieron", "van a cortar", "se sabe algo", "noticia falsa"
    ],
    "🟢 Reporte Oficial / Institucional": [
        "comunicado", "defensa civil", "boletin", "alerta meteorologico", "bomberos", 
        "municipio", "gobierno", "subsecretaria", "smn", "ina", "comite de crisis"
    ],
}

MAPEO_PAIS_GOOGLE = {
    "Argentina": {"gl": "AR", "ceid": "AR:es-419"},
    "Chile": {"gl": "CL", "ceid": "CL:es-419"},
    "Uruguay": {"gl": "UY", "ceid": "UY:es-419"},
    "Paraguay": {"gl": "PY", "ceid": "PY:es-419"},
    "Brasil": {"gl": "BR", "ceid": "BR:pt-419"},
    "Bolivia": {"gl": "BO", "ceid": "BO:es-419"},
    "Perú": {"gl": "PE", "ceid": "PE:es-419"},
    "Colombia": {"gl": "CO", "ceid": "CO:es-419"},
    "México": {"gl": "MX", "ceid": "MX:es-419"},
}


def clasificar_texto(texto):
    texto_lower = texto.lower()
    for cat, kw_list in CATEGORIAS_RIESGO.items():
        if any(kw in texto_lower for kw in kw_list):
            return cat
    return "⚪ Información General / Cobertura"


def limpiar_html(raw_html):
    if not raw_html:
        return ""
    texto = re.sub(r"<[^<]+?>", "", raw_html)
    return html.unescape(texto).strip()


def obtener_noticias_y_redes(kw_riesgo, localidad="", pais_o_region="Argentina", rango_tiempo="1d"):
    noticias = []

    tiempo_map = {"1h": "when:1h", "1d": "when:1d", "7d": "when:7d", "30d": "when:30d"}
    time_filter = tiempo_map.get(rango_tiempo, "when:1d")

    config_geo = MAPEO_PAIS_GOOGLE.get(pais_o_region, {"gl": "AR", "ceid": "AR:es-419"})
    
    loc_limpia = localidad.strip()
    if loc_limpia:
        geo_query = f'"{loc_limpia}"'
    else:
        geo_query = f'"{pais_o_region}"' if pais_o_region != "Toda América Latina" else ""

    if geo_query:
        query_google = f"({kw_riesgo}) AND {geo_query}"
    else:
        query_google = f"({kw_riesgo})"

    terminos_clave = [
        w for w in re.split(r"\s+OR\s+|\s+AND\s+|\s+", kw_riesgo, flags=re.IGNORECASE)
        if w.strip() and w.upper() not in ["OR", "AND", "NOT"]
    ]
    term_principal = terminos_clave[0] if terminos_clave else "emergencia"
    query_simple = f"{term_principal} {loc_limpia}".strip()

    # 1. Google News
    url_news = (
        f"https://news.google.com/rss/search?q={urllib.parse.quote(query_google)}+{time_filter}"
        f"&hl=es-419&gl={config_geo['gl']}&ceid={config_geo['ceid']}"
    )
    
    try:
        feed_main = feedparser.parse(url_news)
        for entry in feed_main.entries:
            fuente_nombre = entry.source.title if hasattr(entry, "source") else "Medio Digital"
            link_lower = entry.link.lower()

            if "instagram.com" in link_lower or "instagram" in entry.title.lower():
                fuente_tipo = f"Redes - Instagram 📸 ({fuente_nombre})"
            elif "x.com" in link_lower or "twitter.com" in link_lower:
                fuente_tipo = f"Redes - X / Twitter 🐦 ({fuente_nombre})"
            elif "facebook.com" in link_lower:
                fuente_tipo = f"Redes - Facebook 📘 ({fuente_nombre})"
            else:
                fuente_tipo = f"Prensa ({fuente_nombre})"

            resumen_texto = limpiar_html(entry.summary if hasattr(entry, "summary") else entry.title)

            noticias.append({
                "titulo": entry.title,
                "resumen": resumen_texto,
                "link": entry.link,
                "fecha": getattr(entry, "published", "Reciente"),
                "fuente": fuente_tipo,
                "categoria": clasificar_texto(f"{entry.title} {resumen_texto}"),
            })
    except Exception as e:
        print(f"Error Google News: {e}")

    # 2. Bluesky
    try:
        url_bsky = f"https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q={urllib.parse.quote(query_simple)}&limit=15"
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
                    "fecha": record.get("createdAt", "Reciente")[:19].replace("T", " "),
                    "fuente": "Redes - Bluesky 🦋",
                    "categoria": clasificar_texto(texto),
                })
    except Exception as e:
        print(f"Error Bluesky: {e}")

    # 3. Reddit
    try:
        url_reddit = f"https://www.reddit.com/search.rss?q={urllib.parse.quote(query_simple)}&sort=new"
        feed_reddit = feedparser.parse(
            url_reddit,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) MonitorSAT/1.0",
        )

        for entry in feed_reddit.entries[:10]:
            resumen_texto = limpiar_html(entry.summary if hasattr(entry, "summary") else entry.title)

            noticias.append({
                "titulo": f"💬 [Reddit] {entry.title}",
                "resumen": resumen_texto[:300] + "..." if len(resumen_texto) > 300 else resumen_texto,
                "link": entry.link,
                "fecha": getattr(entry, "published", "Reciente"),
                "fuente": "Redes - Reddit 💬",
                "categoria": clasificar_texto(f"{entry.title} {resumen_texto}"),
            })
    except Exception as e:
        print(f"Error Reddit: {e}")

    # 4. Mastodon
    try:
        url_masto = f"https://mastodon.social/api/v2/search?q={urllib.parse.quote(query_simple)}&type=statuses&limit=10"
        resp = requests.get(url_masto, timeout=4)
        if resp.status_code == 200:
            statuses = resp.json().get("statuses", [])
            for st in statuses:
                contenido = limpiar_html(st.get("content", ""))
                acct = st.get("account", {}).get("acct", "anon")

                noticias.append({
                    "titulo": f"🐘 [Mastodon @{acct}]: {contenido[:100]}...",
                    "resumen": contenido,
                    "link": st.get("url", ""),
                    "fecha": st.get("created_at", "Reciente")[:10],
                    "fuente": "Redes - Mastodon 🐘",
                    "categoria": clasificar_texto(contenido),
                })
    except Exception as e:
        print(f"Error Mastodon: {e}")

    df = pd.DataFrame(noticias)
    if not df.empty:
        df = df.drop_duplicates(subset=["titulo"]).reset_index(drop=True)

    return df