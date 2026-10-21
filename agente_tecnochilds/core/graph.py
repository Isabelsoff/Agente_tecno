from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import GEMINI_MODEL, GEMINI_API_KEY
from core.state import VocacionalState
from prompts.vocacional_prompt import ROUTER_SYSTEM_PROMPT, CONCEPTUAL_SYSTEM_PROMPT, AGENT_SYSTEM_TEMPLATE
from tools.carreras_tool import consultar_perfil_vocacional

# --- NUEVO IMPORT PARA EL JSON ---
from core.schemas import OrientacionResponse

# 1. Inicializar el modelo de Gemini
modelo = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL, 
    google_api_key=GEMINI_API_KEY, 
    temperature=0.3
)

# 2. Estructura Pydantic para el Enrutador
class DecisionEnrutador(BaseModel):
    ruta: Literal["conceptual", "herramientas"] = Field(
        description="Elige 'conceptual' para dudas generales o 'herramientas' si busca opciones de carreras."
    )
    motivo: str = Field(description="Justificación breve de la decisión.")

# Nodo 1: Clasificador de la consulta
def enrutador_node(state: VocacionalState) -> dict:
    modelo_estructurado = modelo.with_structured_output(DecisionEnrutador)
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
    respuesta = modelo.invoke(mensajes)
    
    return {
        "messages": [respuesta], 
        "pasos_ejecutados": state.get("pasos_ejecutados", []) + ["conceptual"]
    }

# Nodo 3: Razonamiento usando la herramienta de carreras
TOOLS_VOCACIONALES = [consultar_perfil_vocacional]

def agente_vocacional_node(state: VocacionalState) -> dict:
    modelo_con_tools = modelo.bind_tools(TOOLS_VOCACIONALES)
    mensajes = [SystemMessage(content=AGENT_SYSTEM_TEMPLATE)] + state["messages"]
    respuesta = modelo_con_tools.invoke(mensajes)
    
    return {
        "messages": [respuesta], 
        "pasos_ejecutados": state.get("pasos_ejecutados", []) + ["agente_vocacional"]
    }

# Nodo 4: Ejecutor nativo de herramientas de LangGraph
herramientas_node = ToolNode(TOOLS_VOCACIONALES)


# --- NUEVA FUNCIÓN PARA FORMATEAR LA RESPUESTA FINAL ---
def generar_respuesta_api(texto_analisis: str) -> OrientacionResponse:
    """
    Toma el análisis en texto del agente y lo fuerza a convertirse en el 
    esquema estricto OrientacionResponse que espera tu frontend.
    """
    modelo_estructurado = modelo.with_structured_output(OrientacionResponse)
    
    prompt_formateo = f"""
    Eres el estructurador de datos de TecnoChilds.
    Toma el siguiente análisis vocacional y extrae la información para llenar la estructura requerida.
    Asegúrate de que el 'mensaje_motivador' sea inspirador.
    
    ANÁLISIS VOCACIONAL:
    {texto_analisis}
    """
    
    respuesta_json = modelo_estructurado.invoke(prompt_formateo)
    return respuesta_json