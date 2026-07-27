import json
import streamlit as st
import google.generativeai as genai


def analizar_incidente(texto):
    """
    Analiza un texto de forma gratuita usando la API de Google Gemini
    y clasifica el nivel de riesgo, categoría y sentimiento.
    """
    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        return {
            "categoria": "Sin Clave API",
            "urgencia": "Baja",
            "ubicacion": "N/A",
            "sentimiento": "Neutral",
            "resumen_ejecutivo": "Falta configurar la GEMINI_API_KEY en los Secrets de Streamlit."
        }

    try:
        # Configurar la clave de API
        genai.configure(api_key=api_key.strip())

        # Configuración de generación para forzar formato JSON
        generation_config = {
            "temperature": 0.1,
            "response_mime_type": "application/json",
        }

        # Instanciar el modelo oficial de velocidad y bajo consumo
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config
        )

        prompt = f"""
        Eres un analista experto en comunicación de riesgo de desastres e hidrología en América Latina.
        Analiza el siguiente texto y responde EXCLUSIVAMENTE un objeto JSON estricto sin formato markdown ni texto adicional.
        
        Campos requeridos en el JSON:
        - "categoria": Elegir entre ["Inundación/Anegamiento", "Solicitud de Ayuda", "Infraestructura/Cortes", "Rumor/Desinformación", "Información Oficial"]
        - "urgencia": Elegir entre ["Alta", "Media", "Baja"]
        - "ubicacion": Nombre del país, provincia, municipio, barrio o cuenca mencionado (o "No especificado")
        - "sentimiento": Elegir entre ["Pánico/Temor", "Molestia/Reclamo", "Informativo", "Neutral"]
        - "resumen_ejecutivo": Breve resumen de 10 palabras como máximo.

        Texto a analizar: {texto}
        """

        response = model.generate_content(prompt)
        
        # Limpieza de cualquier etiquetado extra de Markdown
        texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
        
        return json.loads(texto_limpio)

    except Exception as e:
        return {
            "categoria": "Error de Procesamiento",
            "urgencia": "Baja",
            "ubicacion": "N/A",
            "sentimiento": "Neutral",
            "resumen_ejecutivo": f"Detalle: {str(e)[:40]}..."
        }