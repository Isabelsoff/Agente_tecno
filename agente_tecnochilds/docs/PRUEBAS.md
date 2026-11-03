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
| T10 | Importación de grafo sin credenciales | Importar módulos y usar modelo simulado sin exigir API key | 1 prueba pasó; sin clave, la instancia real solo se solicita al usar el modelo | PASÓ | La inicialización global impedía recolectar tests sin credenciales | Inicializar Gemini de forma perezosa y fallar claramente solo ante una llamada real |

**Resultado total:** 19 pasaron, 1 omitida, 0 fallaron en la suite final.
La salida inicial tuvo un fallo real en T01; después del arreglo, la suite se
ejecutó otra vez y pasó. Una ejecución intermedia detectó además que la
instanciación global de Gemini exigía credenciales durante la colección; se
aplicó inicialización perezosa y quedó cubierta por T10.

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
  respuesta live ni se añadieron herramientas de navegación.

## Métricas

Consulte el [resumen de métricas](resumen_metricas.md).

| Etapa | Llamadas al modelo por consulta típica |
|---|---:|
| Antes de omitir el enrutador | 5 |
| Después de omitirlo en el formulario | 3 |
