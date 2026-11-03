# Pruebas automáticas y hallazgos

Evidencia real de la ejecución: [docs/evidencias/pytest_salida.txt](evidencias/pytest_salida.txt).
Se ejecutó `python -m pytest -v` con modelo simulado, `RUN_LIVE` desactivado y
`GEMINI_API_KEY` vacío dentro del proceso de pruebas.

| ID | Funcionalidad evaluada | Resultado esperado | Resultado obtenido | Estado | Hallazgo | Acción correctiva |
|---|---|---|---|---|---|---|
| T01 | LangChain Tools: 4 perfiles JSON, consulta inválida y vacía | Coincidencias devuelven string JSON con el perfil del archivo; inválidas no coinciden | 6 casos pasaron; la primera corrida encontró que `""` coincidía con el primer perfil | PASÓ tras corrección | La cadena vacía es subcadena de cualquier nombre | Rechazar consulta normalizada vacía antes de buscar |
| T02 | LangGraph: rutas, tool calls y arista condicional desde START | Rutas conceptual/herramientas/None se clasifican; presencia de tool calls enruta a herramienta | 3 pruebas pasaron; START tiene caminos compilados a `agente` y `enrutador` | PASÓ | Ninguno pendiente | Ninguna |
| T03 | LangGraph + Tools con modelo simulado | Recorrido `agente -> herramientas -> agente`; estado conserva `pasos_ejecutados` | 1 prueba pasó con respuesta simulada y consulta local a la herramienta | PASÓ | Ninguno pendiente | Ninguna |
| T04 | Memoria por thread_id | Mismo ID conserva el historial; distinto ID lo aísla | 1 prueba pasó: mensajes previos se conservan solo en el mismo hilo | PASÓ | Ninguno pendiente | Ninguna |
| T05 | Observabilidad/callbacks | Contar desde cero llamadas, tokens, herramienta, error y una línea JSONL | 1 prueba pasó; el archivo se escribió en `tmp_path`, sin modificar el log real | PASÓ | Ninguno pendiente | Ninguna |
| T06 | Errores Gemini 429/504 | Clasificar y persistir ambos tipos de error | 2 pruebas pasaron para `RESOURCE_EXHAUSTED` y `DEADLINE_EXCEEDED` | PASÓ | Ninguno pendiente | Ninguna |
| T07 | Esquema de respuesta | Rechazar campos requeridos incompletos y fijar las cuatro claves del resumen | 2 pruebas pasaron; claves exactas `Científico`, `Artístico`, `Social`, `Práctico` | PASÓ | Antes se aceptaban diccionarios con claves variables | Validador normaliza las claves y Streamlit rellena los puntajes reales |
| T08 | Texto multimodal de Gemini | Separar bloques de texto sin concatenar palabras | 2 pruebas pasaron para bloques y string simple | PASÓ | El extractor concatenaba con `""` (por ejemplo, `práctico` + `te`) | Unir bloques con espacios |
| T09 | Integración real opcional | Solo llamar a Gemini con `RUN_LIVE=1` | Saltada; la variable no estaba habilitada y no se usó clave | OMITIDA (intencional) | Prueba real consumiría cuota | Mantener desactivada para las corridas ordinarias |
| T10 | Importación de grafo sin credenciales | Importar módulos y usar modelo simulado sin exigir API key | La prueba de inicialización diferida pasó en la suite anterior | PASÓ | La inicialización global impedía recolectar tests sin credenciales | Inicializar Gemini de forma perezosa y fallar claramente solo ante una llamada real |
| T11 | Índice RAG y recuperación top-5 | Construir/cargar índice temporal y devolver cinco documentos con metadata y score | 3 pruebas con `DeterministicFakeEmbedding` verifican construcción/carga, top-5 y campos de cita | PASÓ | La búsqueda anterior usaba k=3 por defecto | Usar k=5 sin descartar por umbral fijo |
| T12 | Tool RAG: datos, índice ausente y consulta vacía | Devolver programa e institución en JSON y mensajes claros para ausencia de índice o consulta vacía | 2 pruebas usan índice temporal; ausencia y consulta vacía devuelven JSON válido | PASÓ | Ninguno pendiente | Preservar campos citables y errores de búsqueda claros |
| T13 | Política híbrida en prompts | Exigir coincidencia de carrera, fuente para resultados verificados y respaldo rotulado no verificado | Prueba inspecciona frases clave en ambos prompts | PASÓ | El agente se negaba a responder sobre carreras fuera del índice | Respaldo transparente rotulado como información no verificada |
| T14 | Tool RAG en grafo y métricas | El agente simulado llama a `buscar_programas_academicos` y métricas registran su nombre | 1 prueba pasó con llamada de herramienta simulada | PASÓ | La búsqueda universitaria no tenía recuperación con fuentes | Registrar la herramienta RAG junto a la tool vocacional existente |
| T15 | Integridad de los datos RAG | Cada línea es JSON, contiene los campos requeridos, ID único y perfil permitido | 1 prueba pasó; el archivo conserva 25 líneas válidas y no fue modificado | PASÓ | Ninguno pendiente | Mantener validación automática para cambios de datos |

**Resultado de la suite completa:** 26 pasaron, 1 omitida, 0 fallaron.
La salida completa está guardada en
[docs/evidencias/pytest_salida.txt](evidencias/pytest_salida.txt).

## Hallazgos y correcciones

- **Modelo configurado por entorno:** `GEMINI_MODEL` definido en `.env` tiene
  precedencia sobre el fallback de `settings.py`, por lo que un valor antiguo
  puede mantener un modelo no disponible aunque cambie el default. La
  configuración actual observada es `gemini-3.5-flash-lite`, que también queda
  como fallback del código. No se imprimió ni se modificó ninguna API key.
- **Cuota/tiempos de Gemini:** hubo respuestas 429 (cuota gratuita diaria) y
  504 con `gemini-3.8-flash`. La acción correctiva es usar
  `GEMINI_MODEL=gemini-3.5-flash-lite`; esta suite no realizó solicitudes reales,
  así que no afirma disponibilidad live del modelo.
- **Llamada de enrutamiento innecesaria:** el formulario siempre solicita
  carreras, por eso inicia con `ruta="herramientas"` y omite el enrutador.
  Para el camino que usa una herramienta, reduce el flujo habitual de unas 5 a
  3 llamadas (agente, agente tras herramienta y estructurador). Los seguimientos
  mantienen `ruta=None` para que el enrutador pueda clasificar la nueva pregunta.
- **Texto motivador sin espacios y resumen variable:** la extracción ya separa
  bloques con espacios (T08); el esquema fija las claves y la UI inserta los
  puntajes del formulario (T07). Esto evita fragmentos pegados como
  `prácticote`/`ungran` y nombres de claves inconsistentes.
- **Datos de universidades sin fuente verificada:** el modelo podía contestar
  desde conocimiento general como si fuera información actual. Se ajustó el
  prompt conceptual para indicar que la información universitaria debe
  verificarse en el sitio oficial y no inventar detalles. No se probó una
  respuesta live ni se añadieron herramientas de navegación. Hallazgo:
  **universidades inventadas -> RAG con fuentes verificables**; la nueva
  herramienta cita los registros disponibles y advierte sobre estado o vigencia.
- **El agente se negaba a responder sobre carreras fuera del índice:** acción:
  **respaldo transparente rotulado como información no verificada**. El modelo
  debe filtrar resultados de otras carreras y, cuando no haya resultados
  relevantes, limitarse a instituciones muy conocidas de la ciudad y declarar
  explícitamente que la información no está verificada; los detalles específicos
  quedan prohibidos en ese modo.

## RAG: fuente de datos

`data/conocimiento/programas.jsonl` ya existía y se dejó intacto. Su contenido
se valida con T13 y no se vuelca en el informe. La reconstrucción del índice
requiere ejecutar manualmente `python scripts/construir_indice.py`, que usa
embeddings remotos y por eso no se ejecuta durante las pruebas.

## Métricas

Consulte el [resumen de métricas](resumen_metricas.md).

| Etapa | Llamadas al modelo por consulta típica |
|---|---:|
| Antes de omitir el enrutador | 5 |
| Después de omitirlo en el formulario | 3 |
