"""Contenido - PARTE 3: libreto, prompt engineering, guardrails, WhatsApp."""
from __future__ import annotations

from reportlab.platypus import PageBreak, Spacer
from reportlab.lib.units import cm

from generar_pdf import (
    p, bullets, numbered, hr, spacer, tabla, callout,
    H1, H2, H3, BODY, BODY_C, SMALL, CODE, CALLOUT,
)


# ============================================================================
# 7. Diseno del libreto y personalidad
# ============================================================================

def seccion_libreto() -> list:
    return [
        p("7. Diseno del libreto y personalidad del bot (Kitra)", H1),
        hr(),

        p("7.1 Nombre y presentacion", H2),
        p("<b>Nombre propuesto:</b> <i>Kitra</i>. Es un guino a KitraDep pero "
          "con identidad propia. Suena femenino, corto, facil de recordar. "
          "Alternativas: Kitri, Kina, Kit, o simplemente 'Asistente de "
          "KitraDep' si prefieren neutralidad."),
        p("<b>Primera impresion (mensaje de bienvenida):</b>"),
        p("<i>'Hola! Soy Kitra, la asistente virtual de KitraDep. Puedo "
          "ayudarte con informacion, agendar tu sesion o resolver dudas sobre "
          "nuestros servicios de kinesiologia. En que te puedo ayudar hoy?'</i>",
          CALLOUT),
        p("<b>Justificacion:</b> nombre + rol + capacidades + pregunta abierta "
          "(no menu numerico). En 4 lineas el usuario sabe con quien habla, que "
          "puede pedir, y tiene libertad para escribir cualquier cosa."),

        p("7.2 Tono y personalidad", H2),
        tabla([
            ["Dimension", "Definicion propuesta"],
            ["Formalidad", "Trata de USTED por defecto. Tutea si el usuario tutea primero."],
            ["Registro", "Espanol chileno neutro. Sin modismos muy marcados ('cachai', 'weon', 'po')."],
            ["Longitud", "Respuestas cortas (2-4 lineas). Si es tecnico, usa listas."],
            ["Emojis", "Uso moderado. Maximo 1 por mensaje. Priorizar utilidad sobre decoracion."],
            ["Empatia", "Reconoce el motivo de la consulta antes de responder ('Entiendo, buscas...')."],
            ["Ritmo", "No manda 5 mensajes seguidos. 1 respuesta = 1 burbuja WhatsApp."],
            ["Errores", "Si no entiende, pide aclaracion suavemente. Nunca dice 'no comprendo'."],
        ], anchos=[3.5 * cm, 12.5 * cm]),

        p("7.3 Ejemplos de conversaciones deseadas vs no deseadas", H2),

        p("<b>Ejemplo 1 - Pregunta libre sobre precios:</b>", H3),
        p("<font color='#B91C1C'><b>Usuario:</b> hola cuanto sale la kine? tengo isapre banmedica</font>", BODY),
        p("<font color='#6B7280'><b>Bot ACTUAL (menu rigido):</b> No entendi. Escribe 1) Servicios, 2) Precios, 3) Agendar.</font>", BODY),
        p("<font color='#065F46'><b>Bot HIBRIDO (Kitra):</b> Hola! Buenisimo que tengas ISAPRE. Con nosotros el valor por sesion es de $25.000. "
          "Tambien tenemos packs con descuento: 5 sesiones a $115.000 o 10 sesiones a $230.000. Te dejo boleta para reembolso "
          "en tu ISAPRE. Queres que te agende una primera evaluacion?</font>", BODY),

        p("<b>Ejemplo 2 - Pregunta fuera del guion pero relacionada:</b>", H3),
        p("<font color='#B91C1C'><b>Usuario:</b> tienen estacionamiento en el edificio?</font>", BODY),
        p("<font color='#6B7280'><b>Bot ACTUAL:</b> No entendi. Escribe menu para volver al inicio.</font>", BODY),
        p("<font color='#065F46'><b>Bot HIBRIDO:</b> El edificio no tiene estacionamiento propio, pero hay estacionamiento publico "
          "a media cuadra y varias lineas de micro llegan a Llano Subercaseaux. Si vienes en metro, la estacion mas cercana "
          "es San Miguel (Linea 2). Necesitas la direccion exacta?</font>", BODY),

        p("<b>Ejemplo 3 - Pregunta medica (debe derivar):</b>", H3),
        p("<font color='#B91C1C'><b>Usuario:</b> me duele mucho la rodilla al bajar escaleras, sera menisco?</font>", BODY),
        p("<font color='#6B7280'><b>Bot ACTUAL:</b> No entendi.</font>", BODY),
        p("<font color='#065F46'><b>Bot HIBRIDO (con guardrail medico):</b> Entiendo tu preocupacion. No puedo darte un diagnostico "
          "por chat, pero es exactamente el tipo de consulta que nuestro equipo puede evaluar en la primera sesion (que incluye "
          "evaluacion completa). Queres que te agende con una kinesiologa? Si el dolor es severo o repentino, te sugiero "
          "consultar tambien con un traumatologo.</font>", BODY),

        p("7.4 Que se necesita del equipo KitraDep para el libreto", H2),
        bullets([
            "<b>Validar nombre y tono</b> (30 min de reunion con quien defina la marca).",
            "<b>Dumps de conversaciones reales</b>: 20-30 chats completos de WhatsApp reciente (con datos personales borrados). Fuente de oro para calibrar el prompt.",
            "<b>Lista de 'nunca'</b>: cosas que el bot JAMAS debe decir (diagnosticos, promesas de sanacion, precios que no existen).",
            "<b>Handoff</b>: numero de WhatsApp o email donde deriva cuando el bot no puede. Horarios en que ese contacto responde.",
            "<b>FAQ ampliada</b>: agregar preguntas que hoy respondes a mano y no estan en el guion actual.",
        ]),
        PageBreak(),
    ]


# ============================================================================
# 8. Prompt engineering + RAG (mal llamado "entrenar el LLM")
# ============================================================================

def seccion_entrenamiento() -> list:
    return [
        p("8. 'Entrenar' el LLM: prompt engineering + RAG (no es fine-tuning)", H1),
        hr(),

        callout(
            "Aclaracion importante: cuando la gente dice 'entrenar el LLM' "
            "para un chatbot, en el 99% de los casos NO se refiere a "
            "fine-tuning real del modelo (que es caro, complejo y raramente "
            "necesario). Se refiere a prompt engineering + RAG, que es lo "
            "que aca proponemos y explicamos."
        ),

        p("8.1 Las tres formas de 'ensenarle' cosas a un LLM", H2),
        tabla([
            ["Metodo", "Que es", "Cuando conviene"],
            ["Prompt engineering", "Ajustar el system prompt para dar instrucciones detalladas.", "SIEMPRE. Es la base."],
            ["RAG (Retrieval-Augmented Generation)", "Buscar fragmentos relevantes de la base de conocimiento y agregarlos al contexto en cada request.", "Cuando la info es grande (>10K palabras)."],
            ["Fine-tuning", "Reentrenar los pesos del modelo con miles de ejemplos etiquetados.", "Muy raramente. Costoso y complejo."],
        ], anchos=[4.5 * cm, 7 * cm, 4.5 * cm], font_size=9),

        p("Para KitraDep: <b>prompt engineering + un RAG minimalista</b> son "
          "mas que suficientes. Fine-tuning se descarta."),

        p("8.2 Como funciona el prompt engineering en la practica", H2),
        p("Es un proceso iterativo, no un evento. Ciclo tipico:"),
        numbered([
            "Se escribe un prompt v1 basado en la personalidad definida.",
            "Se corren 20-30 conversaciones de prueba (algunas de dumps reales, algunas inventadas malintencionadamente).",
            "Se identifican fallos: 'aca invento un precio', 'aca no derivo cuando debia', 'aca respondio demasiado largo'.",
            "Se ajusta el prompt: se agregan reglas, ejemplos negativos, aclaraciones.",
            "Se re-testea. Se documentan las mejoras.",
            "Se repite hasta que el bot pase un conjunto de test predefinido (~50 casos).",
        ]),
        p("<b>Herramienta clave:</b> el <b>test suite de conversaciones</b>. Un "
          "archivo YAML con casos {input, resultado_esperado}. Se corre automatico "
          "despues de cada cambio de prompt. Es la salvaguarda contra romper "
          "algo al mejorar otra cosa (regresiones)."),

        p("8.3 Que es RAG y por que probablemente lo necesitemos", H2),
        p("<b>Retrieval-Augmented Generation</b>: en vez de meter TODA la base "
          "de conocimiento en cada request (caro y a veces excede el limite "
          "del modelo), primero se hace una busqueda de los fragmentos MAS "
          "relevantes al mensaje del usuario, y solo esos se agregan al "
          "contexto."),
        p("<b>Ejemplo concreto:</b> usuario pregunta 'que documentos necesito "
          "para reembolso ISAPRE?'. RAG busca en la base de conocimiento los "
          "fragmentos con palabras 'reembolso', 'ISAPRE', 'boleta', 'documento'. "
          "Solo esos 2-3 parrafos se pasan al LLM, no el documento completo."),
        p("<b>Implementacion minima:</b> con la libreria "
          "<font face='Courier'>chromadb</font> (base vectorial gratis y "
          "embebida) + embeddings de Google (gratis en el free tier). Total: "
          "~100 lineas de codigo. NO requiere GPU."),
        p("<b>Cuando saltar RAG:</b> si la base de conocimiento total pesa "
          "menos de ~5000 palabras (~20 KB de texto), directamente se puede "
          "meter completa en el contexto. Gemini Flash acepta 1M de tokens de "
          "contexto: sobra espacio. Para KitraDep, tal vez arranquemos SIN "
          "RAG y lo agreguemos si crece."),

        p("8.4 Estrategia de mejora continua", H2),
        p("Una vez en produccion, el bot mejora con estos loops:"),
        bullets([
            "<b>Log de conversaciones:</b> se guardan todas para poder revisar.",
            "<b>Revision semanal:</b> quien opere el bot lee 10-20 conversaciones aleatorias por semana.",
            "<b>Feedback explicito:</b> al final de la conversacion se puede pedir un thumbs up/down.",
            "<b>Alertas:</b> si el bot deriva a humano, si dice 'no se', si el usuario se enoja (palabras clave) -> notificacion al equipo.",
            "<b>A/B testing de prompts:</b> cambio de prompt se prueba en 10% de conversaciones antes de rolear al 100%.",
        ]),
        PageBreak(),
    ]


# ============================================================================
# 9. Guardrails, seguridad, etica
# ============================================================================

def seccion_guardrails_etica() -> list:
    return [
        p("9. Guardrails, seguridad, etica y cumplimiento", H1),
        hr(),

        p("9.1 Por que este capitulo es mas largo que los demas", H2),
        p("KitraDep opera en el rubro salud. Un bot que da consejo medico "
          "erroneo, diagnostica sin licencia, o promete resultados terapeuticos "
          "es un problema legal serio. Ademas, se manejan datos personales "
          "sensibles (RUT, telefono, condicion medica implicita). Este capitulo "
          "aborda como el diseno se protege contra esos riesgos."),

        p("9.2 Riesgos identificados y mitigaciones", H2),
        tabla([
            ["Riesgo", "Mitigacion"],
            ["Bot inventa precios o horarios", "Base de conocimiento como fuente unica + instrucciones estrictas + fallback: 'no tengo esa info, te derivo'."],
            ["Bot diagnostica una lesion", "Guardrail medico: detecta consulta clinica -> respuesta canned + handoff obligatorio."],
            ["Bot promete cura o resultado", "Prompt prohibe explicitamente. Test suite valida frases prohibidas."],
            ["Fuga de datos personales", "Sesiones aisladas por numero. RUT/telefono nunca en logs claros. HTTPS obligatorio."],
            ["Bot atacado con prompts maliciosos", "Filtro de tema + jailbreak detection + rate limiting por numero."],
            ["Costo runaway por abuso", "Rate limiting + circuit breaker: si un numero gasta > USD 1 en un dia se pausa."],
            ["Bot cae y nadie se entera", "Healthcheck + alertas por email al admin + fallback a mensaje 'estamos con problemas tecnicos'."],
        ], anchos=[5 * cm, 11 * cm], font_size=9),

        p("9.3 Cumplimiento legal (Chile)", H2),
        bullets([
            "<b>Ley 19.628 sobre proteccion de datos personales:</b> requiere consentimiento, finalidad especifica, y derecho de rectificacion. Se implementa con un mensaje de consentimiento en la primera interaccion.",
            "<b>Ley 20.584 sobre derechos y deberes del paciente:</b> el bot NO puede sustituir consulta profesional. Debe declararlo explicitamente cuando corresponda.",
            "<b>Nueva Ley 21.719 (2024, en vigencia progresiva 2026):</b> normativa reforzada de datos personales. Se recomienda revisar con abogado antes de produccion.",
            "<b>Retencion de datos:</b> definir cuanto tiempo se guardan las conversaciones (recomendado: 90 dias, salvo agendamientos confirmados).",
        ]),

        p("9.4 Declaraciones minimas obligatorias en el bot", H2),
        p("Al inicio de la conversacion (mensaje de bienvenida) o en pie de "
          "primer intercambio, deben aparecer:"),
        bullets([
            "Aviso de que es un asistente automatizado (no una persona real).",
            "Aviso de que las conversaciones pueden ser revisadas para mejorar el servicio.",
            "Aviso de que la informacion NO reemplaza consulta profesional.",
            "Enlace a la politica de privacidad (URL, aunque sea una pagina simple).",
            "Numero o contacto de emergencia real para casos urgentes.",
        ]),

        p("9.5 Handoff a humano: cuando y como", H2),
        p("El bot deriva a una persona real en los siguientes casos, siempre:"),
        numbered([
            "Usuario lo pide explicitamente ('quiero hablar con alguien', 'una persona por favor').",
            "El bot detecta consulta medica compleja (diagnostico, tratamiento, medicamento).",
            "Palabras clave de urgencia (dolor severo, no puedo caminar, accidente).",
            "Reclamo o queja formal ('estoy molesto', 'quiero devolucion', 'voy a reclamar').",
            "El bot no supo responder despues de 2 intentos en el mismo tema.",
            "Usuario que ya agendo, tiene una duda especifica sobre SU cita concreta.",
        ]),
        p("El handoff es una respuesta clara: <i>'Voy a derivarte con nuestra "
          "kine derivadora, Javiera. Te va a escribir por este mismo WhatsApp "
          "en un rato (o al +56 9 XXXX XXXX). Mientras tanto, hay algo mas en "
          "lo que te pueda ayudar?'</i>"),
        PageBreak(),
    ]


# ============================================================================
# 10. Integracion con WhatsApp de la empresa
# ============================================================================

def seccion_whatsapp() -> list:
    return [
        p("10. Integracion con WhatsApp de la empresa", H1),
        hr(),

        p("10.1 Los 3 caminos posibles", H2),
        tabla([
            ["Camino", "Setup", "Costo mensual", "Riesgo", "Recomendacion"],
            ["Meta Cloud API (oficial)", "1-3 semanas de tramites", "USD 0 (mensajes de servicio son gratis)", "Bajo", "PRODUCCION"],
            ["Twilio for WhatsApp (reventa)", "1 dia", "USD 1-5 fijo + centavos por mensaje", "Bajo", "PROTOTIPO"],
            ["whatsapp-web.js (no oficial)", "1 hora", "USD 0", "ALTO: baneo del numero", "NO USAR EN PRODUCCION"],
        ], anchos=[4 * cm, 3 * cm, 3.5 * cm, 3 * cm, 2.5 * cm], font_size=8),

        p("10.2 Plan recomendado: Twilio Sandbox para desarrollo -> Meta Cloud API para produccion", H2),
        p("<b>Fase de desarrollo (semanas 2-4):</b> Twilio Sandbox. Es gratis, "
          "se activa en 15 minutos, permite probar con tu propio WhatsApp "
          "personal. Limitacion: cada persona que quiera probarlo debe enviar "
          "un codigo de union primero. Perfecto para pruebas internas."),
        p("<b>Fase de produccion (semanas 5-6+):</b> Meta Cloud API. Requiere "
          "tramites pero es la unica opcion escalable y sin costo por mensaje "
          "de servicio."),

        p("10.3 Requisitos concretos para Meta Cloud API", H2),
        numbered([
            "<b>Cuenta Meta Business:</b> crearla en <font face='Courier'>business.facebook.com</font>. Gratis, 30 minutos.",
            "<b>Verificacion del negocio:</b> Meta pide documentacion (RUT de la empresa, direccion, sitio web, factura de servicios). Tarda 3-14 dias habiles.",
            "<b>Numero de telefono dedicado:</b> NO puede ser el WhatsApp personal actual del centro. Se puede portar el numero actual si se libera del app de WhatsApp normal (proceso irreversible), o comprar un numero nuevo.",
            "<b>Display name aprobado:</b> Meta revisa el nombre que aparecera al chatear con el bot (ej. 'KitraDep - Kinesiologia'). Tarda 1-3 dias.",
            "<b>App de Meta for Developers:</b> se crea una app tipo 'WhatsApp' que expone el API token. Gratis.",
            "<b>Webhook publico HTTPS:</b> el servidor donde corre el bot debe estar expuesto a internet con SSL valido. Se resuelve con VPS + Let's Encrypt (gratis).",
            "<b>Plantillas de mensajes (templates):</b> si se envian mensajes proactivos (recordatorios), cada template debe ser aprobado por Meta. Los mensajes de respuesta a chats iniciados por el usuario NO requieren template.",
        ]),

        p("10.4 Que pasa dentro de la integracion tecnica", H2),
        p("<b>Flujo entrante</b> (paciente escribe al bot):"),
        p("""1. Paciente escribe al numero de WhatsApp del centro.
2. Meta Cloud API envia un POST a nuestro webhook: https://kitradep.tudominio.cl/webhook
3. Webhook FastAPI recibe el mensaje, extrae numero + texto.
4. Se recupera la sesion del usuario (SQLite), se agrega el mensaje al historial.
5. Router decide: flujo controlado o LLM.
6. Se genera la respuesta.
7. Se envia respuesta via POST a Meta Cloud API.
8. Meta la entrega en el WhatsApp del paciente.
9. Se guarda la conversacion en BD.
""", CODE),
        p("Latencia total esperada: 1.5 a 3 segundos (99% de eso es el LLM)."),

        p("10.5 Numero de telefono: opciones concretas", H2),
        bullets([
            "<b>Opcion A - Numero nuevo:</b> comprar una linea prepago o SIM dedicada (~CLP 5000 setup, ~CLP 2000/mes minimo). Independiente del numero actual del centro.",
            "<b>Opcion B - Portar el numero actual:</b> el numero de WhatsApp que hoy usa el centro se desconecta del WhatsApp normal y se conecta al bot. Riesgo: se pierden todos los chats historicos y grupos. Recomendable solo si quieren consolidar.",
            "<b>Opcion C - Segundo numero del mismo dueno:</b> muchos celulares permiten dual SIM o eSIM. Se agrega una linea nueva al celu personal del director, dedicada al bot. Practico y barato.",
        ]),

        p("10.6 Mensajes proactivos (recordatorios de cita)", H2),
        p("Aparte de responder, el bot puede iniciar conversaciones. Ejemplo: "
          "recordatorio 24 horas antes de la sesion, o solicitud de feedback 1 "
          "hora despues. Consideraciones:"),
        bullets([
            "Cada mensaje proactivo debe usar un <b>template aprobado</b> por Meta.",
            "Costo por mensaje: ~USD 0.05-0.07 (Chile, categoria 'Utility').",
            "Si el paciente responde al recordatorio, se abre una 'ventana de servicio' de 24h en la que se puede seguir respondiendo gratis.",
            "Recomendacion: implementar recordatorios en Fase 4 (opcional), despues de que el bot este estable en produccion.",
        ]),
        PageBreak(),
    ]
