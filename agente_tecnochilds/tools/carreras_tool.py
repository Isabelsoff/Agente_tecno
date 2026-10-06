"""
Herramienta encargada de cargar y consultar la información de
los perfiles vocacionales y sus carreras sugeridas desde data/carreras.json
"""

import json
from pathlib import Path
from functools import lru_cache

# Ruta absoluta al archivo JSON, independiente de dónde se ejecute el proceso
_RUTA_CARRERAS = Path(__file__).resolve().parent.parent / "data" / "carreras.json"


@lru_cache(maxsize=1)
def cargar_carreras() -> dict:
    """
    Carga el archivo data/carreras.json y lo devuelve como diccionario.
    Se cachea en memoria (lru_cache) para no leer el disco en cada petición.

    Returns:
        dict: contenido completo del JSON con la clave "perfiles".

    Raises:
        FileNotFoundError: si el archivo no existe en la ruta esperada.
        json.JSONDecodeError: si el archivo tiene un JSON inválido.
    """
    if not _RUTA_CARRERAS.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de carreras en: {_RUTA_CARRERAS}"
        )

    with open(_RUTA_CARRERAS, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def obtener_perfil_por_id(perfil_id: str) -> dict | None:
    """
    Busca y devuelve un perfil vocacional específico por su id
    (ej: "cientifico_tecnologico").

    Args:
        perfil_id: identificador del perfil vocacional.

    Returns:
        dict con la info del perfil, o None si no existe.
    """
    datos = cargar_carreras()
    for perfil in datos.get("perfiles", []):
        if perfil["id"] == perfil_id:
            return perfil
    return None


def listar_perfiles() -> list[dict]:
    """
    Devuelve la lista completa de los 4 perfiles vocacionales con
    su descripción y carreras sugeridas.
    """
    datos = cargar_carreras()
    return datos.get("perfiles", [])
