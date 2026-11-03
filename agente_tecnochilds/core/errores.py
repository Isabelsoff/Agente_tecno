def clasificar_error_modelo(error: object) -> str | None:
    """Return the stable category for Gemini quota and timeout errors."""
    detalle = str(error)
    if "RESOURCE_EXHAUSTED" in detalle or "429" in detalle:
        return "429"
    if "DEADLINE_EXCEEDED" in detalle or "504" in detalle:
        return "504"
    return None
