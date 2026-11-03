import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = PROJECT_ROOT / "logs" / "metricas.jsonl"
SUMMARY_PATH = PROJECT_ROOT / "docs" / "resumen_metricas.md"


def leer_ejecuciones() -> list[dict[str, Any]]:
    if not METRICS_PATH.exists():
        return []

    registros = []
    with METRICS_PATH.open("r", encoding="utf-8") as archivo:
        for numero_linea, linea in enumerate(archivo, start=1):
            if not linea.strip():
                continue
            try:
                registros.append(json.loads(linea))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"JSON inválido en {METRICS_PATH}, línea {numero_linea}."
                ) from error
    return registros


def crear_resumen(registros: list[dict[str, Any]]) -> str:
    duraciones = [
        float(registro.get("metricas", {}).get("tiempo_total_segundos", 0))
        for registro in registros
    ]
    tokens_totales = sum(
        int(registro.get("metricas", {}).get("tokens", {}).get("total", 0))
        for registro in registros
    )
    llamadas = [
        int(registro.get("metricas", {}).get("llamadas_modelo", 0))
        for registro in registros
    ]
    errores: Counter[str] = Counter()
    herramientas: dict[str, list[float]] = {}

    for registro in registros:
        metricas = registro.get("metricas", {})
        for error in metricas.get("errores", []):
            errores[str(error.get("tipo", "desconocido"))] += 1
        for herramienta in metricas.get("herramientas", []):
            nombre = str(herramienta.get("nombre", "desconocida"))
            herramientas.setdefault(nombre, []).append(
                float(herramienta.get("duracion_segundos", 0))
            )

    filas = [
        "# Resumen de métricas del agente",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
        f"| Ejecuciones registradas | {len(registros)} |",
        f"| Tiempo promedio | {mean(duraciones) if duraciones else 0:.2f} s |",
        f"| Tiempo máximo | {max(duraciones, default=0):.2f} s |",
        f"| Tokens totales | {tokens_totales} |",
        f"| Llamadas al modelo por consulta (promedio) | "
        f"{mean(llamadas) if llamadas else 0:.2f} |",
        "",
        "## Uso por herramienta",
        "",
        "| Herramienta | Llamadas | Duración promedio (s) | Duración máxima (s) |",
        "|---|---:|---:|---:|",
    ]
    if herramientas:
        for nombre, tiempos in sorted(herramientas.items()):
            filas.append(
                f"| {nombre} | {len(tiempos)} | {mean(tiempos):.3f} | {max(tiempos):.3f} |"
            )
    else:
        filas.append("| Sin herramientas registradas | 0 | 0.000 | 0.000 |")

    filas.extend(
        [
            "",
            "## Errores por tipo",
            "",
            "| Tipo | Cantidad |",
            "|---|---:|",
        ]
    )
    if errores:
        filas.extend(f"| {tipo} | {cantidad} |" for tipo, cantidad in sorted(errores.items()))
    else:
        filas.append("| Sin errores | 0 |")
    filas.append("")
    return "\n".join(filas)


def main() -> None:
    resumen = crear_resumen(leer_ejecuciones())
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(resumen, encoding="utf-8")
    print(resumen, end="")
    print(f"\nResumen guardado en: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
