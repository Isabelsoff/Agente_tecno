import os
from pathlib import Path
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


def _limpiar(valor: str | None) -> str:
    return (valor or "").strip().strip('"').strip("'").strip()


def _leer(nombre: str, defecto: str = "") -> str:
    valor = os.getenv(nombre)
    if not valor:
        try:
            import streamlit as st
            valor = st.secrets.get(nombre)
        except Exception:
            valor = None
    return _limpiar(valor) or defecto


GEMINI_API_KEY = _leer("GEMINI_API_KEY")
GEMINI_MODEL = _leer("GEMINI_MODEL", "gemini-3.5-flash-lite")
