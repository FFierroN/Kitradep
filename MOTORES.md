# El "cerebro" del bot: motores de conversacion explicados

> Aqui comparamos las formas de construir la LOGICA que decide que responder.
> No confundir con el CANAL (Meta/Twilio/n8n) ni con las respuestas prediseñadas.
> Esto es el "como piensa" el bot.

---

## Opcion 1: Maquina de estados + respuestas prediseñadas

### De que trata
El bot es como un juego de "elige tu propia aventura". Tiene ESTADOS (pasos de la
conversacion) y en cada estado ofrece opciones. Segun lo que elige el usuario, avanza
a otro estado. Todo esta definido de antemano por ti.

Ejemplo:
```
[INICIO]
  Hola! Soy el asistente. En que te ayudo?
  1) Horarios de atencion
  2) Agendar una cita
  3) Hablar con un humano

  usuario escribe "2"
     v
[AGENDAR_CITA]
  Perfecto. Que dia te acomoda?
  ...
```

### Pros
- **Control total**: sabes EXACTAMENTE que va a responder. Cero sorpresas.
- **Predecible y barato**: no depende de IA, no consume tokens.
- **Facil de depurar**: si algo falla, sigues el arbol y encuentras el nodo.
- **Ideal para aprender**: entiendes de verdad la mecanica de un chatbot.
- **Perfecto para FAQ, citas, menus**: casos con caminos claros.

### Contras
- **Rigido**: si el usuario escribe algo fuera del guion ("oye y tienen delivery?"),
  el bot no entiende salvo que hayas previsto esa rama.
- **Se siente robotico** si no cuidas el copy y los detalles (delays, variaciones).
- Puede crecer mucho si el arbol tiene demasiadas ramas.

### Cuando usarlo
Cuando el flujo es claro y acotado: atencion al cliente, FAQ, agendar citas.
**Es lo que recomiendo para empezar** (y encaja perfecto con tu caso de uso).

---

## Opcion 2: Reglas por palabras clave (keywords / intents)

### De que trata
En vez de menus numerados, el bot LEE el texto libre del usuario y busca palabras clave
o patrones para adivinar la intencion.

Ejemplo:
```
usuario: "a que hora abren?"
   -> detecta palabras {"hora", "abren"} -> intencion HORARIOS
   -> responde con los horarios

usuario: "quiero una cita para el martes"
   -> detecta {"cita"} -> intencion AGENDAR
```

### Pros
- **Mas natural**: el usuario escribe libre, sin elegir numeritos.
- **Flexible**: una misma intencion se activa con muchas frases.
- Sigue siendo barato (no necesita IA obligatoriamente).

### Contras
- **Se rompe con frases raras** o mal escritas ("kiero cita", "horarioo?").
- **Ambiguo**: "no quiero cita" tambien contiene "cita" -> falso positivo.
- Mantener las listas de keywords se vuelve tedioso a medida que creces.
- Requiere pensar bien sinonimos, acentos, typos.

### Cuando usarlo
Cuando quieres que se sienta mas conversacional pero sin meter IA todavia.
Muchas veces se COMBINA con la maquina de estados (estados + deteccion de keywords
dentro de cada estado). Es un buen "nivel 2".

---

## Opcion 3: LLM (IA generativa)

### De que trata
Un modelo de lenguaje (tipo GPT/Claude/Gemini) genera las respuestas. Le das un
"system prompt" con la personalidad y el conocimiento del negocio, y el modelo
responde en lenguaje natural a casi cualquier cosa.

### Pros
- **Se siente muy humano**: entiende frases raras, typos, contexto, matices.
- **Flexible al maximo**: no tienes que prever cada rama.
- Puede resumir, reformular, responder preguntas abiertas.

### Contras
- **Menos control**: puede "inventar" (alucinar) datos si no lo aterrizas bien.
- **Cuesta dinero** (tokens) y **latencia** (tarda un poco mas).
- Requiere guardrails para que no se salga del tema o diga cosas indebidas.
- En Walmart: obligatorio pasar por **AI Innovation Lab / AI Launchpad**.

### Cuando usarlo
Cuando necesitas conversaciones abiertas y muy naturales, o un "cajon de sastre" para
preguntas que no cubre el flujo. Es potente pero es el nivel mas avanzado.

---

## Opcion 4: Hibrido (estados + LLM de respaldo)  <- el "ideal" a futuro

### De que trata
Lo mejor de ambos mundos:
- Un **flujo guiado** (maquina de estados) maneja lo importante: citas, datos, procesos.
  Ahi quieres control total y cero alucinaciones.
- Cuando el usuario se **sale del guion** o hace una pregunta abierta, entra el **LLM**
  como respaldo para responder con naturalidad, y luego devuelve al flujo.

Ejemplo:
```
[AGENDAR_CITA] (maquina de estados, controlado)
  usuario: "y ustedes atienden mascotas grandes?"  <- fuera de guion
     -> el LLM responde la duda con el contexto del negocio
     -> vuelve a: "Perfecto, seguimos con tu cita. Que dia te acomoda?"
```

### Pros
- Control donde importa + naturalidad donde ayuda.
- Es lo que usan los bots profesionales serios.

### Contras
- **Mas complejo** de construir y mantener.
- Costos y guardrails del LLM.
- No es por donde se empieza a aprender.

---

## Tabla resumen

| Motor | Dificultad | Control | Se siente humano | Costo | Cuando |
|---|---|---|---|---|---|
| Maquina de estados | Baja | Total | Medio (mejora con copy) | 0 | **Empezar aqui** |
| Keywords | Media | Alto | Medio-alto | 0 | Nivel 2, mas natural |
| LLM | Alta | Bajo | Muy alto | $ tokens | Conversacion abierta |
| Hibrido | Alta | Alto | Muy alto | $ tokens | Meta final |

---

## Mi recomendacion para TU caso (atencion + FAQ + citas)

Ruta de aprendizaje progresiva:

1. **Maquina de estados + respuestas prediseñadas** -> construyes el esqueleto (menus,
   FAQ, flujo de agendar cita). Aprendes lo fundamental.
2. Le agregamos **deteccion de keywords** para que el usuario pueda escribir libre y no
   solo elegir numeros -> se siente mas humano.
3. (Opcional, mas adelante) **LLM de respaldo** para las preguntas abiertas -> el toque
   profesional.

Asi cada fase te enseña algo nuevo y el bot va sintiendose cada vez mas humano, sin
que te abrumes de golpe.
