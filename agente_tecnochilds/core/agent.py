from typing import TypedDict
from google import genai
from google.genai import types

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from tools.carreras_tool import consultar_carreras

class Estudiante(TypedDict):
    nombre: str
    perfil_vocacional: str

client = genai.Client(api_key=GEMINI_API_KEY)

def construir_contexto(estudiante: Estudiante, memoria: str) -> str:
    return f"""
Eres el Agente Académico de Orientación Vocacional de TecnoChilds.

Tu rol es orientar a jóvenes a descubrir su carrera ideal de forma clara y motivadora.

ESTADO ACTUAL DEL ESTUDIANTE:
Nombre: {estudiante["nombre"]}
Perfil asignado: {estudiante["perfil_vocacional"]}

MEMORIA RECIENTE:
{memoria}

Tienes la herramienta `consultar_carreras`.
Úsala cuando el usuario pregunte por recomendaciones de carreras, opciones de estudio o sobre un perfil.

Sé cordial, breve y motivador.
""".strip()

def responder(mensaje_usuario: str, estudiante: Estudiante, memoria: str) -> str:
    contexto = construir_contexto(estudiante, memoria)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=mensaje_usuario,
        config=types.GenerateContentConfig(
            system_instruction=contexto,
            tools=[consultar_carreras],
        ),
    )

    return response.text or "No fue posible generar una respuesta."