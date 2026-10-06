"""
Herramientas para consultar la base de datos de perfiles vocacionales y
carreras sugeridas (data/carreras.json) del Agente Académico de Orientación
Vocacional de TecnoChilds.
"""

import json
import unicodedata
from pathlib import Path
from functools import lru_cache

from langchain_core.tools import tool

# Ruta absoluta al archivo JSON, equivalente a "../data/carreras.json"
# visto desde esta carpeta (tools/), independiente de dónde se ejecute el proceso.
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


def _normalizar_texto(texto: str) -> str:
    """
    Pasa el texto a minúsculas y le quita las tildes, para poder comparar
    strings sin preocuparse por mayúsculas ni acentos
    (ej: "Científico" y "cientifico" deben matchear).
    """
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(caracter for caracter in texto if not unicodedata.combining(caracter))


@tool
def consultar_perfil_vocacional(consulta: str) -> dict:
    """
    Consulta la base de datos de perfiles vocacionales de TecnoChilds
    (data/carreras.json) por id o por nombre de perfil, y devuelve sus
    datos estructurados: id, nombre, descripción y carreras sugeridas.

    IMPORTANTE: usa SIEMPRE esta herramienta antes de recomendarle carreras
    a un estudiante. Es la única fuente de verdad sobre los perfiles
    vocacionales y las carreras asociadas a cada uno; nunca inventes
    carreras, descripciones ni ids de perfiles que no vengan de aquí.

    Args:
        consulta: id exacto del perfil (ej. "cientifico_tecnologico",
            "artistico_creativo", "social_humanistico", "practico_tecnico")
            o parte de su nombre (ej. "científico", "artístico", "social").
            No distingue mayúsculas/minúsculas ni tildes.

    Returns:
        dict con tres claves:
        - "encontrado" (bool): True si se halló un perfil que coincide
          con la consulta.
        - "perfil" (dict | None): si se encontró, contiene
          {"id", "nombre", "descripcion", "carreras_sugeridas"}; si no,
          es None.
        - "mensaje" (str): mensaje descriptivo del resultado, o de error
          (archivo no encontrado, JSON inválido, perfil inexistente).
          Cuando no se encuentra el perfil, incluye los ids disponibles
          para que el agente pueda reintentar con un valor válido.
    """
    try:
        datos = cargar_carreras()
        perfiles = datos.get("perfiles", [])

        if not perfiles:
            return {
                "encontrado": False,
                "perfil": None,
                "mensaje": "Error: el archivo data/carreras.json no contiene perfiles.",
            }

        consulta_normalizada = _normalizar_texto(consulta)

        for perfil in perfiles:
            id_normalizado = _normalizar_texto(perfil.get("id", ""))
            nombre_normalizado = _normalizar_texto(perfil.get("nombre", ""))

            coincide = (
                consulta_normalizada == id_normalizado
                or consulta_normalizada in nombre_normalizado
            )
            if coincide:
                return {
                    "encontrado": True,
                    "perfil": perfil,
                    "mensaje": f"Perfil '{perfil.get('nombre')}' encontrado correctamente.",
                }

        ids_disponibles = ", ".join(p.get("id", "") for p in perfiles)
        return {
            "encontrado": False,
            "perfil": None,
            "mensaje": (
                f"No se encontró ningún perfil vocacional que coincida con '{consulta}'. "
                f"Los perfiles disponibles son: {ids_disponibles}."
            ),
        }

    except FileNotFoundError:
        return {
            "encontrado": False,
            "perfil": None,
            "mensaje": f"Error: no se encontró el archivo de datos en {_RUTA_CARRERAS}.",
        }
    except json.JSONDecodeError:
        return {
            "encontrado": False,
            "perfil": None,
            "mensaje": "Error: el archivo data/carreras.json tiene un formato JSON inválido.",
        }
    except KeyError as error:
        return {
            "encontrado": False,
            "perfil": None,
            "mensaje": f"Error: falta el campo {error} en uno de los perfiles del JSON.",
        }
    except Exception as error:
        return {
            "encontrado": False,
            "perfil": None,
            "mensaje": f"Error inesperado al consultar el perfil vocacional: {error}",
        }
