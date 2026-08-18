"""Core del chatbot - logica pura, sin I/O.

Este modulo NO sabe si esta corriendo en terminal, en web o en WhatsApp.
Solo mantiene el estado de una conversacion y responde "que dice el bot
ahora" cuando se le entrega un mensaje del usuario.

Los adaptadores (motor.py para CLI, webapp.py para web) usan esta clase
y le agregan el I/O y los delays que correspondan a su medio.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

RUTA_GUION_DEFAULT = Path(__file__).parent / "flujo" / "guion.yaml"


# ============================================================================
# Guion
# ============================================================================


@dataclass
class Guion:
    """Guion parseado: config + estados + mensajes globales."""

    config: dict[str, Any]
    inicio: str
    estados: dict[str, dict[str, Any]]
    globales: dict[str, str]

    @classmethod
    def cargar(cls, ruta: Path) -> "Guion":
        with ruta.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(
            config=data.get("config", {}),
            inicio=data["inicio"],
            estados=data["estados"],
            globales=data.get("globales", {}),
        )

    def estado(self, nombre: str) -> dict[str, Any]:
        if nombre not in self.estados:
            raise KeyError(f"Estado '{nombre}' no existe en el guion.")
        return self.estados[nombre]


# ============================================================================
# Conversacion (core sin I/O)
# ============================================================================


@dataclass
class ConversacionCore:
    """Motor de estados puro. No hace print/input, solo procesa mensajes."""

    guion: Guion
    estado_actual: str = ""
    variables: dict[str, str] = field(default_factory=dict)
    terminada: bool = False

    def __post_init__(self) -> None:
        self.variables.update({k: str(v) for k, v in self.guion.config.items()})
        self.estado_actual = self.guion.inicio

    # ---- utilidades -------------------------------------------------------

    def formatear(self, texto: str) -> str:
        """Reemplaza {variable} por su valor. Si falta, deja el placeholder."""

        def reemplazo(match: re.Match[str]) -> str:
            clave = match.group(1)
            return self.variables.get(clave, match.group(0))

        return re.sub(r"\{(\w+)\}", reemplazo, texto)

    def _estado(self) -> dict[str, Any]:
        return self.guion.estado(self.estado_actual)

    # ---- turno del bot ----------------------------------------------------

    def turno_bot(self) -> list[str]:
        """Ejecuta estados tipo 'mensaje' hasta encontrar uno que requiera
        input del usuario (menu / entrada) o llegue a 'fin'.
        Devuelve la lista de mensajes que el bot dice en esta tanda.
        """
        mensajes: list[str] = []
        # Guardarrail para evitar loops infinitos por un guion mal armado.
        for _ in range(50):
            if self.estado_actual == "fin":
                self.terminada = True
                return mensajes

            estado = self._estado()
            texto = estado.get("mensaje", "")
            if texto:
                mensajes.append(self.formatear(texto).rstrip())

            tipo = estado["tipo"]
            if tipo == "mensaje":
                self.estado_actual = estado.get("ir_a", "fin")
                continue
            if tipo in {"menu", "entrada"}:
                return mensajes  # espera input del usuario
            raise ValueError(f"Tipo de estado desconocido: '{tipo}'")

        raise RuntimeError("turno_bot excedio 50 iteraciones (loop en guion?)")

    # ---- turno del usuario ------------------------------------------------

    def turno_usuario(self, mensaje: str) -> list[str]:
        """Procesa un mensaje del usuario y devuelve la respuesta del bot
        (que puede ser varias burbujas si vienen mensajes encadenados).
        Si el mensaje no matchea en un menu, dispara 'no_entiendo' y
        vuelve a mostrar el mismo estado.
        """
        if self.terminada:
            return []

        entrada = mensaje.strip()
        if not entrada:
            return []

        # Comandos globales (menu, salir) funcionan en cualquier estado.
        salto = self._comando_global(entrada)
        if salto is not None:
            self.estado_actual = salto
            return self.turno_bot()

        estado = self._estado()
        tipo = estado["tipo"]

        if tipo == "menu":
            siguiente = self._match_menu(estado, entrada)
            if siguiente is None:
                no_ent = self.guion.globales.get(
                    "no_entiendo",
                    "No te entendi, intenta con una opcion del menu.",
                )
                # Muestra "no entiendo" + repite el mensaje del estado actual.
                repetir = self.formatear(estado.get("mensaje", "")).rstrip()
                return [self.formatear(no_ent).rstrip(), repetir]
            self.estado_actual = siguiente
            return self.turno_bot()

        if tipo == "entrada":
            clave = estado.get("guardar_en")
            if clave:
                self.variables[clave] = entrada
            self.estado_actual = estado["ir_a"]
            return self.turno_bot()

        # Estados tipo 'mensaje' no deberian recibir input (turno_bot ya
        # los proceso), pero por defensivo: avanzamos igual.
        self.estado_actual = estado.get("ir_a", "fin")
        return self.turno_bot()

    # ---- helpers internos -------------------------------------------------

    def _match_menu(self, estado: dict[str, Any], entrada: str) -> str | None:
        norm = entrada.lower().strip()
        for opcion in estado.get("opciones", []):
            palabras = [p.lower() for p in opcion.get("detecta", [])]
            if any(norm == p or p in norm for p in palabras):
                clave = estado.get("guardar_en")
                if clave:
                    self.variables[clave] = opcion.get("valor", entrada)
                return opcion["ir_a"]
        return None

    def _comando_global(self, entrada: str) -> str | None:
        norm = entrada.lower().strip()
        if norm in {"menu", "inicio", "reiniciar", "reset"}:
            return self.guion.inicio
        if norm in {"salir", "exit", "quit", "chao"}:
            return "despedida" if "despedida" in self.guion.estados else "fin"
        return None
