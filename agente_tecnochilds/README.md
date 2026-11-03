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

## RAG: programas académicos con fuentes

El componente RAG busca programas en `data/conocimiento/programas.jsonl`, con
un documento JSON por línea. Cada registro debe incluir institución, programa,
perfil, ciudad, descripción, URL de fuente, fecha y estado de verificación.
Las fuentes y sus estados se conservan en los metadatos de cada fragmento
recuperado y se entregan a la herramienta `buscar_programas_academicos`.

Para construir o reconstruir el índice local:

```powershell
python scripts/construir_indice.py
```

Este comando llama a la API de embeddings de Google usando
`gemini-embedding-001` y guarda el índice en `data/indice/indice.json`.
Constrúyelo manualmente cuando cambien los datos; no forma parte del arranque
ni de las pruebas automáticas. Las pruebas usan `DeterministicFakeEmbedding` y
archivos temporales, sin consumir cuota.

La recuperación entrega los cinco resultados de mayor similitud; el modelo
debe comprobar si corresponden a la carrera solicitada y descartar resultados
de otras carreras como "sin resultados". No se aplica un umbral de similitud
fijo. Si no hay datos relevantes, puede ofrecer un respaldo transparente bajo
**Información general (no verificada)**: solo instituciones muy conocidas de
la ciudad, aclarando que no están en la base verificada y que deben confirmarse
en sitios oficiales. En ese modo no debe dar costos, duración, acreditaciones,
requisitos, fechas ni detalles específicos. Si no conoce instituciones con
certeza, debe decirlo y dirigir al usuario a fuentes oficiales.

El índice no verifica en tiempo real que una fuente siga vigente ni cubre
instituciones o programas ausentes del JSONL. Revisa las fechas y estados de
verificación y confirma siempre la oferta y cualquier detalle específico en
sitios oficiales. La aplicación cita los resultados recuperados y advierte si
el registro indica fuente secundaria o posible desactualización; nunca debe
presentar resultados de otra carrera como respuesta.
