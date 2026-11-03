from core.graph import extraer_texto_respuesta


def test_bloques_de_texto_separados_por_espacio() -> None:
    assert extraer_texto_respuesta(
        [
            {"type": "text", "text": "un gran"},
            {"type": "text", "text": "perfil práctico"},
        ]
    ) == "un gran perfil práctico"


def test_string_simple_se_conserva() -> None:
    assert extraer_texto_respuesta("Respuesta completa.") == "Respuesta completa."

