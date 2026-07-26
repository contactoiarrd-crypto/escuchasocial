import urllib.parse
import pandas as pd
import streamlit as st
from analizador_ia import analizar_incidente
from capturador import obtener_noticias_y_redes

st.set_page_config(
    page_title="Monitor de Escucha Activa - Riesgo Hídrico",
    page_icon="🌊",
    layout="wide",
)

st.title("🌊 Monitor Institucional de Escucha Social y Medios")
st.caption(
    "Sistema de Alerta Temprana y Clasificación Asistida por IA para Gestión"
    " del Riesgo Hídrico"
)

# ==========================================
# BARRA LATERAL: CONFIGURACIÓN Y VARIABLES
# ==========================================
st.sidebar.header("⚙️ Configuración del Monitoreo")

# Key / Credenciales
user_api_key = st.sidebar.text_input(
    "🔑 Ingresá tu OpenAI API Key", type="password", help="Tu clave sk-..."
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Filtros de Búsqueda")

# Variable 1: Listado completo de Provincias de Argentina
provincias_argentina = [
    "Buenos Aires",
    "Ciudad Autónoma de Buenos Aires (CABA)",
    "Catamarca",
    "Chaco",
    "Chubut",
    "Córdoba",
    "Corrientes",
    "Entre Ríos",
    "Formosa",
    "Jujuy",
    "La Pampa",
    "La Rioja",
    "Mendoza",
    "Misiones",
    "Neuquén",
    "Río Negro",
    "Salta",
    "San Juan",
    "San Luis",
    "Santa Cruz",
    "Santa Fe",
    "Santiago del Estero",
    "Tierra del Fuego",
    "Tucumán",
    "Toda Argentina",
]

provincia_seleccionada = st.sidebar.selectbox(
    "📍 1. Seleccioná la Provincia / Región",
    options=provincias_argentina,
    index=0,
)

# Campo de texto opcional para especificar Municipio o Cuenca
localidad_especifica = st.sidebar.text_input(
    "🏡 Municipio, Cuenca o Arroyo (Opcional)",
    placeholder="Ej: General Villegas, Cuenca Salado, Arroyo El Gato",
)

# Variable 2: Rango Temporal
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

# Variable 3: Términos meteorológicos y de evento ampliados
busqueda_kw = st.sidebar.text_input(
    "🔍 3. Eventos / Términos de búsqueda",
    "inundacion OR crecida OR lluvias OR tormentas OR granizo OR arroyo",
)

st.sidebar.markdown("---")
ejecutar = st.sidebar.button("🚀 Iniciar Captura y Análisis")

# Estado de la sesión
if "datos_procesados" not in st.session_state:
  st.session_state["datos_procesados"] = None

# ==========================================
# EJECUCIÓN DEL MONITOREO
# ==========================================
if ejecutar:
  if not user_api_key:
    st.error(
        "⚠️ Por favor, ingresá tu OpenAI API Key en la barra lateral para poder"
        " realizar el análisis."
    )
  else:
    # Construcción de la ubicación precisa
    region_texto = (
        ""
        if provincia_seleccionada == "Toda Argentina"
        else provincia_seleccionada
    )
    ubicacion_completa = f"{localidad_especifica} {region_texto}".strip()

    with st.spinner(
        f"Rastreando reportes en '{ubicacion_completa}' ({rango_tiempo}) y"
        " procesando con IA..."
    ):
      query_completa = f"{busqueda_kw} {ubicacion_completa}"

      # Captura de datos
      df_noticias = obtener_noticias_y_redes(
          query_completa, rango_tiempo=rango_tiempo
      )

      if not df_noticias.empty:
        df_subset = df_noticias.head(8).copy()
        resultados_ia = []

        for index, row in df_subset.iterrows():
          analisis = analizar_incidente(
              f"{row['titulo']} - {row['resumen']}", user_api_key
          )
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
            f"No se encontraron publicaciones recientes en"
            f" '{ubicacion_completa}' para el rango ({rango_tiempo}). Probá"
            " cambiando los términos o el rango temporal."
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

      # Key única asignada para evitar bugs de React en pantalla
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
    st.bar_chart(df["categoria"].value_counts())

    st.subheader("📡 Origen de los Datos")
    st.bar_chart(df["fuente"].value_counts())

else:
  st.info(
      "👈 Configurá la **Provincia, Municipio y Eventos** a la izquierda,"
      " ingresá tu API Key y presioná **'🚀 Iniciar Captura y Análisis'**."
  )