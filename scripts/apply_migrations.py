"""Aplica las migraciones de `supabase/migrations/` en el proyecto de Supabase.

Intenta tres vias, en este orden:

1. **Management API** con un Personal Access Token (`SUPABASE_ACCESS_TOKEN`).
   Es la opcion recomendada:
       https://supabase.com/dashboard/account/tokens
2. **Conexion directa a Postgres** con `SUPABASE_DB_URL` (requiere `psycopg`).
3. Si no hay ninguna de las dos, imprime el SQL y las instrucciones para
   pegarlo en el SQL Editor del panel de Supabase.

Uso:
    python scripts/apply_migrations.py
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIGRACIONES = ROOT / "supabase" / "migrations"


def leer_env(path: Path) -> dict[str, str]:
    valores: dict[str, str] = {}
    if not path.exists():
        return valores
    for linea in path.read_text(encoding="utf-8").splitlines():
        if "=" in linea and not linea.strip().startswith("#"):
            clave, valor = linea.split("=", 1)
            valores[clave.strip()] = valor.strip()
    return valores


def project_ref(url: str) -> str:
    m = re.search(r"https://([a-z0-9]+)\.supabase\.co", url)
    if not m:
        raise SystemExit(f"No se pudo deducir el 'ref' del proyecto a partir de: {url}")
    return m.group(1)


def aplicar_por_management_api(sql: str, ref: str, token: str) -> bool:
    import httpx

    url = f"https://api.supabase.com/v1/projects/{ref}/database/query"
    respuesta = httpx.post(url, json={"query": sql}, headers={"Authorization": f"Bearer {token}"}, timeout=120)
    if respuesta.status_code >= 300:
        print(f"[X] Management API respondio {respuesta.status_code}: {respuesta.text[:400]}")
        return False
    print("[OK] Migraciones aplicadas con la Management API.")
    return True


def aplicar_por_postgres(sql: str, db_url: str) -> bool:
    try:
        import psycopg
    except ImportError:
        print("[X] Falta psycopg. Instala con: pip install \"psycopg[binary]\"")
        return False
    with psycopg.connect(db_url, autocommit=True) as conexion:
        with conexion.cursor() as cur:
            cur.execute(sql)
    print("[OK] Migraciones aplicadas por conexion directa a Postgres.")
    return True


def main() -> int:
    env = leer_env(ROOT / ".env")
    url_supabase = env.get("SUPABASE_URL", "")
    if not url_supabase:
        print("[X] Falta SUPABASE_URL en el .env")
        return 1

    archivos = sorted(MIGRACIONES.glob("*.sql"))
    if not archivos:
        print("[X] No hay migraciones en supabase/migrations/")
        return 1
    sql = "\n".join(a.read_text(encoding="utf-8") for a in archivos)

    token = os.environ.get("SUPABASE_ACCESS_TOKEN") or env.get("SUPABASE_ACCESS_TOKEN")
    if token:
        ref = project_ref(url_supabase)
        if aplicar_por_management_api(sql, ref, token):
            return 0

    db_url = os.environ.get("SUPABASE_DB_URL") or env.get("SUPABASE_DB_URL")
    if db_url:
        if aplicar_por_postgres(sql, db_url):
            return 0

    print()
    print("=" * 78)
    print("No se pudo aplicar automaticamente. Copia este SQL en el panel de Supabase:")
    print("  Supabase > SQL Editor > New query > (pegar) > Run")
    print("=" * 78)
    print(sql)
    print("=" * 78)
    print("Alternativas: define SUPABASE_ACCESS_TOKEN (Management API) o SUPABASE_DB_URL")
    print("en el entorno y vuelve a ejecutar este script.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
