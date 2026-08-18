"""Contenido - PARTE 2: conceptos, arquitectura, 6 componentes, comparativa LLMs."""
from __future__ import annotations

from reportlab.platypus import PageBreak, Spacer
from reportlab.lib.units import cm

from generar_pdf import (
    p, bullets, numbered, hr, spacer, tabla, callout,
    H1, H2, H3, BODY, BODY_C, SMALL, CODE, CALLOUT,
)


# ============================================================================
# 3. Que es un bot hibrido (conceptos)
# ============================================================================

def seccion_conceptos() -> list:
    return [
        p("3. Que es un bot hibrido con LLM (conceptos)", H1),
        hr(),

        p("3.1 Los tres tipos de bot que existen", H2),
        p("Antes de justificar el enfoque hibrido, conviene ubicar donde se para "
          "cada tecnologia:"),
        tabla([
            ["Tipo", "Como decide", "Pros", "Contras"],
            ["Maquina de estados", "Menus + palabras exactas", "Control total, cero costo, cero alucinacion", "Rigido, robotico, se pierde con texto libre"],
            ["LLM puro", "El modelo genera todo", "Se siente humano, entiende cualquier cosa", "Puede inventar datos, sin garantia de flujo, cuesta tokens"],
            ["Hibrido", "Router: flujo para lo critico, LLM para lo libre", "Lo mejor de ambos mundos", "Mas complejo de construir y afinar"],
        ], anchos=[3.5 * cm, 4 * cm, 5 * cm, 4 * cm], font_size=8),

        p("3.2 El truco: no todo va al LLM", H2),
        p("El error mas comun al hacer un bot 'inteligente' es mandar TODO al "
          "LLM. Suena tentador porque es la parte magica, pero rompe el bot en "
          "las tareas criticas. Ejemplo:"),
        p("<b>Escenario:</b> el usuario dice 'quiero agendar para el martes a las "
          "3 con Javiera'. Un LLM puro podria confirmar la cita alegremente, "
          "aunque Javiera no atienda los martes, aunque las 3 PM no exista en "
          "la agenda, o aunque el paciente no haya dado su nombre ni telefono. "
          "Un flujo controlado nunca cometeria ese error."),
        p("La solucion hibrida:"),
        bullets([
            "<b>Conversacion libre, dudas, FAQ, saludos, aclaraciones</b> -> LLM (natural y flexible).",
            "<b>Recolectar datos criticos, cerrar agenda, confirmar precios</b> -> Flujo controlado (preciso y auditable).",
            "El <b>router</b> es la pieza que decide en cada turno cual usar.",
        ]),

        p("3.3 Analogia util", H2),
        callout(
            "Pensalo asi: el bot hibrido es como un vendedor amable en un "
            "mostrador. Charla contigo sobre el clima, te explica los productos, "
            "responde tus dudas raras (LLM). Pero cuando llega el momento de "
            "cobrar tu tarjeta, saca el POS (flujo controlado) y sigue los "
            "pasos exactos del checkout: no improvisa el numero de tarjeta, no "
            "'redondea' el precio, no salta pasos."
        ),
        p("Esa disciplina es la que hace confiable el enfoque hibrido en un "
          "negocio real, especialmente en un rubro sensible como salud."),
        PageBreak(),
    ]


# ============================================================================
# 4. Arquitectura tecnica propuesta
# ============================================================================

def seccion_arquitectura() -> list:
    diagrama = """+--------------------+     +--------------------+     +--------------------+
|                    |     |                    |     |                    |
|  WhatsApp del      | <-> |  Meta Cloud API    | <-> |  Webhook FastAPI   |
|  paciente          |     |  (canal oficial)   |     |  (nuestro server)  |
|                    |     |                    |     |                    |
+--------------------+     +--------------------+     +--------------------+
                                                              |
                                                              v
                                             +--------------------------------+
                                             |         ROUTER HIBRIDO         |
                                             |  (decide flujo vs LLM)         |
                                             +--------------------------------+
                                                     |               |
                                              [tarea critica]   [charla libre]
                                                     |               |
                                                     v               v
                                       +-------------------+   +-------------------+
                                       | Motor de estados  |   | LLM Gemini 2.0    |
                                       | (guion.yaml)      |   | Flash + prompt    |
                                       +-------------------+   +-------------------+
                                                     |               |
                                                     +-------+-------+
                                                             |
                                                             v
                                             +--------------------------------+
                                             | Memoria + BD (SQLite/Postgres) |
                                             | Historial, agendamientos, log  |
                                             +--------------------------------+
                                                             |
                                                             v
                                             +--------------------------------+
                                             |    Notificacion al staff       |
                                             |    (email / WhatsApp interno)  |
                                             +--------------------------------+
"""
    return [
        p("4. Arquitectura tecnica propuesta", H1),
        hr(),

        p("4.1 Vista general", H2),
        p("La siguiente figura muestra el flujo de datos desde el mensaje del "
          "paciente hasta la respuesta del bot y la notificacion al equipo:"),
        spacer(0.2),
        p(diagrama.replace("\n", "<br/>").replace(" ", "&nbsp;"), CODE),
        spacer(0.3),

        p("4.2 Que se reutiliza del bot actual", H2),
        p("El diseno respeta lo ya construido y solo agrega capas encima. "
          "Concretamente:"),
        tabla([
            ["Componente actual", "Rol en el nuevo bot"],
            ["motor_core.py", "Sigue siendo el motor de la maquina de estados (tareas criticas)."],
            ["guion.yaml", "Sigue definiendo el flujo de agendamiento paso a paso."],
            ["webapp.py + templates", "Se transforma en la interfaz de pruebas y demos internas (opcional)."],
            ["MOTOR.md, WEBAPP.md, casos_reales.md", "Documentacion base que alimenta el system prompt del LLM."],
        ], anchos=[6 * cm, 10 * cm]),

        p("4.3 Que se agrega nuevo", H2),
        bullets([
            "<b>Modulo LLM</b> (nuevo archivo <font face='Courier'>llm_client.py</font>): cliente que habla con Gemini API.",
            "<b>Router hibrido</b> (<font face='Courier'>router.py</font>): logica de decision flujo vs LLM en cada turno.",
            "<b>Base de conocimiento</b> (<font face='Courier'>knowledge/*.md</font>): documento fuente que el LLM lee.",
            "<b>System prompt</b> (<font face='Courier'>prompts/kitra.txt</font>): personalidad, tono, limites, ejemplos.",
            "<b>Memoria de conversacion</b>: buffer de N ultimos turnos + resumen comprimido si excede.",
            "<b>Guardrails</b> (<font face='Courier'>guardrails.py</font>): filtros de tema, PII, deteccion de handoff a humano.",
            "<b>Webhook WhatsApp</b> (<font face='Courier'>whatsapp_webhook.py</font>): endpoints para Meta Cloud API o Twilio.",
            "<b>Persistencia</b> (SQLite inicial, Postgres si escala): conversaciones, agendamientos, logs de LLM.",
            "<b>Notificaciones al staff</b>: email o WhatsApp interno cuando se cierra un agendamiento o el bot deriva a humano.",
        ]),
        PageBreak(),
    ]


# ============================================================================
# 5. Los 6 componentes en detalle
# ============================================================================

def seccion_componentes() -> list:
    out: list = [
        p("5. Los 6 componentes tecnicos en detalle", H1),
        hr(),
        p("Esta seccion desarrolla cada pieza del bot hibrido, con foco en el "
          "'como' y las decisiones de diseno. La lectura es densa pero es el "
          "corazon tecnico de la propuesta; puede saltarse en una primera "
          "lectura y volver luego."),
        spacer(0.2),
    ]

    # 5.1 LLM
    out += [
        p("5.1 El LLM (cerebro que redacta las respuestas)", H2),
        p("<b>Que hace:</b> recibe en cada turno el system prompt, la base de "
          "conocimiento relevante y los ultimos mensajes de la conversacion. "
          "Devuelve una respuesta en lenguaje natural."),
        p("<b>Modelo elegido:</b> Google Gemini 2.0 Flash (razones detalladas en "
          "seccion 6). Tres motivos rapidos:"),
        bullets([
            "Free tier real y utilizable: hasta ~1500 requests por dia gratis para desarrollo.",
            "Costo pagado ridiculamente bajo: USD 0.075 por millon de tokens de entrada, USD 0.30 por millon de salida.",
            "Latencia baja (~0.8-1.5 segundos) que se disimula bien con el 'escribiendo...' del chat.",
        ]),
        p("<b>Implementacion:</b> el SDK oficial de Google se llama "
          "<font face='Courier'>google-generativeai</font> y se instala con "
          "<font face='Courier'>uv pip install google-generativeai</font>. La "
          "llamada minima es de 5 lineas. El modulo se encapsula en "
          "<font face='Courier'>llm_client.py</font> con retry, timeout y "
          "fallback a mensaje generico si el API cae."),
        p("<b>Alternativa gratis 100%:</b> Ollama local con Llama 3.1 8B. "
          "Requiere un PC con 16GB de RAM. Se usa como fallback offline o si "
          "hay que garantizar privacidad total sin salida a internet."),
    ]

    # 5.2 Base de conocimiento
    out += [
        p("5.2 Base de conocimiento (lo que el bot 'sabe' de KitraDep)", H2),
        p("<b>Que es:</b> uno o varios archivos de texto (Markdown) con TODO lo "
          "que el bot puede necesitar responder. Es el 'libro de texto' que se "
          "le pasa al LLM en cada request como contexto."),
        p("<b>Estructura propuesta:</b>"),
        p("""knowledge/
    01_servicios.md       # que se ofrece, duracion, evaluacion inicial, sesion tipica
    02_precios.md         # tabla completa por prevision + reglas legales FONASA
    03_horarios.md        # horarios, kines por turno, sabados
    04_ubicacion.md       # direccion, como llegar, estacionamiento, transporte publico
    05_previsiones.md     # FONASA (no adherido, valor preferencial), ISAPRE, particular
    06_agendamiento.md    # como es el proceso, orden medica, boletas, reembolso
    07_faq.md             # preguntas frecuentes reales de WhatsApp
    08_politicas.md       # cancelaciones, atrasos, primera sesion, pagos
    09_equipo.md          # nombres, especialidades, horarios de cada kine
    10_limites.md         # temas donde el bot NO opina (diagnostico, tratamiento)
""", CODE),
        p("<b>Fuente:</b> se destila de <font face='Courier'>chatbot/flujo/"
          "casos_reales.md</font> ya existente, mas dumps de conversaciones "
          "reales de WhatsApp que aportara el equipo de KitraDep. Total "
          "estimado: 3000-5000 palabras (~15-25 KB de texto). Perfectamente "
          "manejable como contexto del LLM en cada request."),
        p("<b>Actualizacion:</b> cambiar informacion (nuevo precio, nuevo kine, "
          "nuevo horario) es editar un archivo Markdown y reiniciar el servidor. "
          "No se toca codigo Python. Esto es una ventaja enorme del diseno."),
    ]

    # 5.3 System prompt
    out += [
        p("5.3 System prompt (personalidad + limites)", H2),
        p("<b>Que es:</b> el mensaje 'invisible' que se le manda al LLM antes "
          "de cualquier interaccion del usuario. Define quien es el bot, como "
          "habla, que puede y que no puede hacer. Es donde vive el 80% de la "
          "calidad percibida del bot."),
        p("<b>Estructura tipica del prompt:</b>"),
        numbered([
            "<b>Identidad:</b> 'Sos Kitra, la asistente virtual de KitraDep, un centro de kinesiologia en San Miguel, Santiago de Chile'.",
            "<b>Personalidad:</b> 'Tono cercano, chileno neutro (evitar chilenismos muy marcados), empatico, profesional. Trata de usted por defecto, tutea si el usuario tutea primero'.",
            "<b>Alcance:</b> 'Solo respondes sobre KitraDep. Si te preguntan otra cosa (politica, deportes, otros negocios), decis amablemente que no podes ayudar con eso'.",
            "<b>Anti-alucinacion:</b> 'Si no sabes algo con certeza, decilo. NUNCA inventes precios, horarios, nombres de kinesiologos ni fechas'.",
            "<b>Handoff:</b> 'Si el paciente pide hablar con una persona, tiene una duda medica compleja, o el tema es delicado, deriva al WhatsApp de la kine derivadora que se te indique'.",
            "<b>Formato:</b> 'Respuestas cortas (2-4 lineas), usa *negrita* para lo importante, no uses emojis excesivos (maximo 1 por respuesta)'.",
            "<b>Ejemplos:</b> 3-5 conversaciones ideales que muestran el estilo esperado.",
        ]),
        p("Longitud tipica: 100-200 lineas. Es un archivo de texto plano que se "
          "itera decenas de veces hasta que el bot 'suena' como uno quiere. "
          "Ese trabajo iterativo es el arte del prompt engineering (seccion 8)."),
    ]

    # 5.4 Router
    out += [
        p("5.4 El router hibrido (decide flujo vs LLM)", H2),
        p("<b>Que es:</b> la pieza mas critica del diseno hibrido. En cada "
          "mensaje del usuario, decide si atiende el motor de estados o el LLM."),
        p("<b>Reglas propuestas (en orden de prioridad):</b>"),
        numbered([
            "Si el usuario esta en medio de una tarea critica ya iniciada (ej. dio nombre, esta ingresando telefono) -> <b>flujo controlado</b> continua.",
            "Si el LLM detecta intencion de agendar en la conversacion libre -> <b>transfiere</b> al flujo controlado (que empieza a pedir datos ordenadamente).",
            "Si el usuario escribe un comando global (menu, cancelar, hablar con humano) -> <b>manejo especial</b>.",
            "En cualquier otro caso (dudas, FAQ, saludos, aclaraciones) -> <b>LLM</b> responde con contexto.",
        ]),
        p("<b>Implementacion:</b> ~150 lineas de Python en "
          "<font face='Courier'>router.py</font>. La deteccion de intencion "
          "'quiere agendar' la hace el propio LLM devolviendo una etiqueta "
          "estructurada en su respuesta (tecnica conocida como 'function "
          "calling' o 'tool use')."),
    ]

    # 5.5 Memoria
    out += [
        p("5.5 Memoria de conversacion", H2),
        p("<b>Problema:</b> el LLM es amnesico. Cada llamada al API es "
          "independiente. Si no le pasas los mensajes previos, no recuerda "
          "de que estaban hablando."),
        p("<b>Solucion en 3 capas:</b>"),
        bullets([
            "<b>Buffer corto:</b> se guardan y reenvian los ultimos 10 turnos (usuario + bot) en cada request. Cubre 95% de las conversaciones tipicas.",
            "<b>Resumen comprimido:</b> si la charla supera 10 turnos, el LLM resume los turnos mas viejos en 2-3 lineas ('el paciente pregunto por precios FONASA, se le explico...') y se reemplazan los originales por el resumen.",
            "<b>Persistencia:</b> todo se guarda en SQLite ('conversaciones' table) para poder auditar y mejorar el bot despues.",
        ]),
        p("<b>Impacto en costo:</b> los tokens de historial se cobran como "
          "input. Un turno tipico consume ~500-1000 tokens de contexto. Con "
          "Gemini Flash a USD 0.075/M eso son 0.00005-0.0001 dolares por turno. "
          "Practicamente nada para volumenes chicos."),
    ]

    # 5.6 Guardrails
    out += [
        p("5.6 Guardrails de seguridad y prevencion de alucinaciones", H2),
        p("<b>Que son:</b> capas de proteccion que evitan que el bot se salga "
          "del carril. Se implementan en varios puntos:"),
        tabla([
            ["Guardrail", "Como funciona"],
            ["Filtro de temas", "Regex + LLM chequean si el mensaje sale del dominio KitraDep."],
            ["Filtro de PII", "No se logea RUT/telefono/email en claro. Se hashean o enmascaran."],
            ["Anti-alucinacion", "Instrucciones estrictas + verificacion post-respuesta con base de conocimiento."],
            ["Rate limiting", "Max N mensajes por numero por hora, para evitar abuso o costo runaway."],
            ["Deteccion medica", "Si el mensaje es una consulta medica clara -> handoff automatico a humano."],
            ["Deteccion emergencia", "Palabras clave de urgencia (dolor severo, no puedo caminar) -> derivacion inmediata a telefono de emergencia."],
        ], anchos=[4 * cm, 12 * cm]),
        p("<b>Impacto operativo:</b> cada guardrail agrega latencia y complejidad. "
          "Se implementan por orden de importancia. El critico es el de "
          "deteccion medica: en un rubro de salud, un bot que diagnostica es "
          "un riesgo legal serio."),
        PageBreak(),
    ]
    return out


# ============================================================================
# 6. Comparativa de modelos LLM
# ============================================================================

def seccion_comparativa_llms() -> list:
    return [
        p("6. Comparativa de modelos LLM (Gemini vs alternativas)", H1),
        hr(),

        p("6.1 Modelos evaluados", H2),
        p("Se consideran cinco alternativas viables para un bot de este tamano. "
          "La eleccion NO es solo tecnica: influye el costo, la latencia, la "
          "privacidad, y la facilidad de cambio si algo sale mal."),
        tabla([
            ["Modelo", "USD in / 1M tok", "USD out / 1M tok", "Latencia", "Free tier", "Calidad"],
            ["Gemini 2.0 Flash (Google)", "0.075", "0.30", "~1.0s", "Si (generoso)", "Muy alta"],
            ["GPT-4o-mini (OpenAI)", "0.15", "0.60", "~1.2s", "No", "Muy alta"],
            ["Claude Haiku 3.5 (Anthropic)", "0.80", "4.00", "~1.5s", "No", "Muy alta"],
            ["GPT-4o (OpenAI, top)", "2.50", "10.00", "~1.5s", "No", "Excelente"],
            ["Llama 3.1 8B (Ollama local)", "0", "0", "2-5s CPU", "Gratis (auto-host)", "Media-alta"],
        ], anchos=[4 * cm, 2.2 * cm, 2.2 * cm, 1.8 * cm, 2.5 * cm, 2 * cm], font_size=8),

        p("6.2 Por que Gemini 2.0 Flash para KitraDep", H2),
        bullets([
            "<b>Costo:</b> el mas barato de los oficiales por un margen amplio (~50% mas barato que GPT-4o-mini, 10x mas barato que Claude Haiku).",
            "<b>Free tier real:</b> hasta 1500 requests por dia sin pagar. Suficiente para todo el desarrollo y las primeras semanas de produccion de un negocio chico.",
            "<b>Calidad:</b> para tareas de conversacion en espanol con contexto acotado, esta al nivel de GPT-4o-mini.",
            "<b>Cambio de modelo trivial:</b> encapsulamos el LLM detras de una interfaz. Si Gemini decepciona, migrar a GPT-4o-mini o Claude es cambiar 20 lineas.",
        ]),

        p("6.3 Cuando reconsiderar la eleccion", H2),
        tabla([
            ["Escenario", "Modelo recomendado"],
            ["Bot muy complejo con razonamiento medico avanzado", "Claude Sonnet o GPT-4o"],
            ["Volumen enorme (>10k conversaciones/dia) y costo crucial", "Gemini Flash o Llama 3.1 self-hosted"],
            ["Privacidad total obligatoria (sin salida a internet)", "Llama 3.1 con Ollama en servidor propio"],
            ["Necesidad de function calling avanzado y tools", "GPT-4o-mini (mejor documentacion de tools)"],
            ["Si el proyecto migra a Walmart", "OBLIGATORIO: AI Innovation Lab / AI Launchpad interno"],
        ], anchos=[8 * cm, 8 * cm]),

        p("6.4 Estrategia de portabilidad", H2),
        p("El diseno del modulo <font face='Courier'>llm_client.py</font> abstrae "
          "el proveedor detras de una funcion "
          "<font face='Courier'>generar_respuesta(system_prompt, historial, "
          "mensaje) -> str</font>. Cualquier cambio de proveedor futuro no "
          "toca la logica del router ni de los guardrails. Esto es una "
          "aplicacion del principio de <b>dependency inversion</b> (la 'D' de "
          "SOLID): dependemos de una abstraccion, no de una implementacion "
          "concreta."),
        PageBreak(),
    ]
