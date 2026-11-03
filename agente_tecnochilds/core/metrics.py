import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from core.errores import clasificar_error_modelo

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_METRICS_PATH = _PROJECT_ROOT / "logs" / "metricas.jsonl"
_LOG_LOCK = threading.Lock()


class MetricasCallback(BaseCallbackHandler):
    """Collect metrics for one graph request and append a JSONL record."""

    def __init__(self, thread_id: str, entrada_resumida: str) -> None:
        self.thread_id = thread_id
        self.entrada_resumida = entrada_resumida
        self._started_at = time.perf_counter()
        self._model_starts: dict[str, tuple[float, str | None]] = {}
        self._tool_starts: dict[str, tuple[float, str]] = {}
        self._finalized = False
        self._record: dict[str, Any] = {}
        self._state_steps: list[str] = []
        self._nodes: list[str] = []
        self.metricas: dict[str, Any] = {
            "tiempo_total_segundos": 0.0,
            "llamadas_modelo": 0,
            "tiempo_llamadas_modelo_segundos": [],
            "tokens": {"entrada": 0, "salida": 0, "total": 0},
            "herramientas": [],
            "errores": [],
        }

    @staticmethod
    def _run_key(run_id: UUID | str) -> str:
        return str(run_id)

    def _start_model(self, serialized: dict[str, Any], run_id: UUID | str) -> None:
        key = self._run_key(run_id)
        if key in self._model_starts:
            return
        kwargs = serialized.get("kwargs", {})
        model_name = kwargs.get("model") if isinstance(kwargs, dict) else None
        self._model_starts[key] = (time.perf_counter(), model_name)
        self.metricas["llamadas_modelo"] += 1

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._start_model(serialized, run_id)

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._start_model(serialized, run_id)

    def _finish_model(self, run_id: UUID | str) -> None:
        started = self._model_starts.pop(self._run_key(run_id), None)
        if started is not None:
            duration = time.perf_counter() - started[0]
            self.metricas["tiempo_llamadas_modelo_segundos"].append(
                round(duration, 3)
            )

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        usage_found = False
        for generation_group in response.generations:
            for generation in generation_group:
                message = getattr(generation, "message", None)
                usage = getattr(message, "usage_metadata", None)
                if isinstance(usage, dict):
                    tokens = self.metricas["tokens"]
                    input_tokens = int(usage.get("input_tokens", 0) or 0)
                    output_tokens = int(usage.get("output_tokens", 0) or 0)
                    total_tokens = int(
                        usage.get("total_tokens", input_tokens + output_tokens) or 0
                    )
                    tokens["entrada"] += input_tokens
                    tokens["salida"] += output_tokens
                    tokens["total"] += total_tokens
                    usage_found = True

        if not usage_found and isinstance(response.llm_output, dict):
            token_usage = response.llm_output.get("token_usage", {})
            if isinstance(token_usage, dict):
                input_tokens = int(
                    token_usage.get("prompt_tokens", token_usage.get("input_tokens", 0))
                    or 0
                )
                output_tokens = int(
                    token_usage.get(
                        "completion_tokens", token_usage.get("output_tokens", 0)
                    )
                    or 0
                )
                total_tokens = int(
                    token_usage.get("total_tokens", input_tokens + output_tokens) or 0
                )
                tokens = self.metricas["tokens"]
                tokens["entrada"] += input_tokens
                tokens["salida"] += output_tokens
                tokens["total"] += total_tokens
        self._finish_model(run_id)

    def on_llm_error(
        self, error: BaseException, *, run_id: UUID, **kwargs: Any
    ) -> None:
        self._finish_model(run_id)
        self._record_error(error, "modelo")

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        name = str(serialized.get("name") or "herramienta_desconocida")
        self._tool_starts[self._run_key(run_id)] = (time.perf_counter(), name)

    def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        self._finish_tool(run_id)

    def on_tool_error(
        self, error: BaseException, *, run_id: UUID, **kwargs: Any
    ) -> None:
        self._finish_tool(run_id)
        self._record_error(error, "herramienta")

    def _finish_tool(self, run_id: UUID | str) -> None:
        started = self._tool_starts.pop(self._run_key(run_id), None)
        if started is not None:
            duration, name = started
            self.metricas["herramientas"].append(
                {
                    "nombre": name,
                    "duracion_segundos": round(time.perf_counter() - duration, 3),
                }
            )

    def _record_error(self, error: BaseException, origen: str) -> None:
        error_type = clasificar_error_modelo(error) or type(error).__name__
        self.metricas["errores"].append(
            {"tipo": error_type, "excepcion": type(error).__name__, "origen": origen}
        )

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if isinstance(metadata, dict):
            node = metadata.get("langgraph_node")
            if isinstance(node, str) and node:
                self._nodes.append(node)

    def set_state_steps(self, steps: Any) -> None:
        if isinstance(steps, list):
            self._state_steps = [str(step) for step in steps]

    def finish(self, status: str) -> dict[str, Any]:
        if self._finalized:
            return self._record

        for key in list(self._model_starts):
            self._finish_model(key)
        for key in list(self._tool_starts):
            self._finish_tool(key)
        self.metricas["tiempo_total_segundos"] = round(
            time.perf_counter() - self._started_at, 3
        )
        self.metricas["nodos_ejecutados"] = self._nodes
        self.metricas["pasos_ejecutados"] = self._state_steps or self._nodes
        self._record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "thread_id": self.thread_id,
            "entrada_resumida": self.entrada_resumida,
            "estado": "ok" if status == "ok" else "error",
            "metricas": self.metricas,
        }
        _METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_LOCK, _METRICS_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(self._record, ensure_ascii=False) + "\n")
        self._finalized = True
        return self._record


def ultima_metrica(thread_id: str) -> dict[str, Any] | None:
    """Return the newest JSONL record for a thread, if one has been logged."""
    try:
        with _METRICS_PATH.open("r", encoding="utf-8") as log_file:
            ultima: dict[str, Any] | None = None
            for line_number, line in enumerate(log_file, start=1):
                if not line.strip():
                    continue
                try:
                    registro = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"Registro JSON inválido en {_METRICS_PATH}, línea {line_number}."
                    ) from error
                if registro.get("thread_id") == thread_id:
                    ultima = registro
            return ultima
    except FileNotFoundError:
        return None
