import re
import sys
import uuid

from core.agent import app_vocacional
from core.graph import extraer_texto_respuesta, generar_respuesta_api
from core.metrics import MetricasCallback
from langchain_core.messages import AIMessage, HumanMessage

thread_id = str(uuid.uuid4())
metricas = MetricasCallback(
    thread_id=thread_id,
    entrada_resumida="Consulta de prueba de orientación vocacional con puntajes.",
)
config = {
    "configurable": {"thread_id": thread_id},
    "recursion_limit": 10,
    "callbacks": [metricas],
}

mensaje_usuario = """
El estudiante de prueba terminó su test. Obtuvo estos puntajes:
- Científico: 10
- Artístico: 20
- Social: 30
- Práctico: 64

Dime su perfil dominante, dale un mensaje motivador y recomiéndale carreras.
"""

print("Ejecutando el grafo sin Streamlit:", flush=True)
ultimo_mensaje_agente = None
try:
    for actualizacion in app_vocacional.stream(
        {
            "messages": [HumanMessage(content=mensaje_usuario)],
            "ruta": "herramientas",
        },
        config=config,
        stream_mode="updates",
    ):
        for nombre_nodo, salida_nodo in actualizacion.items():
            print(f"Nodo ejecutado: {nombre_nodo}", flush=True)
            metricas.set_state_steps(salida_nodo.get("pasos_ejecutados"))
            mensajes = salida_nodo.get("messages", [])
            ultimo_mensaje_agente = next(
                (
                    mensaje
                    for mensaje in reversed(mensajes)
                    if isinstance(mensaje, AIMessage)
                ),
                ultimo_mensaje_agente,
            )

    if ultimo_mensaje_agente is None:
        raise RuntimeError("El grafo terminó sin producir un mensaje del agente.")

    texto_crudo = extraer_texto_respuesta(ultimo_mensaje_agente.content)
    print("\nEstructurando la respuesta para el frontend...", flush=True)
    respuesta_final_api = generar_respuesta_api(
        texto_crudo,
        callback=metricas,
    )
    metricas.finish("ok")

    print("\n--- JSON FINAL PARA LA API ---")
    print(respuesta_final_api.model_dump_json(indent=2))
except Exception as error:
    metricas.finish("error")
    notas = " ".join(getattr(error, "__notes__", []))
    coincidencia = re.search(r"During task with name '([^']+)'", notas)
    nodo = coincidencia.group(1) if coincidencia else "no identificado"
    print(
        f"El grafo falló en el nodo '{nodo}': {type(error).__name__}: {error}",
        file=sys.stderr,
        flush=True,
    )
    raise
