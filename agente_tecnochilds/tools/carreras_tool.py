import json
from pathlib import Path
from typing import TypedDict

class PerfilVocacional(TypedDict):
    perfil: str
    descripcion: str
    carreras: list[str]

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "carreras.json"

def consultar_carreras(consulta: str) -> list[PerfilVocacional]:
    """Busca perfiles vocacionales y carreras en el archivo JSON."""
    with DATA_FILE.open("r", encoding="utf-8") as archivo:
        carreras_db: list[PerfilVocacional] = json.load(archivo)

    criterio = consulta.lower().strip()
    resultados = []
    
    for item in carreras_db:
        coincide_perfil = criterio in item["perfil"].lower()
        coincide_carrera = any(criterio in c.lower() for c in item["carreras"])
        if coincide_perfil or coincide_carrera:
            resultados.append(item)

    return resultados