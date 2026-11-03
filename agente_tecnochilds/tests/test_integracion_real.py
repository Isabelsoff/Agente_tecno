import os

import pytest

from core.graph import obtener_modelo


@pytest.mark.skipif(
    os.getenv("RUN_LIVE") != "1",
    reason="La integración real requiere RUN_LIVE=1 y consume cuota de Gemini.",
)
def test_integracion_real_gemini_solo_con_opt_in_explicito() -> None:
    respuesta = obtener_modelo().invoke("Responde únicamente con la palabra listo.")
    assert respuesta.content
