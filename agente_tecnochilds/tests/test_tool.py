import json
from pathlib import Path

import pytest

from tools.carreras_tool import consultar_perfil_vocacional

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("consulta", "perfil_id"),
    [
        ("cientifico_tecnologico", "cientifico_tecnologico"),
        ("artistico_creativo", "artistico_creativo"),
        ("social_humanistico", "social_humanistico"),
        ("practico_tecnico", "practico_tecnico"),
    ],
)
def test_perfiles_validos_coinciden_con_json(consulta: str, perfil_id: str) -> None:
    datos = json.loads((PROJECT_ROOT / "data" / "carreras.json").read_text(encoding="utf-8"))
    perfil_json = next(
        perfil for perfil in datos["perfiles"] if perfil["id"] == perfil_id
    )

    resultado = consultar_perfil_vocacional.invoke({"consulta": consulta})
    respuesta = json.loads(resultado)

    assert isinstance(resultado, str)
    assert respuesta["encontrado"] is True
    assert respuesta["perfil"] == perfil_json


@pytest.mark.parametrize("consulta", ["perfil inexistente", ""])
def test_perfil_invalido_y_vacio_devuelven_json(consulta: str) -> None:
    resultado = consultar_perfil_vocacional.invoke({"consulta": consulta})
    respuesta = json.loads(resultado)

    assert isinstance(resultado, str)
    assert respuesta["encontrado"] is False
    assert respuesta["perfil"] is None

