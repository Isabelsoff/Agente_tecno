import streamlit as st

from config.settings import validar_configuracion
from core.agent import responder
from core.state import (
    actualizar_estado_estudiante,
    agregar_mensaje,
    inicializar_estado,
    obtener_memoria,
    reiniciar_estado,
)

st.set_page_config(page_title="TecnoChilds - Agente Vocacional", page_icon="🎓")

try:
    validar_configuracion()
except ValueError as error:
    st.error(str(error))
    st.stop()

inicializar_estado()

st.title("🎓 TecnoChilds")
st.caption("Orientador Vocacional Inteligente")

with st.sidebar:
    st.subheader("Perfil del Estudiante")
    estudiante = st.session_state.estudiante
    st.write("**Nombre:**", estudiante["nombre"])
    st.write("**Perfil:**", estudiante["perfil_vocacional"])
    st.divider()
    if st.button("Reiniciar conversación"):
        reiniciar_estado()
        st.rerun()

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

prompt = st.chat_input("Escribe sobre tus gustos o pregunta por carreras...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    actualizar_estado_estudiante(prompt)
    agregar_mensaje("user", prompt)

    try:
        respuesta = responder(
            mensaje_usuario=prompt,
            estudiante=st.session_state.estudiante,
            memoria=obtener_memoria(),
        )
    except Exception as error:
        respuesta = f"Ocurrió un error: {error}"

    with st.chat_message("assistant"):
        st.markdown(respuesta)

    agregar_mensaje("assistant", respuesta)
    st.rerun()