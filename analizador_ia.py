import json
import streamlit as st
import google.generativeai as genai


def analizar_incidente(texto):
  """Analiza un texto de forma gratuita usando la API de Google Gemini."""
  # Intenta leer la clave desde Streamlit Secrets
  api_key = st.secrets.get("GEMINI_API_KEY")

  if not api_key:
    return {
        "categoria": "Sin Clave API",
        "urgencia": "Baja",
        "ubicacion": "N/A",
        "sentimiento": "Neutral",
        "resumen_ejecutivo": (
            "ERROR: La variable GEMINI_API_KEY no existe en los Secrets de"
            " Streamlit."
        ),
    }

  try:
    genai.configure(api_key=str(api_key).strip())

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

    # Intentamos con los modelos estándar activos en Google AI Studio
    try:
      model = genai.GenerativeModel("gemini-1.5-flash")
      response = model.generate_content(prompt)
    except Exception:
      model = genai.GenerativeModel("gemini-1.5-pro")
      response = model.generate_content(prompt)

    texto_limpio = (
        response.text.replace("```json", "").replace("```", "").strip()
    )
    return json.loads(texto_limpio)

  except Exception as e:
    return {
        "categoria": "Error de Clave API",
        "urgencia": "Baja",
        "ubicacion": "N/A",
        "sentimiento": "Neutral",
        "resumen_ejecutivo": f"Detalle real del error: {str(e)}",
    }