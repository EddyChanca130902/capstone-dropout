"""Tests de la serializacion de fechas hacia Supabase (bug 500 al derivar)."""

from __future__ import annotations

from datetime import datetime, timezone

from api.routers.intervenciones import _serializable


def test_serializable_convierte_fechas_a_iso():
    fila = {
        "dni": "70123456",
        "fecha_deteccion": datetime(2026, 10, 22, 10, 0, tzinfo=timezone.utc),
        "fecha_inicio": None,
        "estado": "DERIVADA",
    }
    salida = _serializable(fila)
    assert isinstance(salida["fecha_deteccion"], str)
    assert salida["fecha_deteccion"].startswith("2026-10-22T10:00:00")
    assert salida["fecha_inicio"] is None
    assert salida["estado"] == "DERIVADA"
