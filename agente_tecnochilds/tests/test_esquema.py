import pytest
from pydantic import ValidationError

from core.schemas import OrientacionResponse


def test_esquema_valido_normaliza_a_claves_fijas() -> None:
    resultado = OrientacionResponse.model_validate(
        {
            "perfil_dominante": "Práctico-Técnico",
            "mensaje_motivador": "Puedes convertir tus ideas en proyectos.",
            "carreras_recomendadas": [
                {"nombre": "Ingeniería Mecánica", "justificacion": "Perfil práctico."}
            ],
            "resumen_perfiles": {
                "cientifico_tecnologico": 10,
                "Artístico-Creativo": 20,
                "social_humanistico": 30,
                "Práctico": 64,
                "clave_inesperada": 999,
            },
        }
    )

    assert resultado.resumen_perfiles == {
        "Científico": 10,
        "Artístico": 20,
        "Social": 30,
        "Práctico": 64,
    }


def test_resumen_incompleto_rellena_claves_y_datos_requeridos_fallan() -> None:
    base = {
        "perfil_dominante": "Social-Humanístico",
        "mensaje_motivador": "Tu empatía aporta mucho.",
        "carreras_recomendadas": [],
        "resumen_perfiles": {"Social": 30},
    }
    resultado = OrientacionResponse.model_validate(base)
    assert set(resultado.resumen_perfiles) == {
        "Científico",
        "Artístico",
        "Social",
        "Práctico",
    }
    assert resultado.resumen_perfiles["Científico"] == 0

    with pytest.raises(ValidationError):
        OrientacionResponse.model_validate(
            {"perfil_dominante": "Social-Humanístico"}
        )

