"""Contenido de la propuesta - PARTE 1: portada, indice, resumen ejecutivo,
contexto y arquitectura de alto nivel.

Cada funcion devuelve una lista de flowables lista para agregar al doc.
"""
from __future__ import annotations
from datetime import date

from reportlab.platypus import PageBreak, Spacer
from reportlab.lib.units import cm

from generar_pdf import (
    p, bullets, numbered, hr, spacer, tabla, callout,
    H1, H2, H3, BODY, BODY_C, SMALL, CODE, CALLOUT,
    COVER_TITLE, COVER_SUB, COVER_META,
)


# ============================================================================
# Portada
# ============================================================================

def seccion_portada() -> list:
    hoy = date.today().strftime("%d de %B de %Y").replace(
        "January", "enero").replace("February", "febrero").replace(
        "March", "marzo").replace("April", "abril").replace("May", "mayo").replace(
        "June", "junio").replace("July", "julio").replace("August", "agosto").replace(
        "September", "septiembre").replace("October", "octubre").replace(
        "November", "noviembre").replace("December", "diciembre")
    return [
        Spacer(1, 5 * cm),
        p("PROPUESTA TECNICA", COVER_META),
        Spacer(1, 0.4 * cm),
        p("Chatbot Hibrido con LLM para KitraDep", COVER_TITLE),
        Spacer(1, 0.6 * cm),
        p("De un menu de opciones rigido<br/>a un asistente conversacional inteligente",
          COVER_SUB),
        Spacer(1, 3 * cm),
        p("Documento tecnico, diseno, despliegue y presupuesto", COVER_META),
        Spacer(1, 0.3 * cm),
        p(f"Preparado por: Kira (asistente de Felipe Fierro)", COVER_META),
        p(f"Fecha: {hoy}", COVER_META),
        p("Version: 1.0", COVER_META),
        PageBreak(),
    ]


# ============================================================================
# Indice
# ============================================================================

def seccion_indice() -> list:
    items = [
        ("1. Resumen ejecutivo", "3"),
        ("2. Contexto del proyecto y estado actual", "4"),
        ("3. Que es un bot hibrido con LLM (conceptos)", "6"),
        ("4. Arquitectura tecnica propuesta", "8"),
        ("5. Los 6 componentes tecnicos en detalle", "10"),
        ("6. Comparativa de modelos LLM (Gemini vs alternativas)", "14"),
        ("7. Diseno del libreto y personalidad del bot (Kitra)", "16"),
        ("8. 'Entrenar' el LLM: prompt engineering + RAG (no es fine-tuning)", "19"),
        ("9. Guardrails, seguridad, etica y cumplimiento", "21"),
        ("10. Integracion con WhatsApp de la empresa", "23"),
        ("11. Despliegue, hosting y operacion 24/7", "26"),
        ("12. Plan de trabajo por fases y cronograma", "28"),
        ("13. COSTOS DETALLADOS: 1 mes, 3, 6 y 12 meses", "30"),
        ("14. Riesgos, mitigaciones y limites eticos", "33"),
        ("15. Checklist de arranque (que necesita Felipe)", "35"),
        ("16. Anexos: ejemplos, glosario, links utiles", "36"),
    ]
    filas = [["Seccion", "Pag."]] + [[k, v] for k, v in items]
    return [
        p("Indice", H1),
        hr(),
        spacer(0.3),
        tabla(filas, anchos=[14 * cm, 2.5 * cm]),
        PageBreak(),
    ]


# ============================================================================
# 1. Resumen ejecutivo
# ============================================================================

def seccion_resumen_ejecutivo() -> list:
    return [
        p("1. Resumen ejecutivo", H1),
        hr(),
        p("<b>Que se propone.</b> Evolucionar el chatbot actual de KitraDep "
          "(hoy una maquina de estados con menus numericos) hacia un asistente "
          "conversacional hibrido que combina inteligencia artificial generativa "
          "(LLM) para la conversacion natural, con un flujo controlado tradicional "
          "para las tareas criticas de agendamiento. El resultado se percibe "
          "humano, entiende texto libre, tolera desvios del guion, y responde "
          "con la personalidad y el conocimiento del negocio."),
        p("<b>Por que.</b> El bot actual es funcional pero rigido: solo entiende "
          "numeros o palabras exactas del menu, y al primer desvio conversacional "
          "'se pierde'. Los usuarios esperan hablar con el bot como con una "
          "persona. Un bot hibrido resuelve ambos mundos: control total en lo "
          "critico (agendar cita, precios, datos personales) y conversacion "
          "natural en lo abierto (dudas, aclaraciones, saludos, preguntas "
          "espontaneas)."),
        p("<b>Como.</b> Se reutiliza toda la base ya construida (motor Python, "
          "webapp FastAPI, guion YAML) y se le agregan seis piezas nuevas: (1) "
          "modelo LLM Gemini 2.0 Flash de Google, (2) base de conocimiento del "
          "negocio en formato documento, (3) system prompt con personalidad y "
          "limites, (4) router hibrido que decide cuando usar LLM vs flujo "
          "estricto, (5) memoria de conversacion, y (6) guardrails de seguridad "
          "y prevencion de alucinaciones."),
        p("<b>Cuanto tarda.</b> Aproximadamente 4 a 6 semanas de trabajo "
          "repartido para llegar a un bot funcional en WhatsApp real de la "
          "empresa, con la mayor parte del tiempo en diseno de contenido y "
          "testing, no en programacion."),
        p("<b>Cuanto cuesta.</b> El costo mensual operativo en produccion se "
          "estima entre <b>USD 10 y USD 30 mensuales</b> para un volumen tipico "
          "de una clinica pequena (100-300 conversaciones por dia). El grueso "
          "del costo no es el LLM (que puede ser incluso gratis con el free tier "
          "de Google), sino el hosting del servidor y eventual mensajes "
          "proactivos de recordatorio. Detalle completo en la seccion 13."),
        p("<b>Que se necesita.</b> Trabajo del equipo de KitraDep para: (a) "
          "validar personalidad y tono del bot, (b) proveer dumps de "
          "conversaciones reales para entrenar el prompt, (c) definir los limites "
          "eticos (que puede y que NO puede responder el bot, dado que es un "
          "rubro de salud), y (d) gestionar los tramites de Meta Business para "
          "el numero de WhatsApp oficial (unos dias a semanas segun agilidad de "
          "Meta)."),
        spacer(0.3),
        callout(
            "Resumen en una frase: por menos de USD 30 al mes y en 4-6 semanas "
            "de trabajo, KitraDep puede tener un bot en WhatsApp que suena "
            "humano, agenda citas confiablemente y esta disponible 24/7."
        ),
        PageBreak(),
    ]


# ============================================================================
# 2. Contexto y estado actual
# ============================================================================

def seccion_contexto() -> list:
    return [
        p("2. Contexto del proyecto y estado actual", H1),
        hr(),

        p("2.1 Que es KitraDep", H2),
        p("Centro de kinesiologia ubicado en Llano Subercaseaux 3791, oficinas "
          "208-209, comuna de San Miguel, Santiago de Chile. Atiende de lunes a "
          "viernes de 8 a 21 horas y sabados de 9 a 13 horas. Cuenta con cuatro "
          "kinesiologos: Javiera Caceres y Jaime en horario AM, Francisco y "
          "Valentina en horario PM. Ofrece kinesiologia individual 1-a-1 de "
          "45-50 minutos, con distincion de precios segun prevision del paciente "
          "(FONASA / ISAPRE / Particular)."),

        p("2.2 Problema actual", H2),
        p("La atencion via WhatsApp la responden manualmente los kinesiologos "
          "en tiempos libres. Consecuencias observadas:"),
        bullets([
            "Los mensajes fuera de horario laboral no se responden hasta el dia siguiente, con perdida de leads.",
            "Preguntas repetitivas (precios, horarios, direccion, previsiones aceptadas) consumen tiempo valioso.",
            "El proceso de agendamiento requiere multiples intercambios manuales.",
            "No hay registro centralizado de conversaciones para analizar patrones.",
            "Escalar a mas horas de atencion implica contratar personal administrativo.",
        ]),

        p("2.3 Que se construyo hasta ahora (fases 1, 2 y 4-A)", H2),
        p("Se implemento un chatbot funcional en tres iteraciones:"),
        bullets([
            "<b>Fase 1 - Guion:</b> archivo YAML con 21 estados y logica bifurcada FONASA/ISAPRE/Particular, extraida de casos reales.",
            "<b>Fase 2 - Motor CLI:</b> interprete Python que lee el YAML y permite conversar en terminal. Sin dependencias mas alla de PyYAML.",
            "<b>Fase 4-A - Simulador web:</b> webapp con FastAPI + HTMX + Tailwind, interfaz identica a WhatsApp, sesiones multiples, corre local sin costo.",
        ]),
        p("Todo esto vive en la carpeta <font face='Courier'>chatbot/</font> del "
          "repositorio, con commits limpios y documentacion completa "
          "(<font face='Courier'>MOTOR.md</font>, <font face='Courier'>WEBAPP.md"
          "</font>, <font face='Courier'>DIAGNOSTICO.md</font>, entre otros)."),

        p("2.4 Limitacion clave que se busca resolver", H2),
        p("El bot actual es una <b>maquina de estados pura</b>: opera en base a "
          "menus numericos y palabras clave exactas. Sus limitaciones son "
          "estructurales del enfoque, no bugs:"),
        tabla([
            ["Comportamiento", "Bot actual", "Bot deseado"],
            ["Usuario escribe '1' o palabra exacta", "Funciona", "Funciona"],
            ["Usuario escribe frase libre", "Se pierde", "Entiende"],
            ["Pregunta fuera del guion", "Responde 'no entendi'", "Responde con contexto"],
            ["Recuerda mensajes previos", "No", "Si"],
            ["Tono conversacional", "Robotico, listas y numeros", "Natural, empatico"],
            ["Maneja typos", "No", "Si"],
            ["Sinonimos y jerga", "No", "Si"],
        ], anchos=[6 * cm, 5 * cm, 5.5 * cm]),
        spacer(0.3),
        callout(
            "El objetivo NO es tirar el bot actual a la basura. Se REUSA "
            "todo lo construido. El LLM se agrega ENCIMA como una capa "
            "adicional que hace al bot conversacional, mientras que el flujo "
            "de estados sigue manejando las tareas criticas donde se necesita "
            "control absoluto (agendar, cobrar, tomar datos)."
        ),
        PageBreak(),
    ]
