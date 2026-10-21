from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class VocacionalState(TypedDict):
    # LangGraph usará add_messages para ir sumando los mensajes en lugar de borrarlos
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Variables de control para saber qué decidió el agente
    ruta: str
    motivo: str
    pasos_ejecutados: list[str]