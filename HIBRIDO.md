# El motor HIBRIDO (maquina de estados + LLM de respaldo)

> El modelo "profesional": flujo controlado para lo importante + IA para lo abierto.
> Aqui: que tan complejo es, que costos trae, que modelo de IA usar, y que se necesita.

---

## 1. Como funciona (la idea)

Dos cerebros trabajando en equipo:

- **Maquina de estados** (el "riel"): maneja los procesos importantes donde NO quieres
  sorpresas -> agendar citas, pedir datos, confirmar, menus. Control total, cero alucinacion.
- **LLM** (el "comodin"): entra SOLO cuando el usuario se sale del guion o hace una pregunta
  abierta que el flujo no cubre. Responde natural y luego devuelve al riel.

```
Mensaje del usuario
      |
      v
  Estoy en medio de un proceso critico (ej. agendando cita)?
      |                                   |
     SI                                  NO / se salio del guion
      |                                   |
  Maquina de estados                   El LLM responde con
  (respuesta controlada)               el contexto del negocio
                                          |
                                       Vuelve al flujo
```

El truco esta en el **enrutador (router)**: la logica que decide "esto lo maneja el flujo"
vs "esto se lo paso al LLM". Ese es el corazon del hibrido.

---

## 2. Que tan complejo es?

**Dificultad: media-alta.** Pero se construye por capas, no de golpe:

| Pieza | Dificultad | Nota |
|---|---|---|
| Maquina de estados base | Baja | Es la Fase 1, ya la construiriamos igual |
| Integrar un LLM (llamar a la API) | Baja | Son ~20 lineas de codigo |
| El router (cuando usar cada uno) | **Media** | Aqui esta el arte del hibrido |
| Base de conocimiento (FAQ para el LLM) | Baja-Media | Un archivo con la info del negocio |
| Guardrails (que no se salga del tema/invente) | Media | Prompt bien hecho + reglas |
| RAG (busqueda en documentos grandes) | Alta | OPCIONAL, solo si tienes mucha info |

**Lo clave**: NO es que sea dificil de programar. Es que hay MAS piezas que coordinar y
requiere afinar el prompt y el router. Por eso se recomienda construir primero la maquina
de estados sola, y AGREGAR el LLM despues como un modulo. Asi no te abrumas.

---

## 3. Hay que usar un modelo de IA? Cuales?

Si, el hibrido necesita un LLM. Tienes 3 caminos:

### A) API en la nube (lo mas facil y comun)
Pagas por uso (tokens). Modelos baratos y muy buenos:

| Modelo | Costo aprox (input / output por 1M tokens) | Nota |
|---|---|---|
| **Gemini 1.5 Flash** (Google) | ~USD 0.075 / 0.30 | Muy barato, generoso free tier |
| **GPT-4o-mini** (OpenAI) | ~USD 0.15 / 0.60 | Excelente relacion precio/calidad |
| **Claude Haiku** (Anthropic) | ~USD 0.25 / 1.25 | Muy bueno siguiendo instrucciones |

Necesitas: crear cuenta en el proveedor + una **API key**. Listo.

### B) Modelo local (gratis, pero necesitas hardware)
Con **Ollama** corres modelos como Llama 3.1 8B en tu propio PC.
- Costo: **USD 0** en tokens.
- Requisito: un PC decente (idealmente GPU, o buena RAM). Mas lento sin GPU.
- Ventaja: privacidad total, sin costo por mensaje.
- Desventaja: calidad algo menor que GPT-4o, y consume tu maquina.

### C) LLM interno de Walmart
Si algun dia esto entra a Walmart, el LLM va OBLIGATORIAMENTE por **AI Innovation Lab /
AI Launchpad** (no se usan APIs externas con datos de la empresa).

---

## 4. Cuanto cuesta el LLM en la practica?

Los LLM se cobran por "tokens" (~ pedacitos de palabra). Un intercambio tipico de chatbot
(pregunta + contexto + respuesta) ronda los **500-1500 tokens**.

Ejemplo con **GPT-4o-mini**:
- Un intercambio ~ USD 0.0003 (tres diezmilesimos de dolar).
- **10.000 intercambios ~ USD 3.** 
- Y eso solo para los mensajes que caen al LLM (los del flujo controlado son gratis).

Con **Gemini Flash** es aun mas barato, e incluso tiene un free tier que para practicar
te puede salir **gratis**.

> Traduccion: para aprender y para volumenes chicos, el costo del LLM son **centavos**.
> El costo se vuelve relevante solo con miles de conversaciones abiertas al dia.

---

## 5. Que se necesita para implementarlo (checklist)

- [ ] La **maquina de estados** ya construida (Fase 1). El LLM se monta encima.
- [ ] Una **cuenta + API key** de un proveedor (Gemini/OpenAI/Anthropic) O tener **Ollama**
      instalado para modo local.
- [ ] Una **base de conocimiento**: un documento con la info del negocio (horarios,
      servicios, precios, politicas) que el LLM usara para responder sin inventar.
- [ ] Un **system prompt** bien escrito: personalidad, tono, limites ("solo hablas de X",
      "si no sabes, deriva a un humano").
- [ ] El **router**: la logica que decide flujo vs LLM.
- [ ] **Guardrails**: reglas para que no se salga del tema ni prometa cosas raras.
- [ ] (Opcional) **RAG** si tu info es muy extensa (busca el fragmento relevante antes de
      responder). Para un FAQ chico NO hace falta.

---

## 6. Costos incluidos del hibrido (resumen)

Todo lo del bot normal MAS:

| Concepto | Costo |
|---|---|
| Canal WhatsApp | Igual que siempre (service = gratis) |
| Hosting | ~USD 5-12/mes (o tu PC en pruebas) |
| **LLM (nube)** | Centavos a pocos dolares al mes con volumen chico |
| **LLM (local con Ollama)** | USD 0 en tokens, "cuesta" tu hardware |
| Tu tiempo afinando prompt/router | El costo mas real, la verdad |

---

## 7. Mi recomendacion honesta

El hibrido es **la meta correcta**, pero NO el punto de partida para aprender. El camino
inteligente:

1. **Fase 1**: maquina de estados + FAQ + citas (simulador local, gratis). Aprendes la base.
2. **Fase 2**: keywords para escribir libre. Se siente mas humano.
3. **Fase 3**: montamos el **LLM de respaldo** encima -> ya tienes el hibrido, y lo
   entiendes de verdad porque construiste cada capa.

Asi llegas al hibrido sin frustrarte, y cuando lo tengas vas a entender CADA pieza (no una
caja negra). Ademas, la Fase 1 y 2 te sirven aunque nunca metas el LLM.
