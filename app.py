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
    "Sistema de Monitoreo en Tiempo Real, Clasificación Operativa y Alerta Temprana para la Gestión Integral del Riesgo de Desastres (GRD)"
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
    keywords_default = "inundacion OR crecida OR lluvias OR evacuados OR arroyo OR anegamiento OR granizo"
elif "Incendios" in tipo_riesgo:
    keywords_default = "incendio OR foco igneo OR humo OR brigadistas OR fuego OR quema"
elif "Geológico" in tipo_riesgo:
    keywords_default = "terremoto OR sismo OR temblor OR erupcion OR volcan OR deslizamiento OR alud"
elif "Tecnológico" in tipo_riesgo:
    keywords_default = "derrame OR explosion OR colapso OR corte de suministro OR fuga"
else:
    keywords_default = "emergencia OR alerta OR evacuados"

busqueda_kw = st.sidebar.text_input(
    "🔍 Términos de búsqueda (modificables)", value=keywords_default
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 2. Filtros Geográficos y Temporales")

paises_disponibles = [
    "Argentina",
    "Chile",
    "Uruguay",
    "Paraguay",
    "Brasil",
    "Bolivia",
    "Perú",
    "Colombia",
    "México",
    "Toda América Latina",
]

pais_seleccionado = st.sidebar.selectbox(
    "🌎 País de Cobertura", options=paises_disponibles, index=0
)

provincia_o_zona = st.sidebar.text_input(
    "📍 Provincia, Región o Estado",
    placeholder="Ej: Buenos Aires, Cordillera, Guayas, Santa Fe",
)

localidad_especifica = st.sidebar.text_input(
    "🏡 Municipio, Ciudad o Localidad Específica",
    placeholder="Ej: General Villegas, La Plata, Bariloche, Guayaquil",
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
    min_value=10,
    max_value=100,
    value=30,
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
    # Construcción concisa de la ubicación
    partes_ubicacion = [p for p in [localidad_especifica, provincia_o_zona] if p.strip()]
    ubicacion_query = " ".join(partes_ubicacion).strip()

    with st.spinner(
        f"Rastreando eventos en '{ubicacion_query if ubicacion_query else pais_seleccionado}' ({rango_tiempo})..."
    ):
        df_noticias = obtener_noticias_y_redes(
            kw_riesgo=busqueda_kw,
            localidad=ubicacion_query,
            pais_o_region=pais_seleccionado,
            rango_tiempo=rango_tiempo,
        )

        if not df_noticias.empty:
            st.session_state["datos_procesados"] = df_noticias.head(cantidad_maxima)
            st.success("¡Captura multirriesgo, escucha social y clasificación completada!")
        else:
            st.session_state["datos_procesados"] = pd.DataFrame()
            st.warning(
                f"No se encontraron publicaciones recientes para esa combinación en ({rango_tiempo}). "
                "Probá ampliando el rango de tiempo o probando términos más generales."
            )

# ==========================================
# DASHBOARD DE RESULTADOS MULTIRRIESGO
# ==========================================
df = st.session_state["datos_procesados"]

if df is not None and not df.empty:
    st.markdown("---")

    # Alerta visual de pico de actividad / volumen
    if len(df) >= 25:
        st.error(
            "⚠️ **ALERTA DE VOLUMEN ELEVADO:** Se ha detectado un pico inusual de publicaciones y actividad en tiempo real. "
            "Verificá la pestaña de 'Categorías Operativas' para priorizar respuestas de emergencia."
        )

    # Separar prensa y redes
    es_red = df["fuente"].str.contains(
        "Redes|Reddit|Bluesky|Mastodon|Twitter|Instagram|Facebook|TikTok|Telegram",
        case=False,
        na=False,
    )
    df_redes = df[es_red]
    df_prensa = df[~es_red]

    # Métricas principales
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Publicaciones", len(df))
    m2.metric("Redes Sociales 📱", len(df_redes))
    m3.metric("Prensa y Medios 📰", len(df_prensa))
    
    solicitudes_auxilio = len(df[df["categoria"].str.contains("Auxilio", case=False, na=False)])
    m4.metric("🔴 Auxilio / Urgencias", solicitudes_auxilio)

    st.markdown("---")

    # Filtros Operativos Rápidos en la vista principal
    st.subheader("🔍 Filtrar por Categoría Operativa del COE")
    categorias_disponibles = ["Todas"] + list(df["categoria"].unique())
    cat_seleccionada = st.selectbox("Seleccioná un eje operativo:", categorias_disponibles, index=0)

    df_filtrado = df if cat_seleccionada == "Todas" else df[df["categoria"] == cat_seleccionada]

    st.markdown("---")

    # Organización en Pestañas (Tabs)
    tab_todos, tab_redes, tab_prensa, tab_categorias, tab_exportar = st.tabs([
        "🌐 Flujo Unificado",
        "📱 Solo Redes Sociales",
        "📰 Solo Prensa / Medios",
        "🏷️ Categorías Operativas",
        "📥 Reporte COE / Exportar",
    ])

    def render_publicaciones(dataframe):
        if dataframe.empty:
            st.info("No hay publicaciones disponibles para esta categoría o filtro.")
            return

        for idx, row in dataframe.iterrows():
            es_red_item = "Redes" in row["fuente"] or any(
                x in row["fuente"]
                for x in ["Reddit", "Bluesky", "Mastodon", "Twitter", "Instagram", "Facebook", "TikTok", "Telegram"]
            )
            icono_tipo = "📱" if es_red_item else "📰"

            with st.expander(
                f"{icono_tipo} [{row['fuente']}] [{row['categoria']}] {row['titulo']}", expanded=True
            ):
                col_info1, col_info2 = st.columns([3, 1])
                with col_info1:
                    st.markdown(f"**Origen / Canal:** `{row['fuente']}`")
                    st.markdown(f"**Categoría Operativa:** `{row['categoria']}`")
                    st.markdown(f"**Fecha / Hora:** `{row['fecha']}`")
                with col_info2:
                    st.markdown(f"🔗 [Ver Publicación Original]({row['link']})")

                if row["resumen"] and row["resumen"] != row["titulo"]:
                    st.info(f"**Extracto / Texto:** {row['resumen']}")

    with tab_todos:
        col_izq, col_der = st.columns([2, 1])
        with col_izq:
            st.subheader(f"📋 Flujo Unificado ({len(df_filtrado)} reportes)")
            render_publicaciones(df_filtrado)
        with col_der:
            st.subheader("📡 Distribución por Fuente")
            st.bar_chart(df["fuente"].value_counts())
            
            st.subheader("📊 Distribución por Categoría")
            st.bar_chart(df["categoria"].value_counts())

    with tab_redes:
        st.subheader("📱 Publicaciones Detectadas en Redes Sociales")
        df_redes_filt = df_redes if cat_seleccionada == "Todas" else df_redes[df_redes["categoria"] == cat_seleccionada]
        render_publicaciones(df_redes_filt)

    with tab_prensa:
        st.subheader("📰 Noticias y Cobertura en Medios Digitales")
        df_prensa_filt = df_prensa if cat_seleccionada == "Todas" else df_prensa[df_prensa["categoria"] == cat_seleccionada]
        render_publicaciones(df_prensa_filt)

    with tab_categorias:
        st.subheader("🏷️ Clasificación para la Toma de Decisiones Tácticas")
        st.write("Agrupación automática según el contenido del mensaje:")
        
        for cat in df["categoria"].unique():
            df_cat = df[df["categoria"] == cat]
            with st.expander(f"📌 {cat} ({len(df_cat)} reportes)", expanded=(cat.startswith("🔴"))):
                render_publicaciones(df_cat)

    with tab_exportar:
        st.subheader("📥 Exportación de Reporte de Inteligencia para el COE")
        st.write("Descargá la base consolidada en formato CSV para incluir en informes de situación (SITREP) o boletines oficiales.")

        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📄 Descargar Reporte Consolidado (CSV)",
            data=csv_data,
            file_name=f"reporte_escucha_social_{rango_tiempo}.csv",
            mime="text/csv",
        )

elif df is not None and df.empty:
    st.info(
        "💡 No hubo coincidencias exactas para esa combinación. Podés probar "
        "ampliando el rango de tiempo o los términos de búsqueda."
    )
else:
    st.info(
        "👈 Seleccioná el **Tipo de Riesgo, Ubicación y Rango de Tiempo** en el "
        "menú de la izquierda y presioná **'🚀 Iniciar Captura en Tiempo Real'**."
    )