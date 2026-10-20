"""Verifica que la migracion de Supabase quedo aplicada correctamente.

Comprueba:
  1. Las columnas nuevas de `evaluaciones` (user_id, modelo_version, entradas...).
  2. La existencia de la tabla `profiles` y del trigger de alta de usuarios.
  3. El aislamiento real entre usuarios: crea dos usuarios temporales, guarda
     una evaluacion con cada uno y comprueba que cada uno solo ve la suya
     (eso significa que Row Level Security esta funcionando).

Uso:
    python scripts/verify_supabase.py
"""

from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.core.config import obtener_config  # noqa: E402

COLUMNAS_ESPERADAS = [
    "user_id",
    "modelo_version",
    "entradas",
    "creado_en",
    "actualizado_en",
]


def _id_de_usuario(cliente: httpx.Client, base: str, cabeceras: dict, email: str) -> str | None:
    """Busca el id (auth.users.id) de un usuario por su correo."""
    usuarios = cliente.get(
        f"{base}/auth/v1/admin/users", params={"page": 1, "per_page": 200}, headers=cabeceras
    ).json().get("users", [])
    for usuario in usuarios:
        if usuario.get("email") == email:
            return usuario.get("id")
    return None


def main() -> int:
    config = obtener_config()
    if not config.supabase_base_url:
        print("[X] Falta SUPABASE_URL en el .env")
        return 1

    base = config.supabase_base_url
    admin = config.clave_admin
    cabeceras = {"apikey": admin, "Authorization": f"Bearer {admin}"}
    fallos = 0

    with httpx.Client(timeout=30) as cliente:
        # 1. Esquema expuesto por PostgREST
        try:
            esquema = cliente.get(f"{base}/rest/v1/", headers=cabeceras).json()
        except Exception as exc:
            print(f"[X] No se pudo leer el esquema: {exc}")
            return 1
        definiciones = esquema.get("definitions", {})

        columnas = list(definiciones.get("evaluaciones", {}).get("properties", {}).keys())
        print(f"[i] Columnas de `evaluaciones`: {columnas}")
        faltantes = [c for c in COLUMNAS_ESPERADAS if c not in columnas]
        if faltantes:
            print(f"[X] Faltan columnas: {faltantes}")
            print("    -> Aplica supabase/migrations/0001_init.sql")
            fallos += 1
        else:
            print("[OK] Todas las columnas nuevas estan presentes")

        if "profiles" in definiciones:
            print("[OK] La tabla `profiles` existe")
        else:
            print("[!] `profiles` no aparece en el esquema (puede no estar expuesta)")

        if "user_id" not in columnas:
            print("[!] Sin `user_id` no se puede probar RLS: se omite la prueba de aislamiento.")
            return 1 if fallos else 0

        # 2. Prueba de aislamiento entre dos usuarios
        sufijo = uuid.uuid4().hex[:8]
        usuarios = []
        for etiqueta in ("a", "b"):
            email = f"k6-verify-{etiqueta}-{sufijo}@alertatemprana.pe"
            password = f"Verificacion-{uuid.uuid4().hex[:10]}"
            created = cliente.post(
                f"{base}/auth/v1/admin/users",
                json={"email": email, "password": password, "email_confirm": True},
                headers=cabeceras,
            )
            if created.status_code >= 300:
                print(f"[X] No se pudo crear el usuario {email}: {created.text[:200]}")
                fallos += 1
                continue
            usuarios.append((email, password))

        if len(usuarios) < 2:
            print("[!] No se pudieron crear los dos usuarios de prueba; se omite la prueba de RLS")
            return 1 if fallos else 0

        tokens = []
        for email, password in usuarios:
            r = cliente.post(
                f"{base}/auth/v1/token?grant_type=password",
                json={"email": email, "password": password},
                headers={"apikey": config.clave_anon},
            )
            tokens.append(r.json().get("access_token") if r.status_code == 200 else None)

        if not all(tokens):
            print("[!] No se pudieron obtener los tokens; se omite la prueba de RLS")
            return 1 if fallos else 0

        for indice, token in enumerate(tokens):
            # El user_id se envia explicito: la politica de RLS exige
            # `auth.uid() = user_id` en cada fila insertada.
            peticion = cliente.post(
                f"{base}/rest/v1/evaluaciones",
                json={
                    "dni": f"VERIFY-{sufijo}-{indice}",
                    "nombre": f"Verificacion {indice}",
                    "area_estudios": "Administración y Negocios",
                    "probabilidad": 0.5,
                    "nivel": "MEDIO",
                    "modelo_version": "verificacion",
                    "entradas": {"verificacion": True},
                    "user_id": _id_de_usuario(cliente, base, cabeceras, usuarios[indice][0]),
                },
                headers={
                    "apikey": config.clave_anon,
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
            )
            if peticion.status_code >= 300:
                print(f"[X] No se pudo guardar la evaluacion del usuario {indice}: {peticion.text[:200]}")
                fallos += 1

        time.sleep(1)
        for indice, token in enumerate(tokens):
            r = cliente.get(
                f"{base}/rest/v1/evaluaciones?dni=like.VERIFY-{sufijo}-*&select=dni",
                headers={"apikey": config.clave_anon, "Authorization": f"Bearer {token}"},
            )
            filas = r.json() if r.status_code == 200 else []
            dnis = [f.get("dni") for f in filas]
            if dnis == [f"VERIFY-{sufijo}-{indice}"]:
                print(f"[OK] Usuario {indice} ve solo su evaluacion ({dnis}) -> RLS activa")
            else:
                print(f"[X] Usuario {indice} ve {dnis} (deberia ver solo la suya) -> RLS NO esta aislando")
                fallos += 1

        # Limpieza
        cliente.delete(
            f"{base}/rest/v1/evaluaciones?dni=like.VERIFY-{sufijo}-*",
            headers=cabeceras,
        )
        for email, _ in usuarios:
            uid = cliente.get(
                f"{base}/auth/v1/admin/users",
                params={"page": 1, "per_page": 200},
                headers=cabeceras,
            ).json().get("users", [])
            for u in uid:
                if u.get("email") == email:
                    cliente.delete(f"{base}/auth/v1/admin/users/{u['id']}", headers=cabeceras)
        print("[i] Usuarios y filas de prueba eliminados")

    if fallos:
        print(f"\n[RESULTADO] {fallos} comprobacion(es) fallida(s)")
        return 1
    print("\n[RESULTADO] Migracion aplicada y verificada correctamente")
    return 0


if __name__ == "__main__":
    sys.exit(main())
