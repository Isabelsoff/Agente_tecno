import json
from uuid import uuid4

from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult

from core import metrics
from core.metrics import MetricasCallback


def test_callback_cuenta_llamadas_tokens_herramientas_errores_y_jsonl(
    tmp_path, monkeypatch
) -> None:
    archivo_log = tmp_path / "metricas.jsonl"
    monkeypatch.setattr(metrics, "_METRICS_PATH", archivo_log)
    callback = MetricasCallback("thread-metricas", "entrada de prueba")

    assert callback.metricas["llamadas_modelo"] == 0
    llm_run_id = uuid4()
    callback.on_chat_model_start({}, [[]], run_id=llm_run_id)
    assert callback.metricas["llamadas_modelo"] == 1
    callback.on_llm_end(
        LLMResult(
            generations=[
                [
                    ChatGeneration(
                        message=AIMessage(
                            content="respuesta",
                            usage_metadata={
                                "input_tokens": 12,
                                "output_tokens": 5,
                                "total_tokens": 17,
                            },
                        )
                    )
                ]
            ]
        ),
        run_id=llm_run_id,
    )

    tool_run_id = uuid4()
    callback.on_tool_start(
        {"name": "buscar_perfil"},
        "consulta",
        run_id=tool_run_id,
    )
    callback.on_tool_end("resultado", run_id=tool_run_id)
    callback.on_llm_error(
        RuntimeError("429 RESOURCE_EXHAUSTED"),
        run_id=uuid4(),
    )
    callback.set_state_steps(["agente", "herramientas"])

    registro = callback.finish("error")
    assert registro["estado"] == "error"
    assert registro["metricas"]["tokens"] == {
        "entrada": 12,
        "salida": 5,
        "total": 17,
    }
    assert registro["metricas"]["llamadas_modelo"] == 1
    assert registro["metricas"]["herramientas"][0]["nombre"] == "buscar_perfil"
    assert registro["metricas"]["errores"][0]["tipo"] == "429"
    assert registro["metricas"]["pasos_ejecutados"] == ["agente", "herramientas"]

    lineas = archivo_log.read_text(encoding="utf-8").splitlines()
    assert len(lineas) == 1
    assert json.loads(lineas[0])["thread_id"] == "thread-metricas"

