from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import START

from core.agent import (
    app_vocacional,
    decidir_inicio,
    decidir_ruta,
    evaluar_herramientas,
)


def test_decidir_ruta_para_ruta_conceptual_herramientas_y_none() -> None:
    assert decidir_ruta({"ruta": "conceptual"}) == "ir_conceptual"
    assert decidir_ruta({"ruta": "herramientas"}) == "ir_agente"
    assert decidir_ruta({"ruta": None}) == "ir_agente"


def test_evaluar_herramientas_con_y_sin_tool_calls() -> None:
    con_herramienta = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "consultar_perfil_vocacional",
                "args": {"consulta": "social"},
                "id": "route-test-call",
                "type": "tool_call",
            }
        ],
    )
    assert evaluar_herramientas({"messages": [con_herramienta]}) == "usar_herramientas"

    sin_herramienta = AIMessage(content="Respuesta.")
    assert evaluar_herramientas({"messages": [sin_herramienta]}) == "finalizar"


def test_start_tiene_arista_condicional_hacia_agente_y_enrutador() -> None:
    aristas_inicio = {
        arista.target
        for arista in app_vocacional.get_graph().edges
        if arista.source == START
    }

    assert decidir_inicio({"ruta": "herramientas"}) == "ir_agente"
    assert decidir_inicio({"ruta": None}) == "ir_enrutador"
    assert aristas_inicio == {"agente", "enrutador"}

