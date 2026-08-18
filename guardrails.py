"""Guardrails: filtros de seguridad del bot.

En un bot de salud, hay reglas que NO se pueden delegar al LLM porque son
demasiado importantes para arriesgar una alucinacion. Este modulo las
implementa con reglas deterministas (regex + keywords), asi corren rapido,
sin costo y sin depender de ninguna API.

Todos los detectores son funciones puras: reciben texto, devuelven un
veredicto. No tienen estado ni I/O.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Riesgo(str, Enum):
    """Tipos de situacion que requieren manejo especial."""

    NINGUNO = "ninguno"
    MEDICO = "medico"          # consulta clinica -> derivar a evaluacion
    EMERGENCIA = "emergencia"  # urgencia -> derivar a emergencias YA
    FUERA_TEMA = "fuera_tema"  # no habla de KitraDep
    HANDOFF = "handoff"        # pide humano explicitamente


@dataclass
class Veredicto:
    riesgo: Riesgo
    motivo: str = ""


# ============================================================================
# Diccionarios de deteccion
# ============================================================================

# Urgencias reales que ameritan derivacion inmediata a emergencias.
_EMERGENCIA = [
    r"\bno puedo (mover|caminar|respirar|sentir)\b",
    r"\bdolor (muy fuerte|insoportable|severo|terrible)\b",
    r"\bme (cai|accidente|frac?ture|quebre)\b",
    r"\bhueso (roto|salido|expuesto)\b",
    r"\bsangr(a|e|ando)\b",
    r"\bperdi (la sensibilidad|el conocimiento|fuerza)\b",
    r"\bemergencia\b",
    r"\burgencia\b",
    r"\bse me durmio (la|el|una|un)\b",
]

# Consultas clinicas: el bot NO diagnostica, deriva a evaluacion presencial.
_MEDICO = [
    r"\bque (tengo|me pasa|sera)\b",
    r"\bes (grave|serio|normal)\b",
    r"\bsera (un|una|el|la)?\s*(esguince|desgarro|menisco|tendinitis|hernia|fractura|lesion)\b",
    r"\bque ejercicios?\b",
    r"\bque me recomend",
    r"\bque puedo (hacer|tomar) para\b",
    r"\bme duele\b.*\b(sera|es|puede ser)\b",
    r"\bdiagnostic",
    r"\btratamiento para\b",
    r"\bque medicamento",
    r"\bpuedo tomar\b",
    r"\bes malo (que|si)\b",
]

# Pedido explicito de hablar con una persona.
_HANDOFF = [
    r"\bhablar con (alguien|una persona|un humano|un profesional|la kine|el kine)\b",
    r"\buna persona (real|de verdad)\b",
    r"\bderivame\b",
    r"\bquiero hablar con\b",
    r"\batencion humana\b",
    r"\bno (eres|sos) real\b",
    r"\beres un bot\b",
    r"\bsos un bot\b",
]

# Temas claramente ajenos a KitraDep (lista corta, ilustrativa).
_FUERA_TEMA = [
    r"\bfutbol\b",
    r"\bpolitica\b",
    r"\bpresidente\b",
    r"\bbitcoin\b|\bcripto\b",
    r"\breceta de cocina\b",
    r"\bclima\b|\bel tiempo\b",
    r"\bchiste\b",
]

# Patrones de PII (para NO logear en claro).
_PII_RUT = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dkK]\b")
_PII_FONO = re.compile(r"\b(\+?56)?\s?9\s?\d{4}\s?\d{4}\b")
_PII_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


# ============================================================================
# Detectores
# ============================================================================


def _matchea(texto: str, patrones: list[str]) -> bool:
    norm = texto.lower()
    return any(re.search(p, norm) for p in patrones)


def evaluar(texto: str) -> Veredicto:
    """Evalua un mensaje del usuario y devuelve el veredicto de riesgo.

    El orden importa: emergencia > handoff > medico > fuera_tema > ninguno.
    Una emergencia siempre gana (es lo mas critico).
    """
    if _matchea(texto, _EMERGENCIA):
        return Veredicto(Riesgo.EMERGENCIA, "Palabra clave de urgencia detectada.")
    if _matchea(texto, _HANDOFF):
        return Veredicto(Riesgo.HANDOFF, "El usuario pide atencion humana.")
    if _matchea(texto, _MEDICO):
        return Veredicto(Riesgo.MEDICO, "Consulta de tipo clinico detectada.")
    if _matchea(texto, _FUERA_TEMA):
        return Veredicto(Riesgo.FUERA_TEMA, "Tema fuera del dominio de KitraDep.")
    return Veredicto(Riesgo.NINGUNO)


def enmascarar_pii(texto: str) -> str:
    """Reemplaza RUT, telefono y email por marcadores. Para logs seguros.

    NO se usa sobre lo que ve el usuario, solo sobre lo que se guarda en
    logs para cumplir con proteccion de datos (Ley 19.628 / 21.719).
    """
    t = _PII_RUT.sub("[RUT]", texto)
    t = _PII_FONO.sub("[FONO]", t)
    t = _PII_EMAIL.sub("[EMAIL]", t)
    return t


# ============================================================================
# Respuestas canned para cada tipo de riesgo
# ============================================================================


def respuesta_para(veredicto: Veredicto, handoff_contacto: str = "") -> str:
    """Devuelve la respuesta segura predefinida para un riesgo dado.

    Estas respuestas NO pasan por el LLM: son fijas, auditadas y seguras.
    """
    contacto = handoff_contacto or "nuestro equipo"

    if veredicto.riesgo is Riesgo.EMERGENCIA:
        return (
            "Por lo que me contas, esto podria necesitar atencion inmediata. "
            "Si es una urgencia, te recomiendo llamar al *131 (SAMU)* o acudir "
            "al servicio de urgencia mas cercano. Tu salud es lo primero. "
            f"Cuando estes estable, {contacto} puede ayudarte con tu recuperacion."
        )
    if veredicto.riesgo is Riesgo.MEDICO:
        return (
            "Entiendo tu inquietud, pero no puedo darte un diagnostico ni "
            "recomendaciones clinicas por chat (seria irresponsable de mi parte). "
            "Esto es justo lo que evaluamos en la primera sesion, que incluye una "
            f"evaluacion kinesica completa. Queres que te agende con {contacto}?"
        )
    if veredicto.riesgo is Riesgo.HANDOFF:
        return (
            f"Claro, te derivo con {contacto}. Te van a escribir por este mismo "
            "medio a la brevedad. Mientras tanto, hay algo mas en lo que te "
            "pueda ayudar?"
        )
    if veredicto.riesgo is Riesgo.FUERA_TEMA:
        return (
            "Jaja, en eso no te puedo ayudar. Soy la asistente de KitraDep, "
            "asi que lo mio es kinesiologia: servicios, precios, horarios y "
            "agendar sesiones. En que de eso te ayudo?"
        )
    return ""  # NINGUNO: no hay respuesta canned, sigue el flujo normal.
