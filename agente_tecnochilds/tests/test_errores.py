import json
from uuid import uuid4

import pytest

from core import metrics
from core.errores import clasificar_error_modelo
from core.metrics import MetricasCallback


@pytest.mark.parametrize(
    ("mensaje", "categoria"),
    [
        ("429 RESOURCE_EXHAUSTED", "429"),
        ("504 DEADLINE_EXCEEDED", "504"),
    ],
)
def test_clasificacion_y_registro_de_errores(
    mensaje: str, categoria: str, tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(metrics, "_METRICS_PATH", tmp_path / "metricas.jsonl")
    error = RuntimeError(mensaje)
    assert clasificar_error_modelo(error) == categoria

    callback = MetricasCallback("thread-error", "entrada resumida")
    run_id = uuid4()
    callback.on_llm_start({}, [], run_id=run_id)
    callback.on_llm_error(error, run_id=run_id)
    registro = callback.finish("error")

    assert registro["metricas"]["errores"][0]["tipo"] == categoria
    guardado = json.loads((tmp_path / "metricas.jsonl").read_text(encoding="utf-8"))
    assert guardado["estado"] == "error"
    assert guardado["metricas"]["errores"][0]["tipo"] == categoria
