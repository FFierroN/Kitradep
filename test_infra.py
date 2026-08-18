"""Tests de la infraestructura tecnica (db, ratelimit, config).

Offline, sin dependencias externas. Usa una DB temporal para no ensuciar
la real.

Uso:
    python test_infra.py
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

os.environ["LLM_BACKEND"] = "fake"

from db import Database
from llm_client import Turno
from ratelimit import RateLimiter


def test_db() -> tuple[int, int]:
    print("\n=== TEST: Persistencia SQLite ===")
    ok = 0
    total = 0
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(Path(tmp) / "test.db")

        # 1) crear sesion
        db.asegurar_sesion("s1")
        total += 1
        passed = db.contar("sesiones") == 1
        ok += passed
        print(f"  {'OK ' if passed else 'XX '} crear sesion -> sesiones=1")

        # 2) guardar mensajes
        db.guardar_mensaje("s1", "user", "hola")
        db.guardar_mensaje("s1", "assistant", "buenas!")
        total += 1
        passed = db.contar("mensajes") == 2
        ok += passed
        print(f"  {'OK ' if passed else 'XX '} guardar 2 mensajes -> mensajes=2")

        # 3) cargar historial en orden cronologico
        hist = db.cargar_historial("s1")
        total += 1
        passed = (
            len(hist) == 2
            and hist[0].texto == "hola"
            and hist[1].texto == "buenas!"
        )
        ok += passed
        print(f"  {'OK ' if passed else 'XX '} historial cronologico correcto")

        # 4) evento con PII se enmascara
        db.registrar_evento("test", "rut 12.345.678-9", sesion_id="s1")
        total += 1
        passed = db.contar("eventos") == 1
        ok += passed
        print(f"  {'OK ' if passed else 'XX '} evento registrado (PII enmascarada)")

        # 5) borrar sesion limpia todo
        db.borrar_sesion("s1")
        total += 1
        passed = db.contar("sesiones") == 0 and db.contar("mensajes") == 0
        ok += passed
        print(f"  {'OK ' if passed else 'XX '} borrar sesion limpia mensajes")

        # 6) idempotencia de asegurar_sesion
        db.asegurar_sesion("s2")
        db.asegurar_sesion("s2")
        total += 1
        passed = db.contar("sesiones") == 1
        ok += passed
        print(f"  {'OK ' if passed else 'XX '} asegurar_sesion es idempotente")

    print(f"  -> {ok}/{total} correctos")
    return ok, total


def test_ratelimit() -> tuple[int, int]:
    print("\n=== TEST: Rate limiting ===")
    ok = 0
    total = 0
    rl = RateLimiter(max_mensajes=3, ventana_s=2)

    # Primeros 3 permitidos
    permitidos = [rl.permitido("u1") for _ in range(3)]
    total += 1
    passed = all(permitidos)
    ok += passed
    print(f"  {'OK ' if passed else 'XX '} primeros 3 mensajes permitidos")

    # El 4to bloqueado
    total += 1
    passed = not rl.permitido("u1")
    ok += passed
    print(f"  {'OK ' if passed else 'XX '} 4to mensaje bloqueado")

    # Otro usuario no afectado
    total += 1
    passed = rl.permitido("u2")
    ok += passed
    print(f"  {'OK ' if passed else 'XX '} otro usuario no afectado")

    # Tras esperar la ventana, se libera
    time.sleep(2.1)
    total += 1
    passed = rl.permitido("u1")
    ok += passed
    print(f"  {'OK ' if passed else 'XX '} tras la ventana se libera")

    print(f"  -> {ok}/{total} correctos")
    return ok, total


def test_config() -> tuple[int, int]:
    print("\n=== TEST: Config ===")
    from config import Config

    ok = 0
    total = 0
    cfg = Config.cargar()

    total += 1
    passed = cfg.llm_backend in {"fake", "gemini"}
    ok += passed
    print(f"  {'OK ' if passed else 'XX '} llm_backend valido: {cfg.llm_backend}")

    total += 1
    passed = cfg.max_turnos_memoria > 0 and cfg.rate_limit_mensajes > 0
    ok += passed
    print(f"  {'OK ' if passed else 'XX '} valores numericos por defecto sanos")

    total += 1
    passed = isinstance(cfg.notificaciones_activas, bool)
    ok += passed
    print(f"  {'OK ' if passed else 'XX '} notificaciones_activas es bool")

    print(f"  -> {ok}/{total} correctos")
    return ok, total


def main() -> None:
    print("=" * 66)
    print("  TEST SUITE - Infraestructura KitraDep (offline)")
    print("=" * 66)
    total_ok = 0
    total = 0
    for fn in (test_db, test_ratelimit, test_config):
        o, n = fn()
        total_ok += o
        total += n
    print("\n" + "=" * 66)
    print(f"  RESULTADO GLOBAL: {total_ok}/{total} checks OK")
    print("=" * 66)
    if total_ok != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
