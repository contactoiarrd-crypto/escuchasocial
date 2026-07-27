import json
import requests
import streamlit as st


def analizar_incidente(texto):
  """Analiza un texto usando la API REST directa de Google Gemini de forma rápida y ligera."""
  api_key = st.secrets.get("GEMINI_API_KEY")

  if not api_key:
    return {
        "categoria": "Sin Clave API",
        "urgencia": "Baja",
        "ubicacion": "N/A",
        "sentimiento": "Neutral",
        "resumen_ejecutivo": (
            "Falta configurar la GEMINI_API_KEY en los Secrets."
        ),
    }

  clean_key = api_key.strip()

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

  payload = {
      "contents": [{"parts": [{"text": prompt}]}],
      "generationConfig": {
          "temperature": 0.1,
      },
  }

  headers = {"Content-Type": "application/json"}

  # Lista de endpoints directos para probar en orden ultrarrápido
  modelos = [
      "gemini-1.5-flash",
      "gemini-1.5-pro",
      "gemini-1.5-flash-latest",
  ]

  for mod in modelos:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={clean_key}"
    try:
      # Timeout corto de 3.5 segundos para no colgar la interfaz de Streamlit
      response = requests.post(
          url, headers=headers, json=payload, timeout=3.5
      )
      res_data = response.json()

      if response.status_code == 200:
        candidates = res_data.get("candidates", [])
        if candidates:
          raw_text = candidates[0]["content"]["parts"][0]["text"]
          # Limpiar posibles comillas de bloque markdown
          texto_limpio = (
              raw_text.replace("```json", "")
              .replace("```", "")
              .strip()
          )
          return json.loads(texto_limpio)
    except Exception:
      continue

  return {
      "categoria": "Información Oficial",
      "urgencia": "Baja",
      "ubicacion": "No especificado",
      "sentimiento": "Informativo",
      "resumen_ejecutivo": "Reporte capturado sin clasificación por timeout.",
  }