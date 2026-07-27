import json
import requests
import streamlit as st


def analizar_incidente(texto):
  """Analiza un texto de forma 100% gratuita utilizando la API REST de Google Gemini."""
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
          "responseMimeType": "application/json",
          "temperature": 0.1,
      },
  }

  headers = {"Content-Type": "application/json"}

  # 1. Intentamos consultar la lista de modelos activos asignados a tu API Key
  modelos_a_probar = []
  try:
    res_list = requests.get(
        f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}",
        timeout=5,
    )
    if res_list.status_code == 200:
      data_list = res_list.json()
      for m in data_list.get("models", []):
        if "generateContent" in m.get("supportedGenerationMethods", []):
          # Extrae el nombre como "gemini-1.5-flash" omitiendo "models/"
          name = m["name"].replace("models/", "")
          modelos_a_probar.append(name)
  except Exception:
    pass

  # 2. Si no se pudo listar o la lista vino vacía, usamos los alias estándar universales
  if not modelos_a_probar:
    modelos_a_probar = [
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-001",
        "gemini-1.5-flash-002",
        "gemini-1.5-pro-latest",
    ]

  # 3. Probamos los modelos obtenidos hasta que uno responda con éxito (HTTP 200)
  for mod in modelos_a_probar:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={clean_key}"
    try:
      response = requests.post(
          url, headers=headers, json=payload, timeout=10
      )
      res_data = response.json()

      if response.status_code == 200:
        candidates = res_data.get("candidates", [])
        if candidates:
          raw_text = candidates[0]["content"]["parts"][0]["text"]
          texto_limpio = (
              raw_text.replace("```json", "").replace("```", "").strip()
          )
          return json.loads(texto_limpio)
    except Exception:
      continue

  return {
      "categoria": "Error de Conexión",
      "urgencia": "Baja",
      "ubicacion": "N/A",
      "sentimiento": "Neutral",
      "resumen_ejecutivo": (
          "No se pudo conectar con ningún modelo activo de tu cuenta."
      ),
  }