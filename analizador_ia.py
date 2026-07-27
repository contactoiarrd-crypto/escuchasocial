import json
import streamlit as st
import google.generativeai as genai


def analizar_incidente(texto):
  """Analiza un texto de forma gratuita detectando automáticamente el modelo Gemini activo."""
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

    # Buscar un modelo disponible que soporte generación de contenido
    modelo_nombre = "gemini-2.0-flash"  # Modelo estándar primario

    try:
      # Probar el modelo 2.0 directamente
      model = genai.GenerativeModel(modelo_nombre)
      response = model.generate_content(prompt)
    except Exception:
      # Si falla, listar dinámicamente los modelos de la API Key
      modelos_disponibles = [
          m.name
          for m in genai.list_models()
          if "generateContent" in m.supported_generation_methods
      ]
      if modelos_disponibles:
        # Tomar el primer modelo disponible compatible (ej: models/gemini-2.0-flash)
        modelo_nombre = modelos_disponibles[0]
        model = genai.GenerativeModel(modelo_nombre)
        response = model.generate_content(prompt)
      else:
        raise Exception("No se encontraron modelos de generación disponibles.")

    texto_limpio = (
        response.text.replace("```json", "").replace("```", "").strip()
    )
    return json.loads(texto_limpio)

  except Exception as e:
    return {
        "categoria": "Error de Conexión",
        "urgencia": "Baja",
        "ubicacion": "N/A",
        "sentimiento": "Neutral",
        "resumen_ejecutivo": f"Error API: {str(e)[:45]}...",
    }