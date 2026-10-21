import streamlit as st
import uuid
from langchain_core.messages import HumanMessage

# Importamos nuestro agente y el formateador que creamos
from core.agent import app_vocacional
from core.graph import generar_respuesta_api

# Configuración básica de la página
st.set_page_config(page_title="TecnoChilds - Agente Vocacional", page_icon="🎓", layout="centered")

# --- LOGO DE TECNOCHILDS ---
# Usamos columnas para centrar la imagen. La columna 2 es la del medio.
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
   
    st.image("tecnoimg.png", width=220)

st.title("🎓 Agente de Orientación Vocacional")
st.markdown("Ingresa los resultados del test de tu estudiante para obtener un análisis personalizado impulsado por IA.")

# --- Formulario de entrada ---
with st.form("test_form"):
    nombre = st.text_input("Nombre del estudiante", placeholder="Ej. Juan Pérez")
    
    st.subheader("Puntajes del Test")
    col1, col2 = st.columns(2)
    with col1:
        pt_cientifico = st.number_input("Científico-Tecnológico", min_value=0, max_value=100, value=85)
        pt_artistico = st.number_input("Artístico-Creativo", min_value=0, max_value=100, value=40)
    with col2:
        pt_social = st.number_input("Social-Humanístico", min_value=0, max_value=100, value=30)
        pt_practico = st.number_input("Práctico-Técnico", min_value=0, max_value=100, value=60)
        
    submitted = st.form_submit_button("Generar Orientación", type="primary")

# --- Lógica de procesamiento ---
if submitted:
    if not nombre.strip():
        st.warning("⚠️ Por favor ingresa el nombre del estudiante.")
    else:
        with st.spinner("🧠 Analizando perfil y consultando base de datos de carreras..."):
            
            # 1. Armamos el mensaje (Prompt) con los datos del formulario
            mensaje_usuario = f"""
            El estudiante {nombre} terminó su test. Obtuvo estos puntajes:
            - Científico-Tecnológico: {pt_cientifico}
            - Artístico-Creativo: {pt_artistico}
            - Social-Humanístico: {pt_social}
            - Práctico-Técnico: {pt_practico}

            Dime su perfil dominante, dale un mensaje motivador y recomiéndale carreras.
            """
            
            try:
                # 2. Ejecutamos nuestro grafo de LangGraph
                # Usamos uuid para generar una sesión única cada vez que se presiona el botón
                config = {"configurable": {"thread_id": str(uuid.uuid4())}}
                respuesta_agente = app_vocacional.invoke(
                    {"messages": [HumanMessage(content=mensaje_usuario)]}, 
                    config=config
                )
                texto_crudo = respuesta_agente["messages"][-1].content
                
                # 3. Pasamos el texto crudo por el estructurador de Pydantic
                resultado_final = generar_respuesta_api(texto_crudo)
                
                # --- Visualización de los Resultados ---
                st.success("¡Análisis completado con éxito!")
                
                st.header(f"🌟 Perfil Dominante: {resultado_final.perfil_dominante}")
                
                st.subheader("Carta para el estudiante")
                st.info(resultado_final.mensaje_motivador)
                
                st.subheader("📚 Carreras Recomendadas")
                # Iteramos sobre las carreras recomendadas (que gracias a Pydantic, sabemos que es una lista de objetos)
                for carrera in resultado_final.carreras_recomendadas:
                    with st.expander(f"**{carrera.nombre}**", expanded=True):
                        st.write(carrera.justificacion)
                        
            except Exception as e:
                st.error(f"Ocurrió un error durante el procesamiento: {e}")