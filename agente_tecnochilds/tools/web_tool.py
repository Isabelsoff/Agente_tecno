from langchain_core.tools import tool
from langchain_tavily import TavilySearch


@tool
def buscar_programas_web(consulta: str) -> str:
    """Busca en internet información actual sobre programas académicos
    (universidades, carreras, pensum, requisitos, admisión).
    Úsala SIEMPRE que buscar_programas_academicos no devuelva resultados
    o devuelva programas que no corresponden a lo que pidió el usuario.
    Incluye en la consulta la carrera y la ciudad, por ejemplo:
    'programa de Física universidades Medellín Colombia'."""
    try:
        buscador = TavilySearch(max_results=4, search_depth="basic")
        resultado = buscador.invoke({"query": consulta})
    except Exception as e:
        return f"ERROR_BUSQUEDA_WEB: {e}"

    items = resultado.get("results", [])
    if not items:
        return "SIN_RESULTADOS_WEB"

    return "\n\n".join(
        f"Fuente: {r['title']} ({r['url']})\n{r['content']}" for r in items
    )