import uuid

from langchain_core.messages import HumanMessage

from core.agent import app_vocacional


def test_grafo_recorrido_agente_herramientas_agente(fake_chat_model: object) -> None:
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    nodos = []

    for actualizacion in app_vocacional.stream(
        {
            "messages": [HumanMessage(content="Recomiéndame carreras prácticas.")],
            "ruta": "herramientas",
        },
        config=config,
        stream_mode="updates",
    ):
        nodos.extend(actualizacion.keys())

    estado_final = app_vocacional.get_state(config).values
    assert nodos == ["agente", "herramientas", "agente"]
    assert estado_final["pasos_ejecutados"] == [
        "agente_vocacional",
        "agente_vocacional",
    ]
    assert estado_final["messages"][-1].content == (
        "Respuesta final simulada con datos de herramienta."
    )
