#  Proyecto Chatbot de WhatsApp — Diagnóstico General

> Proyecto personal de Felipe Fierro. Objetivo a futuro: llevarlo (con adaptaciones) a Walmart.
> Objetivo inmediato: **aprender** a construir un chatbot de WhatsApp con un flujo de
> conversación que se sienta humano, con respuestas prediseñadas, que responda de forma automática.

---

## 1. ¿Qué es realmente un "chatbot de WhatsApp"?

Son 3 piezas que hay que enchufar:

```
   [ WhatsApp ]  <--->  [ Canal / API ]  <--->  [ Tu lógica de conversación ]
   (el usuario)         (el "cartero")          (el "cerebro" que decide qué responder)
```

1. **El canal / API**: cómo tu programa envía y recibe mensajes de WhatsApp.
2. **El motor de conversación (flujo)**: la máquina de estados / árbol de decisión que
   decide qué contestar según lo que escribió el usuario y en qué punto de la charla va.
3. **Las respuestas prediseñadas**: los textos, botones y menús que devuelves.

La parte 2 y 3 son las que TÚ diseñas (y las divertidas). La parte 1 es la que hay que elegir bien.

---

## 2. Opciones para el CANAL (aquí está el 80% de la decisión)

| Opción | Oficial | Costo | Dificultad setup | Para qué sirve |
|---|---|---|---|---|
| **Meta WhatsApp Cloud API** |  Sí | Gratis hasta ~1000 conversaciones/mes, luego por uso |  Media (cuenta Meta Business + número) | La forma "correcta" y profesional. Ideal para lo que luego llevas a Walmart. |
| **Twilio for WhatsApp** |  Sí (revendedor) | De pago desde el inicio (sandbox gratis para pruebas) |  Baja | Rapidísimo para prototipar. El sandbox es perfecto para aprender. |
| **whatsapp-web.js / Baileys** (no oficial) |  No | Gratis |  Baja (escaneas QR con tu celu) | Aprender rápido con tu número personal. **Riesgo de baneo**. NO usar en producción/Walmart. |
| **n8n / plataformas no-code** | Depende del nodo | Freemium |  Baja | Flujos visuales sin código. Bueno para prototipar rápido, menos control fino. |

### Mi recomendación para tu caso (aprender + luego Walmart):
- **Fase de aprendizaje (ahora)**: **Twilio Sandbox** o **Meta Cloud API (número de prueba)**.
  Ambos son oficiales, gratis para probar, y no arriesgas ningún número.
- **Evitaría** whatsapp-web.js salvo para un experimento de una tarde, porque la costumbre
  que aprendas ahí NO se traslada a un entorno corporativo (y te pueden banear el número).

---

## 3. Opciones para el CEREBRO (el flujo de conversación)

| Enfoque | Descripción | Dificultad | Se ve humano? |
|---|---|---|---|
| **Máquina de estados + respuestas prediseñadas** | Árbol de decisión: menús, opciones, ramas. 100% controlado. |  Baja/Media | Sí, si cuidas el copy + delays de "escribiendo…" |
| **Reglas + palabras clave** | Detecta intención por keywords / regex. |  Media | Regular (se rompe con frases raras) |
| **LLM (IA generativa)** | Un modelo genera respuestas libres. |  Alta | Muy humano, pero menos controlable |
| **Híbrido (estados + LLM de respaldo)** | Flujo guiado, y cuando el usuario se sale del guion, entra el LLM. |  Alta | Lo mejor de ambos |

Para **aprender y lograr el objetivo** empezaría con **máquina de estados + respuestas prediseñadas**.
Es donde de verdad entiendes cómo funciona un chatbot. El LLM lo agregas después como topping.

>  Nota Walmart: si algún día metes un LLM, en Walmart eso pasa por **AI Innovation Lab (AI Launchpad)**.
> Pero eso es problema del "Felipe del futuro".

---

## 4. Stack técnico propuesto (si lo hacemos con código, no n8n)

- **Lenguaje**: Python 
- **Web server / webhook**: FastAPI (recibe los mensajes que WhatsApp manda)
- **Motor de flujo**: máquina de estados propia (simple, legible, sin magia)
- **Persistencia de conversación**: SQLite (para recordar en qué paso va cada usuario)
- **Toque humano**: delays de "escribiendo…", variaciones de saludo, emojis con criterio
- **Túnel para pruebas locales**: exponer tu webhook local (ngrok o similar) — *ojo: reglas
  de Walmart prohíben túneles en equipo corporativo; esto lo haríamos en tu entorno personal*.

---

## 5. ¿Qué necesitas conseguir TÚ?

Depende del canal que elijamos, pero en general:

- [ ] Un **número de teléfono** dedicado (no tu personal, idealmente) — para Cloud API/Twilio.
- [ ] Una **cuenta**: Meta Business (para Cloud API) o Twilio (para su sandbox).
- [ ] **Python instalado** en tu PC (ya lo tienes vía Code Puppy, pero para proyecto externo
      conviene un `uv venv` propio).
- [ ] Decidir si esto corre en **tu PC personal** o en un servidor.
- [ ] (Opcional para pruebas) una cuenta de **ngrok** para el túnel.

---

## 6. Dificultad global

| Componente | Dificultad |
|---|---|
| Diseñar el flujo de conversación |  Baja (es diseño, papel y lápiz) |
| Implementar la máquina de estados |  Baja/Media |
| Conectar con la API de WhatsApp |  Media (papeleo de cuentas > código) |
| Hacer que "se vea humano" |  Media (es arte + detalles) |
| Desplegar a producción |  Media |

**Veredicto**: es un proyecto **muy alcanzable** para aprender. Lo más "molesto" no es el código,
son los trámites de las cuentas de WhatsApp Business. El código en sí es amigable.

---

## 7. Plan por fases propuesto

1. **Fase 0 — Diseño del flujo** (sin código): definir el objetivo del bot, mapear el árbol
   de conversación en un diagrama. *Aquí aprendes lo más importante.*
2. **Fase 1 — Simulador local**: un chatbot que corre 100% en tu terminal/navegador, SIN
   WhatsApp todavía. Probamos el flujo y el "tono humano" sin depender de cuentas externas.
3. **Fase 2 — Conexión real**: enchufamos el motor a Twilio Sandbox o Meta Cloud API.
4. **Fase 3 — Toque humano + persistencia**: delays, memoria por usuario, variaciones.
5. **Fase 4 — (Opcional) LLM híbrido** y pensar la ruta Walmart.

> Empezar por la Fase 1 nos deja avanzar YA, sin esperar trámites de cuentas. 
