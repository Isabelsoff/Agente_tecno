import json
from pathlib import Path

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from core import rag
from core.metrics import MetricasCallback
from core.agent import app_vocacional
from prompts.vocacional_prompt import AGENT_SYSTEM_TEMPLATE, CONCEPTUAL_SYSTEM_PROMPT
from tools.programas_tool import buscar_programas_academicos
from langchain_core.messages import HumanMessage

_CAMPOS = {
    "id",
    "institucion",
    "programa",
    "perfil",
    "ciudad",
    "descripcion",
    "fuente_url",
    "fecha_verificacion",
    "estado_verificacion",
}


def _registros_prueba() -> list[dict[str, str]]:
    return [
        {
            "id": f"programa-{i}",
            "institucion": f"Institución {i}",
            "programa": f"Programa de prueba {i}",
            "perfil": perfil,
            "ciudad": f"Ciudad {i}",
            "descripcion": f"DATO CONTROLADO DE PRUEBA, documento {i}.",
            "fuente_url": f"https://example.org/programas/{i}",
            "fecha_verificacion": "2026-01-01",
            "estado_verificacion": "fuente oficial simulada para prueba",
        }
        for i, perfil in enumerate(
            (
                "cientifico_tecnologico",
                "artistico_creativo",
                "social_humanistico",
                "practico_tecnico",
                "cientifico_tecnologico",
            ),
            start=1,
        )
    ]


@pytest.fixture
def rag_temporal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    programas_path = tmp_path / "programas.jsonl"
    indice_path = tmp_path / "indice" / "indice.json"
    registros = _registros_prueba()
    programas_path.write_text(
        "".join(json.dumps(registro) + "\n" for registro in registros),
        encoding="utf-8",
    )
    embedding = DeterministicFakeEmbedding(size=16)
    monkeypatch.setattr(rag, "PROGRAMAS_PATH", programas_path)
    monkeypatch.setattr(rag, "INDEX_PATH", indice_path)
    monkeypatch.setattr(rag, "_embeddings", embedding)
    rag.cargar_indice.cache_clear()
    yield {"embedding": embedding, "index": indice_path, "programs": programas_path}
    rag.cargar_indice.cache_clear()


def test_construir_y_cargar_indice_con_archivos_temporales(rag_temporal: dict) -> None:
    cantidad = rag.construir_indice()
    indice = rag.cargar_indice()

    assert cantidad == 5
    assert rag_temporal["index"].is_file()
    assert len(indice.store) == 5


def test_recuperar_devuelve_cinco_resultados_con_puntaje(rag_temporal: dict) -> None:
    rag.construir_indice()

    resultados = rag.recuperar("programa de prueba")

    assert len(resultados) == 5
    for resultado in resultados:
        assert resultado["texto"]
        assert _CAMPOS.issubset(resultado["metadatos"])
        assert isinstance(resultado["puntaje"], float)


def test_tool_con_indice_presente_devuelve_datos_citados(rag_temporal: dict) -> None:
    rag.construir_indice()

    respuesta = json.loads(
        buscar_programas_academicos.invoke({"consulta": "programa de prueba"})
    )

    assert respuesta["encontrado"] is True
    assert len(respuesta["resultados"]) == 5
    assert {
        "institucion",
        "programa",
        "ciudad",
        "descripcion",
        "fuente_url",
        "fecha_verificacion",
        "estado_verificacion",
        "puntaje",
    }.issubset(respuesta["resultados"][0])


def test_tool_sin_indice_y_consulta_vacia_no_lanza(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rag, "INDEX_PATH", tmp_path / "ausente.json")
    rag.cargar_indice.cache_clear()

    sin_indice = json.loads(
        buscar_programas_academicos.invoke({"consulta": "universidad"})
    )
    vacia = json.loads(buscar_programas_academicos.invoke({"consulta": "  "}))

    assert sin_indice["encontrado"] is False
    assert "no existe" in sin_indice["mensaje"].lower()
    assert vacia["encontrado"] is False
    assert "vacía" in vacia["mensaje"].lower()


def test_datos_jsonl_son_validos_y_perfiles_permitidos() -> None:
    project_root = Path(__file__).resolve().parents[1]
    programas_path = project_root / "data" / "conocimiento" / "programas.jsonl"
    perfiles_path = project_root / "data" / "carreras.json"
    perfiles_permitidos = {
        perfil["id"]
        for perfil in json.loads(perfiles_path.read_text(encoding="utf-8"))["perfiles"]
    }

    registros = [
        json.loads(linea)
        for linea in programas_path.read_text(encoding="utf-8").splitlines()
        if linea.strip()
    ]
    ids = [registro["id"] for registro in registros]

    assert registros
    assert len(ids) == len(set(ids))
    for registro in registros:
        assert _CAMPOS.issubset(registro)
        assert registro["perfil"] in perfiles_permitidos


def test_agente_simulado_invoca_tool_rag_y_metricas_la_registran(
    rag_temporal: dict,
    fake_chat_model,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core import metrics

    fake_chat_model.tool_name = "buscar_programas_academicos"
    monkeypatch.setattr(metrics, "_METRICS_PATH", tmp_path / "metricas.jsonl")
    callback = MetricasCallback("thread-rag-tool", "pregunta sobre programas")
    resultado = app_vocacional.invoke(
        {
            "messages": [HumanMessage(content="¿Dónde estudiar este programa?")],
            "ruta": "herramientas",
        },
        config={
            "configurable": {"thread_id": "thread-rag-tool"},
            "callbacks": [callback],
        },
    )
    callback.set_state_steps(resultado.get("pasos_ejecutados"))
    registro = callback.finish("ok")

    assert resultado["messages"][-1].content == (
        "Respuesta final simulada con datos de herramienta."
    )
    assert any(
        herramienta["nombre"] == "buscar_programas_academicos"
        for herramienta in registro["metricas"]["herramientas"]
    )


def test_prompts_definen_relevancia_y_respaldo_no_verificado() -> None:
    for prompt in (AGENT_SYSTEM_TEMPLATE, CONCEPTUAL_SYSTEM_PROMPT):
        prompt_lower = prompt.lower()
        assert "buscar_programas_academicos" in prompt_lower
        assert "institución, programa, descripción y fuente_url" in prompt_lower
        assert "correspondan a la carrera pedida" in prompt_lower
        assert "información general (no verificada)" in prompt_lower
        assert "no están en tu base verificada" in prompt_lower
        assert "está prohibido dar costos" in prompt_lower
