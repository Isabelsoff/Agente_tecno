"""
Esquemas de Pydantic que definen los contratos de entrada y salida
del endpoint de orientación vocacional.
"""

from pydantic import BaseModel, Field, field_validator


class PuntajesPerfil(BaseModel):
    """
    Puntajes obtenidos por el estudiante en cada uno de los
    4 perfiles vocacionales de TecnoChilds.
    Se espera una escala numérica (por ejemplo 0-100 o 0-40,
    según la ponderación del test del frontend).
    """

    cientifico_tecnologico: float = Field(
        ..., ge=0, description="Puntaje del perfil Científico-Tecnológico"
    )
    artistico_creativo: float = Field(
        ..., ge=0, description="Puntaje del perfil Artístico-Creativo"
    )
    social_humanistico: float = Field(
        ..., ge=0, description="Puntaje del perfil Social-Humanístico"
    )
    practico_tecnico: float = Field(
        ..., ge=0, description="Puntaje del perfil Práctico-Técnico"
    )


class TestVocacionalRequest(BaseModel):
    """
    Cuerpo de la petición que envía el frontend de TecnoChilds
    al finalizar el test vocacional.
    """

    nombre_estudiante: str = Field(
        ..., min_length=1, description="Nombre del estudiante que realizó el test"
    )
    edad: int | None = Field(
        default=None, ge=10, le=25, description="Edad del estudiante (opcional)"
    )
    puntajes: PuntajesPerfil = Field(
        ..., description="Puntajes obtenidos en cada perfil vocacional"
    )

    @field_validator("nombre_estudiante")
    @classmethod
    def nombre_no_vacio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("El nombre del estudiante no puede estar vacío")
        return valor.strip()


class CarreraSugerida(BaseModel):
    """Representa una carrera sugerida dentro de la respuesta."""

    nombre: str
    justificacion: str


class OrientacionResponse(BaseModel):
    """
    Estructura de la respuesta que el microservicio devuelve al frontend
    tras procesar el test con el Agente de Orientación Vocacional.
    """

    perfil_dominante: str = Field(
        ..., description="Nombre del perfil vocacional con mayor puntaje"
    )
    mensaje_motivador: str = Field(
        ..., description="Mensaje generado por Gemini, en tono motivador para el estudiante"
    )
    carreras_recomendadas: list[CarreraSugerida] = Field(
        ..., description="Listado de carreras recomendadas con su justificación"
    )
    resumen_perfiles: dict[str, float] = Field(
        ..., description="Puntajes normalizados de los 4 perfiles, para graficar en el frontend"
    )
