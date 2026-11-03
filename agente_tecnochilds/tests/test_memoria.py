import uuid

from langchain_core.messages import HumanMessage

from core.agent import app_vocacional


def test_memoria_conserva_mensajes_por_thread_y_separa_threads(
    fake_chat_model: object,
) -> None:
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    primer_mensaje = "Recomiéndame carreras prácticas."

    primera_respuesta = app_vocacional.invoke(
        {"messages": [HumanMessage(content=primer_mensaje)], "ruta": "herramientas"},
        config=config,
    )
    segunda_respuesta = app_vocacional.invoke(
        {
            "messages": [HumanMessage(content="¿Y si prefiero algo creativo?")],
            "ruta": None,
        },
        config=config,
    )
    mensajes_mismo_thread = segunda_respuesta["messages"]
    assert any(mensaje.content == primer_mensaje for mensaje in mensajes_mismo_thread)
    assert len(mensajes_mismo_thread) > len(primera_respuesta["messages"])

    otro_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    respuesta_otro_thread = app_vocacional.invoke(
        {"messages": [HumanMessage(content="Pregunta aislada.")], "ruta": None},
        config=otro_config,
    )
    contenidos_otro_thread = [
        mensaje.content for mensaje in respuesta_otro_thread["messages"]
    ]
    assert "Pregunta aislada." in contenidos_otro_thread
    assert primer_mensaje not in contenidos_otro_thread

