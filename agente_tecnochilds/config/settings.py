"""
Configuración global del microservicio Agente Académico de Orientación Vocacional.
Carga las variables de entorno desde el archivo .env usando python-dotenv.
"""

import os
from dotenv import load_dotenv

# Carga las variables definidas en el archivo .env hacia el entorno del proceso
load_dotenv()


class Settings:
    """
    Contenedor centralizado de la configuración de la aplicación.
    """

    # Clave de la API de Gemini, obtenida desde el archivo .env
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Modelo de Gemini que usará el agente
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Puerto en el que correrá el servidor FastAPI
    APP_PORT: int = int(os.getenv("APP_PORT", "5000"))

    # Host del servidor
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")

    def validate(self) -> None:
        """
        Valida que las variables de entorno críticas estén presentes.
        Lanza un error explícito si falta la API Key, para evitar
        fallos silenciosos al llamar a Gemini.
        """
        if not self.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY no está definida. "
                "Verifica que el archivo .env exista y contenga la variable "
                "GEMINI_API_KEY=tu_clave_aqui"
            )


# Instancia única de configuración, importada por el resto del proyecto
settings = Settings()
