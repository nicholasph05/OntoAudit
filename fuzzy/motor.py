"""
Etapa 3: el cerebro difuso de OntoAudit (scikit-fuzzy).

Sistema difuso JERÁRQUICO de dos niveles:

  Nivel 1 (un subsistema por área de BuenasPracticas de la ontología)
    Rendimiento    tiempo_carga (s)  + peso_pagina_mb    -> riesgo 0-100
    Accesibilidad  img_sin_alt_pct   + errores_sintaxis  -> riesgo 0-100
    SEO            fallas_seo_pct                        -> riesgo 0-100

  Nivel 2 (veredicto global)
    riesgo_rendimiento + riesgo_accesibilidad + riesgo_seo
        -> mantenimiento 0-100: Al día | Preventivo | Urgente
"""
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# Conjuntos de salida comunes a los tres subsistemas
def _riesgo(nombre: str) -> ctrl.Consequent:
    r = ctrl.Consequent(np.arange(0, 101, 1), nombre)
    r["Bajo"] = fuzz.trapmf(r.universe, [0, 0, 20, 40])
    r["Medio"] = fuzz.trimf(r.universe, [30, 50, 70])
    r["Alto"] = fuzz.trapmf(r.universe, [60, 80, 100, 100])
    return r


# ------------------------------------------------------------------
# Subsistema 1: Rendimiento
# ------------------------------------------------------------------
tiempo = ctrl.Antecedent(np.arange(0, 10.01, 0.1), "tiempo_carga")
tiempo["Rápido"] = fuzz.trapmf(tiempo.universe, [0, 0, 1.5, 3])
tiempo["Moderado"] = fuzz.trimf(tiempo.universe, [2, 4, 6])
tiempo["Lento"] = fuzz.trapmf(tiempo.universe, [5, 7, 10, 10])

peso = ctrl.Antecedent(np.arange(0, 6.01, 0.05), "peso_pagina_mb")
peso["Liviana"] = fuzz.trapmf(peso.universe, [0, 0, 1, 2.5])
peso["Pesada"] = fuzz.trapmf(peso.universe, [1.5, 3.5, 6, 6])

riesgo_rend = _riesgo("riesgo_rendimiento")

reglas_rend = [
    ctrl.Rule(tiempo["Rápido"] & peso["Liviana"], riesgo_rend["Bajo"], label="RR1"),
    ctrl.Rule(tiempo["Rápido"] & peso["Pesada"], riesgo_rend["Medio"], label="RR2"),
    ctrl.Rule(tiempo["Moderado"] & peso["Liviana"], riesgo_rend["Medio"], label="RR3"),
    ctrl.Rule(tiempo["Moderado"] & peso["Pesada"], riesgo_rend["Alto"], label="RR4"),
    ctrl.Rule(tiempo["Lento"], riesgo_rend["Alto"], label="RR5"),
]

# ------------------------------------------------------------------
# Subsistema 2: Accesibilidad
# ------------------------------------------------------------------
sin_alt = ctrl.Antecedent(np.arange(0, 101, 1), "img_sin_alt_pct")
sin_alt["Bajo"] = fuzz.trapmf(sin_alt.universe, [0, 0, 5, 20])
sin_alt["Medio"] = fuzz.trimf(sin_alt.universe, [10, 35, 60])
sin_alt["Alto"] = fuzz.trapmf(sin_alt.universe, [45, 70, 100, 100])

errores = ctrl.Antecedent(np.arange(0, 51, 1), "errores_sintaxis")
errores["Pocos"] = fuzz.trapmf(errores.universe, [0, 0, 5, 20])
errores["Muchos"] = fuzz.trapmf(errores.universe, [10, 30, 50, 50])

riesgo_acc = _riesgo("riesgo_accesibilidad")

reglas_acc = [
    ctrl.Rule(sin_alt["Bajo"] & errores["Pocos"], riesgo_acc["Bajo"], label="RA1"),
    ctrl.Rule(sin_alt["Bajo"] & errores["Muchos"], riesgo_acc["Medio"], label="RA2"),
    ctrl.Rule(sin_alt["Medio"] & errores["Pocos"], riesgo_acc["Medio"], label="RA3"),
    ctrl.Rule(sin_alt["Medio"] & errores["Muchos"], riesgo_acc["Alto"], label="RA4"),
    ctrl.Rule(sin_alt["Alto"], riesgo_acc["Alto"], label="RA5"),
]

# ------------------------------------------------------------------
# Subsistema 3: SEO
# ------------------------------------------------------------------
fallas_seo = ctrl.Antecedent(np.arange(0, 101, 1), "fallas_seo_pct")
fallas_seo["Pocas"] = fuzz.trapmf(fallas_seo.universe, [0, 0, 10, 40])
fallas_seo["Algunas"] = fuzz.trimf(fallas_seo.universe, [20, 50, 80])
fallas_seo["Muchas"] = fuzz.trapmf(fallas_seo.universe, [60, 90, 100, 100])

riesgo_seo = _riesgo("riesgo_seo")

reglas_seo = [
    ctrl.Rule(fallas_seo["Pocas"], riesgo_seo["Bajo"], label="RS1"),
    ctrl.Rule(fallas_seo["Algunas"], riesgo_seo["Medio"], label="RS2"),
    ctrl.Rule(fallas_seo["Muchas"], riesgo_seo["Alto"], label="RS3"),
]


# ------------------------------------------------------------------
# Nivel 2: veredicto global
# ------------------------------------------------------------------
def _entrada_riesgo(nombre: str) -> ctrl.Antecedent:
    a = ctrl.Antecedent(np.arange(0, 101, 1), nombre)
    a["Bajo"] = fuzz.trapmf(a.universe, [0, 0, 20, 40])
    a["Medio"] = fuzz.trimf(a.universe, [30, 50, 70])
    a["Alto"] = fuzz.trapmf(a.universe, [60, 80, 100, 100])
    return a


g_rend = _entrada_riesgo("rendimiento")
g_acc = _entrada_riesgo("accesibilidad")
g_seo = _entrada_riesgo("seo")

mantenimiento = ctrl.Consequent(np.arange(0, 101, 1), "mantenimiento")
mantenimiento["AlDia"] = fuzz.trapmf(mantenimiento.universe, [0, 0, 20, 40])
mantenimiento["Preventivo"] = fuzz.trimf(mantenimiento.universe, [30, 50, 70])
mantenimiento["Urgente"] = fuzz.trapmf(mantenimiento.universe, [60, 80, 100, 100])

reglas_global = [
    ctrl.Rule(g_rend["Alto"] | g_acc["Alto"], mantenimiento["Urgente"], label="RG1"),
    ctrl.Rule(g_seo["Alto"] & (g_rend["Medio"] | g_acc["Medio"]), mantenimiento["Urgente"], label="RG2"),
    ctrl.Rule(g_rend["Medio"] | g_acc["Medio"] | g_seo["Medio"], mantenimiento["Preventivo"], label="RG3"),
    ctrl.Rule(g_seo["Alto"] & g_rend["Bajo"] & g_acc["Bajo"], mantenimiento["Preventivo"], label="RG4"),
    ctrl.Rule(g_rend["Bajo"] & g_acc["Bajo"] & g_seo["Bajo"], mantenimiento["AlDia"], label="RG5"),
]

EXPLICACION_REGLAS = {
    "RR1": "Carga rápido y es liviana: rendimiento sano.",
    "RR2": "Carga rápido, pero es pesada: en celulares puede ser lenta.",
    "RR3": "Es liviana, pero la carga ya es moderada.",
    "RR4": "Carga moderada y página pesada: los problemas se suman.",
    "RR5": "Carga lenta: la mayoría de usuarios se va antes de verla.",
    "RA1": "Casi todas las imágenes tienen alt y el HTML es limpio.",
    "RA2": "Las imágenes están bien, pero el HTML tiene muchos errores.",
    "RA3": "El HTML está bien, pero varias imágenes no tienen alt.",
    "RA4": "Varias imágenes sin alt y muchos errores de HTML.",
    "RA5": "La mayoría de imágenes no tiene texto alternativo.",
    "RS1": "Cumple casi todas las prácticas básicas de SEO.",
    "RS2": "Le falta alguna práctica básica de SEO.",
    "RS3": "Le faltan las prácticas básicas de SEO (título y descripción).",
    "RG1": "Rendimiento o accesibilidad en riesgo alto: mantenimiento urgente.",
    "RG2": "SEO deficiente sumado a otro riesgo medio: mantenimiento urgente.",
    "RG3": "Algún área en riesgo medio: conviene mantenimiento preventivo.",
    "RG4": "Solo el SEO está mal: mantenimiento preventivo.",
    "RG5": "Las tres áreas en riesgo bajo: el sitio está al día.",
}

_sistemas = {
    "rendimiento": ctrl.ControlSystem(reglas_rend),
    "accesibilidad": ctrl.ControlSystem(reglas_acc),
    "seo": ctrl.ControlSystem(reglas_seo),
    "global": ctrl.ControlSystem(reglas_global),
}


def _simular(nombre_sistema: str, entradas: dict, salida: str) -> tuple[float, list[dict]]:
    """Corre un subsistema y devuelve (valor de salida, reglas activadas)."""
    sistema = _sistemas[nombre_sistema]
    sim = ctrl.ControlSystemSimulation(sistema)
    for k, v in entradas.items():
        sim.input[k] = v
    sim.compute()
    activadas = []
    for regla in sistema.rules:
        grado = float(regla.aggregate_firing[sim])
        if grado > 0.01:
            activadas.append({
                "regla": regla.label,
                "grado": round(grado, 2),
                "explicacion": EXPLICACION_REGLAS[regla.label],
            })
    activadas.sort(key=lambda r: r["grado"], reverse=True)
    return round(float(sim.output[salida]), 1), activadas


def _limitar(valor: float, minimo: float, maximo: float) -> float:
    return max(minimo, min(maximo, float(valor)))


def nivel_linguistico(puntaje: float) -> str:
    """Etiqueta con mayor pertenencia para el puntaje global."""
    grados = {
        etiqueta: fuzz.interp_membership(mantenimiento.universe, mantenimiento[etiqueta].mf, puntaje)
        for etiqueta in ("AlDia", "Preventivo", "Urgente")
    }
    return max(grados, key=grados.get)


def evaluar(metricas: dict) -> dict:
    """
    Recibe las métricas del Analista y devuelve el veredicto difuso completo.
    Claves esperadas: tiempo_carga, peso_pagina_mb, img_sin_alt_pct,
    errores_sintaxis, sin_titulo, sin_meta_descripcion.
    """
    rend, reglas_r = _simular("rendimiento", {
        "tiempo_carga": _limitar(metricas.get("tiempo_carga", 0), 0, 10),
        "peso_pagina_mb": _limitar(metricas.get("peso_pagina_mb", 0), 0, 6),
    }, "riesgo_rendimiento")

    acc, reglas_a = _simular("accesibilidad", {
        "img_sin_alt_pct": _limitar(metricas.get("img_sin_alt_pct", 0), 0, 100),
        "errores_sintaxis": _limitar(metricas.get("errores_sintaxis", 0), 0, 50),
    }, "riesgo_accesibilidad")

    checks_seo = [metricas.get("sin_titulo", 0), metricas.get("sin_meta_descripcion", 0)]
    pct_seo = 100 * sum(1 for c in checks_seo if c) / len(checks_seo)
    seo, reglas_s = _simular("seo", {"fallas_seo_pct": pct_seo}, "riesgo_seo")

    puntaje, reglas_g = _simular("global", {
        "rendimiento": rend, "accesibilidad": acc, "seo": seo,
    }, "mantenimiento")

    return {
        "puntaje": puntaje,
        "nivel": nivel_linguistico(puntaje),
        "riesgos": {"Rendimiento": rend, "Accesibilidad": acc, "SEO": seo},
        "reglas": {
            "Rendimiento": reglas_r, "Accesibilidad": reglas_a,
            "SEO": reglas_s, "Global": reglas_g,
        },
    }


if __name__ == "__main__":
    casos = {
        "Sitio sano": dict(tiempo_carga=1.0, peso_pagina_mb=0.8, img_sin_alt_pct=0,
                           errores_sintaxis=2, sin_titulo=0, sin_meta_descripcion=0),
        "Solo SEO mal": dict(tiempo_carga=1.0, peso_pagina_mb=0.8, img_sin_alt_pct=0,
                             errores_sintaxis=2, sin_titulo=1, sin_meta_descripcion=1),
        "Algo lento": dict(tiempo_carga=4.0, peso_pagina_mb=1.0, img_sin_alt_pct=5,
                           errores_sintaxis=3, sin_titulo=0, sin_meta_descripcion=1),
        "Lento y con muchos errores (regla de la guía)": dict(
            tiempo_carga=8.0, peso_pagina_mb=1.0, img_sin_alt_pct=0,
            errores_sintaxis=35, sin_titulo=0, sin_meta_descripcion=0),
    }
    for nombre_caso, m in casos.items():
        r = evaluar(m)
        print(f"\n{nombre_caso}: {r['nivel']} ({r['puntaje']}/100)  riesgos={r['riesgos']}")
        for regla in r["reglas"]["Global"]:
            print(f"   {regla['regla']} ({regla['grado']}): {regla['explicacion']}")