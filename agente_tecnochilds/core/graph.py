from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import GEMINI_MODEL, GEMINI_API_KEY
from core.state import VocacionalState
from prompts.vocacional_prompt import ROUTER_SYSTEM_PROMPT, CONCEPTUAL_SYSTEM_PROMPT, AGENT_SYSTEM_TEMPLATE
from tools.carreras_tool import consultar_perfil_vocacional
from tools.programas_tool import buscar_programas_academicos
from tools.web_tool import buscar_programas_web

# --- NUEVO IMPORT PARA EL JSON ---
from core.schemas import OrientacionResponse

modelo: ChatGoogleGenerativeAI | None = None


def obtener_modelo() -> ChatGoogleGenerativeAI:
    global modelo
    if modelo is None:
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "Falta GEMINI_API_KEY; configura la variable en el archivo .env."
            )
        modelo = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0.3,
            timeout=90,
            max_retries=1,
        )
    return modelo


def extraer_texto_respuesta(contenido: object) -> str:
    if isinstance(contenido, str):
        return contenido

    if isinstance(contenido, list):
        bloques_texto = []
        for bloque in contenido:
            if isinstance(bloque, str):
                bloques_texto.append(bloque)
            elif isinstance(bloque, dict) and bloque.get("type") == "text":
                texto = bloque.get("text")
                if isinstance(texto, str):
                    bloques_texto.append(texto)
        if bloques_texto:
            return " ".join(texto.strip() for texto in bloques_texto if texto.strip())

    raise ValueError("La respuesta del agente no contiene bloques de texto.")


# 2. Estructura Pydantic para el Enrutador
class DecisionEnrutador(BaseModel):
    ruta: Literal["conceptual", "herramientas"] = Field(
        description="Elige 'conceptual' para dudas generales o 'herramientas' si busca opciones de carreras."
    )
    motivo: str = Field(description="Justificación breve de la decisión.")

# Nodo 1: Clasificador de la consulta
def enrutador_node(state: VocacionalState) -> dict:
    modelo_estructurado = obtener_modelo().with_structured_output(DecisionEnrutador)
    mensajes = [SystemMessage(content=ROUTER_SYSTEM_PROMPT)] + state["messages"]
    decision = modelo_estructurado.invoke(mensajes)
    
    return {
        "ruta": decision.ruta, 
        "motivo": decision.motivo, 
        "pasos_ejecutados": state.get("pasos_ejecutados", []) + ["enrutador"]
    }

# Nodo 2: Respuesta teórica o motivacional
def conceptual_node(state: VocacionalState) -> dict:
    mensajes = [SystemMessage(content=CONCEPTUAL_SYSTEM_PROMPT)] + state["messages"]
    respuesta = obtener_modelo().invoke(mensajes)
    
    return {
        "messages": [respuesta], 
        "pasos_ejecutados": state.get("pasos_ejecutados", []) + ["conceptual"]
    }

# Nodo 3: Razonamiento usando la herramienta de carreras
TOOLS_VOCACIONALES = [
    consultar_perfil_vocacional,
    buscar_programas_academicos,
    buscar_programas_web,
]

def agente_vocacional_node(state: VocacionalState) -> dict:
    modelo_con_tools = obtener_modelo().bind_tools(TOOLS_VOCACIONALES)
    mensajes = [SystemMessage(content=AGENT_SYSTEM_TEMPLATE)] + state["messages"]
    respuesta = modelo_con_tools.invoke(mensajes)
    
    return {
        "messages": [respuesta], 
        "pasos_ejecutados": state.get("pasos_ejecutados", []) + ["agente_vocacional"]
    }

# Nodo 4: Ejecutor nativo de herramientas de LangGraph
herramientas_node = ToolNode(TOOLS_VOCACIONALES)


# --- NUEVA FUNCIÓN PARA FORMATEAR LA RESPUESTA FINAL ---
def generar_respuesta_api(
    texto_analisis: object,
    callback: BaseCallbackHandler | None = None,
) -> OrientacionResponse:
    """
    Toma el análisis en texto del agente y lo fuerza a convertirse en el 
    esquema estricto OrientacionResponse que espera tu frontend.
    """
    texto_analisis = extraer_texto_respuesta(texto_analisis)
    modelo_estructurado = obtener_modelo().with_structured_output(OrientacionResponse)
    
    prompt_formateo = f"""
    Eres el estructurador de datos de TecnoChilds.
    Toma el siguiente análisis vocacional y extrae la información para llenar la estructura requerida.
    Asegúrate de que el 'mensaje_motivador' sea inspirador.
    
    ANÁLISIS VOCACIONAL:
    {texto_analisis}
    """
    
    config = {"callbacks": [callback]} if callback is not None else None
    respuesta_json = modelo_estructurado.invoke(prompt_formateo, config=config)
    return respuesta_json