import json
import streamlit as st
from openai import OpenAI


def analizar_incidente(texto):
  """Analiza un texto utilizando la API Key almacenada en los Secrets del servidor."""
  # Obtiene la clave de forma segura desde los Secrets de Streamlit Cloud
  api_key = st.secrets.get("OPENAI_API_KEY")

  if not api_key:
    return {
        "categoria": "Error",
        "urgencia": "Baja",
        "ubicacion": "N/A",
        "sentimiento": "Neutral",
        "resumen_ejecutivo": (
            "Falta configurar la OPENAI_API_KEY en los Secrets de Streamlit."
        ),
    }

  try:
    client = OpenAI(api_key=api_key.strip())
    prompt_sistema = """
        Eres un analista experto en comunicación de riesgo de desastres e hidrología.
        Analiza el texto proporcionado y responde EXCLUSIVAMENTE en formato JSON estricto.
        
        Campos requeridos:
        - "categoria": Elegir entre ["Inundación/Anegamiento", "Solicitud de Ayuda", "Infraestructura/Cortes", "Rumor/Desinformación", "Información Oficial"]
        - "urgencia": Elegir entre ["Alta", "Media", "Baja"]
        - "ubicacion": Nombre del municipio, barrio, arroyo o cuenca mencionado (o "No especificado")
        - "sentimiento": Elegir entre ["Pánico/Temor", "Molestia/Reclamo", "Informativo", "Neutral"]
        - "resumen_ejecutivo": Breve resumen de 10 palabras como máximo.
        """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": f"Texto a evaluar: {texto}"},
        ],
        temperature=0.1,
    )
    return json.loads(response.choices[0].message.content)

  except Exception as e:
    return {
        "categoria": "Error de API",
        "urgencia": "Baja",
        "ubicacion": "N/A",
        "sentimiento": "Neutral",
        "resumen_ejecutivo": f"Error: {str(e)}",
    }