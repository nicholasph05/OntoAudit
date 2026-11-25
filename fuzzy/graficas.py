"""
Genera las gráficas de la lógica difusa para el informe:
    python -m fuzzy.graficas      -> imágenes en docs/img/
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # dibuja sin abrir ventanas
import matplotlib.pyplot as plt
import numpy as np

from fuzzy import motor

CARPETA = Path(__file__).resolve().parent.parent / "docs" / "img"


def graficar_variable(variable, titulo: str, unidad: str) -> Path:
    fig, ax = plt.subplots(figsize=(7, 3.2))
    for etiqueta, conjunto in variable.terms.items():
        ax.plot(variable.universe, conjunto.mf, linewidth=2, label=etiqueta)
        ax.fill_between(variable.universe, conjunto.mf, alpha=0.12)
    ax.set_title(titulo)
    ax.set_xlabel(unidad)
    ax.set_ylabel("Grado de pertenencia")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="center right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    ruta = CARPETA / f"fuzzy_{variable.label}.png"
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return ruta


def superficie_rendimiento() -> Path:
    """Mapa de decisión: cómo cambia el puntaje global según tiempo y peso."""
    tiempos = np.linspace(0, 10, 26)
    pesos = np.linspace(0, 6, 26)
    z = np.array([[motor.evaluar({"tiempo_carga": t, "peso_pagina_mb": p})["puntaje"]
                   for t in tiempos] for p in pesos])
    fig, ax = plt.subplots(figsize=(6, 4.5))
    mapa = ax.contourf(tiempos, pesos, z, levels=20, cmap="RdYlGn_r")
    fig.colorbar(mapa, label="Necesidad de mantenimiento (0-100)")
    ax.set_xlabel("Tiempo de carga (s)")
    ax.set_ylabel("Peso de la página (MB)")
    ax.set_title("Mapa de decisión (resto de métricas sanas)")
    fig.tight_layout()
    ruta = CARPETA / "fuzzy_mapa_decision.png"
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return ruta


if __name__ == "__main__":
    CARPETA.mkdir(parents=True, exist_ok=True)
    variables = [
        (motor.tiempo, "Tiempo de carga", "segundos"),
        (motor.peso, "Peso de la página", "MB"),
        (motor.sin_alt, "Imágenes sin texto alternativo", "%"),
        (motor.errores, "Errores de sintaxis HTML", "cantidad"),
        (motor.fallas_seo, "Prácticas SEO incumplidas", "%"),
        (motor.mantenimiento, "Nivel de mantenimiento (salida)", "puntaje 0-100"),
    ]
    for var, titulo, unidad in variables:
        print("Creada:", graficar_variable(var, titulo, unidad))
    print("Creada:", superficie_rendimiento())