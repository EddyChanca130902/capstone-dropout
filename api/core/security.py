"""Verificacion de JWT de Supabase y hashing de contrasenas.

La verificacion del JWT se hace LOCAL (JWKS cacheado) y no con
`auth.get_user()` en cada request: eso seria una llamada de red por peticion y
hundiria las pruebas de carga de k6.
"""

from __future__ import annotations

import time
import threading
from typing import Any

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.core.config import Settings, obtener_config

_CACHÉ_JWKS: dict[str, Any] = {"clave": None, "expira": 0.0}
_TTL_JWKS = 3600.0

# El cliente de JWKS se crea UNA vez: instanciarlo en cada peticion hacia la
# red para descargar las claves publicas y anadia ~300 ms a cada request.
_cliente_jwks: PyJWKClient | None = None
_bloqueo = threading.Lock()


def _obtener_cliente_jwks(config: Settings) -> PyJWKClient:
    global _cliente_jwks
    if _cliente_jwks is None:
        with _bloqueo:
            if _cliente_jwks is None:
                _cliente_jwks = PyJWKClient(
                    f"{config.supabase_base_url}/auth/v1/.well-known/jwks.json",
                    cache_keys=True,
                    lifespan=300,
                )
    return _cliente_jwks


bearer_scheme = HTTPBearer(auto_error=False)


def _clave_publica(config: Settings) -> Any:
    """Devuelve la clave publica de Supabase (cacheada 1 h)."""
    ahora = time.time()
    if _CACHÉ_JWKS["clave"] is not None and _CACHÉ_JWKS["expira"] > ahora:
        return _CACHÉ_JWKS["clave"]

    if config.supabase_jwt_secret:
        clave: Any = config.supabase_jwt_secret
    else:
        url_jwks = f"{config.supabase_base_url}/auth/v1/.well-known/jwks.json"
        cliente = PyJWKClient(url_jwks, cache_keys=True, lifespan=300)
        clave = cliente.get_jwk_set()

    _CACHÉ_JWKS["clave"] = clave
    _CACHÉ_JWKS["expira"] = ahora + _TTL_JWKS
    return clave


def verificar_token_supabase(token: str, config: Settings) -> dict[str, Any]:
    """Verifica la firma y las expiraciones del access token de Supabase Auth.

    `leeway` absorbe la desincronizacion del reloj entre el servidor de
    Supabase y la maquina (en desarrollo se observaron ~4 minutos de desfase,
    lo que hacia fallar el `iat`).
    """
    margen = config.jwt_leeway_seconds
    try:
        if config.supabase_jwt_secret:
            claims = jwt.decode(
                token,
                config.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                leeway=margen,
                options={"verify_aud": False},
            )
        else:
            cliente = _obtener_cliente_jwks(config)
            clave = cliente.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                clave,
                algorithms=["RS256", "ES256"],
                audience="authenticated",
                leeway=margen,
                options={"verify_aud": False},
            )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "El token ha expirado") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido") from exc

    if not claims.get("sub"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token sin identificador de usuario")
    return claims


class UsuarioActual:
    """Usuario autenticado (proveniente de Supabase Auth)."""

    def __init__(self, claims: dict[str, Any], token: str | None = None) -> None:
        self.id: str = claims["sub"]
        self.email: str = claims.get("email", "")
        self.rol: str = claims.get("role", "authenticated")
        self.claims: dict[str, Any] = claims
        self.token: str | None = token

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UsuarioActual {self.email or self.id}>"


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    config: Settings = Depends(obtener_config),
) -> UsuarioActual:
    if credenciales is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Falta la cabecera Authorization: Bearer <access_token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    claims = verificar_token_supabase(credenciales.credentials, config)
    return UsuarioActual(claims, credenciales.credentials)


def usuario_opcional(
    credenciales: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    config: Settings = Depends(obtener_config),
) -> UsuarioActual | None:
    if credenciales is None:
        return None
    try:
        return UsuarioActual(verificar_token_supabase(credenciales.credentials, config))
    except HTTPException:
        return None


# --------------------------------------------------------------------------- #
# Hashing de contrasenas (dashboard legacy en SQLite)
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    from argon2 import PasswordHasher

    return PasswordHasher().hash(password)


def verificar_password(password: str, hash_guardado: str) -> bool:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerificationError, VerifyMismatchError

    if not hash_guardado:
        return False
    try:
        PasswordHasher().verify(hash_guardado, password)
        return True
    except (VerifyMismatchError, VerificationError, ValueError):
        return False
