import pytest

from api.seguridad import UrlNoPermitida, verificar_destino


@pytest.mark.parametrize("url", ["http://127.0.0.1/", "http://localhost:8000/", "http://192.168.1.1/"])
def test_bloquea_la_red_interna(url, monkeypatch):
    monkeypatch.delenv("ONTOAUDIT_PERMITIR_RED_LOCAL", raising=False)
    with pytest.raises(UrlNoPermitida):
        verificar_destino(url)