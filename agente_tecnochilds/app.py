"""
Punto de entrada del microservicio Agente Académico de Orientación Vocacional
de TecnoChilds. Expone un servidor FastAPI en el puerto 5000.
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from core.state import TestVocacionalRequest, OrientacionResponse
from core.agent import generar_orientacion

app = FastAPI(
    title="TecnoChilds - Agente Académico de Orientación Vocacional",
    description="Microservicio que procesa los resultados del test vocacional "
                 "y devuelve recomendaciones de carreras personalizadas usando Gemini.",
    version="1.0.0",
)

# Middleware de CORS habilitado para que el frontend web pueda
# consumir este microservicio sin bloqueos del navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def raiz():
    """Endpoint simple para verificar que el servicio está corriendo."""
    return {
        "servicio": "Agente Académico de Orientación Vocacional - TecnoChilds",
        "estado": "activo",
    }


@app.post("/api/orientar", response_model=OrientacionResponse)
def orientar_estudiante(request: TestVocacionalRequest):
    """
    Recibe los puntajes del test vocacional de un estudiante y devuelve
    el perfil dominante, un mensaje motivador y carreras recomendadas,
    generados por el Agente de Orientación Vocacional (Gemini).
    """
    try:
        return generar_orientacion(request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al generar la orientación vocacional: {error}",
        )


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,
    )
