"""Persistencia en SQLite (memoria que sobrevive reinicios).

Guarda conversaciones, sesiones y un log de eventos de auditoria. Usa el
modulo sqlite3 de la stdlib (sin ORM: YAGNI para este volumen).

Diseno pensado para bajo/medio volumen (una clinica): se abre una conexion
por operacion, lo cual es simple y seguro con FastAPI (que puede atender
requests en distintos hilos). Para alto volumen se migraria a Postgres,
pero el resto del codigo no tendria que cambiar (esta encapsulado aca).

Nota de privacidad: el texto de las conversaciones se guarda tal cual
(es necesario para dar el servicio y la memoria del bot). El log de
auditoria (tabla eventos) guarda el texto ENMASCARADO (sin PII), para
poder depurar sin exponer datos personales (Ley 19.628 / 21.719).
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import guardrails
from llm_client import Turno

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sesiones (
    sesion_id   TEXT PRIMARY KEY,
    canal       TEXT NOT NULL DEFAULT 'web',
    creada      TEXT NOT NULL,
    ultimo_acceso TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mensajes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id   TEXT NOT NULL,
    rol         TEXT NOT NULL,          -- 'user' | 'assistant'
    texto       TEXT NOT NULL,
    ts          TEXT NOT NULL,
    FOREIGN KEY (sesion_id) REFERENCES sesiones(sesion_id)
);

CREATE INDEX IF NOT EXISTS idx_mensajes_sesion ON mensajes(sesion_id);

CREATE TABLE IF NOT EXISTS eventos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id   TEXT,
    tipo        TEXT NOT NULL,          -- 'guardrail', 'error', 'handoff', ...
    detalle     TEXT,                   -- SIN PII (enmascarado)
    ts          TEXT NOT NULL
);
"""


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    """Fachada de persistencia. Instanciar una vez y compartir."""

    def __init__(self, ruta: Path) -> None:
        self.ruta = ruta
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.ruta, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    # ---- sesiones ---------------------------------------------------------

    def asegurar_sesion(self, sesion_id: str, canal: str = "web") -> None:
        """Crea la sesion si no existe; si existe, actualiza ultimo_acceso."""
        ahora = _ahora()
        with self._conn() as conn:
            existe = conn.execute(
                "SELECT 1 FROM sesiones WHERE sesion_id = ?", (sesion_id,)
            ).fetchone()
            if existe:
                conn.execute(
                    "UPDATE sesiones SET ultimo_acceso = ? WHERE sesion_id = ?",
                    (ahora, sesion_id),
                )
            else:
                conn.execute(
                    "INSERT INTO sesiones (sesion_id, canal, creada, ultimo_acceso) "
                    "VALUES (?, ?, ?, ?)",
                    (sesion_id, canal, ahora, ahora),
                )

    # ---- mensajes ---------------------------------------------------------

    def guardar_mensaje(self, sesion_id: str, rol: str, texto: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO mensajes (sesion_id, rol, texto, ts) VALUES (?, ?, ?, ?)",
                (sesion_id, rol, texto, _ahora()),
            )

    def cargar_historial(self, sesion_id: str, limite: int = 20) -> list[Turno]:
        """Devuelve los ultimos `limite` turnos en orden cronologico."""
        with self._conn() as conn:
            filas = conn.execute(
                "SELECT rol, texto FROM mensajes WHERE sesion_id = ? "
                "ORDER BY id DESC LIMIT ?",
                (sesion_id, limite),
            ).fetchall()
        # Venian en orden descendente; los damos vuelta a cronologico.
        return [Turno(rol=f["rol"], texto=f["texto"]) for f in reversed(filas)]

    def borrar_sesion(self, sesion_id: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM mensajes WHERE sesion_id = ?", (sesion_id,))
            conn.execute("DELETE FROM sesiones WHERE sesion_id = ?", (sesion_id,))

    # ---- eventos (auditoria, SIN PII) -------------------------------------

    def registrar_evento(
        self, tipo: str, detalle: str = "", sesion_id: str | None = None
    ) -> None:
        detalle_seguro = guardrails.enmascarar_pii(detalle)
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO eventos (sesion_id, tipo, detalle, ts) VALUES (?, ?, ?, ?)",
                (sesion_id, tipo, detalle_seguro, _ahora()),
            )

    # ---- metricas simples -------------------------------------------------

    def contar(self, tabla: str) -> int:
        if tabla not in {"sesiones", "mensajes", "eventos"}:
            raise ValueError(f"Tabla no permitida: {tabla}")
        with self._conn() as conn:
            fila = conn.execute(f"SELECT COUNT(*) AS n FROM {tabla}").fetchone()
        return int(fila["n"])
