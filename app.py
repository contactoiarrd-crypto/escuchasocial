import urllib.parse
import pandas as pd
import streamlit as st
from analizador_ia import analizar_incidente
from capturador import obtener_noticias_y_redes

st.set_page_config(
    page_title="Monitor Interamericano de Escucha Activa - Riesgo Hídrico",
    page_icon="🌊",
    layout="wide",
)

st.title("🌊 Monitor Interamericano de Escucha Social y Medios")
st.caption(
    "Sistema de Alerta Temprana y Clasificación Asistida por IA para Gestión"
    " del Riesgo de Desastres"
)

# ==========================================
# BARRA LATERAL: CONFIGURACIÓN Y FILTROS
# ==========================================
st.sidebar.header("⚙️ Configuración del Monitoreo")
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Filtros de Búsqueda")

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
    "🌎 1. Seleccioná el País / Región", options=paises_y_regiones, index=0
)

localidad_especifica = st.sidebar.text_input(
    "🏡 Municipio, Cuenca o Arroyo (Opcional)",
    placeholder="Ej: General Villegas, Cuenca del Plata, Guayaquil",
)

rango_tiempo = st.sidebar.selectbox(
    "⏱️ 2. Rango de tiempo de la búsqueda",
    options=["1d", "7d", "30d"],
    format_func=lambda x: (
        "Últimas 24 horas"
        if x == "1d"
        else ("Últimos 7 días" if x == "7d" else "Último mes")
    ),
    index=0,
)

busqueda_kw = st.sidebar.text_input(
    "🔍 3. Eventos / Términos de búsqueda",
    "inundacion OR crecida OR lluvias OR tormentas OR granizo OR arroyo",
)

# Cantidad dinámica de reportes a procesar
cantidad_maxima = st.sidebar.slider(
    "📊 Cantidad máxima de reportes a analizar",
    min_value=5,
    max_value=30,
    value=10,
    step=5,
)

st.sidebar.markdown("---")
ejecutar = st.sidebar.button("🚀 Iniciar Captura y Análisis")

if "datos_procesados" not in st.session_state:
  st.session_state["datos_procesados"] = None

# ==========================================
# EJECUCIÓN Y ANÁLISIS
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
      f"Rastreando reportes en '{ubicacion_completa}' ({rango_tiempo}) y"
      " procesando con IA..."
  ):
    query_completa = f"({busqueda_kw}) {ubicacion_completa}"

    df_noticias = obtener_noticias_y_redes(
        query_completa, rango_tiempo=rango_tiempo
    )

    if not df_noticias.empty:
      # Aplica la cantidad dinámica seleccionada en la barra lateral
      df_subset = df_noticias.head(cantidad_maxima).copy()
      resultados_ia = []

      for index, row in df_subset.iterrows():
        analisis = analizar_incidente(f"{row['titulo']} - {row['resumen']}")
        resultados_ia.append(analisis)

      df_ia = pd.DataFrame(resultados_ia)
      df_final = pd.concat(
          [df_subset.reset_index(drop=True), df_ia.reset_index(drop=True)],
          axis=1,
      )
      st.session_state["datos_procesados"] = df_final
      st.success("¡Análisis completado con éxito!")
    else:
      st.warning(
          f"No se encontraron publicaciones recientes en '{ubicacion_completa}'"
          f" para el rango ({rango_tiempo}). Probá cambiando los términos o el"
          " rango temporal."
      )

# ==========================================
# DASHBOARD DE RESULTADOS
# ==========================================
df = st.session_state["datos_procesados"]

if df is not None and not df.empty:
  st.markdown("---")

  col1, col2, col3, col4 = st.columns(4)
  col1.metric("Reportes Procesados", len(df))
  col2.metric(
      "Alertas de Urgencia Alta 🚨",
      len(df[df["urgencia"] == "Alta"]),
      delta_color="inverse",
  )
  col3.metric(
      "Posibles Rumores ⚠️",
      len(df[df["categoria"] == "Rumor/Desinformación"]),
      delta_color="off",
  )
  col4.metric("Estado del Sistema", "Activo")

  st.markdown("---")
  col_izq, col_der = st.columns([2, 1])

  with col_izq:
    st.subheader("📋 Detalle de Reportes Analizados por la IA")
    for idx, row in df.iterrows():
      color = (
          "🔴"
          if row["urgencia"] == "Alta"
          else ("🟡" if row["urgencia"] == "Media" else "🟢")
      )
      fuente_tag = "📱 REDES" if "Redes" in row["fuente"] else "📰 MEDIO"

      with st.expander(
          f"{color} [{row['urgencia']}] [{fuente_tag}] {row['titulo']}",
          expanded=False,
      ):
        st.write(f"**Fuente:** {row['fuente']} | **Fecha:** {row['fecha']}")
        st.write(f"**Ubicación Detectada por IA:** {row['ubicacion']}")
        st.write(f"**Categoría:** {row['categoria']}")
        st.write(f"**Sentimiento:** {row['sentimiento']}")
        st.write(f"**Resumen IA:** {row['resumen_ejecutivo']}")
        st.markdown(f"[Ver publicación original]({row['link']})")

  with col_der:
    st.subheader("📊 Distribución por Categoría")
    # Filtro para omitir la etiqueta "Error de API" en la gráfica si existiera
    df_grafico = df[~df["categoria"].str.contains("Error", na=False)]
    if not df_grafico.empty:
      st.bar_chart(df_grafico["categoria"].value_counts())
    else:
      st.info("Procesando métricas...")

    st.subheader("📡 Origen de los Datos")
    st.bar_chart(df["fuente"].value_counts())

else:
  st.info(
      "👈 Ajustá los filtros de **País/Región, Tiempo y Eventos** en la barra"
      " lateral y presioná **'🚀 Iniciar Captura y Análisis'**."
  )