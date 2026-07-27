import urllib.parse
import pandas as pd
import streamlit as st
from capturador import obtener_noticias_y_redes

st.set_page_config(
    page_title="Monitor Interamericano de Escucha Activa - Riesgo de Desastres",
    page_icon="🚨",
    layout="wide",
)

st.title("🚨 Monitor Interamericano Multirriesgo y Escucha Social")
st.caption(
    "Sistema de Monitoreo en Tiempo Real y Alerta Temprana para la Gestión"
    " Integral del Riesgo de Desastres"
)

# ==========================================
# BARRA LATERAL: FILTROS MULTIRRIESGO Y GEOGRÁFICOS
# ==========================================
st.sidebar.header("⚙️ Configuración del Monitoreo")
st.sidebar.markdown("---")

# 1. Selección de Tipo de Riesgo
st.sidebar.subheader("🔥 1. Tipo de Riesgo / Evento")
tipo_riesgo = st.sidebar.selectbox(
    "Seleccioná la tipología de riesgo:",
    options=[
        "🌊 Riesgo Hídrico / Meteorológico",
        "🔥 Incendios Forestales / Pastizales",
        "🌋 Riesgo Geológico (Sismos/Volcanes/Alud)",
        "⚠️ Riesgo Tecnológico / Antrópico",
        "✏️ Personalizado (Escribir términos)",
    ],
    index=0,
)

# Mapeo automático de términos según el tipo de riesgo elegido
if "Hídrico" in tipo_riesgo:
  keywords_default = (
      "inundacion OR crecida OR lluvias OR evacuados OR arroyo OR anegamiento OR"
      " granizo"
  )
elif "Incendios" in tipo_riesgo:
  keywords_default = (
      "incendio OR foco igneo OR humo OR brigadistas OR fuego OR quema"
  )
elif "Geológico" in tipo_riesgo:
  keywords_default = (
      "terremoto OR sismo OR temblor OR erupcion OR volcan OR deslizamiento OR"
      " alud"
  )
elif "Tecnológico" in tipo_riesgo:
  keywords_default = (
      "derrame OR explosion OR colapso OR corte de suministro OR fuga"
  )
else:
  keywords_default = "emergencia OR alerta OR evacuados"

busqueda_kw = st.sidebar.text_input(
    "🔍 Términos de búsqueda (modificables)", value=keywords_default
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 2. Filtros Geográficos y Temporales")

# 2. Cobertura Geográfica Interamericana
paises_y_regiones = [
    "Argentina (Todas las provincias)",
    "Argentina - Buenos Aires",
    "Argentina - CABA",
    "Argentina - Córdoba",
    "Argentina - Santa Fe",
    "Argentina - Entre Ríos",
    "Argentina - Corrientes",
    "Argentina - Misiones",
    "Argentina - Chaco",
    "Argentina - Formosa",
    "Argentina - Salta",
    "Argentina - Jujuy",
    "Argentina - Tucumán",
    "Argentina - Catamarca",
    "Argentina - La Rioja",
    "Argentina - San Juan",
    "Argentina - Mendoza",
    "Argentina - San Luis",
    "Argentina - La Pampa",
    "Argentina - Neuquén",
    "Argentina - Río Negro",
    "Argentina - Chubut",
    "Argentina - Santa Cruz",
    "Argentina - Tierra del Fuego",
    "Bolivia",
    "Brasil",
    "Chile",
    "Colombia",
    "Costa Rica",
    "Cuba",
    "Ecuador",
    "El Salvador",
    "Guatemala",
    "Honduras",
    "México",
    "Nicaragua",
    "Panamá",
    "Paraguay",
    "Perú",
    "República Dominicana",
    "Uruguay",
    "Venezuela",
    "Toda América Latina",
]

pais_seleccionado = st.sidebar.selectbox(
    "🌎 País / Región", options=paises_y_regiones, index=0
)

localidad_especifica = st.sidebar.text_input(
    "🏡 Municipio, Zona o Localidad (Opcional)",
    placeholder="Ej: Bariloche, Cordillera, Guayaquil, San Juan",
)

# 3. Rango Temporal
rango_tiempo = st.sidebar.selectbox(
    "⏱️ Rango de tiempo",
    options=["1h", "1d", "7d", "30d"],
    format_func=lambda x: (
        "Última hora 🔥"
        if x == "1h"
        else (
            "Últimas 24 horas"
            if x == "1d"
            else ("Últimos 7 días" if x == "7d" else "Último mes")
        )
    ),
    index=1,
)

# 4. Cantidad Máxima de publicaciones
cantidad_maxima = st.sidebar.slider(
    "📊 Máximo de publicaciones a recuperar",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
)

st.sidebar.markdown("---")
ejecutar = st.sidebar.button("🚀 Iniciar Captura en Tiempo Real")

# Estado de la sesión
if "datos_procesados" not in st.session_state:
  st.session_state["datos_procesados"] = None

# ==========================================
# EJECUCIÓN DE LA CAPTURA
# ==========================================
if ejecutar:
  if pais_seleccionado == "Toda América Latina":
    geografia_query = "América Latina"
  elif "Argentina (" in pais_seleccionado:
    geografia_query = "Argentina"
  else:
    geografia_query = pais_seleccionado.replace("Argentina - ", "")

  ubicacion_completa = f"{localidad_especifica} {geografia_query}".strip()

  with st.spinner(
      f"Rastreando eventos de '{tipo_riesgo.split()[1]}' en '{ubicacion_completa}'"
      f" ({rango_tiempo})..."
  ):
    query_completa = f"({busqueda_kw}) {ubicacion_completa}"

    df_noticias = obtener_noticias_y_redes(
        query_completa, rango_tiempo=rango_tiempo
    )

    if not df_noticias.empty:
      st.session_state["datos_procesados"] = df_noticias.head(cantidad_maxima)
      st.success("¡Captura multirriesgo completada en tiempo real!")
    else:
      st.session_state["datos_procesados"] = pd.DataFrame()
      st.warning(
          f"No se encontraron publicaciones recientes en '{ubicacion_completa}'"
          f" para el rango ({rango_tiempo}). Probá ampliando los términos o el"
          " rango temporal."
      )

# ==========================================
# DASHBOARD DE RESULTADOS MULTIRRIESGO
# ==========================================
df = st.session_state["datos_procesados"]

if df is not None and not df.empty:
  st.markdown("---")

  # Métricas
  m1, m2, m3 = st.columns(3)
  m1.metric("Total Publicaciones Capturadas", len(df))
  m2.metric(
      "Publicaciones en Redes Sociales 📱",
      len(df[df["fuente"].str.contains("Redes")]),
  )
  m3.metric(
      "Reportes de Prensa / Medios 📰",
      len(df[~df["fuente"].str.contains("Redes")]),
  )

  st.markdown("---")
  col_izq, col_der = st.columns([2, 1])

  with col_izq:
    st.subheader("📋 Publicaciones y Alertas de Redes y Medios")
    for idx, row in df.iterrows():
      icono_tipo = "📱" if "Redes" in row["fuente"] else "📰"

      with st.expander(
          f"{icono_tipo} [{row['fuente']}] {row['titulo']}", expanded=True
      ):
        st.markdown(f"**Origen / Red:** `{row['fuente']}`")
        st.markdown(f"**Fecha / Hora:** `{row['fecha']}`")
        if row["resumen"] and row["resumen"] != row["titulo"]:
          st.write(f"**Extracto:** {row['resumen']}")
        st.markdown(
            f"🔗 [Ver publicación original o perfil en la red]({row['link']})"
        )

  with col_der:
    st.subheader("📡 Distribución por Origen de Fuente")
    st.bar_chart(df["fuente"].value_counts())

elif df is not None and df.empty:
  st.info(
      "💡 No hubo coincidencias exactas para esa combinación. Podés probar"
      " ampliando el rango de tiempo o los términos de búsqueda."
  )
else:
  st.info(
      "👈 Seleccioná el **Tipo de Riesgo, Ubicación y Rango de Tiempo** en el"
      " menú de la izquierda y presioná **'🚀 Iniciar Captura en Tiempo"
      " Real'**."
  )