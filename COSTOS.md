# Costos de implementar un Chatbot de WhatsApp

> Desglose honesto de costos FIJOS y VARIABLES.
> IMPORTANTE: los precios exactos de Meta cambian seguido y dependen del PAIS.
> Aqui uso rangos y referencias tipicas para Chile/LatAm (USD). Siempre verifica
> el precio oficial vigente antes de decidir.

---

## Resumen en una frase

**Aprender y prototipar puede costar 0 dolares.** Recien cuando envias mensajes
proactivos (marketing/recordatorios) a muchos usuarios empiezas a pagar por mensaje.
Responder a quien TE escribe primero es, hoy, gratis o casi gratis.

---

## 1. El CANAL de WhatsApp

### Opcion A) Meta WhatsApp Cloud API (oficial, directo con Meta)

**Se paga?** La plataforma en si NO tiene mensualidad. Pagas POR CONVERSACION/MENSAJE
segun categoria. Modelo actual de Meta:

| Categoria de mensaje | Quien inicia | Costo tipico |
|---|---|---|
| **Service** (el cliente te escribe y respondes dentro de 24h) | Cliente | **GRATIS** (ilimitado) |
| **Utility** (confirmacion de cita, estado de pedido, dentro de ventana 24h) | Negocio | **Gratis** dentro de la ventana; si no, ~USD 0.01-0.03 |
| **Marketing** (promos, mensajes proactivos) | Negocio | ~USD 0.05 - 0.07 por mensaje (Chile) |
| **Authentication** (codigos OTP) | Negocio | ~USD 0.02 - 0.03 |

- **Para un bot de atencion/FAQ**: la gran mayoria de tus mensajes son "Service"
  (respondes a quien te escribe) = **GRATIS**.
- **Costos fijos**: 0 de plataforma. Pero necesitas un NUMERO de telefono (ver mas abajo).
- **Costo variable**: solo si mandas marketing/recordatorios proactivos fuera de la ventana de 24h.

> Historicamente Meta daba "1000 conversaciones de servicio gratis al mes"; luego las
> conversaciones de servicio pasaron a ser gratis SIN limite. Este es el punto que mas
> cambia, revisa: https://developers.facebook.com/docs/whatsapp/pricing

### Opcion B) Twilio (revendedor oficial)

**Se paga?** Si, siempre paga algo, pero tiene **Sandbox GRATIS** para practicar.

- **Costo variable**: precio de Meta (arriba) + **markup de Twilio ~USD 0.005 por mensaje**.
- **Numero de WhatsApp Business**: ~USD 1 - 5 al mes (fijo).
- **Sandbox**: gratis para desarrollo (con limitaciones: numero compartido, hay que
  "unirse" con un codigo). Perfecto para aprender.
- Ventaja: setup mas facil y rapido que Meta directo.
- Desventaja: pagas un pequeno extra por mensaje de por vida.

### Opcion C) whatsapp-web.js / Baileys (NO oficial)

- **Costo**: GRATIS (usa tu numero real via QR).
- **Costo real oculto**: riesgo de que Meta te **banee el numero**. No sirve para Walmart
  ni para produccion seria. Solo para un experimento de una tarde.

---

## 2. El NUMERO de telefono

- Para Cloud API / Twilio necesitas un numero dedicado (no tu personal, idealmente).
- **Twilio**: te vende uno (~USD 1 - 5/mes).
- **Meta Cloud API**: puedes registrar un numero propio; Meta da un numero de PRUEBA gratis
  para desarrollo (limitado a pocos destinatarios de prueba).
- **Costo fijo**: USD 0 (numero de prueba) a ~5/mes (numero real dedicado).

---

## 3. n8n (plataforma de flujos no-code)

**Se paga?** Depende de como lo uses:

| Modalidad | Costo |
|---|---|
| **n8n self-hosted** (lo instalas en tu servidor) | Software GRATIS (open source). Pagas solo el servidor donde corre (~USD 5-10/mes VPS). |
| **n8n Cloud - Starter** | ~USD 20-25/mes (incluye X ejecuciones/mes) |
| **n8n Cloud - planes mayores** | USD 50+/mes segun volumen |

- n8n **NO reemplaza** el costo del canal de WhatsApp; es solo el "cerebro/orquestador".
  Igual necesitas la API de Meta o Twilio por debajo (con sus costos).
- Ventaja: flujos visuales, rapido de armar.
- Desventaja: mensualidad (cloud) o mantener un servidor (self-hosted), y menos control fino
  que codigo propio.

---

## 4. HOSTING (donde corre tu bot 24/7)

Si hacemos el bot con codigo (FastAPI), necesita estar prendido para recibir mensajes:

| Opcion | Costo |
|---|---|
| **Tu PC** (solo para pruebas, con ngrok) | Gratis, pero se cae si apagas el PC |
| **VPS** (DigitalOcean, Hetzner, etc.) | ~USD 5 - 12/mes (fijo) |
| **Servicios serverless / free tier** | Gratis con limites (se "duermen") |
| **ngrok** (tunel para pruebas locales) | Plan gratis suficiente para practicar |

> Recordatorio Walmart: no se permite software de tunel en equipo corporativo.
> El tunel/ngrok se usa en tu entorno PERSONAL.

---

## 5. Extras opcionales

| Item | Costo |
|---|---|
| **Dominio propio** (ej. mibot.cl) | ~USD 10 - 15 al ano |
| **LLM (IA generativa)** si algun dia lo agregas | Por tokens; ~USD 0.15-15 por millon de tokens segun modelo. Para pocos usuarios, centavos. En Walmart: via AI Innovation Lab. |
| **Base de datos administrada** | Innecesario al inicio (SQLite gratis). |

---

## 6. Escenarios de costo total mensual

### Escenario "Aprendiendo" (lo que haremos ahora)
- Simulador local: **USD 0**
- Twilio Sandbox o numero de prueba Meta: **USD 0**
- Corriendo en tu PC con ngrok: **USD 0**
- **TOTAL: USD 0/mes** 

### Escenario "Bot real chico, solo atencion/FAQ"
- Cloud API (mensajes de servicio gratis): **USD 0** en mensajes
- Numero dedicado: ~USD 0-5/mes
- VPS para hosting: ~USD 5-12/mes
- **TOTAL: ~USD 5 - 17/mes** (casi todo es el hosting)

### Escenario "Bot con marketing proactivo"
- Todo lo anterior +
- Mensajes de marketing: ~USD 0.05-0.07 c/u -> 1000 promos/mes = ~USD 50-70
- **TOTAL: ~USD 55 - 90/mes** segun cuanto marketing envies

### Escenario "Con n8n Cloud"
- n8n Cloud Starter: ~USD 20-25/mes
- Numero + mensajes segun uso
- **TOTAL: ~USD 25 - 40/mes** base (sin hosting propio, pero atado a la mensualidad)

---

## 7. Conclusion de costos

- **Practicar y aprender = GRATIS.** No hay excusa para no empezar hoy.
- El **costo fijo** minimo real de un bot en produccion es el **hosting** (~USD 5-12/mes) y,
  si quieres, el **numero** (~USD 0-5/mes).
- El **costo variable** solo aparece con **mensajes proactivos de marketing**; responder a
  quien te escribe es gratis.
- **n8n** agrega una mensualidad (cloud) o un servidor (self-hosted), pero NO evita los
  costos del canal de WhatsApp.
- Con **codigo propio** (FastAPI) el unico costo real es el hosting; tienes control total y
  cero mensualidad de plataforma.
