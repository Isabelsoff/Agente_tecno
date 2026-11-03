import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

candidatos = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-3.8-flash",
]

for nombre in candidatos:
    try:
        llm = ChatGoogleGenerativeAI(
            model=nombre,
            google_api_key=os.getenv("GEMINI_API_KEY"),
            timeout=30,
            max_retries=0,
        )
        respuesta = llm.invoke("Responde solo: ok")
        print(nombre, "->", respuesta.content)
    except Exception as e:
        print(nombre, "-> ERROR:", str(e)[:150])