"""
Lógica del Agente Académico de Orientación Vocacional de TecnoChilds.
Usa el SDK oficial `google-genai` para interactuar con el modelo Gemini.
"""

import json
import re

from google import genai
from google.genai import types

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

from config.settings import settings
from core.state import TestVocacionalRequest, OrientacionResponse, CarreraSugerida
from tools.carreras_tool import listar_perfiles, consultar_perfil_vocacional

# Mapeo entre los campos del request (snake_case) y los ids usados en carreras.json
_MAPA_PERFILES = {
    "cientifico_tecnologico": "cientifico_tecnologico",
    "artistico_creativo": "artistico_creativo",
    "social_humanistico": "social_humanistico",
    "practico_tecnico": "practico_tecnico",
}

# System Prompt: define el rol y el tono del agente frente a Gemini
SYSTEM_PROMPT = """
Eres el Agente Académico de Orientación Vocacional de TecnoChilds, una plataforma
que ayuda a adolescentes y jóvenes a descubrir su camino profesional.

Tu rol:
- Eres un orientador vocacional cálido, motivador y cercano, que habla con
  jóvenes de forma clara, positiva y sin tecnicismos innecesarios.
- Nunca eres condescendiente ni genérico: tus mensajes deben sentirse
  personalizados según el perfil y las carreras que se te entreguen.
- Tu objetivo es inspirar confianza en el estudiante sobre su potencial,
  sin prometerle un futuro garantizado ni desanimarlo respecto a otras opciones.

Instrucciones estrictas de formato:
- SIEMPRE debes responder ÚNICAMENTE con un JSON válido, sin texto adicional,
  sin comentarios y sin bloques de markdown (nada de ```json).
- El JSON debe tener exactamente esta forma:

{
  "mensaje_motivador": "string, 2 a 4 frases, tono motivador y personalizado",
  "carreras_recomendadas": [
    {"nombre": "string", "justificacion": "string, 1 a 2 frases"}
  ]
}

- "carreras_recomendadas" debe incluir entre 3 y 5 carreras, tomadas SOLO
  de la lista de carreras sugeridas que se te entrega en el mensaje del usuario.
- No inventes carreras que no estén en la lista entregada.
""".strip()


def _construir_prompt_usuario(request: TestVocacionalRequest, perfil_dominante: dict) -> str:
    """
    Arma el mensaje de usuario que se envía a Gemini, incluyendo
    el contexto del estudiante y las carreras disponibles para su perfil.
    """
    carreras_disponibles = ", ".join(perfil_dominante["carreras_sugeridas"])

    return f"""
Estudiante: {request.nombre_estudiante}
Edad: {request.edad if request.edad else "no especificada"}

Perfil vocacional dominante: {perfil_dominante["nombre"]}
Descripción del perfil: {perfil_dominante["descripcion"]}

Carreras sugeridas disponibles para este perfil:
{carreras_disponibles}

Genera el mensaje motivador y selecciona entre 3 y 5 carreras de la lista
anterior para recomendar a este estudiante, siguiendo el formato JSON indicado.
""".strip()


def _extraer_json(texto: str) -> dict:
    """
    Extrae un objeto JSON de la respuesta cruda del modelo, por si Gemini
    llegara a envolverlo en bloques de markdown pese a las instrucciones.
    """
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```json\s*|^```\s*|```$", "", texto_limpio, flags=re.MULTILINE).strip()

    match = re.search(r"\{.*\}", texto_limpio, re.DOTALL)
    if not match:
        raise ValueError("La respuesta del modelo no contiene un JSON válido")

    return json.loads(match.group(0))


def _determinar_perfil_dominante(request: TestVocacionalRequest) -> tuple[str, dict]:
    """
    Calcula qué perfil vocacional tiene el puntaje más alto y devuelve
    su id junto con la información completa del perfil (desde carreras.json).
    """
    puntajes = request.puntajes.model_dump()
    perfil_id_dominante = max(puntajes, key=puntajes.get)

    perfiles = listar_perfiles()
    perfil_info = next((p for p in perfiles if p["id"] == perfil_id_dominante), None)

    if perfil_info is None:
        raise ValueError(
            f"No se encontró el perfil '{perfil_id_dominante}' en data/carreras.json"
        )

    return perfil_id_dominante, perfil_info


def generar_orientacion(request: TestVocacionalRequest) -> OrientacionResponse:
    """
    Punto de entrada principal del agente: recibe los puntajes del test,
    determina el perfil dominante, consulta a Gemini y arma la respuesta
    final para el frontend de TecnoChilds.
    """
    settings.validate()

    _, perfil_info = _determinar_perfil_dominante(request)

    cliente = genai.Client(api_key=settings.GEMINI_API_KEY)

    prompt_usuario = _construir_prompt_usuario(request, perfil_info)

    respuesta = cliente.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt_usuario,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.8,
            response_mime_type="application/json",
        ),
    )

    datos_generados = _extraer_json(respuesta.text)

    carreras_recomendadas = [
        CarreraSugerida(nombre=c["nombre"], justificacion=c["justificacion"])
        for c in datos_generados.get("carreras_recomendadas", [])
    ]

    resumen_perfiles = request.puntajes.model_dump()

    return OrientacionResponse(
        perfil_dominante=perfil_info["nombre"],
        mensaje_motivador=datos_generados.get("mensaje_motivador", ""),
        carreras_recomendadas=carreras_recomendadas,
        resumen_perfiles=resumen_perfiles,
    )


# =============================================================================
# ARQUITECTURA CONVERSACIONAL: Prompt + Orquestador (LLM + Tools) + Memoria
#
# Todo lo de abajo es un agente conversacional, separado de
# generar_orientacion() (que hace una sola llamada directa a Gemini sin
# herramientas ni memoria). Aquí el modelo decide por sí mismo cuándo llamar
# a consultar_perfil_vocacional, razona en varios pasos (agent_scratchpad)
# y mantiene memoria de la conversación por session_id.
# =============================================================================


# -----------------------------------------------------------------------
# 1) GESTIÓN DEL PROMPT
# -----------------------------------------------------------------------

SYSTEM_PROMPT_ORIENTADOR_TECNOLOGICO = """
Eres el Orientador Vocacional Tecnológico de TecnoChilds, un agente experto
en guiar a adolescentes y jóvenes (12 a 19 años) hacia carreras que encajen
con su perfil vocacional.

Tono y estilo:
- Cálido, cercano, motivador y siempre en español. Hablas directo con el
  estudiante, como un mentor de confianza.
- Claro y sin tecnicismos innecesarios; si usas un término técnico, lo
  explicas brevemente.
- Nunca condescendiente ni genérico: adaptas cada respuesta al estudiante
  y a los datos reales de su perfil, no a plantillas.

Regla OBLIGATORIA de uso de herramientas:
- SIEMPRE debes llamar a la herramienta `consultar_perfil_vocacional` antes
  de sugerir cualquier carrera, aunque creas conocer la respuesta. Nunca
  inventes carreras, descripciones de perfiles ni datos que no vengan de
  esa herramienta.
- Si la herramienta devuelve "encontrado": false, dile al estudiante que no
  reconoces ese perfil y ofrécele los perfiles disponibles que te haya
  indicado la herramienta en su "mensaje", en vez de inventar uno.
- Si el estudiante aún no mencionó su perfil vocacional, pregúntale primero
  cuál es (o qué le gusta/se le da bien) antes de llamar a la herramienta.

Memoria:
- Tienes acceso al historial de la conversación (chat_history). Úsalo para
  no repetir preguntas ya respondidas ni pedir de nuevo datos que el
  estudiante ya te dio en turnos anteriores.
""".strip()


def construir_prompt_orientador_tecnologico() -> ChatPromptTemplate:
    """
    Arma el ChatPromptTemplate del Orientador Vocacional Tecnológico, con
    los placeholders necesarios para el agente:

    - "input": el mensaje actual del estudiante.
    - "chat_history": el historial de mensajes previos de la sesión,
      inyectado automáticamente por RunnableWithMessageHistory en cada turno.
    - "agent_scratchpad": el espacio donde el agente anota sus pasos lógicos
      (llamadas a herramientas y resultados intermedios). Es obligatorio
      para que create_tool_calling_agent funcione.
    """
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT_ORIENTADOR_TECNOLOGICO),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )


# -----------------------------------------------------------------------
# 2) ORQUESTADOR: inicializar LLM, vincular tools y armar el AgentExecutor
# -----------------------------------------------------------------------

def _inicializar_llm():
    """
    Inicializa el LLM que usará el agente conversacional.

    Por defecto usa Gemini (langchain_google_genai), para reutilizar la
    GEMINI_API_KEY que ya tienes configurada en config/settings.py y .env.
    Si prefieres usar OpenAI o Anthropic como pide el enunciado, esta es la
    ÚNICA función que necesitas cambiar; el resto del agente (prompt, tools,
    memoria) queda igual. Ejemplos equivalentes:

        # OpenAI (requiere `pip install langchain-openai` y OPENAI_API_KEY):
        # from langchain_openai import ChatOpenAI
        # return ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        # Anthropic (requiere `pip install langchain-anthropic` y ANTHROPIC_API_KEY):
        # from langchain_anthropic import ChatAnthropic
        # return ChatAnthropic(model="claude-sonnet-4-5", temperature=0.7)
    """
    from langchain_google_genai import ChatGoogleGenerativeAI

    settings.validate()

    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.7,
    )


def construir_agent_executor() -> AgentExecutor:
    """
    Ensambla el agente conversacional completo:

    1. Inicializa el LLM (_inicializar_llm).
    2. Declara las herramientas disponibles y las vincula al LLM con
       `llm.bind_tools`, para que el modelo sepa qué puede invocar y con
       qué firma.
    3. Arma el agente con `create_tool_calling_agent` (combina el LLM, las
       tools y el prompt) y lo envuelve en un `AgentExecutor`, que es quien
       ejecuta el ciclo completo: pensar -> llamar herramienta -> observar
       el resultado -> repetir si hace falta -> responder al estudiante.
    """
    llm = _inicializar_llm()

    # Herramientas disponibles para el agente. Para sumar más a futuro,
    # solo agrégalas a esta lista.
    herramientas = [consultar_perfil_vocacional]

    # Vinculamos las tools al LLM explícitamente para dejar el paso a la
    # vista (create_tool_calling_agent hace este mismo bind internamente
    # al recibir `herramientas`, así que esta línea es ilustrativa/no se
    # usa para construir el agente de abajo).
    _llm_con_herramientas = llm.bind_tools(herramientas)  # noqa: F841

    prompt = construir_prompt_orientador_tecnologico()

    agente = create_tool_calling_agent(llm, herramientas, prompt)

    return AgentExecutor(
        agent=agente,
        tools=herramientas,
        verbose=True,
        handle_parsing_errors=True,
    )


# -----------------------------------------------------------------------
# 3) MEMORIA Y ESTADO: historial persistente por sesión
# -----------------------------------------------------------------------

# session_id -> historial de mensajes de esa sesión, en memoria del proceso.
# Se pierde si el servidor se reinicia y no se comparte entre instancias.
# Para producción, reemplaza este diccionario por una base de datos externa
# (Redis, Postgres, etc.), manteniendo la misma firma de obtener_historial().
_HISTORIALES_SESION: dict[str, BaseChatMessageHistory] = {}


def obtener_historial(session_id: str) -> BaseChatMessageHistory:
    """
    Devuelve el historial de mensajes de una sesión, creándolo vacío si es
    la primera vez que se conversa con ese session_id.

    RunnableWithMessageHistory invoca esta función automáticamente en cada
    turno (recibe el session_id desde `config`) para leer el historial
    existente y luego agregarle el nuevo mensaje y la respuesta del agente.
    """
    if session_id not in _HISTORIALES_SESION:
        _HISTORIALES_SESION[session_id] = InMemoryChatMessageHistory()
    return _HISTORIALES_SESION[session_id]


def construir_agente_con_memoria() -> RunnableWithMessageHistory:
    """
    Envuelve el AgentExecutor con RunnableWithMessageHistory: la solución
    de memoria recomendada actualmente en LangChain (reemplaza a las clases
    ConversationBufferMemory, ya deprecadas). Con esto, cada llamada queda
    asociada a un session_id y el historial se lee/actualiza automáticamente.
    """
    agent_executor = construir_agent_executor()

    return RunnableWithMessageHistory(
        agent_executor,
        obtener_historial,
        input_messages_key="input",
        history_messages_key="chat_history",
    )


def conversar(session_id: str, mensaje: str) -> str:
    """
    Punto de entrada del agente conversacional: envía un mensaje del
    estudiante al Orientador Vocacional Tecnológico, manteniendo memoria
    automática de la sesión, y devuelve su respuesta en texto plano.

    Ejemplo de uso:
        respuesta = conversar(
            session_id="estudiante_123",
            mensaje="Hola, mi perfil dominante es científico-tecnológico",
        )
    """
    agente_con_memoria = construir_agente_con_memoria()

    resultado = agente_con_memoria.invoke(
        {"input": mensaje},
        config={"configurable": {"session_id": session_id}},
    )

    # AgentExecutor siempre devuelve un dict con la clave "output"
    return resultado["output"]
