"""Rate limiting: proteccion anti-abuso.

Limita cuantos mensajes puede enviar un mismo usuario (por sesion o numero)
en una ventana de tiempo. Evita:
  - Abuso / spam contra el bot.
  - Costo runaway de tokens del LLM si alguien lo bombardea.

Implementacion: sliding window en memoria (suficiente para un solo proceso).
Para multiples procesos/servidores se usaria Redis, pero YAGNI por ahora.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    """Limita a `max_mensajes` por `ventana_s` segundos, por clave."""

    def __init__(self, max_mensajes: int = 30, ventana_s: int = 60) -> None:
        self.max_mensajes = max_mensajes
        self.ventana_s = ventana_s
        self._historial: dict[str, deque[float]] = defaultdict(deque)

    def permitido(self, clave: str) -> bool:
        """True si la clave puede enviar otro mensaje ahora; False si excedio."""
        ahora = time.monotonic()
        ventana = self._historial[clave]

        # Descarta timestamps fuera de la ventana.
        limite = ahora - self.ventana_s
        while ventana and ventana[0] < limite:
            ventana.popleft()

        if len(ventana) >= self.max_mensajes:
            return False

        ventana.append(ahora)
        return True

    def restantes(self, clave: str) -> int:
        """Cuantos mensajes le quedan a la clave en la ventana actual."""
        ahora = time.monotonic()
        ventana = self._historial[clave]
        limite = ahora - self.ventana_s
        while ventana and ventana[0] < limite:
            ventana.popleft()
        return max(0, self.max_mensajes - len(ventana))

    def reset(self, clave: str) -> None:
        self._historial.pop(clave, None)


MENSAJE_LIMITE = (
    "Esta enviando mensajes muy rapido. Espere un momentito y vuelva a "
    "escribir, por favor."
)
