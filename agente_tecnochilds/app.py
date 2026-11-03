import uuid
from pathlib import Path

import streamlit as st
from langchain_core.messages import HumanMessage

from core.agent import app_vocacional
from core.errores import clasificar_error_modelo
from core.graph import extraer_texto_respuesta, generar_respuesta_api
from core.metrics import MetricasCallback, ultima_metrica

# Ruta base del proyecto: funciona igual en Windows y en Streamlit Cloud (Linux)
BASE_DIR = Path(__file__).resolve().parent
RUTA_LOGO = BASE_DIR / "tecnoimg.png"

st.set_page_config(
    page_title="TecnoChilds - Agente Vocacional",
    page_icon="🎓",
    layout="centered",
)

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "historial" not in st.session_state:
    st.session_state.historial = []
if "ultimo_resultado" not in st.session_state:
    st.session_state.ultimo_resultado = None


def nueva_consulta() -> None:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.historial = []
    st.session_state.ultimo_resultado = None


def mostrar_error(error: Exception) -> None:
    categoria = clasificar_error_modelo(error)
    if categoria == "429":
        st.error(
            "Se agotó la cuota diaria del modelo. Intenta más tarde "
            "o cambia GEMINI_MODEL en el .env."
        )
    elif categoria == "504":
        st.error("El modelo tardó demasiado, intenta de nuevo")
    else:
        st.error(f"Ocurrió un error durante el procesamiento: {error}")


def renderizar_metricas_sidebar() -> None:
    with st.sidebar:
        st.subheader("Observabilidad")
        st.caption(f"thread_id: `{st.session_state.thread_id}`")
        try:
            registro = ultima_metrica(st.session_state.thread_id)
        except (OSError, ValueError) as error:
            st.error(f"No se pudieron leer las métricas: {error}")
            return

        if registro is None:
            st.caption("Aún no hay métricas para esta consulta.")
            return

        metricas = registro.get("metricas", {})
        tokens = metricas.get("tokens", {})
        st.metric("Tiempo de respuesta", f"{metricas.get('tiempo_total_segundos', 0)} s")
        st.metric("Tokens totales", tokens.get("total", 0))
        st.metric("Llamadas al modelo", metricas.get("llamadas_modelo", 0))
        herramientas = metricas.get("herramientas", [])
        if herramientas:
            st.write("**Herramientas usadas**")
            for herramienta in herramientas:
                st.write(
                    f"- {herramienta.get('nombre', 'desconocida')}: "
                    f"{herramienta.get('duracion_segundos', 0)} s"
                )
        else:
            st.write("**Herramientas usadas:** ninguna")
        if registro.get("estado") == "error":
            st.warning("La última ejecución terminó con error.")


with st.sidebar:
    if st.button("Nueva consulta", type="secondary"):
        nueva_consulta()
        st.rerun()

renderizar_metricas_sidebar()

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    # Si la imagen no existe en el servidor, la app sigue funcionando sin logo
    if RUTA_LOGO.exists():
        st.image(str(RUTA_LOGO), width=220)

st.title("🎓 Agente de Orientación Vocacional")
st.markdown(
    "Ingresa los resultados del test de tu estudiante para obtener un análisis "
    "personalizado impulsado por IA."
)

with st.form("test_form"):
    nombre = st.text_input("Nombre del estudiante", placeholder="Ej. Juan Pérez")
    st.subheader("Puntajes del Test")
    col1, col2 = st.columns(2)
    with col1:
        pt_cientifico = st.number_input(
            "Científico-Tecnológico", min_value=0, max_value=100, value=85
        )
        pt_artistico = st.number_input(
            "Artístico-Creativo", min_value=0, max_value=100, value=40
        )
    with col2:
        pt_social = st.number_input(
            "Social-Humanístico", min_value=0, max_value=100, value=30
        )
        pt_practico = st.number_input(
            "Práctico-Técnico", min_value=0, max_value=100, value=60
        )
    submitted = st.form_submit_button("Generar Orientación", type="primary")

if submitted:
    if not nombre.strip():
        st.warning("⚠️ Por favor ingresa el nombre del estudiante.")
    else:
        mensaje_usuario = f"""
El estudiante {nombre} terminó su test. Obtuvo estos puntajes:
- Científico-Tecnológico: {pt_cientifico}
- Artístico-Creativo: {pt_artistico}
- Social-Humanístico: {pt_social}
- Práctico-Técnico: {pt_practico}

Dime su perfil dominante, dale un mensaje motivador y recomiéndale carreras.
"""
        metricas = MetricasCallback(
            thread_id=st.session_state.thread_id,
            entrada_resumida="Consulta inicial de orientación vocacional con puntajes.",
        )
        config = {
            "configurable": {"thread_id": st.session_state.thread_id},
            "recursion_limit": 10,
            "callbacks": [metricas],
        }
        try:
            respuesta_agente = app_vocacional.invoke(
                {
                    "messages": [HumanMessage(content=mensaje_usuario)],
                    "ruta": "herramientas",
                },
                config=config,
            )
            metricas.set_state_steps(respuesta_agente.get("pasos_ejecutados"))
            texto_crudo = extraer_texto_respuesta(
                respuesta_agente["messages"][-1].content
            )
            resultado_final = generar_respuesta_api(
                texto_crudo,
                callback=metricas,
            )
            resultado_final = resultado_final.model_copy(
                update={
                    "resumen_perfiles": {
                        "Científico": pt_cientifico,
                        "Artístico": pt_artistico,
                        "Social": pt_social,
                        "Práctico": pt_practico,
                    }
                }
            )
            metricas.finish("ok")
            st.session_state.ultimo_resultado = resultado_final
            st.session_state.historial = [
                {
                    "role": "user",
                    "content": (
                        f"Completé el test vocacional: científico {pt_cientifico}, "
                        f"artístico {pt_artistico}, social {pt_social} y "
                        f"práctico {pt_practico}."
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        f"**Perfil dominante: {resultado_final.perfil_dominante}**\n\n"
                        f"{resultado_final.mensaje_motivador}\n\n"
                        "**Carreras recomendadas**\n"
                        + "\n".join(
                            f"- **{carrera.nombre}:** {carrera.justificacion}"
                            for carrera in resultado_final.carreras_recomendadas
                        )
                    ),
                },
            ]
        except Exception as error:
            metricas.finish("error")
            mostrar_error(error)
        renderizar_metricas_sidebar()

if st.session_state.ultimo_resultado is not None:
    st.success("¡Análisis completado con éxito!")
    for mensaje in st.session_state.historial:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    pregunta = st.chat_input("Escribe tu pregunta de seguimiento...")
    if pregunta:
        st.session_state.historial.append({"role": "user", "content": pregunta})
        with st.chat_message("user"):
            st.write(pregunta)
        metricas = MetricasCallback(
            thread_id=st.session_state.thread_id,
            entrada_resumida="Pregunta de seguimiento sobre orientación vocacional.",
        )
        config = {
            "configurable": {"thread_id": st.session_state.thread_id},
            "recursion_limit": 10,
            "callbacks": [metricas],
        }
        try:
            respuesta = app_vocacional.invoke(
                {
                    "messages": [HumanMessage(content=pregunta)],
                    "ruta": None,
                },
                config=config,
            )
            metricas.set_state_steps(respuesta.get("pasos_ejecutados"))
            texto_respuesta = extraer_texto_respuesta(
                respuesta["messages"][-1].content
            )
            st.session_state.historial.append(
                {"role": "assistant", "content": texto_respuesta}
            )
            metricas.finish("ok")
            st.rerun()
        except Exception as error:
            metricas.finish("error")
            mostrar_error(error)
        renderizar_metricas_sidebar()