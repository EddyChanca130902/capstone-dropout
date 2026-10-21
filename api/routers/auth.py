"""Autenticacion: login y refresh contra Supabase Auth.

El frontend (Angular) no necesita el SDK de Supabase: hace login contra este
endpoint y usa el `access_token` devuelto como Bearer en cada peticion. FastAPI
verifica la firma del JWT localmente (JWKS cacheado), sin llamadas extra.
"""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.core.config import Settings, obtener_config
from api.core.security import UsuarioActual, usuario_actual
from api.core.sesion_cache import CACHE_SESIONES

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str = Field(min_length=5, description="Correo del usuario")
    password: str = Field(min_length=4)


class RefreshIn(BaseModel):
    refresh_token: str


def _error_supabase(respuesta: httpx.Response) -> HTTPException:
    detalle = respuesta.text
    codigo_error = ""
    try:
        cuerpo = respuesta.json()
        detalle = cuerpo.get("msg") or cuerpo.get("error_description") or cuerpo.get("message") or detalle
        codigo_error = str(cuerpo.get("error_code") or cuerpo.get("code") or "")
    except Exception:
        pass

    # 429: Supabase esta limitando la tasa de intentos (no son credenciales erroneas).
    if respuesta.status_code == 429 or "too_many" in codigo_error.lower() or "rate" in codigo_error.lower():
        return HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Demasiados intentos de inicio de sesion. Espera unos minutos e intentalo de nuevo.",
        )
    codigo = status.HTTP_401_UNAUTHORIZED if respuesta.status_code in (400, 401) else status.HTTP_400_BAD_REQUEST
    return HTTPException(codigo, str(detalle))


@router.post("/login", summary="Inicia sesion y devuelve los tokens de Supabase")
def login(datos: LoginIn, config: Settings = Depends(obtener_config)) -> dict[str, Any]:
    if not config.supabase_base_url:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Supabase no esta configurado")

    # Cache corta: evita gastar el limite de tasa de Supabase Auth.
    cacheada = CACHE_SESIONES.obtener(datos.email, datos.password)
    if cacheada is not None:
        return cacheada

    url = f"{config.supabase_base_url}/auth/v1/token?grant_type=password"
    with httpx.Client(timeout=15) as cliente:
        respuesta = cliente.post(
            url,
            json={"email": datos.email, "password": datos.password},
            headers={"apikey": config.clave_anon, "Content-Type": "application/json"},
        )
    if respuesta.status_code != 200:
        raise _error_supabase(respuesta)
    cuerpo = respuesta.json()
    sesion = {
        "access_token": cuerpo.get("access_token"),
        "refresh_token": cuerpo.get("refresh_token"),
        "token_type": cuerpo.get("token_type", "bearer"),
        "expires_in": cuerpo.get("expires_in"),
        "usuario": {
            "id": (cuerpo.get("user") or {}).get("id"),
            "email": (cuerpo.get("user") or {}).get("email"),
        },
    }
    CACHE_SESIONES.guardar(datos.email, datos.password, sesion)
    return sesion


@router.post("/refresh", summary="Renueva el access token")
def refresh(datos: RefreshIn, config: Settings = Depends(obtener_config)) -> dict[str, Any]:
    url = f"{config.supabase_base_url}/auth/v1/token?grant_type=refresh_token"
    with httpx.Client(timeout=15) as cliente:
        respuesta = cliente.post(
            url,
            json={"refresh_token": datos.refresh_token},
            headers={"apikey": config.clave_anon},
        )
    if respuesta.status_code != 200:
        raise _error_supabase(respuesta)
    cuerpo = respuesta.json()
    return {
        "access_token": cuerpo.get("access_token"),
        "refresh_token": cuerpo.get("refresh_token"),
        "expires_in": cuerpo.get("expires_in"),
    }


@router.get("/me", summary="Datos del usuario autenticado")
def perfil(usuario: UsuarioActual = Depends(usuario_actual)) -> dict[str, Any]:
    return {
        "id": usuario.id,
        "email": usuario.email,
        "rol": usuario.rol,
        "autenticado": True,
    }
