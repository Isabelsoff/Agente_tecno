import json
from typing import Any

from langchain_core.tools import tool

from core.rag import recuperar


@tool
def buscar_programas_academicos(consulta: str) -> str:
    """Busca programas académicos con fuentes verificables en el índice RAG.

    Usa esta herramienta para preguntas sobre universidades, programas
    académicos o dónde estudiar. Busca siempre con la carrera y ciudad pedidas.
    Determina si los programas recuperados corresponden a la carrera solicitada;
    no presentes programas distintos como resultados. Cita la institución, el
    programa y la fuente_url. Advierte si el estado de verificación indica una
    fuente secundaria o información desactualizada, y recomienda confirmarla
    en el sitio oficial. Nunca inventes datos que no devuelva la búsqueda.

    Args:
        consulta: universidad, programa, perfil o ciudad que desea buscar.

    Returns:
        Un JSON string con resultados documentados o un mensaje claro cuando
        no haya índice, la consulta esté vacía o no existan coincidencias.
    """
    def respuesta(encontrado: bool, resultados: list[dict[str, Any]], mensaje: str) -> str:
        return json.dumps(
            {
                "encontrado": encontrado,
                "resultados": resultados,
                "mensaje": mensaje,
            },
            ensure_ascii=False,
        )

    if not isinstance(consulta, str) or not consulta.strip():
        return respuesta(False, [], "La consulta está vacía.")

    try:
        fragmentos = recuperar(consulta, k=5)
    except FileNotFoundError:
        return respuesta(
            False,
            [],
            "El índice académico aún no existe. Solicita que se construya "
            "con scripts/construir_indice.py.",
        )
    except (OSError, ValueError, RuntimeError) as error:
        return respuesta(
            False,
            [],
            f"No se pudo consultar el índice académico: {error}",
        )

    resultados = [
        {
            "institucion": metadatos.get("institucion", ""),
            "programa": metadatos.get("programa", ""),
            "ciudad": metadatos.get("ciudad", ""),
            "descripcion": metadatos.get("descripcion", ""),
            "fuente_url": metadatos.get("fuente_url", ""),
            "fecha_verificacion": metadatos.get("fecha_verificacion", ""),
            "estado_verificacion": metadatos.get("estado_verificacion", ""),
            "puntaje": fragmento["puntaje"],
        }
        for fragmento in fragmentos
        for metadatos in [fragmento["metadatos"]]
    ]
    if not resultados:
        return respuesta(
            False,
            [],
            "No hay datos verificados que coincidan. Consulta los sitios oficiales "
            "de las instituciones para confirmar la oferta vigente.",
        )
    return respuesta(
        True,
        resultados,
        "Resultados recuperados del índice con sus fuentes; verifica vigencia "
        "en el sitio oficial según el estado de verificación.",
    )
