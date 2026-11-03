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
    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name

    def invoke(self, messages: list[Any]) -> AIMessage:
        if any(isinstance(message, ToolMessage) for message in messages):
            return AIMessage(content="Respuesta final simulada con datos de herramienta.")
        consulta = (
            "programas universitarios"
            if self.tool_name == "buscar_programas_academicos"
            else "practico_tecnico"
        )
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": self.tool_name,
                    "args": {"consulta": consulta},
                    "id": "test-call-1",
                    "type": "tool_call",
                }
            ],
        )


class FakeChatModel:
    def __init__(self) -> None:
        self.tool_name = "consultar_perfil_vocacional"

    def with_structured_output(self, schema: type[Any]) -> FakeStructuredModel:
        return FakeStructuredModel(schema)

    def bind_tools(self, tools: list[Any]) -> FakeToolBoundModel:
        return FakeToolBoundModel(self.tool_name)

    def invoke(self, messages: list[Any]) -> AIMessage:
        return AIMessage(content="Respuesta conceptual simulada.")


@pytest.fixture
def fake_chat_model(monkeypatch: pytest.MonkeyPatch) -> FakeChatModel:
    from core import graph

    fake = FakeChatModel()
    monkeypatch.setattr(graph, "modelo", fake)
    return fake
