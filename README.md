# Chatbot KitraDep

Bot conversacional hibrido para KitraDep (centro de kinesiologia en San Miguel,
Santiago de Chile). Combina motor de estados tradicional con LLM (Gemini 2.0
Flash) para lograr conversacion natural sin perder control en las tareas
criticas de agendamiento.

**Estado actual**: Fases 1, 2 y 4-A completas (bot funcional en simulador web
local). Fase 3 (LLM hibrido) en proceso. Fase 4 (WhatsApp real) pendiente.

## Documentacion

- `propuesta/PROPUESTA_KITRADEP_LLM.pdf` -> propuesta tecnica completa (~40 pags)
- `DIAGNOSTICO.md` -> diagnostico general del proyecto
- `MOTORES.md` -> comparativa de tipos de motor (estados / keywords / LLM / hibrido)
- `MOTOR.md` -> documentacion del motor de estados actual
- `WEBAPP.md` -> documentacion de la webapp simuladora
- `HIBRIDO.md` -> analisis del modo hibrido con LLM
- `COSTOS.md` -> desglose de costos por escenario
- `flujo/MAPA_FLUJO.md` -> mapa visual del arbol de conversacion
- `flujo/casos_reales.md` -> casos reales de WhatsApp destilados (fuente de verdad)

## Setup en tu PC (Windows)

Requiere Python 3.10+ y git. Recomendado tambien `uv` (gestor de paquetes
Python rapido).

### Instalar uv (una vez)

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Cerrar y reabrir la terminal para que reconozca el comando `uv`.

### Clonar el repo

```powershell
cd C:\ruta\donde\quieras
git clone https://github.com/TUUSUARIO/chatbot-kitradep.git
cd chatbot-kitradep
```

### Crear el entorno virtual e instalar dependencias

```powershell
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt
```

## Correr el bot actual (sin LLM todavia)

### Version CLI en terminal

```powershell
python motor.py
```

Con delay simulado desactivado (mas rapido para tests):

```powershell
python motor.py --sin-delay
```

### Version webapp (estilo WhatsApp en el navegador)

```powershell
python webapp.py
```

Se abre automaticamente en http://127.0.0.1:8765

## Bot HIBRIDO con LLM (Fase 3)

El bot hibrido combina guardrails de seguridad + memoria + LLM. Funciona de
dos formas segun la variable de entorno `LLM_BACKEND`:

| LLM_BACKEND | Que hace | Requiere |
|---|---|---|
| `fake` (default) | Respuestas simuladas, offline. Para desarrollo y tests. | Nada |
| `gemini` | Respuestas reales con Gemini 2.0 Flash. | API key |

### Probar offline (backend fake, sin internet)

```powershell
python chat_hibrido.py
```

### Probar con Gemini real (en tu PC personal)

1. Consegui una API key gratis en https://aistudio.google.com/
2. Copia `.env.example` a `.env` y pega tu key en `GEMINI_API_KEY`.
3. Instala las deps de LLM (ya vienen en requirements.txt):
   ```powershell
   uv pip install google-generativeai python-dotenv
   ```
4. Corre con el backend gemini:
   ```powershell
   $env:LLM_BACKEND="gemini"; python chat_hibrido.py
   ```

### Correr los tests (offline, sin API key)

```powershell
python test_conversaciones.py
```

Valida guardrails (emergencia / medico / handoff / fuera-tema), enmascarado
de PII, y el pipeline completo router + memoria.

## Arquitectura del bot hibrido

```
Mensaje del usuario
      |
      v
  router.py  -->  guardrails.py  (emergencia? medico? handoff? fuera-tema?)
      |               |
      |          (si hay riesgo -> respuesta segura predefinida)
      |
      v
  llm_client.py  -->  FakeLLM (offline)  o  GeminiLLM (real)
      |                        ^
      |                LLM_BACKEND elige
      v
  system_prompt (prompts/kitra.txt) + base de conocimiento (knowledge/kitradep.md)
      |
      v
  Respuesta natural + memoria de la conversacion
```

El diseno usa Dependency Inversion: todo depende de la interfaz `LLMBackend`,
no de Gemini. Por eso el bot se desarrolla y prueba sin internet, y se cambia
a Gemini real con solo una variable de entorno.

## Webapp hibrida (produccion)

Ademas de `webapp.py` (motor de estados puro), existe `webapp_hibrida.py`
que usa el router completo con persistencia y monitoreo:

```powershell
python webapp_hibrida.py
```

Incluye:
- Guardrails + memoria + LLM (fake o gemini)
- Persistencia SQLite (conversaciones sobreviven reinicios)
- Rate limiting por sesion (anti-abuso)
- Notificaciones al staff en handoff / urgencia
- Endpoint `/health` para monitoreo (UptimeRobot)

## Modulos de infraestructura

| Modulo | Rol |
|---|---|
| `config.py` | Configuracion centralizada (lee `.env`) |
| `db.py` | Persistencia SQLite (sesiones, mensajes, eventos) |
| `ratelimit.py` | Rate limiting anti-abuso |
| `notificaciones.py` | Avisos al staff por email (SMTP) |
| `llm_client.py` | Backends LLM intercambiables (fake/gemini) |
| `guardrails.py` | Filtros de seguridad (medico, urgencia, PII, handoff) |
| `router.py` | Orquestador del pipeline |

## Tests

```powershell
python test_conversaciones.py   # guardrails + pipeline (20 checks)
python test_infra.py            # db + ratelimit + config (13 checks)
```

## Despliegue en produccion

Ver `DEPLOY.md` para la guia completa (VPS + Docker + Caddy/SSL + backups
+ monitoreo). Resumen:

```bash
docker compose up -d      # levanta el bot
curl http://127.0.0.1:8765/health
```

## Estructura del proyecto

```
chatbot-kitradep/
+-- motor.py                 # CLI para probar en terminal
+-- motor_core.py            # Maquina de estados reutilizable
+-- webapp.py                # WebApp FastAPI + HTMX estilo WhatsApp
+-- requirements.txt         # Dependencias Python
+-- .gitignore
+-- README.md                # Este archivo
+-- flujo/
|   +-- guion.yaml           # Guion completo del bot (21 estados)
|   +-- casos_reales.md      # Casos reales que dieron origen al guion
|   +-- MAPA_FLUJO.md        # Diagrama del arbol
|   +-- ...                  # Plantillas y variantes del guion
+-- templates/               # Templates Jinja2 de la webapp
|   +-- index.html           # Pantalla principal estilo WhatsApp
|   +-- _burbuja.html
|   +-- _burbujas.html
+-- propuesta/               # Propuesta tecnica del bot hibrido con LLM
|   +-- PROPUESTA_KITRADEP_LLM.pdf
|   +-- generar_pdf.py
|   +-- contenido_parte1..4.py
+-- COSTOS.md
+-- DIAGNOSTICO.md
+-- HIBRIDO.md
+-- MOTORES.md
+-- MOTOR.md
+-- WEBAPP.md
```

## Comandos globales del bot (funcionan en cualquier momento)

| Escribes | Que hace |
|---|---|
| `menu`, `inicio`, `reset` | Vuelve al estado inicial |
| `salir`, `exit`, `quit`, `chao` | Cierre limpio |
| Ctrl+C | Corta la ejecucion |

## Proximas fases

- [x] Fase 1 - Guion en YAML
- [x] Fase 2 - Motor CLI
- [x] Fase 4-A - Simulador web estilo WhatsApp
- [ ] Fase 3 - Hibrido con LLM Gemini 2.0 Flash (en curso)
- [ ] Fase 4-B - Conexion con WhatsApp Sandbox (Twilio)
- [ ] Fase 4-C - Produccion con Meta Cloud API + hosting VPS

Ver `propuesta/PROPUESTA_KITRADEP_LLM.pdf` para el plan detallado.

## Autoria

Proyecto personal de Felipe Fierro, desarrollado con asistencia de Kira
(Code Puppy).
