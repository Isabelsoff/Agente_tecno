# Agente Académico de Orientación Vocacional - TecnoChilds

Microservicio en **Python + FastAPI** que utiliza el modelo **Gemini** (SDK `google-genai`)
para procesar los resultados del test vocacional de TecnoChilds y devolver
recomendaciones de carreras personalizadas para cada estudiante.

## Estructura del proyecto

```
agente_tecnochilds/
├── app.py                  # Servidor FastAPI (puerto 5000)
├── config/
│   └── settings.py         # Carga de variables de entorno (.env)
├── core/
│   ├── agent.py            # Lógica de interacción con Gemini
│   └── state.py            # Esquemas Pydantic (request/response)
├── tools/
│   └── carreras_tool.py    # Carga de data/carreras.json
├── data/
│   └── carreras.json       # 4 perfiles vocacionales y carreras sugeridas
├── .env                    # Variables de entorno (NO subir al repo)
├── .gitignore
├── requirements.txt
└── README.md
```

## Requisitos previos

- Python 3.10 o superior
- Una API Key de Gemini (Google AI Studio): https://aistudio.google.com/app/apikey

## Instrucciones de instalación y ejecución

### 1. Ubicarse en la carpeta del proyecto

```bash
cd agente_tecnochilds
```

### 2. Crear y activar un entorno virtual (recomendado)

En Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

En Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la API Key de Gemini

Abre el archivo `.env` y reemplaza el valor de ejemplo por tu clave real:

```
GEMINI_API_KEY=tu_clave_de_api_de_gemini_aqui
```

### 5. Levantar el servidor

```bash
python app.py
```

O, de forma equivalente, usando uvicorn directamente:

```bash
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

El servicio quedará disponible en:

```
http://localhost:5000
```

Documentación interactiva (Swagger UI) generada automáticamente por FastAPI:

```
http://localhost:5000/docs
```

## Endpoint principal

### `POST /api/orientar`

Recibe los puntajes del test vocacional del estudiante y devuelve
el perfil dominante, un mensaje motivador y carreras recomendadas.

**Ejemplo de body (JSON):**

```json
{
  "nombre_estudiante": "Valentina",
  "edad": 16,
  "puntajes": {
    "cientifico_tecnologico": 32,
    "artistico_creativo": 18,
    "social_humanistico": 20,
    "practico_tecnico": 15
  }
}
```

**Ejemplo de respuesta:**

```json
{
  "perfil_dominante": "Científico-Tecnológico",
  "mensaje_motivador": "Valentina, tu curiosidad y pensamiento lógico son un gran motor...",
  "carreras_recomendadas": [
    {
      "nombre": "Ingeniería en Inteligencia Artificial",
      "justificacion": "Tu perfil analítico encaja con el diseño de sistemas inteligentes."
    }
  ],
  "resumen_perfiles": {
    "cientifico_tecnologico": 32,
    "artistico_creativo": 18,
    "social_humanistico": 20,
    "practico_tecnico": 15
  }
}
```

### Probar el endpoint con `curl`

```bash
curl -X POST http://localhost:5000/api/orientar \
  -H "Content-Type: application/json" \
  -d '{
    "nombre_estudiante": "Valentina",
    "edad": 16,
    "puntajes": {
      "cientifico_tecnologico": 32,
      "artistico_creativo": 18,
      "social_humanistico": 20,
      "practico_tecnico": 15
    }
  }'
```

## Notas

- El archivo `.env` está excluido del control de versiones mediante `.gitignore`;
  nunca subas tu API Key real a un repositorio público.
- Este microservicio es independiente del backend actual de TecnoChilds
  (Node.js + Express); puede correr en paralelo, en el puerto `5000`,
  y ser consumido por el frontend como un servicio adicional de IA.
