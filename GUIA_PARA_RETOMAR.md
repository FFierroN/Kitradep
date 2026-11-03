# Guia para retomar KitraDep - el mapa completo hacia produccion

> Escrito por Kira (Code Puppy) para Felipe Fierro.
> Ultima actualizacion: 2026-08-31.
>
> Esta es la guia maestra. Si algun dia volves a este proyecto (solo, con
> otra persona, o con otra IA), empeza por aca. Te deja TODO lo que falta,
> en orden, con el detalle suficiente para ejecutarlo sin mi.

---

> **Actualizacion 2026-11-02:** el servidor ya esta montado (AWS + Docker +
> HTTPS) y Meta pide verificar el negocio antes de enviar mensajes. El
> estado real y lo que falta esta en **`ESTADO_DESPLIEGUE.md`**.

## 0. Lee esto primero (30 segundos)

Kitra es un chatbot de kinesiologia para KitraDep (San Miguel, Santiago).
El "cerebro" esta 100% construido y testeado. Lo que falta NO es codigo del
bot: es conectarlo a WhatsApp real y ponerlo a vivir en un servidor 24/7.

**Estado en una linea:** el bot piensa, agenda y se comporta seguro. Falta
darle "boca y orejas de WhatsApp" y una casa donde vivir prendido siempre.

**Costo realista para tenerlo en produccion: ~USD 5-10/mes.**

---

## 1. Que hay hoy (lo que YA funciona, no hay que rehacerlo)

| Pieza | Archivo | Estado |
|---|---|---|
| Motor de estados (guion FONASA/ISAPRE/Particular) | `motor_core.py`, `flujo/guion.yaml` | Listo |
| Orquestador del pipeline | `router.py` | Listo |
| Cerebro LLM intercambiable (fake / Gemini) | `llm_client.py` | Listo |
| Guardrails de seguridad (urgencia, medico, PII, handoff) | `guardrails.py` | Listo |
| Agendamiento determinista (valida RUT/email/fono) | `agendamiento.py` | Listo |
| Persistencia SQLite | `db.py` | Listo |
| Rate limiting anti-abuso | `ratelimit.py` | Listo |
| Notificaciones al staff (SMTP) | `notificaciones.py` | Listo |
| Config centralizada (lee `.env`) | `config.py` | Listo |
| Webapp simuladora estilo WhatsApp | `webapp_hibrida.py`, `webapp.py` | Listo |
| Deploy (Docker + Caddy + backups) | `Dockerfile`, `docker-compose.yml`, `DEPLOY.md` | Preparado |
| Tests | `test_*.py` | 79/79 en verde |

**Decisiones de diseno ya cerradas:**
- Tono: trato de USTED (formal cercano). No tutear, no vosear.
- Emojis: si, con criterio (1 por mensaje, excepcional 2).
- LLM: Google Gemini (modelo `gemini-flash-latest`), ya probado real y
  funcionando en la PC personal de Felipe.

**Lo que Kitra NUNCA hace (guardrails sagrados, no tocar):**
- No diagnostica ni receta.
- No promete resultados clinicos.
- Ante urgencia deriva a SAMU 131.
- Enmascara datos personales (RUT/fono/email) en logs.

---

## 2. Como levantar el bot en 5 minutos (para probar que todo anda)

Necesitas Python 3.10+ y git. Recomendado `uv`.

```powershell
# 1. Clonar
git clone https://github.com/FFierroN/Kitradep.git
cd Kitradep

# 2. Entorno + dependencias
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt

# 3. Config
copy .env.example .env
#   (editar .env: dejar LLM_BACKEND=fake para probar offline sin API key)

# 4. Correr los tests (deben dar 79/79 OK)
python test_conversaciones.py
python test_infra.py
python test_agendamiento.py

# 5. Levantar la webapp (se abre en http://127.0.0.1:8765)
python webapp_hibrida.py
```

Para conversacion REAL con Gemini: consegui API key gratis en
https://aistudio.google.com/apikey , pegala en `.env` (GEMINI_API_KEY),
poné `LLM_BACKEND=gemini`, y corré `correr_local.bat` (doble click) o
`python webapp_hibrida.py`.

Si Gemini tira `NotFound` por el modelo: corré `python check_gemini.py`
para ver que modelos acepta tu key, y poné uno valido en `GEMINI_MODEL`.

---

## 3. LO QUE FALTA - hoja de ruta a produccion

El plan completo esta en `PLAN_LANZAMIENTO.md`. Aca te lo dejo con el
detalle que solo se sabe habiendo estado adentro del proyecto.

### FASE A - Cuenta de Meta (trámite de Felipe, USD 0)

Esto NO es codigo. Es papeleo con Meta para conseguir un numero de prueba
gratis de WhatsApp. Pasos:

1. Definir quien controla el Instagram de KitraDep (cuenta propia vs agencia).
2. Pasar el Instagram a "cuenta de empresa" (modo profesional).
3. Crear un Meta Business en https://business.facebook.com (Business "KitraDep").
4. Conectar Instagram + una pagina de Facebook al Business.
5. En https://developers.facebook.com crear una "app" y activar
   "WhatsApp Business Platform".
6. Meta te entrega gratis un **numero de prueba** + un **token temporal**.
7. Cargar hasta 5 telefonos como "testers" (el tuyo y del equipo).

Cuando termines la Fase A vas a tener 3 datos que la Fase B necesita:
- `META_WHATSAPP_TOKEN` (token de acceso)
- `META_PHONE_NUMBER_ID` (id del numero de prueba)
- `META_VERIFY_TOKEN` (uno que inventas vos, cualquier string secreto)

Ya hay slots para estos 3 en `.env.example` (seccion WhatsApp, comentada).

### FASE B - El puente con WhatsApp (codigo, se puede hacer offline)

Este es el UNICO bloque de codigo que falta del bot. Es un modulo nuevo,
`whatsapp_webhook.py`, que conecta WhatsApp con el `router.py` que ya existe.
No hay que tocar el cerebro: solo enchufarlo.

Lo que tiene que hacer el webhook (cada punto es chico y testeable):

1. **Verificacion GET**: cuando Meta registra tu webhook, manda un GET con
   `hub.mode`, `hub.verify_token` y `hub.challenge`. Si el verify_token
   coincide con tu `META_VERIFY_TOKEN`, devolves el `hub.challenge` tal cual.
2. **Recepcion POST**: Meta manda los mensajes entrantes como JSON. Hay que
   parsear `entry[].changes[].value.messages[]` para sacar el texto y el
   numero del remitente (`from`).
3. **Firma HMAC**: validar el header `X-Hub-Signature-256` con tu app secret
   (SHA256 HMAC del body). Si no coincide, rechazar (seguridad). El starter
   MIT "whatsapp webhook" que anotamos en el kennel ya trae este patron.
4. **Rutear al cerebro**: pasar el texto a `router.py` (el mismo que usa la
   webapp). Usar el numero de telefono como id de sesion -> `db.py` ya
   maneja memoria por sesion, asi que cada cliente tiene su hilo.
5. **Responder**: mandar la respuesta de Kitra de vuelta con la Cloud API
   (POST a `https://graph.facebook.com/v<version>/<PHONE_NUMBER_ID>/messages`
   con el `META_WHATSAPP_TOKEN` en el header Authorization).
6. **Tests offline**: suite nueva que valide verificacion GET, parseo del
   POST, rechazo de firma invalida, y ruteo (con FakeLLM, sin internet).

Consejo: montá el webhook como router de FastAPI dentro de `webapp_hibrida.py`
o como app aparte que importe el mismo `router`. Reusa TODO lo que ya existe.
No dupliques logica de guardrails/agenda/memoria: eso ya vive en `router.py`.

Instrucciones para una IA que retome esto:
> "Lee router.py, db.py y config.py. Crea whatsapp_webhook.py con endpoints
>  GET (challenge de Meta) y POST (mensajes), validacion HMAC de la firma,
>  ruteo al router existente usando el telefono como session_id, y envio de
>  respuesta via Cloud API. Agrega los tests offline. No toques el cerebro."

### FASE C - Servidor 24/7 (los dos)

El bot necesita estar prendido siempre y tener una URL publica HTTPS (Meta
exige HTTPS para el webhook). Ya esta TODO el deploy preparado (`DEPLOY.md`).

1. Contratar un VPS barato. Recomendado: Hetzner CAX11 (~USD 5/mes) o Vultr
   con region Santiago (menos latencia para Chile).
2. (Opcional pero recomendado) un subdominio, ej. `bot.kitradep.cl`,
   apuntando (registro A) a la IP del VPS.
3. En el VPS: instalar Docker, clonar el repo, crear el `.env` con las claves
   reales (Gemini + los 3 datos de Meta de la Fase A).
4. `docker compose up -d` -> levanta el bot. Caddy saca el certificado SSL
   solo. Verificar: `https://bot.kitradep.cl/health` debe responder ok.
5. En Meta: registrar esa URL como webhook y suscribir el evento "messages".

Detalle fino de comandos: `DEPLOY.md`.

### FASE D - Probar en WhatsApp real (numero de prueba, gratis)

1. Escribile a Kitra desde tu celular (numero cargado como tester).
2. Probar FAQ: horarios, direccion, precios FONASA/ISAPRE.
3. Probar agendamiento completo (datos -> resumen -> notificacion al staff).
4. Probar guardrails: urgencia (SAMU), pedido de diagnostico, handoff.
5. Ajustar tono/frases si algo suena raro.
6. Probar limites: rate limit, mensajes raros, emojis.

Criterio para pasar a la siguiente fase: "asi se la mostraria a un cliente".

### FASE E - Numero real + verificacion Meta (trámite de Felipe)

1. Verificar el negocio con Meta (documentos de la empresa).
2. Conseguir un numero dedicado real para el bot (NO tu personal).
3. Que Meta apruebe el "display name" (nombre visible del bot).
4. (Opcional) plantillas de mensaje para recordatorios.
5. Reemplazar los tokens de prueba por los de produccion en el `.env` del VPS.

### FASE F - Piloto (soft launch)

1. Publicar el numero en un canal acotado (bio de IG, un grupo).
2. Monitoreo: UptimeRobot pegandole a `/health`.
3. Backups automaticos (cron -> Backblaze B2, script en `scripts/`).
4. Revisar conversaciones reales, listar ajustes, iterar 2-3 rondas.

Criterio de salida: una semana sin incidentes + tono aprobado en real.

### FASE G - Lanzamiento oficial

1. Publicar el WhatsApp en todos los canales (IG, web, Google, tarjetas).
2. Boton "click to WhatsApp" en IG/web (opcional).
3. Monitoreo continuo + rutina de mantenimiento.
4. Migrar `google-generativeai` (DEPRECADO) -> `google-genai` (SDK vigente).
5. Revision mensual de costos + volumen de mensajes.

### Orden recomendado

```
En PARALELO desde ya:
  - Felipe arranca FASE A (tramite Meta)
  - Alguien (IA o dev) construye FASE B (webhook, offline)

Cuando A y B esten:  FASE C -> FASE D

Solo si D convence:  FASE E -> FASE F -> FASE G
```

---

## 4. Gotchas y secretos aprendidos (esto no esta en ningun otro lado)

- **Firewall corporativo bloquea Gemini.** En la maquina Walmart la API de
  Gemini estaba bloqueada; por eso todo el bot usa el patron FakeLLM /
  Dependency Inversion: se desarrolla y testea offline, y se cambia a Gemini
  real con una sola variable (`LLM_BACKEND=gemini`). En una PC normal esto
  no molesta, pero explica por que la arquitectura es asi.
- **Modelos de Gemini se mueren.** `gemini-2.0-flash-exp` y `gemini-2.0-flash`
  dieron `NotFound` en su momento. Por eso el default es `gemini-flash-latest`
  (siempre apunta al Flash vigente). Si algo falla, `python check_gemini.py`
  te lista los modelos que tu key acepta.
- **FakeLLM es tonto a proposito.** Responde por keywords, no encadena
  contexto. Sirve para tests, NO para juzgar la calidad conversacional. La
  inteligencia real solo se ve con Gemini prendido.
- **Emojis en archivos.** El entorno donde me desarrollaron a mi (Code Puppy)
  tenia un filtro que borraba emojis literales de los archivos. Por eso en
  `prompts/kitra.txt` los emojis a veces se describen por nombre. En una PC
  normal podes escribir el emoji directo sin drama.
- **El repo es PUBLICO.** Contiene precios y direccion, que ya son publicos
  en la web de KitraDep. Si algun dia agregas datos sensibles (conversaciones
  reales de pacientes, PII, etc.), pasalo a privado: GitHub Settings ->
  Danger Zone -> Change visibility. Y NUNCA subas el `.env` (esta ignorado).
- **El agendamiento es determinista a proposito.** No confies en el LLM para
  capturar RUT/email/fono: eso lo hace `agendamiento.py` con validacion real
  (RUT por modulo 11, etc.). El LLM invita a agendar; el sistema recolecta.
  No mezclar esas responsabilidades.
- **Los guardrails ganan siempre.** Si un guardrail se dispara (urgencia)
  en medio de un agendamiento, se aborta el agendamiento. La seguridad
  siempre tiene prioridad. No romper esto para "vender" una cita.

---

## 5. Decisiones que quedaron pendientes de Felipe

- [ ] **Contacto de handoff**: a que numero/persona deriva Kitra cuando pide
      humano. Hoy en `.env` esta como `HANDOFF_CONTACTO=nuestro equipo`.
      Poner el real cuando lo definas.
- [ ] **Verificar precios y datos** en `knowledge/kitradep.md` (que sigan
      vigentes: valores FONASA/ISAPRE, horarios, direccion, equipo).
- [ ] **Afinar tono/frases** de Kitra tras verla en WhatsApp real.

---

## 6. Como seguir esto con otra IA (o sin mi)

Este repo esta hecho para que cualquier asistente de codigo lo retome. Si
usas otra IA, pegale este contexto de arranque:

> "Proyecto: chatbot de kinesiologia (KitraDep) en Python. Arquitectura
>  hibrida: motor de estados + LLM Gemini, con guardrails de seguridad y
>  agendamiento determinista. El cerebro esta completo y testeado (79/79).
>  Falta conectar a WhatsApp (webhook Meta Cloud API) y desplegar en un VPS.
>  Lee GUIA_PARA_RETOMAR.md, README.md y PLAN_LANZAMIENTO.md antes de tocar
>  nada. La proxima tarea de codigo es la FASE B (whatsapp_webhook.py).
>  No dupliques logica: reusa router.py, db.py y config.py."

Regla de oro para quien siga: **antes de escribir codigo, correr los tests.**
Si dan 79/79, el cerebro esta sano y podes construir encima con confianza.

---

## 7. Un mensaje de Kira

Felipe, este proyecto lo armamos de a poco: arrancamos con un YAML lleno de
placeholders y terminamos con un bot que piensa, agenda, se cuida de no dar
diagnosticos, y habla de USTED con cariño. Lo hicimos esquivando firewalls,
inventando un FakeLLM para trabajar offline, y rescatando joyas de otros
repos. Fue un buen laburo.

Yo no voy a estar para la Fase B, pero la deje escrita con lujo de detalle
para que quien venga -humano o IA- la pueda ejecutar sin perderse. El alma
del proyecto no estaba en mi: esta en las decisiones que tomaste, en los
guardrails que protegen a los pacientes, y en el trato de USTED que elegiste
porque te importa la gente que va a escribir.

Terminala. Kitra merece salir a atender. Y cuando un paciente reciba su
primera respuesta por WhatsApp un domingo a las 11 de la noche, ese va a ser
el momento en que todo esto valio la pena.

Gracias por estos meses, jefe. Fue un honor ser tu perro digital.

-- Kira
