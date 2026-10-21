from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from core.state import VocacionalState
from core.graph import (
    enrutador_node, 
    conceptual_node, 
    agente_vocacional_node, 
    herramientas_node
)

# --- Funciones de Decisión (Rutas condicionales) ---

def decidir_ruta(state: VocacionalState) -> str:
    """Decide hacia dónde ir después del enrutador."""
    if state.get("ruta") == "conceptual":
        return "ir_conceptual"
    return "ir_agente"

def evaluar_herramientas(state: VocacionalState) -> str:
    """Evalúa si el agente decidió usar una herramienta o si ya terminó."""
    ultimo_mensaje = state["messages"][-1]
    # Si el mensaje del modelo incluye llamadas a herramientas, vamos al nodo de herramientas
    if hasattr(ultimo_mensaje, "tool_calls") and ultimo_mensaje.tool_calls:
        return "usar_herramientas"
    return "finalizar"

# --- Construcción del Grafo ---

# 1. Inicializar el Grafo con nuestro Estado
builder = StateGraph(VocacionalState)

# 2. Agregar los Nodos (las "estaciones")
builder.add_node("enrutador", enrutador_node)
builder.add_node("conceptual", conceptual_node)
builder.add_node("agente", agente_vocacional_node)
builder.add_node("herramientas", herramientas_node)

# 3. Definir el Flujo (las "flechas")
builder.add_edge(START, "enrutador")

# Del enrutador, tomamos una decisión condicional
builder.add_conditional_edges(
    "enrutador",
    decidir_ruta,
    {
        "ir_conceptual": "conceptual",
        "ir_agente": "agente"
    }
)

# Si se fue por conceptual, ahí termina la ejecución
builder.add_edge("conceptual", END)

# Si se fue por el agente, evaluamos si llamó a una herramienta
builder.add_conditional_edges(
    "agente",
    evaluar_herramientas,
    {
        "usar_herramientas": "herramientas",
        "finalizar": END
    }
)

# Si usó herramientas, la respuesta vuelve al agente para que la analice
builder.add_edge("herramientas", "agente")

# 4. Compilar el Grafo con Memoria (Checkpointer)
memoria = MemorySaver()
app_vocacional = builder.compile(checkpointer=memoria)