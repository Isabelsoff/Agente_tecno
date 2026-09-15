import re
import streamlit as st

ESTUDIANTE_INICIAL = {
    "nombre": "No registrado",
    "perfil_vocacional": "No registrado",
}

def inicializar_estado() -> None:
    if "estudiante" not in st.session_state:
        st.session_state.estudiante = ESTUDIANTE_INICIAL.copy()
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

def actualizar_estado_estudiante(texto: str) -> None:
    patron_nombre = r"(?:soy|me llamo)\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+)"
    coincidencia = re.search(patron_nombre, texto, re.IGNORECASE)
    if coincidencia:
        st.session_state.estudiante["nombre"] = coincidencia.group(1).capitalize()

    texto_lower = texto.lower()
    if "tecnología" in texto_lower or "programación" in texto_lower or "sistemas" in texto_lower:
        st.session_state.estudiante["perfil_vocacional"] = "Científico-Tecnológico"
    elif "diseño" in texto_lower or "arte" in texto_lower or "dibujar" in texto_lower:
        st.session_state.estudiante["perfil_vocacional"] = "Artístico-Creativo"
    elif "personas" in texto_lower or "enseñar" in texto_lower or "ayudar" in texto_lower:
        st.session_state.estudiante["perfil_vocacional"] = "Social-Humanístico"

def agregar_mensaje(role: str, content: str) -> None:
    st.session_state.mensajes.append({"role": role, "content": content})

def obtener_memoria(limite: int = 6) -> str:
    mensajes = st.session_state.mensajes[-limite:]
    return "\n".join(f"{m['role']}: {m['content']}" for m in mensajes)

def reiniciar_estado() -> None:
    st.session_state.mensajes = []
    st.session_state.estudiante = ESTUDIANTE_INICIAL.copy()