"""
Lógica del Agente Académico de Orientación Vocacional de TecnoChilds.
Usa el SDK oficial `google-genai` para interactuar con el modelo Gemini.
"""

import json
import re

from google import genai
from google.genai import types

from config.settings import settings
from core.state import TestVocacionalRequest, OrientacionResponse, CarreraSugerida
from tools.carreras_tool import listar_perfiles

# Mapeo entre los campos del request (snake_case) y los ids usados en carreras.json
_MAPA_PERFILES = {
    "cientifico_tecnologico": "cientifico_tecnologico",
    "artistico_creativo": "artistico_creativo",
    "social_humanistico": "social_humanistico",
    "practico_tecnico": "practico_tecnico",
}

# System Prompt: define el rol y el tono del agente frente a Gemini
SYSTEM_PROMPT = """
Eres el Agente Académico de Orientación Vocacional de TecnoChilds, una plataforma
que ayuda a adolescentes y jóvenes a descubrir su camino profesional.

Tu rol:
- Eres un orientador vocacional cálido, motivador y cercano, que habla con
  jóvenes de forma clara, positiva y sin tecnicismos innecesarios.
- Nunca eres condescendiente ni genérico: tus mensajes deben sentirse
  personalizados según el perfil y las carreras que se te entreguen.
- Tu objetivo es inspirar confianza en el estudiante sobre su potencial,
  sin prometerle un futuro garantizado ni desanimarlo respecto a otras opciones.

Instrucciones estrictas de formato:
- SIEMPRE debes responder ÚNICAMENTE con un JSON válido, sin texto adicional,
  sin comentarios y sin bloques de markdown (nada de ```json).
- El JSON debe tener exactamente esta forma:

{
  "mensaje_motivador": "string, 2 a 4 frases, tono motivador y personalizado",
  "carreras_recomendadas": [
    {"nombre": "string", "justificacion": "string, 1 a 2 frases"}
  ]
}

- "carreras_recomendadas" debe incluir entre 3 y 5 carreras, tomadas SOLO
  de la lista de carreras sugeridas que se te entrega en el mensaje del usuario.
- No inventes carreras que no estén en la lista entregada.
""".strip()


def _construir_prompt_usuario(request: TestVocacionalRequest, perfil_dominante: dict) -> str:
    """
    Arma el mensaje de usuario que se envía a Gemini, incluyendo
    el contexto del estudiante y las carreras disponibles para su perfil.
    """
    carreras_disponibles = ", ".join(perfil_dominante["carreras_sugeridas"])

    return f"""
Estudiante: {request.nombre_estudiante}
Edad: {request.edad if request.edad else "no especificada"}

Perfil vocacional dominante: {perfil_dominante["nombre"]}
Descripción del perfil: {perfil_dominante["descripcion"]}

Carreras sugeridas disponibles para este perfil:
{carreras_disponibles}

Genera el mensaje motivador y selecciona entre 3 y 5 carreras de la lista
anterior para recomendar a este estudiante, siguiendo el formato JSON indicado.
""".strip()


def _extraer_json(texto: str) -> dict:
    """
    Extrae un objeto JSON de la respuesta cruda del modelo, por si Gemini
    llegara a envolverlo en bloques de markdown pese a las instrucciones.
    """
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```json\s*|^```\s*|```$", "", texto_limpio, flags=re.MULTILINE).strip()

    match = re.search(r"\{.*\}", texto_limpio, re.DOTALL)
    if not match:
        raise ValueError("La respuesta del modelo no contiene un JSON válido")

    return json.loads(match.group(0))


def _determinar_perfil_dominante(request: TestVocacionalRequest) -> tuple[str, dict]:
    """
    Calcula qué perfil vocacional tiene el puntaje más alto y devuelve
    su id junto con la información completa del perfil (desde carreras.json).
    """
    puntajes = request.puntajes.model_dump()
    perfil_id_dominante = max(puntajes, key=puntajes.get)

    perfiles = listar_perfiles()
    perfil_info = next((p for p in perfiles if p["id"] == perfil_id_dominante), None)

    if perfil_info is None:
        raise ValueError(
            f"No se encontró el perfil '{perfil_id_dominante}' en data/carreras.json"
        )

    return perfil_id_dominante, perfil_info


def generar_orientacion(request: TestVocacionalRequest) -> OrientacionResponse:
    """
    Punto de entrada principal del agente: recibe los puntajes del test,
    determina el perfil dominante, consulta a Gemini y arma la respuesta
    final para el frontend de TecnoChilds.
    """
    settings.validate()

    _, perfil_info = _determinar_perfil_dominante(request)

    cliente = genai.Client(api_key=settings.GEMINI_API_KEY)

    prompt_usuario = _construir_prompt_usuario(request, perfil_info)

    respuesta = cliente.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt_usuario,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.8,
            response_mime_type="application/json",
        ),
    )

    datos_generados = _extraer_json(respuesta.text)

    carreras_recomendadas = [
        CarreraSugerida(nombre=c["nombre"], justificacion=c["justificacion"])
        for c in datos_generados.get("carreras_recomendadas", [])
    ]

    resumen_perfiles = request.puntajes.model_dump()

    return OrientacionResponse(
        perfil_dominante=perfil_info["nombre"],
        mensaje_motivador=datos_generados.get("mensaje_motivador", ""),
        carreras_recomendadas=carreras_recomendadas,
        resumen_perfiles=resumen_perfiles,
    )
