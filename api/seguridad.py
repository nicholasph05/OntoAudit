"""
Evita que la API se use para escanear la red interna (ataque SSRF):
solo se permiten sitios con IP pública, salvo que se habilite explícitamente.
"""
import ipaddress
import os
import socket
from urllib.parse import urlparse


class UrlNoPermitida(Exception):
    pass


def permitir_red_local() -> bool:
    return os.getenv("ONTOAUDIT_PERMITIR_RED_LOCAL") == "1"


def verificar_destino(url: str) -> None:
    host = urlparse(url).hostname or ""
    if permitir_red_local():
        return
    try:
        direcciones = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except socket.gaierror:
        raise UrlNoPermitida(f"No se encontró el dominio {host!r}")
    for direccion in direcciones:
        ip = ipaddress.ip_address(direccion)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise UrlNoPermitida("Solo se pueden auditar sitios públicos de internet")