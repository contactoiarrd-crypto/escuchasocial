import json
import streamlit as st
import google.generativeai as genai


def analizar_incidente(texto):
  """Analiza el texto y clasifica el nivel de riesgo/urgencia usando la API de Gemini."""
  api_key = st.secrets.get("GEMINI_API_KEY")

  if not api_key:
    return {
        "categoria": "Sin Clave API",
        "urgencia": "Baja",
        "ubicacion": "N/A",
        "sentimiento": "Neutral",
        "resumen_ejecutivo": (
            "Falta configurar la GEMINI_API_KEY en los Secrets de Streamlit."
        ),
    }

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

  genai.configure(api_key=api_key.strip())

  # Lista de modelos compatibles para intentar en orden
  modelos_a_probar = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]

  for nombre_modelo in modelos_a_probar:
    try:
      model = genai.GenerativeModel(model_name=nombre_modelo)
      response = model.generate_content(prompt)

      # Limpieza de marcado markdown en caso de existir
      texto_limpio = (
          response.text.replace("```json", "").replace("```", "").strip()
      )
      return json.loads(texto_limpio)
    except Exception:
      continue  # Si falla un nombre de modelo, intenta el siguiente de la lista

  # Si ninguno de los modelos respondió
  return {
      "categoria": "Error de Conexión",
      "urgencia": "Baja",
      "ubicacion": "N/A",
      "sentimiento": "Neutral",
      "resumen_ejecutivo": (
          "No se pudo conectar con los modelos de Gemini. Revisá la API Key."
      ),
  }