import urllib.parse
import pandas as pd
import streamlit as st
from capturador import obtener_noticias_prensa
from escucha_redes import capturar_escucha_ciudadana

st.set_page_config(
    page_title="Monitor Interamericano de Escucha Activa - IIARRD",
    page_icon="🚨",
    layout="wide",
)

# Encabezado Institucional IIARRD
st.title("🚨 Monitor Interamericano Multirriesgo y Escucha Social")
st.markdown("### 🏛️ **Herramienta del Instituto Interamericano para la Reducción de Riesgo de Desastres (IIARRD)**")
st.caption(
    "Sistema de Monitoreo en Tiempo Real, Clasificación Operativa y Alerta Temprana para la Gestión Integral del Riesgo de Desastres (GRD)"
)

# ==========================================
# BARRA LATERAL: CONFIGURACIÓN GENERAL
# ==========================================
st.sidebar.title("IIARRD - Monitoreo")
st.sidebar.markdown("**Gestión del Riesgo y Escucha Activa**")
st.sidebar.markdown("---")

st.sidebar.header("⚙️ Configuración Geográfica y Riesgo")

# 1. Selección de Tipo de Riesgo
tipo_riesgo = st.sidebar.selectbox(
    "🔥 Tipología de riesgo:",
    options=[
        "🌊 Riesgo Hídrico / Meteorológico",
        "🔥 Incendios Forestales / Pastizales",
        "🌋 Riesgo Geológico (Sismos/Volcanes/Alud)",
        "⚠️ Riesgo Tecnológico / Antrópico",
        "✏️ Personalizado (Escribir términos)",
    ],
    index=0,
)

if "Hídrico" in tipo_riesgo:
    keywords_default = "inundacion OR crecida OR lluvias OR evacuados OR arroyo OR anegamiento"
elif "Incendios" in tipo_riesgo:
    keywords_default = "incendio OR foco igneo OR humo OR brigadistas OR fuego OR quema"
elif "Geológico" in tipo_riesgo:
    keywords_default = "terremoto OR sismo OR temblor OR erupcion OR volcan OR alud"
elif "Tecnológico" in tipo_riesgo:
    keywords_default = "derrame OR explosion OR colapso OR corte de suministro OR fuga"
else:
    keywords_default = "emergencia OR alerta OR evacuados"

busqueda_kw = st.sidebar.text_input("🔍 Términos clave:", value=keywords_default)

st.sidebar.markdown("---")
paises_disponibles = ["Argentina", "Chile", "Uruguay", "Paraguay", "Brasil", "Bolivia", "Perú", "Colombia", "México", "Toda América Latina"]
pais_seleccionado = st.sidebar.selectbox("🌎 País de Cobertura", options=paises_disponibles, index=0)

provincia_o_zona = st.sidebar.text_input("📍 Provincia / Estado", placeholder="Ej: Buenos Aires, Córdoba, Guayas")
localidad_especifica = st.sidebar.text_input("🏡 Municipio / Localidad", placeholder="Ej: General Villegas, Bariloche, Guayaquil")

rango_tiempo = st.sidebar.selectbox("⏱️ Rango temporal", options=["1h", "1d", "7d", "30d"], index=1)

# PESTAÑAS PRINCIPALES DEL MONITOR
tab_prensa, tab_escucha_social = st.tabs([
    "📰 Cobertura de Prensa y Medios Digitales",
    "🗣️ Escucha Social Ciudadana (Voz de la Comunidad)"
])

# ==========================================
# SECCIÓN 1: MEDIOS Y PRENSA DIGITAL
# ==========================================
with tab_prensa:
    st.subheader("📰 Cobertura en Prensa y Comunicados Oficiales")
    st.write("Filtra reportes periodísticos, alertas meteorológicas e información de medios digitales.")

    if st.button("🚀 Rastrear Medios Digitales"):
        with st.spinner("Buscando noticias e informes institucionales..."):
            df_prensa = obtener_noticias_prensa(
                kw_riesgo=busqueda_kw,
                localidad=localidad_especifica,
                provincia=provincia_o_zona,
                pais_o_region=pais_seleccionado,
                rango_tiempo=rango_tiempo
            )

            if not df_prensa.empty:
                st.success(f"Se encontraron {len(df_prensa)} reportes de medios.")
                
                # Métricas rápidas
                col1, col2 = st.columns(2)
                col1.metric("Total Noticias", len(df_prensa))
                col2.metric("Alertas / Urgencias", len(df_prensa[df_prensa['categoria'].str.contains('Auxilio', na=False)]))
                
                for idx, row in df_prensa.iterrows():
                    with st.expander(f"📰 [{row['categoria']}] {row['titulo']}", expanded=True):
                        st.markdown(f"**Medio:** `{row['fuente']}` | **Fecha:** `{row['fecha']}`")
                        st.write(row['resumen'])
                        st.markdown(f"🔗 [Leer noticia completa]({row['link']})")
                
                # Botón exportación CSV para COE
                csv = df_prensa.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Reporte de Medios (CSV)", csv, "reporte_prensa_iiarrd.csv", "text/csv")
            else:
                st.warning("No se encontraron noticias recientes con esos términos en el área indicada.")

# ==========================================
# SECCIÓN 2: ESCUCHA SOCIAL CIUDADANA
# ==========================================
with tab_escucha_social:
    st.subheader("🗣️ Buscador de Escucha Social y Voz Ciudadana")
    st.info("Monitorea lo que la población publica directamente en redes sociales durante la emergencia (necesidades, modismos, solicitudes de ayuda).")

    col_term_red, col_loc_red = st.columns(2)
    with col_term_red:
        term_redes = st.text_input("Término o modismo a escuchar en redes:", value="inundacion", key="kw_redes_input")
    with col_loc_red:
        loc_redes = st.text_input("Municipio / Zona específica redes:", value=localidad_especifica, key="loc_redes_input")

    if st.button("🔍 Iniciar Escucha en Redes Sociales"):
        with st.spinner("Escuchando conversaciones de la comunidad en tiempo real..."):
            df_redes = capturar_escucha_ciudadana(
                termino_clave=term_redes,
                ciudad=loc_redes,
                provincia=provincia_o_zona,
                limite=40
            )

            if not df_redes.empty:
                st.success(f"Se detectaron {len(df_redes)} publicaciones directas de la comunidad.")

                for idx, row in df_redes.iterrows():
                    with st.chat_message("user"):
                        st.write(f"**[{row['red']}] {row['usuario_o_titulo']}** • *{row['fecha']}*")
                        st.write(f"\"{row['mensaje']}\"")
                        st.markdown(f"🔗 [Ver publicación original]({row['link']})")

                # Exportación exclusiva de datos de escucha social
                csv_redes = df_redes.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Datos de Escucha Social (CSV)", csv_redes, "escucha_ciudadana_iiarrd.csv", "text/csv")
            else:
                st.warning("No se encontraron publicaciones de la comunidad con esos términos o ubicación específica en las últimas horas.")