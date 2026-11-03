from langchain_core.tools import tool
from langchain_tavily import TavilySearch


@tool
def buscar_programas_web(consulta: str) -> str:
    """Busca en internet información actual sobre programas académicos
    (universidades, carreras, pensum, requisitos, admisión).
    Úsala SIEMPRE que buscar_programas_academicos no devuelva resultados
    relevantes o devuelva programas que no corresponden a lo que pidió el usuario.
    Prioriza sitios oficiales de universidades y cita el título, el programa y la URL.
    Incluye en la consulta la carrera y la ciudad, por ejemplo:
    'programa de Física universidades Medellín Colombia'."""
    if not consulta.strip():
        return "ERROR_BUSQUEDA_WEB: indica la carrera y la ciudad que deseas consultar."

    try:
        buscador = TavilySearch(max_results=4, search_depth="basic")
        resultado = buscador.invoke({"query": consulta})
    except Exception as error:
        if "TAVILY_API_KEY" in str(error):
            return (
                "ERROR_BUSQUEDA_WEB: TAVILY_API_KEY no está configurada; "
                "no fue posible realizar la búsqueda web."
            )
        return (
            "ERROR_BUSQUEDA_WEB: la búsqueda web no está disponible por un "
            "problema de conexión o del servicio. No inventes resultados."
        )

    items = resultado.get("results", []) if isinstance(resultado, dict) else []
    if not items:
        return "SIN_RESULTADOS_WEB"

    return "\n\n".join(
        f"Fuente: {r.get('title', 'Sin título')} "
        f"({r.get('url', 'URL no disponible')})\n{r.get('content', '')}"
        for r in items
    )