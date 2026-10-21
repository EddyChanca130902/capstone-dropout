"""Tests de la cache de sesiones de autenticacion."""

from __future__ import annotations

import time

from api.core.sesion_cache import CacheDeSesiones


def test_guarda_y_recupera():
    cache = CacheDeSesiones(ttl=60)
    cache.guardar("a@b.com", "secreta", {"access_token": "abc"})
    assert cache.obtener("a@b.com", "secreta") == {"access_token": "abc"}


def test_no_devuelve_credenciales_distintas():
    cache = CacheDeSesiones(ttl=60)
    cache.guardar("a@b.com", "secreta", {"access_token": "abc"})
    assert cache.obtener("a@b.com", "otra") is None
    assert cache.obtener("otro@b.com", "secreta") is None


def test_el_correo_no_distingue_mayusculas_ni_espacios():
    cache = CacheDeSesiones(ttl=60)
    cache.guardar("A@B.com", "secreta", {"access_token": "abc"})
    assert cache.obtener("a@b.com ", "secreta") == {"access_token": "abc"}


def test_caduca():
    cache = CacheDeSesiones(ttl=0.05)
    cache.guardar("a@b.com", "secreta", {"access_token": "abc"})
    assert cache.obtener("a@b.com", "secreta") is not None
    time.sleep(0.08)
    assert cache.obtener("a@b.com", "secreta") is None


def test_limita_el_tamano():
    cache = CacheDeSesiones(ttl=60, maximo=3)
    for i in range(6):
        cache.guardar(f"u{i}@b.com", "x", {"access_token": str(i)})
    assert cache.tamano <= 3


def test_invalidar():
    cache = CacheDeSesiones(ttl=60)
    cache.guardar("a@b.com", "secreta", {"access_token": "abc"})
    cache.invalidar("a@b.com", "secreta")
    assert cache.obtener("a@b.com", "secreta") is None


def test_no_guarda_la_contrasena_en_claro():
    cache = CacheDeSesiones(ttl=60)
    cache.guardar("a@b.com", "contrasena-secreta", {"access_token": "abc"})
    # La clave interna es un hash: la contrasena no aparece en el estado.
    claves = list(cache._entradas)
    assert claves
    assert all("contrasena-secreta" not in clave for clave in claves)
