"""Flujo de agendamiento: recoleccion DETERMINISTA de datos del paciente.

Cuando la conversacion (via LLM) llega al punto de que la persona quiere
agendar, el control pasa a este modulo. La idea es NO delegar la captura de
datos sensibles al LLM, porque:

  - Un LLM puede alucinar, olvidar un campo o "confirmar" datos inventados.
  - Los datos de agendamiento (nombre, RUT, correo, telefono) tienen que ser
    EXACTOS: se los mandamos al staff para contactar al paciente.
  - Validar un RUT chileno o un email es logica determinista, no probabilistica.

Por eso este recolector es una pequena maquina de estados pura (sin I/O ni
LLM): pregunta un campo a la vez, valida la respuesta, y solo avanza cuando el
dato es correcto. Es totalmente testeable offline.

Este modulo NO sabe de web, terminal ni WhatsApp: solo procesa texto y
devuelve texto. Los adaptadores (router / webapp) se encargan del I/O y de
notificar al staff cuando se completa.

Diseno LLM-agnostico a proposito: el mismo flujo corre con FakeLLM (tests) o
con Gemini real. El "function calling" nativo de Gemini es un pulido opcional
que puede envolver a este mismo recolector mas adelante.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

# Link de autogestion (fuente de verdad: knowledge/kitradep.md).
LINK_AGENDA = "https://encuadrado.com/centro/kitradep"

# Palabras para abortar el flujo en cualquier momento.
_CANCELAR = {"cancelar", "cancela", "olvidalo", "dejalo", "despues", "mejor no"}


# ============================================================================
# Deteccion de intencion de agendar
# ============================================================================

# Frases que indican que la persona QUIERE dar el paso de reservar una hora.
# Se busca como subcadena sobre el mensaje en minusculas. Deliberadamente
# especificas para no dispararse en medio de la conversacion consultiva
# (ej: NO incluimos "hora" sola, que aparece en "a que hora atienden").
_INTENCION = [
    "quiero agendar",
    "quiero reservar",
    "quiero una hora",
    "quiero tomar hora",
    "quiero sacar hora",
    "quiero pedir hora",
    "necesito una hora",
    "necesito agendar",
    "sacar una hora",
    "sacar hora",
    "pedir hora",
    "tomar hora",
    "reservar una hora",
    "reservar hora",
    "agendar una",
    "agendar mi",
    "agendar sesion",
    "agendemos",
    "me agendas",
    "me agenda",
    "dame una hora",
    "quiero mi evaluacion",
    "agendar evaluacion",
]


def detectar_intencion(mensaje: str) -> bool:
    """True si el mensaje expresa intencion clara de agendar una hora."""
    m = mensaje.lower().strip()
    return any(frase in m for frase in _INTENCION)


def quiere_cancelar(mensaje: str) -> bool:
    """True si el usuario quiere abortar el agendamiento en curso."""
    return mensaje.lower().strip() in _CANCELAR


# ============================================================================
# Validadores y normalizadores de campos
# ============================================================================
#
# Cada validador recibe el texto crudo y devuelve:
#   - None si es valido (y se normaliza aparte), o
#   - un string con el mensaje de error (calido) para volver a preguntar.


_EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")
_FONO_RE = re.compile(r"^(\+?56)?0?9\d{8}$")


def _validar_nombre(valor: str) -> str | None:
    limpio = valor.strip()
    if len(limpio) < 3 or " " not in limpio:
        return (
            "Necesito tu *nombre y apellido* para dejarlo en la ficha. "
            "Me lo pasas completo?"
        )
    if any(ch.isdigit() for ch in limpio):
        return "Un nombre no lleva numeros. Me lo escribis de nuevo?"
    return None


def _norm_nombre(valor: str) -> str:
    # Title-case simple respetando espacios simples.
    return " ".join(p.capitalize() for p in valor.split())


def _validar_rut(valor: str) -> str | None:
    v = valor.replace(".", "").replace("-", "").strip().upper()
    if len(v) < 2 or not v[:-1].isdigit():
        return "Ese RUT no lo entendi. Escribilo asi: *12.345.678-9*"
    cuerpo, dv = v[:-1], v[-1]
    suma, factor = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    dv_calc = {10: "K", 11: "0"}.get(resto, str(resto))
    if dv != dv_calc:
        return "Ese RUT no me cuadra (el digito verificador). Lo revisas?"
    return None


def _norm_rut(valor: str) -> str:
    v = valor.replace(".", "").replace("-", "").strip().upper()
    cuerpo, dv = v[:-1], v[-1]
    # Formato con puntos: 12.345.678-9
    partes = []
    while len(cuerpo) > 3:
        partes.insert(0, cuerpo[-3:])
        cuerpo = cuerpo[:-3]
    partes.insert(0, cuerpo)
    return ".".join(partes) + "-" + dv


def _validar_correo(valor: str) -> str | None:
    if not _EMAIL_RE.match(valor.strip()):
        return "Ese correo no parece valido. Me lo pasas de nuevo?"
    return None


def _validar_fono(valor: str) -> str | None:
    limpio = re.sub(r"[\s()-]", "", valor.strip())
    if not _FONO_RE.match(limpio):
        return (
            "Necesito un celular chileno valido (9 + 8 digitos). "
            "Ej: *9 1234 5678*"
        )
    return None


def _norm_fono(valor: str) -> str:
    limpio = re.sub(r"[\s()-]", "", valor.strip())
    # Nos quedamos con los ultimos 9 digitos (9XXXXXXXX).
    digitos = re.sub(r"\D", "", limpio)[-9:]
    return f"+56 {digitos[0]} {digitos[1:5]} {digitos[5:]}"


_PREVISIONES = {
    "fonasa": "FONASA",
    "isapre": "ISAPRE",
    "particular": "Particular",
}


def _validar_prevision(valor: str) -> str | None:
    m = valor.lower()
    if any(k in m for k in _PREVISIONES):
        return None
    return "No te entendi la prevision. Es *FONASA*, *ISAPRE* o *particular*?"


def _norm_prevision(valor: str) -> str:
    m = valor.lower()
    for k, etiqueta in _PREVISIONES.items():
        if k in m:
            return etiqueta
    return valor.strip()


def _validar_franja(valor: str) -> str | None:
    m = valor.lower()
    if any(k in m for k in ("manana", "mañana", "am", "temprano")):
        return None
    if any(k in m for k in ("tarde", "pm", "noche")):
        return None
    return "Preferis en la *manana* o en la *tarde*?"


def _norm_franja(valor: str) -> str:
    m = valor.lower()
    if any(k in m for k in ("manana", "mañana", "am", "temprano")):
        return "Manana (AM)"
    return "Tarde (PM)"


# ============================================================================
# Definicion de los campos a recolectar
# ============================================================================


@dataclass(frozen=True)
class Campo:
    """Un dato a capturar: como preguntarlo, como validarlo y normalizarlo."""

    clave: str
    etiqueta: str
    pregunta: str
    validar: Callable[[str], str | None]
    normalizar: Callable[[str], str] = staticmethod(lambda s: s.strip())


# El orden sigue el "Proceso de agendamiento" de la base de conocimiento.
CAMPOS: list[Campo] = [
    Campo(
        clave="nombre",
        etiqueta="Nombre",
        pregunta="Genial! Para dejar tu hora, cual es tu *nombre y apellido*?",
        validar=_validar_nombre,
        normalizar=_norm_nombre,
    ),
    Campo(
        clave="rut",
        etiqueta="RUT",
        pregunta="Perfecto. Cual es tu *RUT*? (ej: 12.345.678-9)",
        validar=_validar_rut,
        normalizar=_norm_rut,
    ),
    Campo(
        clave="correo",
        etiqueta="Correo",
        pregunta="Anotado. A que *correo* te enviamos la confirmacion?",
        validar=_validar_correo,
        normalizar=lambda s: s.strip().lower(),
    ),
    Campo(
        clave="telefono",
        etiqueta="Telefono",
        pregunta="Y un *telefono* de contacto? (celular)",
        validar=_validar_fono,
        normalizar=_norm_fono,
    ),
    Campo(
        clave="prevision",
        etiqueta="Prevision",
        pregunta="Con que *prevision* te atenderias: FONASA, ISAPRE o particular?",
        validar=_validar_prevision,
        normalizar=_norm_prevision,
    ),
    Campo(
        clave="franja",
        etiqueta="Horario",
        pregunta="Ultima cosa: preferis en la *manana* o en la *tarde*?",
        validar=_validar_franja,
        normalizar=_norm_franja,
    ),
]


# ============================================================================
# Resultado de cada paso
# ============================================================================


@dataclass
class PasoResultado:
    """Que responde el bot y en que estado quedo el recolector."""

    texto: str
    completado: bool = False
    cancelado: bool = False
    # Cuando completado=True, resumen con los datos listos para el staff.
    datos_staff: str | None = None


# ============================================================================
# Recolector (maquina de estados pura)
# ============================================================================


@dataclass
class Agendamiento:
    """Recolecta, uno a uno, los datos necesarios para agendar.

    Uso tipico:
        ag = Agendamiento()
        print(ag.iniciar())            # primera pregunta
        r = ag.procesar("Juan Perez")  # valida y pide el siguiente
        ...
        if r.completado:
            notificar_staff(r.datos_staff)
    """

    datos: dict[str, str] = field(default_factory=dict)
    indice: int = 0
    completado: bool = False
    cancelado: bool = False

    @property
    def activo(self) -> bool:
        return not (self.completado or self.cancelado)

    def _campo_actual(self) -> Campo:
        return CAMPOS[self.indice]

    def iniciar(self) -> str:
        """Devuelve la primera pregunta del flujo."""
        self.indice = 0
        return CAMPOS[0].pregunta

    def procesar(self, mensaje: str) -> PasoResultado:
        """Valida la respuesta al campo actual y avanza (o repite/cancela)."""
        if not self.activo:
            return PasoResultado(texto="", completado=self.completado,
                                 cancelado=self.cancelado)

        if quiere_cancelar(mensaje):
            self.cancelado = True
            return PasoResultado(
                texto=(
                    "Sin problema, dejamos el agendamiento para cuando quieras. "
                    "Aca estoy para lo que necesites."
                ),
                cancelado=True,
            )

        campo = self._campo_actual()
        error = campo.validar(mensaje)
        if error is not None:
            return PasoResultado(texto=error)

        # Dato valido: normalizar y guardar.
        self.datos[campo.clave] = campo.normalizar(mensaje)
        self.indice += 1

        # Quedan campos? Preguntamos el siguiente.
        if self.indice < len(CAMPOS):
            return PasoResultado(texto=self._campo_actual().pregunta)

        # Se completaron todos.
        self.completado = True
        return PasoResultado(
            texto=self._mensaje_cierre(),
            completado=True,
            datos_staff=self.resumen(),
        )

    def resumen(self) -> str:
        """Texto con los datos, para enviar al staff (contiene PII real)."""
        lineas = [
            f"{c.etiqueta}: {self.datos.get(c.clave, '-')}" for c in CAMPOS
        ]
        return "\n".join(lineas)

    def _mensaje_cierre(self) -> str:
        nombre = self.datos.get("nombre", "").split(" ")[0] or "Listo"
        return (
            f"Buenisimo, {nombre}! Ya deje tus datos y un kinesiologo te "
            "confirma el horario exacto por correo o telefono. "
            f"Si preferis, tambien podes elegir tu hora aca: {LINK_AGENDA} "
            "Nos vemos pronto en KitraDep."
        )
