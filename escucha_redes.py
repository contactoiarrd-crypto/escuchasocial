import html
import re
import urllib.parse
import feedparser
import pandas as pd
import requests

MODISMOS_CIUDADANOS = [
    "se inundo", "agua adentro", "sin luz", "sin agua", "corte de luz",
    "no pasa el", "calle anegada", "alguien sabe", "no podemos salir",
    "se desbordo", "mucha lluvia", "tremenda tormenta", "cayo un arbol",
    "postes caidos", "no hay servicio", "pedir ayuda", "auxilio", "intransitable"
]


def limpiar_texto(raw_text):
    if not raw_text:
        return ""
    texto = re.sub(r"<[^<]+?>", "", raw_text)
    return html.unescape(texto).strip()


def es_conversacion_real(texto, ciudad, provincia):
    texto_lower = texto.lower()
    loc_limpia = ciudad.strip().lower()
    prov_limpia = provincia.strip().lower()

    menciona_lugar = (loc_limpia and loc_limpia in texto_lower) or (prov_limpia and prov_limpia in texto_lower)
    tiene_modismo = any(m in texto_lower for m in MODISMOS_CIUDADANOS)

    if loc_limpia:
        return menciona_lugar or tiene_modismo
    return tiene_modismo or len(texto.split()) > 3


def capturar_escucha_ciudadana(termino_clave, ciudad="", provincia="", limite=40):
    publicaciones = []
    
    loc_limpia = ciudad.strip()
    prov_limpia = provincia.strip()
    ubicacion_query = f'"{loc_limpia}"' if loc_limpia else (f'"{prov_limpia}"' if prov_limpia else "")

    # 1. PROXY DE REDES
    query_social = f'(site:x.com OR site:facebook.com OR site:instagram.com OR site:tiktok.com) "{termino_clave}" {ubicacion_query}'.strip()
    url_gnews_social = f"https://news.google.com/rss/search?q={urllib.parse.quote(query_social)}&hl=es-419&gl=AR&ceid=AR:es-419"
    
    try:
        feed_social = feedparser.parse(url_gnews_social)
        for entry in feed_social.entries[:limite]:
            link = entry.link.lower()
            if "x.com" in link or "twitter.com" in link:
                red = "X / Twitter 🐦"
            elif "facebook.com" in link:
                red = "Facebook 📘"
            elif "instagram.com" in link:
                red = "Instagram 📸"
            elif "tiktok.com" in link:
                red = "TikTok 🎵"
            else:
                red = "Redes Sociales 🌐"

            resumen = limpiar_texto(entry.summary if hasattr(entry, "summary") else entry.title)
            
            if es_conversacion_real(f"{entry.title} {resumen}", ciudad, provincia):
                publicaciones.append({
                    "red": red,
                    "usuario_o_titulo": entry.title,
                    "mensaje": resumen,
                    "fecha": getattr(entry, "published", "Reciente"),
                    "link": entry.link
                })
    except Exception as e:
        print(f"Error Social Proxy: {e}")

    # 2. BLUESKY
    bsky_query = f'{termino_clave} {loc_limpia}'.strip()
    try:
        url_bsky = f"https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q={urllib.parse.quote(bsky_query)}&limit=20"
        resp = requests.get(url_bsky, timeout=4)
        if resp.status_code == 200:
            posts = resp.json().get("posts", [])
            for p in posts:
                handle = p.get("author", {}).get("handle", "usuario")
                texto = p.get("record", {}).get("text", "")
                post_id = p.get("uri", "").split("/")[-1]

                if es_conversacion_real(texto, ciudad, provincia):
                    publicaciones.append({
                        "red": "Bluesky 🦋",
                        "usuario_o_titulo": f"@{handle}",
                        "mensaje": texto,
                        "fecha": p.get("record", {}).get("createdAt", "Reciente")[:19].replace("T", " "),
                        "link": f"https://bsky.app/profile/{handle}/post/{post_id}"
                    })
    except Exception as e:
        print(f"Error Bluesky: {e}")

    # 3. MASTODON
    try:
        url_masto = f"https://mastodon.social/api/v2/search?q={urllib.parse.quote(bsky_query)}&type=statuses&limit=15"
        resp = requests.get(url_masto, timeout=4)
        if resp.status_code == 200:
            for st in resp.json().get("statuses", []):
                contenido = limpiar_texto(st.get("content", ""))
                acct = st.get("account", {}).get("acct", "usuario")

                if es_conversacion_real(contenido, ciudad, provincia):
                    publicaciones.append({
                        "red": "Mastodon 🐘",
                        "usuario_o_titulo": f"@{acct}",
                        "mensaje": contenido,
                        "fecha": st.get("created_at", "Reciente")[:10],
                        "link": st.get("url", "")
                    })
    except Exception as e:
        print(f"Error Mastodon: {e}")

    df = pd.DataFrame(publicaciones)
    if not df.empty:
        df = df.drop_duplicates(subset=["mensaje"]).reset_index(drop=True)
    return df