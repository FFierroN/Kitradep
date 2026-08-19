# Checklist KitraDep - Estado y proximos pasos

> Ultima actualizacion: 2026-08-18 (fin de sesion)
> Repo: chatbot-kitradep (standalone) | Commits: 9940075 -> 6948646 -> fab9e86 -> 8cc80ef

---

##  YA HECHO (no tocar salvo mejoras)

### Arquitectura y motor
- [x] Backend LLM intercambiable (FakeLLM offline / GeminiLLM real) via env `LLM_BACKEND`
- [x] Router orquestador (guardrails + memoria + LLM)
- [x] Guardrails de seguridad (medico, urgencia/SAMU, PII, handoff, fuera de tema)
- [x] Memoria de conversacion (en RAM + rehidratacion desde DB)
- [x] Base de conocimiento del negocio (`knowledge/kitradep.md`)

### Personalidad (sesion de hoy)
- [x] Flujo consultivo de 5 fases (conversar antes de precios)
- [x] Propuesta de valor integrada (especializacion, 1-a-1, postop, deporte)
- [x] Bugfix: deportes ya no son "fuera de tema"

### Agendamiento (Joya 1 - sesion 2026-08-19)
- [x] Recolector DETERMINISTA de datos (`agendamiento.py`), LLM-agnostico
- [x] Deteccion de intencion de agendar (integrada en el router)
- [x] Validacion real: RUT (modulo 11), email, telefono CL, prevision, franja
- [x] Reintento ante dato invalido + cancelacion en cualquier momento
- [x] Al completar: notifica al staff + link encuadrado.com
- [x] Guardrail de urgencia aborta un agendamiento en curso (seguridad gana)
- [x] Prompt ajustado: el LLM invita, el sistema recolecta (sin pisarse)

### Infraestructura
- [x] Config centralizada (`config.py` lee `.env`)
- [x] Persistencia SQLite (`db.py`)
- [x] Rate limiting anti-abuso (`ratelimit.py`)
- [x] Notificaciones al staff via SMTP (`notificaciones.py`)
- [x] Webapp hibrida con `/health` (`webapp_hibrida.py`)
- [x] Deploy: Dockerfile + compose + DEPLOY.md + backup a B2

### Calidad
- [x] Tests: 22 conversacion + 13 infra + 44 agendamiento = 79 checks OK

---

##  PROXIMA SESION (prioridad alta)

### 1. Subir a GitHub  (bloquea el trabajo en 2 PCs)
- [ ] Felipe: crear repo privado `chatbot-kitradep` en GitHub
- [ ] Felipe: pasar la URL a Kira
- [ ] Kira: `git remote add origin <URL>` + `git push` (viajan los 4 commits)

### 2. Probar con Gemini REAL (necesita PC personal de Felipe)
- [ ] Felipe: en su PC, `uv pip install google-generativeai`
- [ ] Felipe: crear `.env` con `LLM_BACKEND=gemini` + `GEMINI_API_KEY`
- [ ] Felipe: obtener API key gratis en https://aistudio.google.com/
- [ ] Probar la conversacion real (aca se ve la magia que el FakeLLM no puede)
- [ ] Moldear tono/frases segun lo que responda Gemini de verdad

### 3. Implementar Joya 1: flujo de agendamiento con function calling
- [x] Definir las "tools" de agendamiento (recolectar nombre/RUT/correo/fono/prevision)
- [x] Switching: cuando detecta intencion de agendar -> modo recoleccion de datos
- [x] Al completar datos -> notificar al staff + link encuadrado.com
- [x] Tests del flujo de agendamiento (44 checks)
- [ ] PULIDO OPCIONAL (necesita PC personal): envolver el recolector con el
      function calling NATIVO de Gemini para captura mas flexible/natural.
      El recolector determinista ya funciona y es mas robusto (datos exactos).

---

##  DECISIONES PENDIENTES DE FELIPE

- [ ] Confirmar **tuteo vs usted** (hoy quedo en tuteo)
- [ ] Confirmar **emojis** si/no y cuantos (hoy: max 1 por mensaje)
- [ ] Confirmar **contacto de handoff** (a quien/que numero deriva)
- [ ] Verificar que **precios y datos** en `knowledge/kitradep.md` esten vigentes
- [ ] Revisar/afinar el **tono y las frases** de Kitra tras ver Gemini real

---

##  BACKLOG (mas adelante, no urgente)

### Fase 4: WhatsApp real (usar Joya 2)
- [ ] Felipe: verificar cuenta Meta Business
- [ ] Felipe: numero dedicado para el bot
- [ ] Kira: modulo `whatsapp_webhook.py` (adaptar starter MIT: webhook + firma HMAC)
- [ ] Conectar webhook -> router existente
- [ ] Probar en Meta Sandbox antes de produccion
- [ ] Mensajes template para recordatorios

### Despliegue produccion
- [ ] Contratar VPS (Hetzner / Vultr Santiago)
- [ ] Dominio + apuntar DNS
- [ ] `docker compose up -d` + Caddy (SSL automatico)
- [ ] UptimeRobot monitoreando `/health`
- [ ] Cron de backups a Backblaze B2
- [ ] Configurar SMTP para notificaciones reales al staff

### Mejoras opcionales (nice to have)
- [ ] Trim de contexto por tokens (mejora sobre recorte por turnos - idea del appointment-agent)
- [ ] Inyectar fecha/hora actual en el prompt (manejar "manana", "el viernes")
- [ ] Panel simple para que el staff vea conversaciones/metricas
- [ ] Investigar (opcional): ejemplos de prompts de bots de atencion en espanol

---

##  Notas importantes para recordar

- **Firewall Walmart**: la API de Gemini esta BLOQUEADA en la maquina de trabajo.
  Kira programa con FakeLLM; Felipe prueba Gemini real en su PC personal.
- **FakeLLM es limitado**: respuestas fijas por keyword, no encadena contexto.
  La conversacion inteligente real solo se ve con Gemini.
- **Guardrails son sagrados**: nunca romperlos para persuadir (no diagnosticar,
  no prometer resultados, urgencia -> SAMU 131).
- **2 joyas rescatadas** de repos: (1) function calling Gemini para agendar,
  (2) webhook Meta + firma HMAC (starter MIT) para WhatsApp.
