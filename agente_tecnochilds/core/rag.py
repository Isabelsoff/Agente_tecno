import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config.settings import GEMINI_API_KEY

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROGRAMAS_PATH = _PROJECT_ROOT / "data" / "conocimiento" / "programas.jsonl"
INDEX_PATH = _PROJECT_ROOT / "data" / "indice" / "indice.json"
EMBEDDING_MODEL = "gemini-embedding-001"
MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.35"))

_embeddings: Embeddings | None = None


def obtener_embeddings() -> Embeddings:
    global _embeddings
    if _embeddings is None:
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "Falta GEMINI_API_KEY; configura la variable en el archivo .env."
            )
        _embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            api_key=GEMINI_API_KEY,
        )
    return _embeddings


def construir_indice() -> int:
    documentos: list[Document] = []
    campos_requeridos = {
        "id",
        "institucion",
        "programa",
        "perfil",
        "ciudad",
        "descripcion",
        "fuente_url",
        "fecha_verificacion",
        "estado_verificacion",
    }

    with PROGRAMAS_PATH.open("r", encoding="utf-8") as archivo:
        for numero_linea, linea in enumerate(archivo, start=1):
            if not linea.strip():
                continue
            try:
                registro: dict[str, Any] = json.loads(linea)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"JSON inválido en {PROGRAMAS_PATH}, línea {numero_linea}."
                ) from error
            if not isinstance(registro, dict) or not campos_requeridos.issubset(registro):
                raise ValueError(
                    f"Registro incompleto en {PROGRAMAS_PATH}, línea {numero_linea}."
                )
            texto = " ".join(
                str(registro[campo]).strip()
                for campo in ("institucion", "programa", "descripcion")
            )
            documentos.append(Document(page_content=texto, metadata=registro))

    if not documentos:
        raise ValueError(f"No hay programas para indexar en {PROGRAMAS_PATH}.")

    vectorstore = InMemoryVectorStore(embedding=obtener_embeddings())
    vectorstore.add_documents(documents=documentos)
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    vectorstore.dump(str(INDEX_PATH))
    cargar_indice.cache_clear()
    return len(documentos)


@lru_cache(maxsize=1)
def cargar_indice() -> InMemoryVectorStore:
    if not INDEX_PATH.is_file():
        raise FileNotFoundError(
            f"No existe el índice RAG en {INDEX_PATH}. "
            "Ejecuta `python scripts/construir_indice.py` para crearlo."
        )
    return InMemoryVectorStore.load(
        str(INDEX_PATH),
        embedding=obtener_embeddings(),
    )


def recuperar(
    consulta: str,
    k: int = 5,
    min_similarity: float | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(consulta, str) or not consulta.strip():
        return []
    if k <= 0:
        return []
    if min_similarity is None:
        min_similarity = MIN_SIMILARITY

    coincidencias = cargar_indice().similarity_search_with_score(
        consulta.strip(),
        k=k,
    )
    return [
        {
            "texto": documento.page_content,
            "metadatos": documento.metadata,
            "puntaje": float(puntaje),
        }
        for documento, puntaje in coincidencias
        if float(puntaje) >= min_similarity
    ]
