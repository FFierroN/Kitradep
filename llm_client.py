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

        # El FakeLLM imita groseramente el FLUJO CONSULTIVO (conversar antes de
        # precios) para poder probar el pipeline offline. NO es inteligente: el
        # bot real (Gemini) leera el system prompt y conversara de verdad. Aca
        # solo simulamos el espiritu de cada fase.

        # Fase 1: conexion / saludo -> calido + pregunta abierta (nunca precio).
        if any(w in m for w in ("hola", "buenas", "buenos dias", "buenas tardes", "que tal")):
            return (
                "Hola! Que bueno que nos escribas, soy Kitra de KitraDep. "
                "Contame, en que te puedo ayudar? Que es lo que te esta pasando? "
                "[simulada - FakeLLM]"
            )

        # Postoperatorio -> empatia + acompanamiento + descubrimiento.
        if any(w in m for w in ("operac", "operado", "opere", "cirugia", "postop", "post op")):
            return (
                "Entiendo, un postoperatorio necesita un acompanamiento cercano. "
                "Justo eso es lo nuestro: el kinesiologo te acompana *toda la sesion*, "
                "uno a uno. Hace cuanto fue la operacion y como te sentis con el "
                "movimiento? [simulada - FakeLLM]"
            )

        # Deporte -> reintegro deportivo + descubrimiento.
        if any(w in m for w in ("deporte", "corr", "futbol", "gimnasio", "entren", "running", "crossfit")):
            return (
                "Que bueno que hagas deporte! Trabajamos mucho el reintegro deportivo "
                "para que vuelvas a tu actividad de forma segura. Contame que "
                "molestia tenes y hace cuanto la arrastras? [simulada - FakeLLM]"
            )

        # Dolor / lesion -> empatia + descubrimiento (no diagnostica).
        if any(w in m for w in ("dolor", "duele", "lesion", "molest", "rodilla", "espalda", "hombro", "tobillo")):
            return (
                "Uy, entiendo que debe ser incomodo. Para ayudarte mejor, contame: "
                "hace cuanto lo tenes y te afecta en tu dia a dia o en alguna "
                "actividad? Tenes alguna orden medica? [simulada - FakeLLM]"
            )

        # Precio -> NO tirar cifra directa: primero contexto + preguntar prevision.
        if any(w in m for w in ("precio", "cuanto", "valor", "cuesta", "sale", "cobran")):
            return (
                "Con gusto te cuento los valores. Antes, para darte el correcto: "
                "tene en cuenta que cada sesion es *personalizada, uno a uno* con "
                "un kinesiologo. Con que prevision te atenderias: Fonasa, Isapre "
                "o particular? [simulada - FakeLLM]"
            )

        # Prevision declarada -> ahora si, valores enmarcados en el valor.
        if "fonasa" in m:
            return (
                "Perfecto. Con Fonasa manejamos un *valor preferencial* (no somos "
                "centro adherido, no trabajamos con bonos): la sesion sale $20.000, "
                "y hay packs con descuento. Te gustaria que agendemos tu evaluacion "
                "inicial? [simulada - FakeLLM]"
            )
        if any(w in m for w in ("isapre", "particular")):
            return (
                "Buenisimo. El valor por sesion es $25.000, con packs de 5 y 10 con "
                "descuento, y te damos boleta para el reembolso. Lo ideal es partir "
                "con la evaluacion inicial. Te agendo? [simulada - FakeLLM]"
            )

        # Horarios / ubicacion (info util sin cortar la conversacion).
        if any(w in m for w in ("hora", "horario", "atienden", "abren")):
            return (
                "Atendemos de lunes a viernes de 8 a 21h y sabados de 9 a 13h. "
                "Preferis en la manana o en la tarde? [simulada - FakeLLM]"
            )
        if any(w in m for w in ("donde", "direccion", "ubicacion", "llegar")):
            return (
                "Estamos en Llano Subercaseaux 3791, oficinas 208-209, San Miguel "
                "(a pasos del metro San Miguel). [simulada - FakeLLM]"
            )

        # Aceptacion de agendar.
        if any(w in m for w in ("si", "dale", "agenda", "agendar", "quiero", "reservar")):
            return (
                "Genial! Para dejar todo listo necesito tu *nombre, RUT, correo, "
                "telefono y prevision*, y si preferis manana o tarde. Un kine "
                "confirma el horario exacto contigo. [simulada - FakeLLM]"
            )

        if any(w in m for w in ("gracias", "genial", "perfecto")):
            return "De nada! Aca estoy para lo que necesites. [simulada - FakeLLM]"

        # Fallback: reconducir con calidez hacia el descubrimiento.
        return (
            f"Te leo: '{mensaje}'. Contame un poco mas de lo que necesitas asi "
            "te ayudo mejor. Buscas rehabilitacion para alguna molestia o lesion? "
            "[simulada - FakeLLM]"
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
