import pytest

from fuzzy.motor import evaluar

SANO = dict(tiempo_carga=1.0, peso_pagina_mb=0.8, img_sin_alt_pct=0,
            errores_sintaxis=2, sin_titulo=0, sin_meta_descripcion=0)


def test_sitio_sano_esta_al_dia():
    assert evaluar(SANO)["nivel"] == "AlDia"


def test_regla_de_la_guia_lento_y_muchos_errores_es_urgente():
    r = evaluar({**SANO, "tiempo_carga": 8.0, "errores_sintaxis": 35})
    assert r["nivel"] == "Urgente"


def test_solo_seo_mal_es_preventivo():
    r = evaluar({**SANO, "sin_titulo": 1, "sin_meta_descripcion": 1})
    assert r["nivel"] == "Preventivo"


def test_mas_lento_nunca_mejora_el_puntaje():
    # Propiedad de monotonía: empeorar una métrica no debe bajar el puntaje
    puntajes = [evaluar({**SANO, "tiempo_carga": t})["puntaje"] for t in (0, 2, 4, 6, 8, 10)]
    assert puntajes == sorted(puntajes)


@pytest.mark.parametrize("tiempo", [-5, 0, 50])
def test_valores_fuera_de_rango_no_rompen(tiempo):
    r = evaluar({**SANO, "tiempo_carga": tiempo})
    assert 0 <= r["puntaje"] <= 100


def test_explica_que_reglas_se_activaron():
    r = evaluar({**SANO, "tiempo_carga": 8.0})
    globales = [x["regla"] for x in r["reglas"]["Global"]]
    assert "RG1" in globales