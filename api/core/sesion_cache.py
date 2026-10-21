"""Caché corta de sesiones de autenticación.

Motivo: el login se delega en Supabase Auth, que aplica limite de tasa al
endpoint de contrasena y, cuando lo alcanza, responde `Invalid login
credentials` (enmascara el rate limit para no filtrar que cuentas existen).
Con varias personas orientadoras entrando y saliendo, ese limite se agota
con facilidad y el usuario ve un error de credenciales cuando sus datos son
correctos.

Esta cache guarda la sesion ya emitida durante `ttl` segundos, indexada por
un SHA-256 de (correo + contrasena): la contrasena en claro nunca se guarda
y la ventana de exposicion es acotada.

Cuando la cache se llena, el login vuelve a ir a Supabase, que es el
comportamiento correcto.
"""

from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class _Entrada:
    sesion: dict[str, Any]
    expira: float


class CacheDeSesiones:
    def __init__(self, ttl: float = 60.0, maximo: int = 64) -> None:
        self.ttl = ttl
        self.maximo = maximo
        self._entradas: dict[str, _Entrada] = {}
        self._bloqueo = threading.Lock()

    @staticmethod
    def _clave(correo: str, contrasena: str) -> str:
        return hashlib.sha256(f"{correo.strip().lower()}|{contrasena}".encode()).hexdigest()

    def obtener(self, correo: str, contrasena: str) -> dict[str, Any] | None:
        clave = self._clave(correo, contrasena)
        ahora = time.time()
        with self._bloqueo:
            entrada = self._entradas.get(clave)
            if entrada is None:
                return None
            if entrada.expira <= ahora:
                self._entradas.pop(clave, None)
                return None
            return dict(entrada.sesion)

    def guardar(self, correo: str, contrasena: str, sesion: dict[str, Any]) -> None:
        clave = self._clave(correo, contrasena)
        ahora = time.time()
        with self._bloqueo:
            # Purga de caducadas y limite de tamano.
            for k in [k for k, v in self._entradas.items() if v.expira <= ahora]:
                self._entradas.pop(k, None)
            if len(self._entradas) >= self.maximo:
                mas_antigua = min(self._entradas, key=lambda k: self._entradas[k].expira)
                self._entradas.pop(mas_antigua, None)
            self._entradas[clave] = _Entrada(dict(sesion), ahora + self.ttl)

    def invalidar(self, correo: str, contrasena: str) -> None:
        with self._bloqueo:
            self._entradas.pop(self._clave(correo, contrasena), None)

    @property
    def tamano(self) -> int:
        with self._bloqueo:
            return len(self._entradas)


CACHE_SESIONES = CacheDeSesiones(ttl=60.0)
