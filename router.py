"""Router hibrido: orquesta guardrails, memoria y LLM.

Este es el cerebro que decide, en cada mensaje del usuario, que hacer:

  1. Pasar por los GUARDRAILS (emergencia / medico / handoff / fuera-tema).
     Si alguno se dispara, responde con un texto seguro predefinido y corta.
  2. Si no hay riesgo, arma el contexto (system prompt + base de conocimiento
     + historial) y se lo pasa al LLM para una respuesta natural.
  3. Mantiene la MEMORIA de la conversacion (ultimos N turnos).

La deteccion de intencion de agendar y el salto al flujo estricto de la
maquina de estados (motor_core) es el siguiente paso; queda marcado como
punto de extension (ver METODO manejar y el TODO).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import guardrails
from llm_client import LLMBackend, Turno, crear_llm

BASE_DIR = Path(__file__).parent
RUTA_PROMPT = BASE_DIR / "prompts" / "kitra.txt"
RUTA_KNOWLEDGE = BASE_DIR / "knowledge" / "kitradep.md"

# Cuantos turnos de historial recordamos y reenviamos al LLM.
MAX_TURNOS_MEMORIA = 20


# ============================================================================
# Carga de recursos (prompt + base de conocimiento)
# ============================================================================


def cargar_texto(ruta: Path) -> str:
    if not ruta.exists():
        return ""
    return ruta.read_text(encoding="utf-8").strip()


def construir_system_prompt() -> str:
    """Combina el prompt de personalidad con la base de conocimiento.

    La base de conocimiento se inyecta como contexto para que el LLM
    responda con datos reales del negocio y no invente.
    """
    prompt = cargar_texto(RUTA_PROMPT)
    kb = cargar_texto(RUTA_KNOWLEDGE)
    return (
        f"{prompt}\n\n"
        "## Base de conocimiento (usa SOLO estos datos)\n\n"
        f"{kb}\n"
    )


# ============================================================================
# Sesion de conversacion (memoria por usuario)
# ============================================================================


@dataclass
class SesionChat:
    """Estado de una conversacion con un usuario."""

    historial: list[Turno] = field(default_factory=list)

    def agregar(self, rol: str, texto: str) -> None:
        self.historial.append(Turno(rol=rol, texto=texto))
        # Recorte de memoria: nos quedamos con los ultimos N turnos.
        if len(self.historial) > MAX_TURNOS_MEMORIA:
            self.historial = self.historial[-MAX_TURNOS_MEMORIA:]

    def contexto(self) -> list[Turno]:
        """Historial SIN el mensaje actual (ese se pasa aparte)."""
        return list(self.historial)


# ============================================================================
# Router
# ============================================================================


@dataclass
class Router:
    """Orquesta el manejo de cada mensaje entrante."""

    llm: LLMBackend
    system_prompt: str
    handoff_contacto: str = "nuestro equipo"

    @classmethod
    def crear(cls, handoff_contacto: str = "nuestro equipo") -> "Router":
        system_prompt = construir_system_prompt()
        kb = cargar_texto(RUTA_KNOWLEDGE)
        # El FakeLLM aprovecha algo de la KB; el Gemini la recibe en el prompt.
        llm = crear_llm(base_conocimiento=kb)
        return cls(
            llm=llm,
            system_prompt=system_prompt,
            handoff_contacto=handoff_contacto,
        )

    def manejar(self, sesion: SesionChat, mensaje: str) -> str:
        """Procesa un mensaje del usuario y devuelve la respuesta del bot."""
        mensaje = mensaje.strip()
        if not mensaje:
            return ""

        # 1) Guardrails: lo mas critico primero.
        veredicto = guardrails.evaluar(mensaje)
        if veredicto.riesgo is not guardrails.Riesgo.NINGUNO:
            respuesta = guardrails.respuesta_para(veredicto, self.handoff_contacto)
            # Registramos igual en memoria para que el LLM tenga contexto luego.
            sesion.agregar("user", mensaje)
            sesion.agregar("assistant", respuesta)
            return respuesta

        # 2) TODO (siguiente iteracion): detectar intencion de agendar y saltar
        #    al flujo estricto de motor_core.ConversacionCore para recolectar
        #    datos con control total. Por ahora, el LLM guia el agendamiento
        #    segun las instrucciones del system prompt.

        # 3) Respuesta conversacional via LLM.
        contexto = sesion.contexto()
        respuesta = self.llm.generar(self.system_prompt, contexto, mensaje)

        sesion.agregar("user", mensaje)
        sesion.agregar("assistant", respuesta)
        return respuesta

    @property
    def backend(self) -> str:
        return self.llm.nombre
