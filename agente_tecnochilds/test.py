from core.agent import app_vocacional
from core.graph import generar_respuesta_api
from langchain_core.messages import HumanMessage

config = {"configurable": {"thread_id": "sesion_test_api_1"}}

# Simulamos que el frontend nos manda los resultados del test
mensaje_usuario = """
El estudiante Juan terminó su test. Obtuvo estos puntajes:
- Científico-Tecnológico: 85
- Artístico-Creativo: 40
- Social-Humanístico: 30
- Práctico-Técnico: 60

Dime su perfil dominante, dale un mensaje motivador y recomiéndale 2 carreras.
"""

print("1. El agente está analizando los resultados...")
respuesta_agente = app_vocacional.invoke(
    {"messages": [HumanMessage(content=mensaje_usuario)]}, 
    config=config
)

texto_crudo = respuesta_agente["messages"][-1].content
print("\n2. Estructurando la respuesta para el frontend...")

# Pasamos el texto crudo por nuestro estructurador de Pydantic
respuesta_final_api = generar_respuesta_api(texto_crudo)

print("\n--- JSON FINAL PARA LA API ---")
# El model_dump_json() de Pydantic nos muestra el JSON perfecto
print(respuesta_final_api.model_dump_json(indent=2))