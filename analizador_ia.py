import json
import streamlit as st
import google.generativeai as genai


def analizar_incidente(texto):
  """Analiza un texto detectando dinámicamente el modelo activo en la cuenta."""
  api_key = st.secrets.get("GEMINI_API_KEY")

  if not api_key:
    return {
        "categoria": "Sin Clave API",
        "urgencia": "Baja",
        "ubicacion": "N/A",
        "sentimiento": "Neutral",
        "resumen_ejecutivo": (
            "ERROR: La variable GEMINI_API_KEY no existe en los Secrets."
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

    # Buscar dinámicamente los modelos habilitados en la clave de Google Studio
    modelos = [
        m.name
        for m in genai.list_models()
        if "generateContent" in m.supported_generation_methods
    ]

    if not modelos:
      raise Exception("No hay modelos de generación de contenido disponibles.")

    # Filtrar preferentemente los modelos flash y limpiar el prefijo 'models/' si existe
    modelo_elegido = modelos[0]
    for m in modelos:
      if "flash" in m:
        modelo_elegido = m
        break

    # Remover 'models/' si la API lo incluyó
    nombre_limpio = modelo_elegido.replace("models/", "")

    model = genai.GenerativeModel(nombre_limpio)
    response = model.generate_content(prompt)

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
        "resumen_ejecutivo": f"Detalle: {str(e)[:45]}...",
    }