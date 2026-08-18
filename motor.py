"""Adaptador CLI del chatbot. Usa motor_core para la logica.

Uso:
    python motor.py
    python motor.py --guion otra/ruta.yaml
    python motor.py --sin-delay
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

from motor_core import RUTA_GUION_DEFAULT, ConversacionCore, Guion


class Tipeador:
    """Simula el delay antes de cada 'burbuja' del bot."""

    def __init__(self, min_s: float, max_s: float, activo: bool = True):
        self.min_s = min_s
        self.max_s = max_s
        self.activo = activo

    def esperar(self) -> None:
        if self.activo:
            time.sleep(random.uniform(self.min_s, self.max_s))


def mostrar_burbujas(mensajes: list[str], tipeador: Tipeador) -> None:
    for msg in mensajes:
        tipeador.esperar()
        print(f"\nBot > {msg}\n")


def escuchar() -> str:
    try:
        return input("Tu  > ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "salir"


def parsear_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Motor del chatbot KitraDep (CLI).")
    parser.add_argument("--guion", type=Path, default=RUTA_GUION_DEFAULT)
    parser.add_argument("--sin-delay", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parsear_args()

    if not args.guion.exists():
        print(f"ERROR: no encuentro el guion en {args.guion}", file=sys.stderr)
        return 1

    guion = Guion.cargar(args.guion)
    tipeador = Tipeador(
        min_s=float(guion.config.get("delay_min", 1.0)),
        max_s=float(guion.config.get("delay_max", 2.5)),
        activo=not args.sin_delay,
    )
    conv = ConversacionCore(guion=guion)

    print("=" * 66)
    print(f"  {guion.config.get('nombre_bot', 'Chatbot')} - modo terminal")
    print("  (escribi 'menu' para reiniciar, 'salir' para cerrar)")
    print("=" * 66)

    try:
        # Turno inicial del bot.
        mostrar_burbujas(conv.turno_bot(), tipeador)
        while not conv.terminada:
            entrada = escuchar()
            if not entrada:
                continue
            respuestas = conv.turno_usuario(entrada)
            mostrar_burbujas(respuestas, tipeador)
    except KeyboardInterrupt:
        print("\n\n[Conversacion interrumpida]")
        return 0

    print("\n[Fin de la conversacion]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
