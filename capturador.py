import html
import re
import urllib.parse
import feedparser
import pandas as pd

# Categorías operativas para la Gestión Integral del Riesgo de Desastres (GRD) - IIARRD
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
    """Clasifica el texto en una categoría operativa de riesgo según palabras clave."""
    texto_lower = texto.lower()
    for cat, kw_list in CATEGORIAS_RIESGO.items():
        if any(kw in texto_lower for kw in kw_list):
            return cat
    return "⚪ Cobertura Periodística General"


def limpiar_html(raw_html):
    """Limpia etiquetas HTML y entidades codificadas (&quot;, &amp;, etc.)."""
    if not raw_html:
        return ""
    texto = re.sub(r"<[^<]+?>", "", raw_html)
    return html.unescape(texto).strip()


def obtener_noticias_prensa(kw_riesgo, localidad="", provincia="", pais_o_region="Argentina", rango_tiempo="1d"):
    """Motor dedicado EXCLUSIVAMENTE a Medios Digitales, Prensa e Información Institucional."""
    noticias = []

    tiempo_map = {"1h": "when:1h", "1d": "when:1d", "7d": "when:7d", "30d": "when:30d"}
    time_filter = tiempo_map.get(rango_tiempo, "when:1d")

    config_geo = MAPEO_PAIS_GOOGLE.get(pais_o_region, {"gl": "AR", "ceid": "AR:es-419"})
    
    # Construir filtro geográfico para medios
    partes_geo = [p.strip() for p in [localidad, provincia] if p.strip()]
    loc_query = ' AND '.join([f'"{p}"' for p in partes_geo])

    if loc_query:
        query_google = f"({kw_riesgo}) AND {loc_query}"
    else:
        geo_pais = f'"{pais_o_region}"' if pais_o_region != "Toda América Latina" else ""
        query_google = f"({kw_riesgo}) AND {geo_pais}" if geo_pais else f"({kw_riesgo})"

    # Captura vía Google News RSS
    url_news = (
        f"https://news.google.com/rss/search?q={urllib.parse.quote(query_google)}+{time_filter}"
        f"&hl=es-419&gl={config_geo['gl']}&ceid={config_geo['ceid']}"
    )
    
    try:
        feed_main = feedparser.parse(url_news)
        for entry in feed_main.entries:
            fuente_nombre = entry.source.title if hasattr(entry, "source") else "Medio Digital"
            resumen_texto = limpiar_html(entry.summary if hasattr(entry, "summary") else entry.title)

            noticias.append({
                "titulo": entry.title,
                "resumen": resumen_texto,
                "link": entry.link,
                "fecha": getattr(entry, "published", "Reciente"),
                "fuente": f"Prensa ({fuente_nombre})",
                "categoria": clasificar_texto(f"{entry.title} {resumen_texto}"),
            })
    except Exception as e:
        print(f"Error cargando prensa en Google News: {e}")

    df = pd.DataFrame(noticias)
    if not df.empty:
        df = df.drop_duplicates(subset=["titulo"]).reset_index(drop=True)

    return df