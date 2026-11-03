# Agente de Orientación Vocacional - TecnoChilds

Aplicación de orientación vocacional con Streamlit, LangGraph, LangChain y Gemini.
El grafo usa una herramienta local respaldada por `data/carreras.json`, un
checkpointer en memoria para el chat de seguimiento y callbacks que registran
métricas por ejecución.

## Requisitos e instalación

Se requiere Python 3.11 o superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Configuración

Crea `.env` en la raíz del proyecto. No compartas ni subas credenciales reales:

```dotenv
GEMINI_API_KEY=REEMPLAZAR_POR_TU_CLAVE
GEMINI_MODEL=gemini-3.5-flash-lite
```

`config/settings.py` carga el archivo antes de leer las variables. Las pruebas
automáticas usan un modelo falso y no requieren una clave ni consumen cuota.

## Ejecutar la aplicación

Desde la carpeta del proyecto:

```powershell
python -m streamlit run app.py
```

El botón **Nueva consulta** crea una conversación nueva. Las preguntas de
seguimiento reutilizan el mismo `thread_id` para conservar memoria.

## Pruebas automáticas

```powershell
python -m pytest -v
```

La suite simula el modelo; la prueba en vivo se omite de forma predeterminada.
Solo opta por ella expresamente con `RUN_LIVE=1` si deseas consumir cuota.

La salida de referencia está en [docs/evidencias/pytest_salida.txt](docs/evidencias/pytest_salida.txt)
y el informe de resultados en [docs/PRUEBAS.md](docs/PRUEBAS.md).

## Métricas

Las ejecuciones se agregan en `logs/metricas.jsonl`. Para regenerar el resumen:

```powershell
python scripts/resumen_metricas.py
```

Consulta el reporte en [docs/resumen_metricas.md](docs/resumen_metricas.md).
