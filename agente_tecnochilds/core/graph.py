"""
Grafo del Orientador Vocacional Tecnológico de TecnoChilds, listo para
desplegar en LangGraph Platform.

A diferencia de core/agent.py (que usa AgentExecutor + RunnableWithMessageHistory,
pensado para correr localmente desde Streamlit), este archivo expone un grafo
compilado con create_react_agent: es lo que langgraph.json necesita para
desplegar el agente como una API.

La memoria de la conversación (por thread_id) la maneja automáticamente
LangGraph Platform -- no hace falta un diccionario de historiales propio.
"""

from langgraph.prebuilt import create_react_agent

from core.agent import _inicializar_llm, SYSTEM_PROMPT_ORIENTADOR_TECNOLOGICO
from tools.carreras_tool import consultar_perfil_vocacional

# Herramientas disponibles para el agente desplegado
_HERRAMIENTAS = [consultar_perfil_vocacional]

# Grafo compilado: esta es la variable que langgraph.json apunta a exponer
# (ver la clave "graphs" en langgraph.json: "./core/graph.py:graph").
graph = create_react_agent(
    model=_inicializar_llm(),
    tools=_HERRAMIENTAS,
    prompt=SYSTEM_PROMPT_ORIENTADOR_TECNOLOGICO,
)