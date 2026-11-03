import pytest

from core import graph


def test_importar_grafo_no_requiere_api_key(monkeypatch) -> None:
    monkeypatch.setattr(graph, "GEMINI_API_KEY", "")
    monkeypatch.setattr(graph, "modelo", None)

    with pytest.raises(RuntimeError, match="Falta GEMINI_API_KEY"):
        graph.obtener_modelo()

    assert graph.modelo is None
