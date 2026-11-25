"""
Etapa 4: la "percepción" del Agente Analista.

Visita una URL pública y mide las métricas que la ontología sabe interpretar
(propiedad oa:metrica de cada oa:Problema):

    tiempo_carga          s   HTML + recursos (imágenes, CSS, JS) descargados en paralelo
    peso_pagina_mb        MB  suma de lo descargado
    img_sin_alt_pct       %   imágenes <img> sin atributo alt
    errores_sintaxis      n   errores de análisis según el estándar HTML5
    sin_titulo            0/1 no tiene <title> o está vacío
    sin_meta_descripcion  0/1 no tiene <meta name="description">

Ética: respeta robots.txt, se identifica con su User-Agent, usa tiempos de espera
y no guarda el HTML ni datos personales, solo números agregados.
"""
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import html5lib
import requests
from bs4 import BeautifulSoup

USER_AGENT = "OntoAuditBot/1.0 (+https://github.com/nicholasph05/OntoAudit)"
TIEMPO_ESPERA = 10      # segundos máximos por petición
MAX_RECURSOS = 40       # límite de recursos a descargar por página
HILOS = 6               # descargas simultáneas, como un navegador


class AnalisisNoPermitido(Exception):
    """El sitio no permite robots en esa ruta (robots.txt)."""


class SitioNoDisponible(Exception):
    """No se pudo descargar la página."""


def normalizar_url(url: str) -> str:
    url = url.strip()
    if not urlparse(url).scheme:
        url = "https://" + url
    partes = urlparse(url)
    if partes.scheme not in ("http", "https") or not partes.netloc:
        raise ValueError(f"URL no válida: {url!r}")
    return url


def permitido_por_robots(url: str, sesion: requests.Session) -> bool:
    try:
        r = sesion.get(urljoin(url, "/robots.txt"), timeout=5)
    except requests.RequestException:
        return True  # si no hay robots.txt accesible, se asume permitido
    if r.status_code >= 400:
        return True
    reglas = RobotFileParser()
    reglas.parse(r.text.splitlines())
    return reglas.can_fetch(USER_AGENT, url)


def contar_errores_sintaxis(html: str) -> int:
    parser = html5lib.HTMLParser(strict=False)
    parser.parse(html)
    # Un error por posición; 'invalid-codepoint' salta con emojis válidos
    return len({pos for pos, codigo, _ in parser.errors if codigo != "invalid-codepoint"})


def recursos_de(soup: BeautifulSoup, base: str) -> list[str]:
    urls = []
    for img in soup.find_all("img", src=True):
        urls.append(img["src"])
    for link in soup.find_all("link", href=True):
        if "stylesheet" in (link.get("rel") or []):
            urls.append(link["href"])
    for script in soup.find_all("script", src=True):
        urls.append(script["src"])
    absolutas = [urljoin(base, u) for u in urls if not u.startswith("data:")]
    return list(dict.fromkeys(absolutas))[:MAX_RECURSOS]  # sin repetidos


def _descargar_bytes(sesion: requests.Session, url: str) -> int:
    try:
        return len(sesion.get(url, timeout=TIEMPO_ESPERA).content)
    except requests.RequestException:
        return 0


def analizar(url: str) -> dict:
    """Descarga la página y devuelve sus métricas."""
    url = normalizar_url(url)
    sesion = requests.Session()
    sesion.headers["User-Agent"] = USER_AGENT

    if not permitido_por_robots(url, sesion):
        raise AnalisisNoPermitido(f"robots.txt no permite analizar {url}")

    inicio = time.perf_counter()
    try:
        respuesta = sesion.get(url, timeout=TIEMPO_ESPERA)
    except requests.RequestException as e:
        raise SitioNoDisponible(f"No se pudo abrir {url}: {e}") from e
    if respuesta.status_code >= 400:
        raise SitioNoDisponible(f"{url} respondió con error HTTP {respuesta.status_code}")
    html = respuesta.text
    soup = BeautifulSoup(html, "html.parser")

    recursos = recursos_de(soup, respuesta.url)
    with ThreadPoolExecutor(max_workers=HILOS) as hilos:
        pesos = list(hilos.map(lambda u: _descargar_bytes(sesion, u), recursos))
    tiempo_total = time.perf_counter() - inicio

    imagenes = soup.find_all("img")
    sin_alt = [img for img in imagenes if not img.has_attr("alt")]
    titulo = soup.title.get_text(strip=True) if soup.title else ""
    meta = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "description"})

    return {
        "url": url,
        "url_final": respuesta.url,
        "codigo_http": respuesta.status_code,
        "tiempo_carga": round(tiempo_total, 2),
        "peso_pagina_mb": round((len(respuesta.content) + sum(pesos)) / 1_048_576, 2),
        "total_imagenes": len(imagenes),
        "imagenes_sin_alt": len(sin_alt),
        "img_sin_alt_pct": round(100 * len(sin_alt) / len(imagenes), 1) if imagenes else 0.0,
        "errores_sintaxis": contar_errores_sintaxis(html),
        "sin_titulo": 0 if titulo else 1,
        "sin_meta_descripcion": 0 if meta and meta.get("content", "").strip() else 1,
        "recursos_descargados": len(recursos),
    }


if __name__ == "__main__":
    import json
    import sys

    destino = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    print(json.dumps(analizar(destino), indent=2, ensure_ascii=False))