# Plan de accion - De pruebas a lanzamiento en WhatsApp real

> Objetivo: llevar a Kitra desde el estado actual (cerebro completo y testeado,
> probado en simulador web) hasta atender clientes reales por la app de WhatsApp,
> con un lanzamiento oficial controlado.
>
> Ultima actualizacion: 2026-08-24

---

## Punto de partida (lo que YA esta listo)

- Cerebro completo: router + guardrails + agendamiento determinista + memoria
- LLM real (Gemini) funcionando en PC personal de Felipe
- Infraestructura: config, SQLite, rate limit, notificaciones, /health
- Deploy preparado: Dockerfile + docker-compose + Caddy/SSL + backups
- Calidad: 79/79 tests OK
- Repo en GitHub (FFierroN/Kitradep), sincronizado

## Lo que FALTA para WhatsApp real

1. El "puente" con WhatsApp (modulo webhook) -> **codigo (Kira)**
2. La cuenta y numero de Meta -> **tramite (Felipe)**
3. Un servidor 24/7 donde vivir -> **VPS (los dos)**
4. Pruebas desde telefonos reales -> **los dos**
5. Verificacion Meta + numero real -> **tramite (Felipe)**
6. Lanzamiento oficial -> **los dos**

---

## FASE A - Preparacion de la cuenta Meta (Felipe)

**Meta:** tener la plataforma de WhatsApp lista y un numero de PRUEBA gratis.

| # | Tarea | Responsable | Listo cuando... |
|---|-------|-------------|-----------------|
| A1 | Confirmar quien controla el login del Instagram de KitraDep | Felipe | Se sabe si es cuenta propia o de agencia |
| A2 | Instagram en modo profesional/empresa | Felipe | IG es "cuenta de empresa" |
| A3 | Crear/acceder a Meta Business (business.facebook.com) | Felipe | Existe el Business "KitraDep" |
| A4 | Conectar Instagram (+ pagina de Facebook) al Business | Felipe | IG y pagina aparecen en el Business |
| A5 | Activar WhatsApp Business Platform + app developer | Felipe (Kira guia) | App creada en developers.facebook.com |
| A6 | Obtener numero de PRUEBA gratis + token temporal | Felipe | Meta entrega numero de prueba |
| A7 | Agregar hasta 5 telefonos como testers | Felipe | Numeros de Felipe/equipo cargados |

**Costo:** USD 0. **No requiere verificacion de negocio todavia.**

---

## FASE B - Construir el puente WhatsApp (Kira, offline)

**Meta:** que un mensaje de WhatsApp llegue al cerebro de Kitra y vuelva la respuesta.

| # | Tarea | Responsable | Listo cuando... |
|---|-------|-------------|-----------------|
| B1 | `whatsapp_webhook.py`: verificacion GET (challenge de Meta) | Kira | Endpoint responde el challenge |
| B2 | Recepcion POST de mensajes entrantes + parseo | Kira | Extrae texto + numero del remitente |
| B3 | Validacion de firma HMAC (seguridad) | Kira | Rechaza requests no firmados por Meta |
| B4 | Envio de respuestas via Cloud API (mensajes salientes) | Kira | Kitra contesta por WhatsApp |
| B5 | Enganche al `router.py` existente (reusar cerebro) | Kira | Guardrails + agenda + Gemini funcionan igual |
| B6 | Manejo de sesion por numero de telefono (usa `db.py`) | Kira | Cada cliente tiene su memoria |
| B7 | Tests offline del webhook (firma, parseo, ruteo) | Kira | Suite nueva en verde |

**Nota:** todo esto lo puedo hacer desde la maquina Walmart con FakeLLM. No
depende de tener Meta listo todavia.

---

## FASE C - Desplegar a un servidor 24/7 (los dos)

**Meta:** Kitra prendida siempre, con URL publica HTTPS para el webhook de Meta.

| # | Tarea | Responsable | Listo cuando... |
|---|-------|-------------|-----------------|
| C1 | Contratar VPS (Hetzner CAX11 ~USD 5/mes) | Felipe | Acceso SSH al servidor |
| C2 | Dominio o subdominio (ej. bot.kitradep.cl) apuntando al VPS | Felipe | Registro A configurado |
| C3 | Instalar Docker + clonar repo + `.env` (Gemini + tokens Meta) | Kira guia | `docker compose up -d` corriendo |
| C4 | Caddy con SSL automatico | Kira guia | `https://bot.kitradep.cl/health` responde ok |
| C5 | Registrar la URL del webhook en Meta + suscribir eventos | Felipe (Kira guia) | Meta marca el webhook como verificado |

**Costo:** ~USD 5/mes VPS + ~USD 10-15/ano dominio (opcional).

---

## FASE D - Pruebas en WhatsApp real (numero de prueba)

**Meta:** validar el bot desde telefonos reales antes de gastar en verificacion.

| # | Tarea | Responsable | Listo cuando... |
|---|-------|-------------|-----------------|
| D1 | Escribir a Kitra desde el celular (Felipe) | Felipe | Kitra responde por WhatsApp |
| D2 | Probar flujo FAQ (horarios, direccion, precios FONASA/ISAPRE) | Felipe + equipo | Respuestas correctas |
| D3 | Probar flujo de agendamiento completo (datos + resumen staff) | Felipe + equipo | Llega la notificacion al staff |
| D4 | Probar guardrails (urgencia -> SAMU, no diagnostico, handoff) | Felipe + equipo | Se comporta seguro en todos los casos |
| D5 | Ajustar tono/frases de Kitra segun lo visto | Kira | Felipe aprueba el tono |
| D6 | Probar limites (rate limit, mensajes raros, emojis) | Felipe + equipo | No se cae ni se rompe |

**Criterio de salida:** Felipe dice "asi la mostraria a un cliente".

---

## FASE E - Verificacion Meta + numero real (Felipe)

**Meta:** pasar del numero de prueba a un numero real de produccion.

| # | Tarea | Responsable | Listo cuando... |
|---|-------|-------------|-----------------|
| E1 | Verificacion del negocio con Meta (documentos empresa) | Felipe | Business verificado |
| E2 | Numero dedicado real para el bot (no personal) | Felipe | Numero registrado en WhatsApp Manager |
| E3 | Aprobar el "display name" (nombre visible del bot) | Felipe | Meta aprueba el nombre |
| E4 | (Opcional) Plantillas de mensaje para recordatorios | Kira + Felipe | Templates aprobados por Meta |
| E5 | Cambiar tokens de prueba por los de produccion en `.env` | Kira guia | Bot corre con numero real |

**Costo:** numero dedicado ~USD 0-5/mes. Verificacion gratis (toma dias por Meta).

---

## FASE F - Soft launch / piloto (los dos)

**Meta:** primeros clientes reales, en un canal controlado, monitoreando de cerca.

| # | Tarea | Responsable | Listo cuando... |
|---|-------|-------------|-----------------|
| F1 | Publicar el numero en un canal acotado (bio IG, un grupo) | Felipe | Clientes empiezan a escribir |
| F2 | Monitoreo activo: UptimeRobot en /health + revisar logs | Kira guia | Alertas configuradas |
| F3 | Backups automaticos (cron a Backblaze B2) | Kira guia | Backup diario andando |
| F4 | Revisar conversaciones reales + detectar fallas de tono/flujo | Felipe + Kira | Lista de ajustes |
| F5 | Iterar (2-3 rondas de ajuste sobre datos reales) | Kira | Metricas estables |

**Criterio de salida:** una semana sin incidentes + tono aprobado en real.

---

## FASE G - Lanzamiento oficial (los dos)

**Meta:** abrir el bot a todos los clientes.

| # | Tarea | Responsable | Listo cuando... |
|---|-------|-------------|-----------------|
| G1 | Publicar el WhatsApp en todos los canales (IG, web, Google, tarjetas) | Felipe | Difundido |
| G2 | Boton "click to WhatsApp" en Instagram/web (opcional) | Felipe | Link directo activo |
| G3 | Monitoreo continuo + plan de mantenimiento | Kira guia | Rutina definida |
| G4 | Migrar `google-generativeai` -> `google-genai` (SDK vigente) | Kira | Sin paquete deprecado |
| G5 | Revision mensual de costos + volumen de mensajes | Felipe | Presupuesto bajo control |

---

## Orden recomendado (para no perder tiempo)

```
En PARALELO desde ya:
  - Felipe arranca FASE A (tramite Meta)
  - Kira construye FASE B (webhook, offline)

Cuando A y B esten listas:
  - FASE C (desplegar) -> FASE D (probar en WhatsApp de prueba)

Solo si D convence:
  - FASE E (verificacion + numero real)
  - FASE F (soft launch) -> FASE G (oficial)
```

## Resumen de costos hasta produccion

| Item | Costo |
|------|-------|
| Cuenta Meta + numero de prueba | USD 0 |
| VPS (hosting 24/7) | ~USD 5/mes |
| Dominio (opcional) | ~USD 10-15/ano |
| Numero dedicado real | ~USD 0-5/mes |
| Mensajes de servicio (responder al cliente) | GRATIS |
| Mensajes de marketing (recordatorios masivos) | ~USD 0.05-0.07 c/u (solo si se usan) |

**Costo fijo realista en produccion: ~USD 5-10/mes.**
