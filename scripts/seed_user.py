"""Crea (o reutiliza) el usuario de prueba en Supabase Auth.

Uso:
    python scripts/seed_user.py --email orientador@alertatemprana.pe --password MiClaveFuerte

Usa la clave de servicio (`SUPABASE_SERVICE_ROLE_KEY` o `SUPABASE_KEY`) para
administrar los usuarios de `auth.users`. La clave de servicio NUNCA debe
llegar al frontend.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def leer_env(path: Path) -> dict[str, str]:
    valores: dict[str, str] = {}
    if not path.exists():
        return valores
    for linea in path.read_text(encoding="utf-8").splitlines():
        if "=" in linea and not linea.strip().startswith("#"):
            clave, valor = linea.split("=", 1)
            valores[clave.strip()] = valor.strip()
    return valores


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea un usuario en Supabase Auth")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--nombre", default="Orientador")
    parser.add_argument("--rol", default="orientador")
    args = parser.parse_args()

    env = leer_env(ROOT / ".env")
    url = env.get("SUPABASE_URL", "").rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[: -len("/rest/v1")]
    clave = env.get("SUPABASE_SERVICE_ROLE_KEY") or env.get("SUPABASE_KEY")
    if not url or not clave:
        print("[X] Faltan SUPABASE_URL y la clave de servicio en el .env")
        return 1

    import httpx

    headers = {"apikey": clave, "Authorization": f"Bearer {clave}", "Content-Type": "application/json"}
    payload = {
        "email": args.email,
        "password": args.password,
        "email_confirm": True,
        "user_metadata": {"nombre": args.nombre, "rol": args.rol},
    }

    with httpx.Client(timeout=30) as cliente:
        respuesta = cliente.post(f"{url}/auth/v1/admin/users", json=payload, headers=headers)
        if respuesta.status_code == 422 and "already" in respuesta.text.lower():
            print(f"[i] El usuario {args.email} ya existe.")
            return 0
        if respuesta.status_code >= 300:
            print(f"[X] {respuesta.status_code}: {respuesta.text[:400]}")
            return 1
        cuerpo = respuesta.json()
        print(f"[OK] Usuario creado: {cuerpo.get('email')} (id={cuerpo.get('id')})")
        print(f"     Contrasena: {args.password}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
