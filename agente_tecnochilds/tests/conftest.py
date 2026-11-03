import os
from typing import Any

import pytest
from langchain_core.messages import AIMessage, ToolMessage

if os.getenv("RUN_LIVE") != "1":
    os.environ["GEMINI_API_KEY"] = ""


class FakeStructuredModel:
    def __init__(self, schema: type[Any]) -> None:
        self.schema = schema

    def invoke(self, prompt: Any, config: dict[str, Any] | None = None) -> Any:
        return self.schema(ruta="conceptual", motivo="Pregunta conceptual simulada.")


class FakeToolBoundModel:
    def invoke(self, messages: list[Any]) -> AIMessage:
        if any(isinstance(message, ToolMessage) for message in messages):
            return AIMessage(content="Respuesta final simulada con datos de herramienta.")
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "consultar_perfil_vocacional",
                    "args": {"consulta": "practico_tecnico"},
                    "id": "test-call-1",
                    "type": "tool_call",
                }
            ],
        )


class FakeChatModel:
    def with_structured_output(self, schema: type[Any]) -> FakeStructuredModel:
        return FakeStructuredModel(schema)

    def bind_tools(self, tools: list[Any]) -> FakeToolBoundModel:
        return FakeToolBoundModel()

    def invoke(self, messages: list[Any]) -> AIMessage:
        return AIMessage(content="Respuesta conceptual simulada.")


@pytest.fixture
def fake_chat_model(monkeypatch: pytest.MonkeyPatch) -> FakeChatModel:
    from core import graph

    fake = FakeChatModel()
    monkeypatch.setattr(graph, "modelo", fake)
    return fake
