import json
import requests
import streamlit as st


def analizar_incidente(texto):
  """Analiza un texto de forma 100% gratuita usando la API REST directa de Google Gemini."""
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

  # URL directa del endpoint REST oficial de Gemini
  url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key.strip()}"

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
          "response_mime_type": "application/json",
          "temperature": 0.1,
      },
  }

  headers = {"Content-Type": "application/json"}

  try:
    response = requests.post(
        url, headers=headers, json=payload, timeout=10
    )
    res_data = response.json()

    if response.status_code == 200:
      # Extraer el texto devuelto por Gemini
      raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
      texto_limpio = (
          raw_text.replace("```json", "").replace("```", "").strip()
      )
      return json.loads(texto_limpio)
    else:
      # En caso de error de la API (ej. clave inválida)
      err_msg = res_data.get("error", {}).get("message", "Error desconocido")
      return {
          "categoria": "Error API",
          "urgencia": "Baja",
          "ubicacion": "N/A",
          "sentimiento": "Neutral",
          "resumen_ejecutivo": f"HTTP {response.status_code}: {err_msg[:35]}",
      }

  except Exception as e:
    return {
        "categoria": "Error de Conexión",
        "urgencia": "Baja",
        "ubicacion": "N/A",
        "sentimiento": "Neutral",
        "resumen_ejecutivo": f"Fallo: {str(e)[:40]}",
    }