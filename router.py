"""Router hibrido: orquesta guardrails, memoria y LLM.

Este es el cerebro que decide, en cada mensaje del usuario, que hacer:

  1. Pasar por los GUARDRAILS (emergencia / medico / handoff / fuera-tema).
     Si alguno se dispara, responde con un texto seguro predefinido y corta.
  2. Si no hay riesgo, arma el contexto (system prompt + base de conocimiento
     + historial) y se lo pasa al LLM para una respuesta natural.
  3. Mantiene la MEMORIA de la conversacion (ultimos N turnos).

  4. Maneja el agendamiento (link de AgendaPro, datos por chat, "ya agende")
     de forma determinista, y controla que Kitra no insista con agendar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import agendamiento
import guardrails
from agendamiento import Agendamiento
from llm_client import LLMBackend, Turno, crear_llm
BASE_DIR = Path(__file__).parent
RUTA_PROMPT = BASE_DIR / "prompts" / "kitra.txt"
RUTA_KNOWLEDGE = BASE_DIR / "knowledge" / "kitradep.md"

# Cuantos turnos de historial recordamos y reenviamos al LLM.
MAX_TURNOS_MEMORIA = 20

# Control de invitaciones a agendar (para no sonar insistente).
MAX_INVITACIONES = 3          # tope por conversacion
ESPERA_SIN_SENAL = 4          # mensajes del paciente antes de re-invitar
ESPERA_CON_SENAL = 2          # ...o menos si muestra interes

NOTA_NO_INVITAR = (
    "\n\n## Nota interna del sistema (no la menciones)\n"
    "En ESTE mensaje NO invites a agendar ni preguntes si quiere agendar. "
    "Responde solo lo que la persona pregunta."
)
NOTA_LINK_ENVIADO = (
    "\n\n## Nota interna del sistema (no la menciones)\n"
    "Ya se le envio el link de AgendaPro. NO vuelvas a invitar a agendar. "
    "Si pregunta como agendar, recuerdale el link: " + agendamiento.LINK_AGENDA
)
NOTA_ESPERANDO_DATOS = (
    "\n\n## Nota interna del sistema (no la menciones)\n"
    "Le pediste sus datos para agendar por chat. Responde su duda en corto y "
    "recuerdale que puede enviar los datos cuando quiera."
)


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
    # Recolector de agendamiento activo (None = conversacion normal).
    agenda: Agendamiento | None = None
    # Control de invitaciones a agendar.
    invitaciones: int = 0              # cuantas veces Kitra invito a agendar
    mensajes_desde_invitacion: int = 0  # mensajes del paciente desde la ultima
    ultima_fue_invitacion: bool = False  # el ultimo mensaje de Kitra invitaba?
    link_enviado: bool = False          # ya recibio el link de AgendaPro?

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
class RespuestaBot:
    """Respuesta del router con metadata para que el caller decida acciones.

    - texto: lo que se le muestra al usuario.
    - riesgo: el veredicto de guardrails (NINGUNO si fue conversacion normal).
    - notificar_staff: True si el caller deberia avisar al equipo (handoff/urgencia).
    """

    texto: str
    riesgo: guardrails.Riesgo = guardrails.Riesgo.NINGUNO
    notificar_staff: bool = False
    # Cuando se completa un agendamiento, trae el resumen de datos para el
    # staff (PII real). El caller decide como notificar (email/log).
    datos_agendamiento: str | None = None


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

    def manejar_detallado(self, sesion: SesionChat, mensaje: str) -> RespuestaBot:
        """Procesa un mensaje y devuelve texto + metadata de evento."""
        mensaje = mensaje.strip()
        if not mensaje:
            return RespuestaBot(texto="")

        # 1) Guardrails: lo mas critico primero. La seguridad SIEMPRE gana,
        #    incluso en medio de un agendamiento (una urgencia lo aborta).
        veredicto = guardrails.evaluar(mensaje)
        if veredicto.riesgo is not guardrails.Riesgo.NINGUNO:
            sesion.agenda = None  # cortamos cualquier recoleccion en curso
            respuesta = guardrails.respuesta_para(veredicto, self.handoff_contacto)
            sesion.ultima_fue_invitacion = False
            sesion.agregar("user", mensaje)
            sesion.agregar("assistant", respuesta)
            # Urgencia y handoff ameritan avisar al staff.
            notificar = veredicto.riesgo in {
                guardrails.Riesgo.EMERGENCIA,
                guardrails.Riesgo.HANDOFF,
            }
            return RespuestaBot(
                texto=respuesta,
                riesgo=veredicto.riesgo,
                notificar_staff=notificar,
            )

        # 2) Agendamiento por chat en curso: leemos los datos de forma
        #    determinista (sin LLM). Si en vez de datos hace una pregunta,
        #    la responde el LLM y el recolector sigue esperando.
        if sesion.agenda is not None and sesion.agenda.activo:
            if "?" in mensaje and not agendamiento.extraer_datos(mensaje)[0]:
                return self._responder_llm(sesion, mensaje, NOTA_ESPERANDO_DATOS)
            return self._paso_agenda(sesion, mensaje)

        # 3) Ya tiene el link y avisa que agendo -> agradecer + tips.
        if sesion.link_enviado and agendamiento.ya_agendo(mensaje):
            return self._fijo(sesion, mensaje, agendamiento.mensaje_gracias())

        # 4) No puede/quiere usar el link -> pedir los datos en un mensaje.
        contexto_agenda = (sesion.link_enviado or sesion.ultima_fue_invitacion
                           or agendamiento.detectar_intencion(mensaje))
        if contexto_agenda and agendamiento.prefiere_chat(mensaje):
            sesion.agenda = Agendamiento()
            return self._fijo(sesion, mensaje, sesion.agenda.iniciar())

        # 5) Acepta agendar (lo pide, o dice "si" a una invitacion) -> link.
        if agendamiento.detectar_intencion(mensaje) or (
            sesion.ultima_fue_invitacion and agendamiento.es_afirmativo(mensaje)
        ):
            sesion.link_enviado = True
            return self._fijo(sesion, mensaje, agendamiento.mensaje_link())

        # 6) Respuesta conversacional via LLM (sin insistir con agendar).
        return self._responder_llm(sesion, mensaje)

    def _puede_invitar(self, sesion: SesionChat, mensaje: str) -> bool:
        """Decide si Kitra puede invitar a agendar en este mensaje."""
        if sesion.link_enviado or sesion.invitaciones >= MAX_INVITACIONES:
            return False
        if sesion.invitaciones == 0:
            return True
        espera = (ESPERA_CON_SENAL if agendamiento.hay_senal_interes(mensaje)
                  else ESPERA_SIN_SENAL)
        return sesion.mensajes_desde_invitacion >= espera

    def _responder_llm(
        self, sesion: SesionChat, mensaje: str, nota: str | None = None
    ) -> RespuestaBot:
        sesion.mensajes_desde_invitacion += 1
        puede_invitar = self._puede_invitar(sesion, mensaje)
        if nota is None and not puede_invitar:
            nota = NOTA_LINK_ENVIADO if sesion.link_enviado else NOTA_NO_INVITAR
        contexto = sesion.contexto()
        respuesta = self.llm.generar(self.system_prompt + (nota or ""), contexto, mensaje)
        # WhatsApp marca negrita con *un* asterisco; Gemini a veces usa dos.
        respuesta = re.sub(r"\*\*(.+?)\*\*", r"*\1*", respuesta)

        # Red de seguridad: si igual invito sin permiso (y el paciente no
        # pregunto por agendar/horarios), quitamos esa frase.
        if (not puede_invitar and agendamiento.es_invitacion(respuesta)
                and not agendamiento.hay_senal_interes(mensaje)):
            respuesta = agendamiento.quitar_invitacion(respuesta)

        self._registrar_invitacion(sesion, respuesta)
        sesion.agregar("user", mensaje)
        sesion.agregar("assistant", respuesta)
        return RespuestaBot(texto=respuesta)

    def _registrar_invitacion(self, sesion: SesionChat, respuesta: str) -> None:
        invito = (not sesion.link_enviado and sesion.agenda is None
                  and agendamiento.es_invitacion(respuesta))
        sesion.ultima_fue_invitacion = invito
        if invito:
            sesion.invitaciones += 1
            sesion.mensajes_desde_invitacion = 0

    def _fijo(self, sesion: SesionChat, mensaje: str, texto: str) -> RespuestaBot:
        """Respuesta predefinida (no pasa por el LLM)."""
        sesion.ultima_fue_invitacion = False
        sesion.agregar("user", mensaje)
        sesion.agregar("assistant", texto)
        return RespuestaBot(texto=texto)

    def _paso_agenda(self, sesion: SesionChat, mensaje: str) -> RespuestaBot:
        """Avanza el recolector de agendamiento y arma la RespuestaBot."""
        assert sesion.agenda is not None  # garantizado por el caller
        paso = sesion.agenda.procesar(mensaje)
        sesion.agregar("user", mensaje)
        sesion.agregar("assistant", paso.texto)
        if paso.completado or paso.cancelado:
            sesion.agenda = None  # cerramos el flujo
        return RespuestaBot(
            texto=paso.texto,
            notificar_staff=paso.completado,
            datos_agendamiento=paso.datos_staff,
        )

    def manejar(self, sesion: SesionChat, mensaje: str) -> str:
        """Version simple: devuelve solo el texto (compatibilidad)."""
        return self.manejar_detallado(sesion, mensaje).texto

    @property
    def backend(self) -> str:
        return self.llm.nombre
