"""Flujo de agendamiento de KitraDep.

Cuando la persona acepta agendar, el camino principal es el link de
AgendaPro (ella elige dia y hora y deja sus datos alla). Este modulo arma ese
mensaje y detecta las respuestas tipicas alrededor del agendamiento:

  - "quiero agendar" / "si" (a una invitacion) -> enviar link de AgendaPro.
  - "no puedo con el link" / "agendame por aca" -> pedir los datos en UN
    solo mensaje (lista para copiar y completar) y leerlos de la respuesta.
  - "listo, ya agende" -> agradecer y recordar ubicacion + tips.

La captura de datos por chat NO se delega al LLM, porque:

  - Un LLM puede alucinar, olvidar un campo o "confirmar" datos inventados.
  - Los datos (nombre, RUT, correo, telefono) tienen que ser EXACTOS: se los
    mandamos al staff para contactar al paciente.
  - Validar un RUT chileno o un email es logica determinista, no probabilistica.

Por eso el recolector es una pequena maquina de estados pura (sin I/O ni
LLM), totalmente testeable offline. Este modulo NO sabe de web, terminal ni
WhatsApp: solo procesa texto y devuelve texto.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable

# Link oficial para agendar (fuente de verdad: knowledge/kitradep.md).
LINK_AGENDA = "https://kitradep.site.agendapro.com/cl/sucursal/548882"

UBICACION = (
    "*Llano Subercaseaux 3791, 2° piso, oficina 208-209* "
    "(salida poniente del metro San Miguel)"
)

# Palabras para abortar el flujo en cualquier momento.
_CANCELAR = {"cancelar", "cancela", "olvidalo", "dejalo", "despues", "mejor no"}


def normalizar(texto: str) -> str:
    """Minusculas y sin tildes: 'Agéndame' -> 'agendame'. Para comparar."""
    sin_tildes = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn").strip()


def _sin_puntuacion(texto: str) -> str:
    return re.sub(r"[^\w\s]", "", normalizar(texto)).strip()


# ============================================================================
# Deteccion de intenciones alrededor del agendamiento
# ============================================================================

# Frases que indican que la persona QUIERE dar el paso de reservar una hora.
# Se busca como subcadena sobre el mensaje normalizado. Deliberadamente
# especificas para no dispararse en medio de la conversacion consultiva
# (ej: NO incluimos "hora" sola, que aparece en "a que hora atienden").
_INTENCION = [
    "quiero agendar",
    "quiero reservar",
    "gustaria agendar",
    "gustaria reservar",
    "quisiera agendar",
    "quisiera reservar",
    "puedo agendar",
    "podria agendar",
    "agendar hora",
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
    "agendame",
    "dame una hora",
    "quiero mi evaluacion",
    "agendar evaluacion",
    "como agendo",
    "como puedo agendar",
    "donde agendo",
]

# Respuestas cortas de aceptacion a una invitacion ("¿te parece si agendamos?").
_AFIRMATIVOS = {
    "si", "sii", "siii", "si por favor", "si porfa", "dale", "ya", "ya po",
    "bueno", "ok", "okay", "oka", "claro", "claro que si", "me parece",
    "perfecto", "de acuerdo", "si dale", "dale si", "si me interesa",
    "me interesa", "si quiero", "obvio", "por favor", "bueno dale", "vamos",
    "ya dale", "si me parece", "me parece bien", "si gracias",
}

# "Ya agende" (despues de recibir el link).
_YA_AGENDO = [
    "ya agende", "listo agende", "agende para", "ya reserve", "ya tome hora",
    "ya tome la hora", "ya saque hora", "ya saque la hora", "ya quede",
    "quede agendad", "ya esta agendad", "ya tengo hora", "ya tengo mi hora",
    "agendado", "reservado", "ya lo hice",
]
_YA_AGENDO_EXACTO = {"listo", "listoo", "hecho", "ya esta", "listo gracias"}

# "No puedo / prefiero por aca" (quiere agendar por chat, sin el link).
_PREFIERE_CHAT = [
    "por aqui", "por aca", "por whatsapp", "por el chat", "por chat",
    "no puedo", "no me funciona", "no funciona", "no me abre", "no abre",
    "no se usar", "no se como", "me cuesta", "agendame tu", "agendenme",
    "prefiero que me agend", "mejor ustedes", "no me carga", "no carga",
    "no tengo internet",
]

# Raices que indican que un texto del bot invita a agendar.
_RAICES_INVITACION = ("agend", "reserv", "tomar hora", "tomar tu hora")

# Senales de interes del paciente: autorizan a volver a invitar.
_SENALES_INTERES = (
    "agend", "reserv", "horario", "una hora", "que hora", "disponib", "cupo",
    "cuando pued",
    "me interesa", "precio", "valor", "cuanto", "cuesta",
)


def detectar_intencion(mensaje: str) -> bool:
    """True si el mensaje expresa intencion clara de agendar una hora."""
    m = normalizar(mensaje)
    return any(frase in m for frase in _INTENCION)


def es_afirmativo(mensaje: str) -> bool:
    """True si es un 'si' corto (respuesta a una invitacion a agendar)."""
    if "?" in mensaje:
        return False
    m = _sin_puntuacion(mensaje)
    if m in _AFIRMATIVOS:
        return True
    palabras = m.split()
    return bool(palabras) and palabras[0] in {"si", "dale", "claro"} and len(palabras) <= 5


def ya_agendo(mensaje: str) -> bool:
    """True si avisa que ya reservo (en AgendaPro)."""
    m = normalizar(mensaje)
    return _sin_puntuacion(mensaje) in _YA_AGENDO_EXACTO or any(f in m for f in _YA_AGENDO)


def prefiere_chat(mensaje: str) -> bool:
    """True si no puede/quiere usar el link y prefiere agendar por chat."""
    m = normalizar(mensaje)
    return any(f in m for f in _PREFIERE_CHAT)


def es_invitacion(texto_bot: str) -> bool:
    """True si un mensaje del bot invita a agendar."""
    t = normalizar(texto_bot)
    return any(r in t for r in _RAICES_INVITACION)


def hay_senal_interes(mensaje: str) -> bool:
    """True si el paciente muestra interes (horarios, valores, agendar...)."""
    m = normalizar(mensaje)
    return any(s in m for s in _SENALES_INTERES)


def quitar_invitacion(texto_bot: str) -> str:
    """Quita las frases que invitan a agendar. Si no queda nada, deja el original.

    Red de seguridad por si el LLM invita aunque se le pidio que no lo hiciera.
    """
    frases = re.split(r"(?<=[.!?…])\s+|\n+", texto_bot.strip())
    # Fuera las invitaciones y los restos sin letras (ej: un "📅" suelto).
    quedan = [f for f in frases
              if re.search(r"\w", f) and not es_invitacion(f)]
    return " ".join(quedan).strip() or texto_bot


def quiere_cancelar(mensaje: str) -> bool:
    """True si el usuario quiere abortar el agendamiento en curso."""
    return _sin_puntuacion(mensaje) in _CANCELAR


# ============================================================================
# Mensajes fijos (tono de la clinica: tuteo, calido, con emojis)
# ============================================================================


def mensaje_link() -> str:
    """Se envia cuando la persona acepta agendar."""
    return (
        "¡Qué bueno! 😊 Puedes agendar tu evaluación aquí:\n"
        f"👉 {LINK_AGENDA}\n\n"
        "1️⃣ Elige el servicio, el día y la hora que más te acomoden\n"
        "2️⃣ Completa tus datos\n"
        "3️⃣ Confirma tu reserva\n\n"
        "¡Muchas gracias por confiar en KitraDep! Si prefieres que te "
        "agendemos por aquí, solo dime 💬"
    )


def mensaje_gracias() -> str:
    """Se envia cuando la persona avisa que ya agendo."""
    return (
        "¡Muchas gracias por agendar con nosotros! 🙌\n\n"
        f"Te esperamos en {UBICACION}. Ven con ropa cómoda y, si tienes orden "
        "médica, tráela. La sesión dura 45 minutos.\n\n"
        "¡Nos vemos pronto en KitraDep!"
    )


# ============================================================================
# Validadores y normalizadores de campos
# ============================================================================
#
# Cada validador recibe el texto crudo y devuelve:
#   - None si es valido (y se normaliza aparte), o
#   - un string con el mensaje de error (calido) para volver a pedirlo.


_EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")
_FONO_RE = re.compile(r"^(\+?56)?0?9\d{8}$")


def _validar_nombre(valor: str) -> str | None:
    limpio = valor.strip()
    if len(limpio) < 3 or " " not in limpio:
        return "Necesito tu *nombre y apellido* para la ficha."
    if any(ch.isdigit() for ch in limpio):
        return "El nombre no puede llevar números."
    return None


def _norm_nombre(valor: str) -> str:
    # Title-case simple respetando espacios simples.
    return " ".join(p.capitalize() for p in valor.split())


def _validar_rut(valor: str) -> str | None:
    v = valor.replace(".", "").replace("-", "").replace(" ", "").strip().upper()
    if len(v) < 2 or not v[:-1].isdigit():
        return "El RUT no lo entendí. Escríbelo así: *12.345.678-9*"
    cuerpo, dv = v[:-1], v[-1]
    suma, factor = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    dv_calc = {10: "K", 11: "0"}.get(resto, str(resto))
    if dv != dv_calc:
        return "El RUT no me cuadra (el dígito verificador). ¿Lo revisas?"
    return None


def _norm_rut(valor: str) -> str:
    v = valor.replace(".", "").replace("-", "").replace(" ", "").strip().upper()
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
        return "El correo no parece válido."
    return None


def _validar_fono(valor: str) -> str | None:
    limpio = re.sub(r"[\s()-]", "", valor.strip())
    if not _FONO_RE.match(limpio):
        return "Necesito un celular chileno válido (9 + 8 dígitos), ej: *9 1234 5678*"
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
    m = normalizar(valor)
    if any(k in m for k in _PREVISIONES):
        return None
    return "La previsión debe ser *Fonasa*, *Isapre* o *Particular*."


def _norm_prevision(valor: str) -> str:
    m = normalizar(valor)
    for k, etiqueta in _PREVISIONES.items():
        if k in m:
            return etiqueta
    return valor.strip()


_MANANA_RE = re.compile(r"\b(manana|am|temprano)\b")
_TARDE_RE = re.compile(r"\b(tarde|pm|noche)\b")


def _validar_franja(valor: str) -> str | None:
    m = normalizar(valor)
    if _MANANA_RE.search(m) or _TARDE_RE.search(m):
        return None
    return "¿Prefieres en la *mañana* o en la *tarde*?"


def _norm_franja(valor: str) -> str:
    if _MANANA_RE.search(normalizar(valor)):
        return "Mañana (AM)"
    return "Tarde (PM)"


def _validar_direccion(valor: str) -> str | None:
    return None if len(valor.strip()) >= 4 else "La dirección quedó incompleta."


# ============================================================================
# Definicion de los campos a recolectar
# ============================================================================


@dataclass(frozen=True)
class Campo:
    """Un dato a capturar: como se rotula, como validarlo y normalizarlo."""

    clave: str
    etiqueta: str            # como se muestra en la lista y al staff
    linea: str               # linea de la plantilla que se le envia al paciente
    sinonimos: tuple[str, ...]  # rotulos que reconocemos en la respuesta
    validar: Callable[[str], str | None]
    normalizar: Callable[[str], str] = staticmethod(lambda s: s.strip())
    opcional: bool = False


# Mismo orden que el mensaje de "datos" que usa la clinica en WhatsApp.
CAMPOS: list[Campo] = [
    Campo("nombre", "Nombre", "📝 Nombre:", ("nombre",),
          _validar_nombre, _norm_nombre),
    Campo("rut", "RUT", "🆔 RUT:", ("rut",),
          _validar_rut, _norm_rut),
    Campo("correo", "Correo", "📧 Correo electrónico:",
          ("correo", "email", "e-mail", "mail"),
          _validar_correo, lambda s: s.strip().lower()),
    Campo("telefono", "Teléfono", "📞 Número de contacto:",
          ("numero", "telefono", "contacto", "celular", "fono"),
          _validar_fono, _norm_fono),
    Campo("prevision", "Previsión", "🏥 Previsión de salud (Fonasa, Isapre, Particular):",
          ("prevision",),
          _validar_prevision, _norm_prevision),
    Campo("direccion", "Dirección", "🏠 Dirección (opcional):",
          ("direccion", "domicilio"),
          _validar_direccion, opcional=True),
    Campo("franja", "Horario", "🕐 ¿Prefieres mañana o tarde?:",
          ("manana o tarde", "horario", "franja", "jornada", "prefieres"),
          _validar_franja, _norm_franja),
]

_POR_CLAVE = {c.clave: c for c in CAMPOS}

# Patrones para reconocer datos aunque vengan sin rotulo.
_BUSCA_CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_BUSCA_RUT = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dkK]\b")
_BUSCA_FONO = re.compile(r"(?:\+?56\s?)?9[\s-]?\d{4}[\s-]?\d{4}\b")

# Palabras que delatan que una frase suelta NO es un nombre ("buenas tardes").
_NO_NOMBRE = {
    "hola", "buenas", "buenos", "gracias", "quiero", "tengo", "que", "como",
    "donde", "cuanto", "no", "si", "ya", "listo", "ok", "mi", "es", "soy",
    "por", "favor", "dias", "tardes", "noches", "cancelar", "una", "pregunta",
}


def _campo_por_rotulo(rotulo: str) -> Campo | None:
    r = normalizar(rotulo)
    for c in CAMPOS:
        if any(s in r for s in c.sinonimos):
            return c
    return None


def extraer_datos(mensaje: str) -> tuple[dict[str, str], list[str]]:
    """Lee los datos que vengan en el mensaje (con o sin rotulo).

    Devuelve (datos_validos_normalizados, errores). Acepta la plantilla
    completada ("🆔 RUT: 12.345.678-5"), una linea por dato sin rotulo, o
    todo mezclado en una linea.
    """
    crudos: dict[str, str] = {}
    sueltas: list[str] = []

    # 1) Lineas con rotulo "Algo: valor".
    for linea in mensaje.splitlines():
        if ":" in linea:
            rotulo, valor = linea.split(":", 1)
            campo = _campo_por_rotulo(rotulo)
            if campo is not None:
                if valor.strip():
                    crudos[campo.clave] = valor.strip()
                continue
        if linea.strip():
            sueltas.append(linea.strip())

    # 2) Datos sin rotulo, reconocibles por su forma.
    resto = "\n".join(sueltas)
    for clave, patron in (("correo", _BUSCA_CORREO), ("rut", _BUSCA_RUT),
                          ("telefono", _BUSCA_FONO)):
        if clave not in crudos:
            hallado = patron.search(resto)
            if hallado:
                crudos[clave] = hallado.group(0)
                resto = resto.replace(hallado.group(0), " ")
    resto_norm = normalizar(resto)
    if "prevision" not in crudos and any(k in resto_norm for k in _PREVISIONES):
        crudos["prevision"] = resto
    if "franja" not in crudos and (_MANANA_RE.search(resto_norm) or _TARDE_RE.search(resto_norm)):
        crudos["franja"] = resto

    # Nombre sin rotulo: una linea solo con letras (2 a 5 palabras) que no
    # sea una prevision ni una franja.
    if "nombre" not in crudos:
        for trozo in re.split(r"[\n,;]", resto):
            limpia = trozo.strip(" .")
            ln = normalizar(limpia)
            if (re.fullmatch(r"[^\W\d_]+(?: [^\W\d_]+){1,4}", limpia)
                    and not set(ln.split()) & _NO_NOMBRE
                    and not any(k in ln for k in _PREVISIONES)
                    and not _MANANA_RE.search(ln) and not _TARDE_RE.search(ln)):
                crudos["nombre"] = limpia
                break

    # 3) Validar y normalizar.
    datos: dict[str, str] = {}
    errores: list[str] = []
    for clave, valor in crudos.items():
        campo = _POR_CLAVE[clave]
        error = campo.validar(valor)
        if error is None:
            datos[clave] = campo.normalizar(valor)
        else:
            errores.append(error)
    return datos, errores


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
    # True si el mensaje no traia ningun dato (ej: una pregunta).
    sin_datos: bool = False


# ============================================================================
# Recolector (maquina de estados pura)
# ============================================================================


@dataclass
class Agendamiento:
    """Pide todos los datos en un mensaje y luego solo los que falten.

    Uso tipico:
        ag = Agendamiento()
        print(ag.iniciar())                      # lista para completar
        r = ag.procesar("Nombre: Juan Perez ...")  # lee lo que venga
        if r.completado:
            notificar_staff(r.datos_staff)
    """

    datos: dict[str, str] = field(default_factory=dict)
    completado: bool = False
    cancelado: bool = False

    @property
    def activo(self) -> bool:
        return not (self.completado or self.cancelado)

    def faltantes(self) -> list[Campo]:
        return [c for c in CAMPOS if not c.opcional and c.clave not in self.datos]

    def iniciar(self) -> str:
        """Mensaje con la lista de datos para copiar y completar."""
        lineas = "\n".join(c.linea for c in CAMPOS)
        return (
            "¡Perfecto! Te agendamos por aquí 😊 Copia este mensaje, complétalo "
            "y envíamelo:\n\n"
            f"{lineas}\n\n"
            "Luego alguien de nuestro equipo te confirma el día y la hora."
        )

    def procesar(self, mensaje: str) -> PasoResultado:
        """Lee los datos que vengan y pide solo lo que falte (o cancela)."""
        if not self.activo:
            return PasoResultado(texto="", completado=self.completado,
                                 cancelado=self.cancelado)

        if quiere_cancelar(mensaje):
            self.cancelado = True
            return PasoResultado(
                texto=(
                    "Sin problema, lo dejamos para cuando quieras 😊 "
                    "Aquí estoy para lo que necesites."
                ),
                cancelado=True,
            )

        nuevos, errores = extraer_datos(mensaje)
        self.datos.update(nuevos)

        faltan = self.faltantes()
        if not faltan:
            self.completado = True
            return PasoResultado(
                texto=self._mensaje_cierre(),
                completado=True,
                datos_staff=self.resumen(),
            )

        lista = "\n".join(f"• {c.etiqueta}" for c in faltan)
        partes = []
        if errores:
            partes.append("\n".join(errores))
        partes.append(f"{'¡Gracias! ' if nuevos else ''}Me falta:\n{lista}")
        return PasoResultado(texto="\n\n".join(partes),
                             sin_datos=not nuevos and not errores)

    def resumen(self) -> str:
        """Texto con los datos, para enviar al staff (contiene PII real)."""
        lineas = [
            f"{c.etiqueta}: {self.datos.get(c.clave, '-')}" for c in CAMPOS
        ]
        return "\n".join(lineas)

    def _mensaje_cierre(self) -> str:
        nombre = self.datos.get("nombre", "").split(" ")[0]
        saludo = f"¡Listo, {nombre}! 🙌" if nombre else "¡Listo! 🙌"
        return (
            f"{saludo} Ya tenemos tus datos y alguien de nuestro equipo te "
            "escribirá para confirmar el día y la hora.\n\n"
            f"Te esperamos en {UBICACION}. Ven con ropa cómoda 👟\n\n"
            "¡Muchas gracias por confiar en KitraDep!"
        )
