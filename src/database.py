"""Persistencia local (SQLite) del dashboard legacy en Streamlit.

El dashboard en Angular + FastAPI + Supabase es el producto; este modulo se
mantiene como cliente de referencia y como respaldo offline.

Las contrasenas se guardan con hash argon2 (antes se guardaban en texto plano).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "sistema_orientacion.db"

PREFIXO_HASH = "$argon2"


def _hash_contrasena(password: str) -> str:
    from argon2 import PasswordHasher

    return PasswordHasher().hash(password)


def _verificar_contrasena(password: str, almacenado: str) -> bool:
    from argon2 import PasswordHasher
    from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

    if not almacenado:
        return False
    try:
        PasswordHasher().verify(almacenado, password)
        return True
    except (VerifyMismatchError, VerificationError, InvalidHashError, ValueError):
        return False


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Tabla de usuarios (Orientadores)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT
        )
    """
    )
    # Tabla de estudiantes evaluados
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dni TEXT,
            nombre TEXT,
            carrera TEXT,
            fecha_evaluacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            riesgo REAL,
            nivel TEXT
        )
    """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evaluaciones_dni ON evaluaciones (dni)")

    # Usuario admin por defecto: se crea con hash y se migra si estaba en claro.
    fila = cursor.execute("SELECT password FROM usuarios WHERE username = 'admin'").fetchone()
    if fila is None:
        cursor.execute(
            "INSERT INTO usuarios (username, password, nombre) VALUES (?, ?, ?)",
            ("admin", _hash_contrasena("123"), "Orientador"),
        )
    elif not str(fila[0]).startswith(PREFIXO_HASH):
        cursor.execute(
            "UPDATE usuarios SET password = ? WHERE username = 'admin'",
            (_hash_contrasena(str(fila[0])),),
        )
    conn.commit()
    conn.close()


def verificar_login(username: str, password: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, password FROM usuarios WHERE username = ?", (username,))
    resultado = cursor.fetchone()
    conn.close()
    if not resultado:
        return None
    nombre, almacenado = resultado
    if not _verificar_contrasena(password, almacenado):
        return None
    return nombre or "Orientador"


def guardar_evaluacion(dni, nombre, carrera, riesgo, nivel):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO evaluaciones (dni, nombre, carrera, riesgo, nivel)
        VALUES (?, ?, ?, ?, ?)
        """,
        (dni, nombre, carrera, riesgo, nivel),
    )
    conn.commit()
    conn.close()


def actualizar_evaluacion(evaluacion_id, dni, nombre, carrera, riesgo, nivel):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE evaluaciones
        SET dni=?, nombre=?, carrera=?, riesgo=?, nivel=?
        WHERE id=?
        """,
        (dni, nombre, carrera, riesgo, nivel, evaluacion_id),
    )
    conn.commit()
    actualizada = cursor.rowcount > 0
    conn.close()
    return actualizada


def eliminar_evaluacion(evaluacion_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM evaluaciones WHERE id=?", (evaluacion_id,))
    conn.commit()
    eliminada = cursor.rowcount > 0
    conn.close()
    return eliminada


def obtener_historial():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM evaluaciones ORDER BY fecha_evaluacion DESC", conn)
    conn.close()
    return df


# Inicializar al importar
init_db()
