"""Contenido - PARTE 4: despliegue, cronograma, COSTOS, riesgos, checklist, anexos."""
from __future__ import annotations

from reportlab.platypus import PageBreak, Spacer
from reportlab.lib.units import cm

from generar_pdf import (
    p, bullets, numbered, hr, spacer, tabla, callout,
    H1, H2, H3, BODY, BODY_C, SMALL, CODE, CALLOUT,
)


# ============================================================================
# 11. Despliegue, hosting, operacion
# ============================================================================

def seccion_despliegue() -> list:
    return [
        p("11. Despliegue, hosting y operacion 24/7", H1),
        hr(),

        p("11.1 Opciones de hosting", H2),
        tabla([
            ["Opcion", "Costo/mes", "Ventajas", "Desventajas"],
            ["PC personal + ngrok", "USD 0", "Cero setup, ideal para desarrollo", "Se cae si apagas el PC. NO produccion."],
            ["Hetzner CX11 (VPS)", "USD 4.60", "Barato, potente, buena reputacion", "Requiere setup Linux basico"],
            ["DigitalOcean Basic Droplet", "USD 6.00", "Interfaz amigable, docs excelentes", "Un pelo mas caro"],
            ["Railway.app", "USD 5-10", "Deploy con un click desde Git", "Se puede disparar con trafico"],
            ["Fly.io", "USD 0-5 (free tier)", "Deploy simple, escala automatico", "Free tier limitado"],
            ["AWS/GCP/Azure", "USD 20-50+", "Escala infinito, features avanzadas", "Overkill para el volumen"],
        ], anchos=[4 * cm, 2.5 * cm, 4.5 * cm, 5 * cm], font_size=8),

        p("<b>Recomendacion:</b> Hetzner CX11 (USD 4.60/mes) para produccion. "
          "Excelente relacion precio/potencia, ubicacion europea (latencia OK a "
          "Chile), stack Ubuntu estandar."),

        p("11.2 Stack de servidor propuesto", H2),
        p("""Sistema operativo:  Ubuntu 24.04 LTS
Runtime:            Python 3.12 con uv
Web server:         Uvicorn (dev) + Gunicorn (prod)
Reverse proxy:      Caddy (o nginx) con SSL automatico Let's Encrypt
BD inicial:         SQLite (archivo en disco)
BD si escala:       PostgreSQL 16
Proceso manager:    systemd (nativo Linux)
Logs:               journalctl + archivo rotado en disco
Backups:            script cron diario a S3-compatible (Backblaze B2, USD 6/TB)
Monitoreo:          UptimeRobot (free tier) + Sentry (free tier)
""", CODE),

        p("11.3 CI/CD y deploy", H2),
        bullets([
            "<b>Repositorio Git</b> privado (GitHual, gratis).",
            "<b>Deploy automatico:</b> push a rama <font face='Courier'>main</font> -> GitHub Actions ejecuta tests -> si pasan, se conecta por SSH al servidor y hace pull + restart del servicio.",
            "<b>Rollback:</b> git revert + push. En 2 minutos vuelve a la version anterior.",
            "<b>Environments:</b> staging (para probar cambios) + production. Ambos en el mismo VPS con puertos distintos, o dos VPS baratos.",
        ]),

        p("11.4 Backups y disaster recovery", H2),
        bullets([
            "<b>Datos criticos:</b> BD SQLite (conversaciones, agendamientos, sesiones), base de conocimiento (git), configuracion (.env cifrado).",
            "<b>Frecuencia:</b> BD se backupea diariamente a las 3 AM Chile. Retencion 30 dias.",
            "<b>Ubicacion:</b> Backblaze B2 (USD 0.006/GB/mes) o Google Drive (15 GB gratis).",
            "<b>Restauracion:</b> documentada en <font face='Courier'>RUNBOOK.md</font>, testeada trimestralmente.",
        ]),

        p("11.5 Monitoreo y alertas", H2),
        bullets([
            "<b>UptimeRobot:</b> pinga <font face='Courier'>/health</font> cada 5 minutos. Alerta por email si cae.",
            "<b>Sentry:</b> captura errores no manejados con stack trace. Notifica al admin.",
            "<b>Metricas custom:</b> requests/min, latencia LLM, costo diario acumulado. Dashboard simple con Grafana o incluso un flat HTML.",
            "<b>Alertas de negocio:</b> mas de 5 handoffs por hora, o costo LLM > USD 1/dia -> email.",
        ]),
        PageBreak(),
    ]


# ============================================================================
# 12. Plan de trabajo por fases
# ============================================================================

def seccion_plan() -> list:
    return [
        p("12. Plan de trabajo por fases y cronograma", H1),
        hr(),

        p("Timeline realista de 6 semanas asumiendo dedicacion parcial de "
          "Felipe (~10 hrs/semana) y trabajo asincronico con la asistente IA "
          "(Kira/Code Puppy) para la programacion:"),

        p("12.1 Fase A - Bot hibrido en simulador local (Semana 1)", H2),
        p("<b>Objetivo:</b> Kitra funcionando en la webapp local con LLM. "
          "Aun no toca WhatsApp real.", BODY),
        bullets([
            "Sacar API key de Gemini (Felipe, 5 min).",
            "Instalar SDK google-generativeai (Kira, 10 min).",
            "Programar llm_client.py con retry/timeout (Kira, 2 hrs).",
            "Programar router hibrido primera version (Kira, 3 hrs).",
            "Escribir system prompt v1 basado en casos_reales.md (Kira, 2 hrs).",
            "Convertir guion.yaml a base de conocimiento en Markdown (Kira, 2 hrs).",
            "Integrar todo en webapp.py (Kira, 2 hrs).",
            "Testing y primeras iteraciones de prompt (Felipe + Kira, 4 hrs).",
        ]),
        p("<b>Entregable:</b> corre <font face='Courier'>python webapp.py</font> "
          "y Kitra responde conversacionalmente a cualquier cosa, con memoria "
          "de los ultimos turnos, y activa el flujo estricto cuando detecta "
          "intencion de agendar."),

        p("12.2 Fase B - Calibrar personalidad y conocimiento (Semana 2)", H2),
        bullets([
            "Recibir dumps de conversaciones reales de WhatsApp (Felipe, 3 hrs).",
            "Expandir base de conocimiento (FAQ, casos borde, politicas) (Kira + Felipe, 4 hrs).",
            "Crear test suite con 30-50 conversaciones esperadas (Kira, 3 hrs).",
            "Iterar prompt en 5-10 rondas hasta que pase >90% de tests (Felipe + Kira, 6 hrs).",
            "Implementar guardrails (filtro tema, PII, medico) (Kira, 3 hrs).",
            "Persistencia SQLite + notificaciones al staff (Kira, 3 hrs).",
        ]),
        p("<b>Entregable:</b> bot en simulador que suena humano, evita "
          "alucinaciones, notifica al staff cuando alguien agenda."),

        p("12.3 Fase C - Conectar a WhatsApp Sandbox (Semana 3)", H2),
        bullets([
            "Crear cuenta Twilio (Felipe, 30 min).",
            "Activar Sandbox de WhatsApp (Felipe, 30 min).",
            "Programar webhook Twilio en FastAPI (Kira, 3 hrs).",
            "Configurar ngrok para exponer el PC personal (Felipe, 30 min).",
            "Testing end-to-end con WhatsApp real de Felipe y 2-3 personas de confianza (Felipe, 4 hrs).",
            "Ajustes por comportamiento en canal real (Kira, 3 hrs).",
        ]),
        p("<b>Entregable:</b> Kitra responde en WhatsApp real via Twilio "
          "Sandbox. Cero costo, cero tramite Meta."),

        p("12.4 Fase D - Migrar a Meta Cloud API para produccion (Semanas 4-5)", H2),
        bullets([
            "Iniciar tramites Meta Business (Felipe, 2 hrs iniciales, luego espera).",
            "Consegur numero de telefono dedicado (Felipe, 2 hrs).",
            "Contratar VPS y setup basico (Kira + Felipe, 4 hrs).",
            "Configurar dominio + SSL (Kira, 2 hrs).",
            "Programar webhook Meta Cloud API (Kira, 3 hrs).",
            "Deploy CI/CD desde GitHub (Kira, 3 hrs).",
            "Monitoreo, alertas, backups (Kira, 4 hrs).",
            "Esperar aprobacion Meta (3-14 dias, en paralelo).",
        ]),
        p("<b>Entregable:</b> Kitra corriendo 24/7 en VPS, expuesta al numero "
          "oficial de KitraDep via Meta Cloud API."),

        p("12.5 Fase E - Piloto controlado y hardening (Semana 6)", H2),
        bullets([
            "Anunciar Kitra a un grupo piloto (pacientes recurrentes, 20-30 personas) (Felipe, 2 hrs).",
            "Monitoreo intensivo 7 dias: revisar todas las conversaciones (Felipe + Kira, 6 hrs).",
            "Ajustes finales de prompt y guardrails segun feedback real (Kira, 4 hrs).",
            "Documentacion final: runbook, manual de operacion, guia para actualizar base de conocimiento (Kira, 3 hrs).",
        ]),
        p("<b>Entregable:</b> Kitra en produccion, con proceso claro para "
          "operarla, actualizarla y monitorearla. Proyecto cerrado."),

        p("12.6 Fase F (Opcional, Semanas 7+) - Mejoras", H2),
        bullets([
            "Recordatorios automaticos 24hs antes de la cita.",
            "Encuesta post-sesion.",
            "Dashboard interno de metricas (conversaciones, agendamientos, tasas de handoff).",
            "Integracion con calendario del centro (Google Calendar API).",
            "Migracion a Postgres si SQLite queda chico.",
        ]),
        PageBreak(),
    ]


# ============================================================================
# 13. COSTOS DETALLADOS (la seccion estrella)
# ============================================================================

def seccion_costos() -> list:
    return [
        p("13. Costos detallados: 1 mes, 3, 6 y 12 meses", H1),
        hr(),

        p("Esta seccion desglosa TODOS los costos previsibles, separando setup "
          "unico (upfront) y operacion recurrente. Los precios estan en USD y "
          "reflejan valores publicos al momento de este documento. Se incluyen "
          "escenarios pesimistas y optimistas."),

        p("13.1 Supuestos de volumen", H2),
        tabla([
            ["Escenario", "Conversaciones/dia", "Turnos/conversacion", "Turnos/mes"],
            ["Bajo (piloto)", "20", "6", "3.600"],
            ["Medio (estable)", "100", "8", "24.000"],
            ["Alto (exito)", "300", "8", "72.000"],
        ], anchos=[4 * cm, 4 * cm, 4 * cm, 4 * cm]),

        p("Un 'turno' es un mensaje del usuario + respuesta del bot. En el "
          "escenario medio, el bot procesa ~800 turnos por dia."),

        p("13.2 Costo LLM (Gemini 2.0 Flash) por escenario", H2),
        p("Precio publico: USD 0.075 por 1M tokens input, USD 0.30 por 1M "
          "tokens output. Estimacion tipica por turno: ~1200 tokens input "
          "(system prompt + KB + historial) + ~200 tokens output. Costo por "
          "turno: ~USD 0.00015."),
        tabla([
            ["Escenario", "Turnos/mes", "Costo LLM/mes", "Free tier cubre?"],
            ["Bajo", "3.600", "USD 0.54", "SI (100% gratis)"],
            ["Medio", "24.000", "USD 3.60", "Parcialmente"],
            ["Alto", "72.000", "USD 10.80", "No (paga completo)"],
        ], anchos=[3 * cm, 3.5 * cm, 4 * cm, 5.5 * cm]),
        callout(
            "Con Gemini Flash el costo del LLM es marginal. Incluso a 300 "
            "conversaciones/dia (300 pacientes distintos!), el LLM cuesta "
            "menos que una pizza. No es el driver de costo del proyecto."
        ),

        p("13.3 Costo mensual comparado por proveedor LLM (escenario medio)", H2),
        tabla([
            ["Modelo", "USD/mes con 24k turnos", "Vs Gemini Flash"],
            ["Gemini 2.0 Flash", "USD 3.60", "baseline"],
            ["GPT-4o-mini", "USD 7.20", "2x mas caro"],
            ["Claude Haiku 3.5", "USD 43.20", "12x mas caro"],
            ["GPT-4o", "USD 132.00", "37x mas caro"],
            ["Llama 3.1 8B local", "USD 0", "gratis, pero requiere VPS potente ~USD 40/mes"],
        ], anchos=[4.5 * cm, 5 * cm, 6.5 * cm]),

        p("13.4 Costos fijos mensuales (infra + servicios)", H2),
        tabla([
            ["Item", "Proveedor sugerido", "USD/mes"],
            ["VPS servidor", "Hetzner CX11", "4.60"],
            ["Numero WhatsApp Business", "Portacion o SIM nueva CL", "2.00"],
            ["Backups", "Backblaze B2 (~5 GB)", "0.30"],
            ["Dominio propio", "Namecheap (.cl)", "1.20 (~USD 14/ano)"],
            ["Monitoreo uptime", "UptimeRobot free", "0.00"],
            ["Monitoreo errores", "Sentry free tier", "0.00"],
            ["Email transaccional (opcional)", "Resend free 3000/mes", "0.00"],
            ["<b>SUBTOTAL infra</b>", "", "<b>8.10</b>"],
        ], anchos=[6 * cm, 6 * cm, 4 * cm]),

        p("13.5 Costos WhatsApp (Meta Cloud API)", H2),
        p("La categoria de mensaje determina el costo:"),
        tabla([
            ["Categoria", "Ejemplo", "Costo Chile"],
            ["Service (respuesta a chat del usuario dentro de 24h)", "Toda la operacion normal del bot", "GRATIS ilimitado"],
            ["Utility (proactivo con proposito claro)", "Recordatorio 24h antes de cita", "~USD 0.038"],
            ["Marketing (promocional)", "Oferta de packs", "~USD 0.058"],
            ["Authentication (OTP)", "Codigos de verificacion", "~USD 0.021"],
        ], anchos=[4.5 * cm, 6.5 * cm, 5 * cm], font_size=8),
        p("Para KitraDep en operacion normal (responder consultas), el costo "
          "WhatsApp es <b>CERO</b>. Solo empieza a costar si se activan "
          "recordatorios masivos o campanas."),

        p("13.6 Costo de setup (unico, no se repite)", H2),
        tabla([
            ["Concepto", "Costo"],
            ["Registro Meta Business", "USD 0"],
            ["Setup VPS + dominio + SSL", "USD 0 (dominio primer ano ~USD 14)"],
            ["Portacion numero (si aplica)", "USD 0-10 segun operador"],
            ["Codigo del bot (si Felipe lo hace con Kira)", "USD 0"],
            ["Codigo del bot (si contrata un dev freelance)", "USD 800-2500 estimados"],
            ["<b>SETUP TOTAL (con Kira)</b>", "<b>USD 0-25</b>"],
            ["<b>SETUP TOTAL (con freelance)</b>", "<b>USD 800-2500</b>"],
        ], anchos=[10 * cm, 6 * cm]),
        PageBreak(),

        # -------- proyecciones temporales --------
        p("13.7 Proyeccion consolidada: 1, 3, 6 y 12 meses", H1),
        hr(),

        p("Todas las cifras asumen escenario <b>MEDIO</b> (100 conversaciones/dia, "
          "sin campanas de marketing WhatsApp) y Gemini 2.0 Flash como LLM."),

        p("13.7.1 Escenario BAJO (piloto, 20 conv/dia)", H2),
        tabla([
            ["Concepto", "Mes 1", "Mes 3 (acum)", "Mes 6 (acum)", "Mes 12 (acum)"],
            ["Setup unico", "14", "14", "14", "14"],
            ["Infra fija (USD 8.10/mes)", "8.10", "24.30", "48.60", "97.20"],
            ["LLM Gemini Flash", "0 (free tier)", "0", "0", "0"],
            ["WhatsApp Service", "0", "0", "0", "0"],
            ["<b>TOTAL acumulado (USD)</b>", "<b>22.10</b>", "<b>38.30</b>", "<b>62.60</b>", "<b>111.20</b>"],
        ], anchos=[4.5 * cm, 2.9 * cm, 2.9 * cm, 2.9 * cm, 2.9 * cm], font_size=8),

        p("13.7.2 Escenario MEDIO (estable, 100 conv/dia)", H2),
        tabla([
            ["Concepto", "Mes 1", "Mes 3 (acum)", "Mes 6 (acum)", "Mes 12 (acum)"],
            ["Setup unico", "14", "14", "14", "14"],
            ["Infra fija (USD 8.10/mes)", "8.10", "24.30", "48.60", "97.20"],
            ["LLM Gemini Flash", "3.60", "10.80", "21.60", "43.20"],
            ["WhatsApp Service", "0", "0", "0", "0"],
            ["Recordatorios opcionales (50/dia)", "57 (opcional)", "171", "342", "684"],
            ["<b>TOTAL sin recordatorios (USD)</b>", "<b>25.70</b>", "<b>49.10</b>", "<b>84.20</b>", "<b>154.40</b>"],
            ["<b>TOTAL con recordatorios (USD)</b>", "<b>82.70</b>", "<b>220.10</b>", "<b>426.20</b>", "<b>838.40</b>"],
        ], anchos=[4.5 * cm, 2.9 * cm, 2.9 * cm, 2.9 * cm, 2.9 * cm], font_size=8),

        p("13.7.3 Escenario ALTO (exito, 300 conv/dia)", H2),
        tabla([
            ["Concepto", "Mes 1", "Mes 3 (acum)", "Mes 6 (acum)", "Mes 12 (acum)"],
            ["Setup unico", "14", "14", "14", "14"],
            ["Infra fija VPS mas grande (USD 12/mes)", "12", "36", "72", "144"],
            ["LLM Gemini Flash", "10.80", "32.40", "64.80", "129.60"],
            ["WhatsApp Service", "0", "0", "0", "0"],
            ["Recordatorios (150/dia)", "171", "513", "1026", "2052"],
            ["<b>TOTAL sin recordatorios (USD)</b>", "<b>36.80</b>", "<b>82.40</b>", "<b>150.80</b>", "<b>287.60</b>"],
            ["<b>TOTAL con recordatorios (USD)</b>", "<b>207.80</b>", "<b>595.40</b>", "<b>1176.80</b>", "<b>2339.60</b>"],
        ], anchos=[4.5 * cm, 2.9 * cm, 2.9 * cm, 2.9 * cm, 2.9 * cm], font_size=8),

        p("13.8 Resumen para tomar decision", H2),
        callout(
            "Para KitraDep escenario tipico (medio, sin campanas de marketing "
            "WhatsApp), el costo total del PRIMER ANO completo es de "
            "aproximadamente USD 154. Es decir, ~USD 13 por mes en promedio, "
            "todo incluido: LLM, VPS, dominio, backups. El bot literalmente "
            "cuesta menos que una suscripcion de streaming."
        ),

        p("13.9 Costos NO monetarios que hay que considerar", H2),
        bullets([
            "<b>Tiempo de Felipe:</b> ~60-80 hrs repartidas en las 6 semanas de implementacion.",
            "<b>Tiempo de KitraDep:</b> ~10-15 hrs para validar prompt, dumps de conversaciones, feedback.",
            "<b>Tramites Meta:</b> 3-14 dias de espera sin nada que hacer, solo esperar.",
            "<b>Mantenimiento post-launch:</b> ~2-4 hrs/mes revisando conversaciones y ajustando prompt.",
            "<b>Contingencia legal:</b> revisar con abogado antes de produccion en salud (~USD 100-300 pago unico).",
        ]),
        PageBreak(),
    ]


# ============================================================================
# 14. Riesgos y mitigaciones
# ============================================================================

def seccion_riesgos() -> list:
    return [
        p("14. Riesgos, mitigaciones y limites eticos", H1),
        hr(),

        p("14.1 Matriz de riesgos", H2),
        tabla([
            ["Riesgo", "Probabilidad", "Impacto", "Mitigacion"],
            ["Bot alucina precio/horario", "Media", "Alto", "Base de conocimiento + prompt estricto + tests"],
            ["Bot da diagnostico medico", "Baja", "Muy alto (legal)", "Guardrail medico + handoff obligatorio"],
            ["Costo LLM se dispara", "Baja", "Medio", "Rate limiting + circuit breaker + alertas"],
            ["VPS cae", "Media", "Medio", "Monitoreo UptimeRobot + auto-restart systemd"],
            ["Meta rechaza cuenta business", "Media", "Alto (bloquea produccion)", "Documentacion completa desde el inicio + plan B Twilio"],
            ["Numero WhatsApp baneado", "Muy baja con canal oficial", "Alto", "Usar solo Meta Cloud API o Twilio, nunca no-oficiales"],
            ["Usuario abusa del bot", "Media", "Bajo", "Rate limiting + bloqueo temporal por numero"],
            ["Fuga de datos", "Baja", "Muy alto (legal)", "HTTPS + logs enmascarados + backups cifrados"],
            ["Kira/Google discontinua Gemini", "Muy baja", "Medio", "Abstraccion LLM + facil migrar"],
            ["Equipo KitraDep no adopta el bot", "Media", "Alto (proyecto fracasa)", "Involucrarlos desde diseno + capacitacion + iterar con feedback"],
        ], anchos=[4.5 * cm, 2.2 * cm, 2.2 * cm, 7.1 * cm], font_size=8),

        p("14.2 Limites eticos que el bot NO cruza", H2),
        p("Estas son reglas duras codificadas en el prompt y verificadas por "
          "guardrails. Son <b>innegociables</b>:"),
        bullets([
            "NUNCA da un diagnostico ni sugiere una causa clinica para un dolor o sintoma.",
            "NUNCA recomienda ejercicios o tratamientos por chat.",
            "NUNCA promete resultados terapeuticos ni tiempos de recuperacion.",
            "NUNCA recomienda medicamentos, ni siquiera OTC.",
            "NUNCA dice 'no es grave' o 'no te preocupes' ante un sintoma reportado.",
            "SIEMPRE deriva a evaluacion presencial si hay una duda clinica.",
            "SIEMPRE reconoce que es un bot al inicio de la conversacion.",
        ]),

        p("14.3 Plan B: que hacer si algo falla en produccion", H2),
        numbered([
            "<b>Bot caido:</b> mensaje automatico 'Estamos con problemas tecnicos, escribinos al numero X'. Se dispara desde monitoreo.",
            "<b>Bot alucina en algo serio:</b> comando <font face='Courier'>PAUSA</font> del admin desactiva el bot y todos los mensajes se derivan a humano.",
            "<b>Costo LLM disparado:</b> circuit breaker corta automaticamente. Admin recibe alerta.",
            "<b>Meta suspende cuenta:</b> se activa fallback a Twilio (ya configurado).",
            "<b>Fuga de datos sospechada:</b> shutdown inmediato + rotacion de credenciales + notificacion legal.",
        ]),
        PageBreak(),
    ]


# ============================================================================
# 15. Checklist de arranque
# ============================================================================

def seccion_checklist() -> list:
    return [
        p("15. Checklist de arranque (que necesita Felipe)", H1),
        hr(),

        p("Todo lo que Felipe debe hacer para arrancar el proyecto, agrupado "
          "por fase. Los tiempos son estimaciones realistas."),

        p("15.1 Antes de escribir la primera linea de codigo", H2),
        p("Prep (~2 hrs, se puede hacer en un rato):"),
        bullets([
            "[ ] Confirmar con equipo KitraDep que quieren avanzar (buy-in gerencial).",
            "[ ] Definir nombre del bot y personalidad basica (30 min de conversacion interna).",
            "[ ] Recopilar 20-30 chats reales de WhatsApp (con datos borrados o anonimos).",
            "[ ] Listar los 'nunca' del bot: cosas que NO puede decir.",
            "[ ] Decidir a que numero/WhatsApp deriva cuando pide humano.",
            "[ ] Definir horarios de handoff (o si es 24/7 automatico).",
        ]),

        p("15.2 Cuentas y accesos a crear", H2),
        bullets([
            "[ ] <b>Cuenta Google AI Studio</b> para Gemini API key (5 min, gratis) - <font face='Courier'>https://aistudio.google.com/</font>",
            "[ ] <b>Cuenta Twilio</b> para Sandbox WhatsApp (15 min, gratis) - <font face='Courier'>https://www.twilio.com/</font>",
            "[ ] <b>Cuenta Meta Business</b> (30 min inicial + documentacion) - <font face='Courier'>https://business.facebook.com/</font>",
            "[ ] <b>Cuenta Hetzner o DigitalOcean</b> para VPS (15 min + tarjeta) - <font face='Courier'>https://www.hetzner.com/</font>",
            "[ ] <b>Cuenta Namecheap o similar</b> para dominio (15 min + tarjeta, ~USD 14/ano)",
            "[ ] <b>Cuenta Backblaze B2</b> para backups (15 min, gratis primeros 10 GB) - <font face='Courier'>https://www.backblaze.com/b2</font>",
            "[ ] <b>Cuenta UptimeRobot</b> para monitoreo (5 min, gratis)",
            "[ ] <b>Cuenta Sentry</b> para errores (5 min, gratis)",
            "[ ] <b>Repositorio Git privado</b> (GitHub personal, gratis)",
        ]),

        p("15.3 Documentacion a preparar", H2),
        bullets([
            "[ ] Documento de personalidad de Kitra (1 pagina, plantilla en Anexo A).",
            "[ ] Base de conocimiento inicial (Markdown, plantilla en Anexo B).",
            "[ ] Politica de privacidad publica (1 pagina web).",
            "[ ] RUT y documentos legales del centro para Meta Business.",
            "[ ] Foto de perfil del bot (logo de KitraDep, 640x640 px).",
        ]),

        p("15.4 Presupuesto a aprobar internamente", H2),
        bullets([
            "[ ] Setup unico: USD 14 (dominio primer ano)",
            "[ ] Operacion mensual estimada: USD 13-25",
            "[ ] Contingencia legal (abogado): USD 100-300 (pago unico)",
            "[ ] <b>Total primer ano estimado: USD 250-450</b>",
        ]),

        p("15.5 Personas a involucrar", H2),
        bullets([
            "<b>Felipe:</b> product owner + testing + integrador (60-80 hrs)",
            "<b>Kira (asistente IA):</b> programacion + documentacion (asincronico)",
            "<b>Equipo KitraDep:</b> validacion de tono, dumps de chats, feedback (10-15 hrs)",
            "<b>Abogado (una consulta):</b> revisar cumplimiento legal antes de produccion",
            "<b>Kine derivadora:</b> punto de handoff, monitorear notificaciones del bot",
        ]),
        PageBreak(),
    ]


# ============================================================================
# 16. Anexos
# ============================================================================

def seccion_anexos() -> list:
    return [
        p("16. Anexos", H1),
        hr(),

        p("Anexo A - Plantilla de personalidad del bot", H2),
        p("""NOMBRE: Kitra
ROL: Asistente virtual de KitraDep, centro de kinesiologia en San Miguel.
TONO: Cercano, profesional, empatico. Espanol chileno neutro.
FORMALIDAD: Usted por defecto. Tutea si el usuario tutea primero.
LONGITUD: Respuestas cortas, 2-4 lineas. Listas si es tecnico.
EMOJIS: Uso moderado, maximo 1 por mensaje.
NUNCA:
- Da diagnosticos medicos.
- Recomienda ejercicios o tratamientos.
- Promete resultados.
- Recomienda medicamentos.
SIEMPRE:
- Reconoce que es un bot al inicio.
- Deriva a evaluacion presencial ante duda clinica.
- Recuerda datos ya dados en la conversacion.
- Ofrece ayuda concreta y proactiva.
HANDOFF: Al WhatsApp de [NOMBRE_KINE_DERIVADORA] +56 9 XXXX XXXX
HORARIO HUMANO: Lu-Vi 8-21h, Sab 9-13h.
FRUERA DE HORARIO: 'Nuestro equipo humano responde en horario de atencion.
                    Te respondemos ni bien abramos manana!'
""", CODE),

        p("Anexo B - Plantilla de fragmento de base de conocimiento", H2),
        p("""# Precios KitraDep (por sesion)

## FONASA (no adherido, valor preferencial)
- 1 sesion:   CLP $20.000
- Pack 5:     CLP $100.000 (ahorro: CLP $0)
- Pack 10:    CLP $180.000 (ahorro: CLP $20.000)

**Aclaracion legal:** KitraDep no esta adherido a FONASA. Los valores anteriores
son "valor preferencial" que ofrecemos a beneficiarios FONASA.
NO se emite bono FONASA ni se descuenta cotizacion.

## ISAPRE (todas) y Particular
- 1 sesion:   CLP $25.000
- Pack 5:     CLP $115.000 (ahorro: CLP $10.000)
- Pack 10:    CLP $230.000 (ahorro: CLP $20.000)

Se entrega boleta de honorarios para reembolso en ISAPRE.

## Metodos de pago
Efectivo, transferencia, tarjeta debito y credito (POS).
""", CODE),

        p("Anexo C - Glosario tecnico", H2),
        tabla([
            ["Termino", "Definicion"],
            ["LLM", "Large Language Model. Modelo de IA que genera texto (GPT, Gemini, Claude)."],
            ["Token", "Unidad de texto ~4 caracteres. Los LLM cobran por tokens procesados."],
            ["System prompt", "Instrucciones invisibles que definen personalidad y limites del bot."],
            ["Fine-tuning", "Reentrenar los pesos del LLM. Complejo y raramente necesario."],
            ["RAG", "Retrieval-Augmented Generation. Busca fragmentos relevantes antes de generar."],
            ["Router", "Logica que decide si un mensaje va al flujo o al LLM."],
            ["Guardrail", "Regla o filtro que impide que el bot haga algo indebido."],
            ["Handoff", "Derivar la conversacion a una persona real."],
            ["Webhook", "Endpoint HTTP que recibe eventos de un servicio externo (WhatsApp)."],
            ["VPS", "Virtual Private Server. Servidor virtual barato en la nube."],
            ["Meta Cloud API", "API oficial de WhatsApp Business, provista por Meta."],
            ["Free tier", "Nivel gratuito de un servicio en la nube."],
            ["Alucinacion", "Cuando el LLM inventa informacion falsa con confianza."],
            ["Prompt engineering", "Arte de escribir instrucciones efectivas para un LLM."],
        ], anchos=[3.5 * cm, 12.5 * cm], font_size=9),

        p("Anexo D - Links utiles", H2),
        bullets([
            "Gemini API docs: <font face='Courier'>https://ai.google.dev/gemini-api/docs</font>",
            "Meta WhatsApp Cloud API: <font face='Courier'>https://developers.facebook.com/docs/whatsapp/cloud-api</font>",
            "Twilio WhatsApp Sandbox: <font face='Courier'>https://www.twilio.com/docs/whatsapp/sandbox</font>",
            "FastAPI docs: <font face='Courier'>https://fastapi.tiangolo.com/</font>",
            "Hetzner cloud: <font face='Courier'>https://www.hetzner.com/cloud</font>",
            "Ley 19.628 Chile: <font face='Courier'>https://www.bcn.cl/leychile/navegar?idNorma=141599</font>",
            "Ley 21.719 Chile (nueva 2024): <font face='Courier'>https://www.bcn.cl/leychile/navegar?idNorma=1209272</font>",
        ]),

        p("Anexo E - Contactos del proyecto", H2),
        p("""Product Owner:   Felipe Fierro (KitraDep)
Asistente IA:    Kira (via Code Puppy)
Revisor externo: [NOMBRE DE TU AMIGO]
Kine derivadora: [A COMPLETAR]
Contacto Meta:   Meta Business Help Center
Contacto legal:  [ABOGADO A DEFINIR]
""", CODE),

        spacer(0.4),
        hr(),
        p("<i>Fin del documento. Version 1.0. Preparado con dedicacion por "
          "Kira para su humano favorito, Felipe.</i>", SMALL),
    ]
