"""Cliente LLM con backends intercambiables (Fake / Gemini).

El objetivo de este modulo es que TODO el resto del bot dependa de una
abstraccion (`LLMBackend`) y NO de un proveedor concreto. Asi podemos:

- Desarrollar y testear el bot completo SIN internet ni API key, usando
  `FakeLLM` (respuestas simuladas). Ideal para maquinas con firewall que
  bloquea la API de Gemini (ej. entorno corporativo).
- Cambiar a Gemini real en produccion con solo una variable de entorno,
  sin tocar una sola linea del router, los guardrails ni la webapp.

Se selecciona el backend con la variable de entorno LLM_BACKEND:
    LLM_BACKEND=fake     -> FakeLLM   (por defecto, offline)
    LLM_BACKEND=gemini   -> GeminiLLM (requiere GEMINI_API_KEY)

Este es el principio de Dependency Inversion (la 'D' de SOLID):
dependemos de una interfaz, no de una implementacion concreta.
"""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass


# ============================================================================
# Modelo de datos del historial
# ============================================================================


@dataclass
class Turno:
    """Un turno de conversacion. rol: 'user' o 'assistant'."""

    rol: str
    texto: str


# ============================================================================
# Interfaz abstracta
# ============================================================================


class LLMBackend(ABC):
    """Contrato que cualquier backend LLM debe cumplir."""

    @abstractmethod
    def generar(
        self,
        system_prompt: str,
        historial: list[Turno],
        mensaje: str,
    ) -> str:
        """Genera una respuesta del bot.

        Args:
            system_prompt: instrucciones de personalidad y limites.
            historial: turnos previos de la conversacion (memoria).
            mensaje: el mensaje actual del usuario.

        Returns:
            El texto de respuesta del bot.
        """
        raise NotImplementedError

    @property
    def nombre(self) -> str:
        return self.__class__.__name__


# ============================================================================
# Backend FAKE (offline, para desarrollo y tests)
# ============================================================================


class FakeLLM(LLMBackend):
    """Backend simulado que NO llama a ninguna API.

    Sirve para desarrollar y probar toda la maquinaria del bot (router,
    guardrails, memoria, integracion web) sin depender de Gemini.

    No es 'inteligente': responde con reglas simples basadas en palabras
    clave y un poco de la base de conocimiento inyectada. Suficiente para
    validar que el pipeline funciona de punta a punta.
    """

    def __init__(self, base_conocimiento: str = "") -> None:
        self.base_conocimiento = base_conocimiento

    def generar(
        self,
        system_prompt: str,
        historial: list[Turno],
        mensaje: str,
    ) -> str:
        m = mensaje.lower().strip()

        # Respuestas canned basadas en intencion detectada por keywords.
        # Esto imita groseramente lo que haria el LLM real, para poder
        # probar el flujo completo sin internet.
        if any(w in m for w in ("hola", "buenas", "buenos dias", "buenas tardes")):
            return (
                "Hola! Soy Kitra, la asistente virtual de KitraDep. "
                "En que te puedo ayudar hoy? [respuesta simulada - FakeLLM]"
            )
        if any(w in m for w in ("precio", "cuanto", "valor", "cuesta", "sale")):
            return (
                "Te cuento los valores: sesion particular/isapre $25.000, "
                "FONASA valor preferencial $20.000. Hay packs con descuento. "
                "Queres que te agende una evaluacion? [simulada - FakeLLM]"
            )
        if any(w in m for w in ("hora", "horario", "atienden", "abren")):
            return (
                "Atendemos de lunes a viernes de 8 a 21h y sabados de 9 a 13h. "
                "[respuesta simulada - FakeLLM]"
            )
        if any(w in m for w in ("donde", "direccion", "ubicacion", "llegar")):
            return (
                "Estamos en Llano Subercaseaux 3791, oficinas 208-209, San Miguel. "
                "[respuesta simulada - FakeLLM]"
            )
        if any(w in m for w in ("gracias", "genial", "perfecto", "dale")):
            return "De nada! Cualquier cosa me avisas. [simulada - FakeLLM]"

        # Fallback generico: eco reflexivo (util para ver el pipeline).
        return (
            f"Entiendo que dices: '{mensaje}'. Puedo ayudarte con informacion "
            "sobre servicios, precios, horarios o agendar una sesion. "
            "[respuesta simulada - FakeLLM]"
        )


# ============================================================================
# Backend GEMINI (real, para produccion / PC personal)
# ============================================================================


class GeminiLLM(LLMBackend):
    """Backend real usando Google Gemini.

    Import de google-generativeai es LAZY (dentro de __init__) para que este
    modulo se pueda importar en maquinas donde el paquete no esta instalado
    o la API esta bloqueada, siempre que no se instancie GeminiLLM.
    """

    def __init__(
        self,
        api_key: str | None = None,
        modelo: str = "gemini-2.0-flash-exp",
        timeout_s: int = 30,
    ) -> None:
        try:
            import google.generativeai as genai  # noqa: WPS433 (lazy import a proposito)
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "google-generativeai no esta instalado. Instalalo con:\n"
                "  uv pip install google-generativeai\n"
                "O usa LLM_BACKEND=fake para desarrollo offline."
            ) from exc

        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "Falta GEMINI_API_KEY. Ponela en tu .env o exportala. "
                "Obtene una gratis en https://aistudio.google.com/"
            )

        genai.configure(api_key=key)
        self._genai = genai
        self._modelo = modelo
        self._timeout_s = timeout_s

    def generar(
        self,
        system_prompt: str,
        historial: list[Turno],
        mensaje: str,
    ) -> str:
        # Gemini usa roles 'user' y 'model'. Mapeamos 'assistant' -> 'model'.
        contents = []
        for t in historial:
            rol = "model" if t.rol == "assistant" else "user"
            contents.append({"role": rol, "parts": [t.texto]})
        contents.append({"role": "user", "parts": [mensaje]})

        model = self._genai.GenerativeModel(
            model_name=self._modelo,
            system_instruction=system_prompt,
        )
        try:
            resp = model.generate_content(
                contents,
                request_options={"timeout": self._timeout_s},
            )
            return (resp.text or "").strip()
        except Exception as exc:  # pragma: no cover - depende de red
            # Fallback defensivo: nunca dejar al usuario sin respuesta.
            return (
                "Perdon, tuve un problema tecnico momentaneo. "
                "Podes repetir tu mensaje? Si el problema sigue, escribinos "
                f"directamente. [error interno: {type(exc).__name__}]"
            )


# ============================================================================
# Factory: elige el backend segun el entorno
# ============================================================================


def crear_llm(base_conocimiento: str = "") -> LLMBackend:
    """Devuelve el backend LLM segun la variable de entorno LLM_BACKEND.

    - 'fake' (default): FakeLLM, offline, para desarrollo.
    - 'gemini': GeminiLLM real.
    """
    backend = os.getenv("LLM_BACKEND", "fake").lower().strip()

    if backend == "gemini":
        modelo = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        return GeminiLLM(modelo=modelo)

    if backend == "fake":
        return FakeLLM(base_conocimiento=base_conocimiento)

    raise ValueError(
        f"LLM_BACKEND desconocido: '{backend}'. Usa 'fake' o 'gemini'."
    )
