"""Acceso a Supabase (Postgres) para las evaluaciones.

Se usa **PostgREST directamente** (y no el cliente `supabase` completo) por dos
motivos:

1. El cliente `supabase` 2.33.0 instalado tiene una incompatibilidad con su
   modulo de autenticacion (`ClientOptions` no expone `storage`), que rompe la
   creacion del cliente.
2. PostgREST es mas ligero: la API solo necesita operaciones de tabla, y cada
   llamada de red de menos se nota en las pruebas de carga.

Dos modos de acceso:

* **Con RLS (recomendado):** clave publica (`anon`) + access token del usuario,
  de modo que las politicas de Row Level Security aplican en la base de datos.
* **Con clave de servicio:** si no hay clave publica configurada, el
  aislamiento por usuario se aplica explicitamente en las consultas.
"""

from __future__ import annotations

import threading
from typing import Any

from api.core.config import Settings

_cargador = threading.Lock()
_clientes: dict[str, Any] = {}
_columnas_cache: dict[str, list[str]] = {}


def _crear_cliente(config: Settings, clave: str, cabeceras: dict[str, str] | None = None):
    from postgrest import SyncPostgrestClient

    cabeceras_completas = {
        "apikey": clave,
        "Authorization": f"Bearer {clave}",
        "Content-Type": "application/json",
    }
    cabeceras_completas.update(cabeceras or {})
    return SyncPostgrestClient(
        f"{config.supabase_base_url}/rest/v1",
        headers=cabeceras_completas,
        schema="public",
        timeout=15,
    )


def cliente_admin(config: Settings):
    """Cliente con clave de servicio (operaciones administrativas / semilla)."""
    clave = config.clave_admin
    if not clave:
        raise RuntimeError("Falta SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY en el .env")
    if "admin" not in _clientes:
        with _cargador:
            if "admin" not in _clientes:
                _clientes["admin"] = _crear_cliente(config, clave)
    return _clientes["admin"]


def modo_rls_activo(config: Settings, tabla: str = "evaluaciones") -> bool:
    """Indica si la tabla ya tiene el esquema con `user_id`.

    Mientras la migracion `supabase/migrations/0001_init.sql` no se haya
    aplicado, la tabla no tiene `user_id` y las politicas RLS no se pueden
    aplicar; en ese caso se opera con la clave de servicio y el aislamiento
    por usuario se hace en el codigo (no hay columna donde filtrar).
    """
    return "user_id" in columnas_tabla(config, tabla)


def cliente_usuario(config: Settings, access_token: str | None = None):
    """Cliente que opera con el JWT del usuario (para que aplique RLS).

    Si la tabla todavia no tiene `user_id` (migracion pendiente), se usa la
    clave de servicio: las escrituras con RLS sin politicas serian rechazadas.
    """
    if not access_token or not config.supabase_anon_key or not modo_rls_activo(config):
        return cliente_admin(config)
    if access_token not in _clientes:
        with _cargador:
            if access_token not in _clientes:
                _clientes[access_token] = _crear_cliente(
                    config,
                    config.supabase_anon_key,
                    {"Authorization": f"Bearer {access_token}"},
                )
    return _clientes[access_token]


def columnas_tabla(config: Settings, tabla: str = "evaluaciones") -> list[str]:
    """Columnas reales de una tabla (se leen del esquema publico de PostgREST)."""
    if tabla in _columnas_cache:
        return _columnas_cache[tabla]
    columnas: list[str] = []
    try:
        import httpx

        respuesta = httpx.get(
            f"{config.supabase_base_url}/rest/v1/",
            headers={"apikey": config.clave_admin, "Authorization": f"Bearer {config.clave_admin}"},
            timeout=10,
        )
        respuesta.raise_for_status()
        definiciones = respuesta.json().get("definitions", {})
        columnas = list(definiciones.get(tabla, {}).get("properties", {}).keys())
    except Exception:  # pragma: no cover - si falla, se asume el esquema minimo
        columnas = []
    _columnas_cache[tabla] = columnas
    return columnas


def filtrar_columnas(fila: dict[str, Any], columnas: list[str]) -> dict[str, Any]:
    """Descarta las claves que la tabla no soporta."""
    if not columnas:
        return fila
    return {k: v for k, v in fila.items() if k in columnas}


_estado_cache: dict[str, Any] = {"valor": None, "expira": 0.0}


def estado_supabase(config: Settings, ttl: float = 30.0) -> dict[str, Any]:
    """Comprueba (con cache de 30 s) que la API puede hablar con Supabase."""
    import time

    ahora = time.time()
    if _estado_cache["valor"] is not None and _estado_cache["expira"] > ahora:
        return _estado_cache["valor"]

    estado: dict[str, Any] = {"estado": "desconocido"}
    if not config.supabase_base_url:
        estado = {"estado": "sin_configurar"}
    else:
        try:
            import httpx

            inicio = time.perf_counter()
            respuesta = httpx.get(
                f"{config.supabase_base_url}/rest/v1/",
                headers={
                    "apikey": config.clave_admin,
                    "Authorization": f"Bearer {config.clave_admin}",
                },
                timeout=5,
            )
            latencia = (time.perf_counter() - inicio) * 1000
            estado = {
                "estado": "ok" if respuesta.status_code < 400 else "error",
                "http_status": respuesta.status_code,
                "latencia_ms": round(latencia, 1),
                "tablas": list(respuesta.json().get("definitions", {}).keys())
                if respuesta.status_code < 400
                else [],
            }
        except Exception as exc:
            estado = {"estado": "error", "error": f"{type(exc).__name__}: {exc}"}

    _estado_cache["valor"] = estado
    _estado_cache["expira"] = ahora + ttl
    return estado
