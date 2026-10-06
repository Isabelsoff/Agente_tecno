"""
Interfaz de chat del Orientador Vocacional - TecnoChilds, hecha con Streamlit.
"""

import uuid

import streamlit as st

from core.agent import conversar

# --- 1. Configuración básica ---
st.title("Orientador Vocacional - TecnoChilds")

# --- 2. Estado de la sesión (memoria visual: lo que se ve en pantalla) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Id único por pestaña del navegador. Se lo pasamos al agente para que
# RunnableWithMessageHistory (core/agent.py) recuerde esta conversación.
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# --- 3. Renderizado del historial de chat ---
for mensaje in st.session_state.messages:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

# --- 4. Entrada del usuario ---
entrada_usuario = st.chat_input("Escribe tu duda aquí...")

if entrada_usuario:
    # Mostrar el mensaje del usuario y guardarlo en el historial visual
    st.session_state.messages.append({"role": "user", "content": entrada_usuario})
    with st.chat_message("user"):
        st.markdown(entrada_usuario)

    # --- 5. Conexión con el agente ---
    try:
        respuesta = conversar(
            session_id=st.session_state.session_id,
            mensaje=entrada_usuario,
        )
    except Exception as error:
        respuesta = f"Tuve un problema al responder: {error}"

    # Mostrar la respuesta del agente y guardarla en el historial visual
    st.session_state.messages.append({"role": "assistant", "content": respuesta})
    with st.chat_message("assistant"):
        st.markdown(respuesta)