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
