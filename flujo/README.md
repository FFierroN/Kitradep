# Como llenar el guion del chatbot (Fase 1)

Todo el contenido del bot vive en **`guion.yaml`**. Tu solo editas TEXTOS. La logica
(el motor) va aparte, asi nunca rompes el bot por cambiar un mensaje.

## Los 3 tipos de estado

| tipo | que hace | campos que usa |
|---|---|---|
| `menu` | Muestra opciones numeradas y salta segun la eleccion | `mensaje`, `opciones` |
| `entrada` | Hace una pregunta y GUARDA la respuesta en una variable | `mensaje`, `guardar_en`, `ir_a` |
| `mensaje` | Solo muestra un texto y avanza | `mensaje`, `ir_a` |

## Anatomia de una opcion (dentro de un menu)

```yaml
opciones:
  - detecta: ["1", "corte", "cortar"]   # que escribe el usuario para activarla
    valor: "Corte de pelo"              # (opcional) que se guarda en la variable
    ir_a: cita_dia                      # a que estado saltar
```

- `detecta`: lista de palabras/numeros que activan esa opcion. Pon sinonimos y el numero.
- `ir_a`: el nombre del estado destino (debe existir en `estados:`).
- `valor`: solo si quieres guardar algo (usado junto con `guardar_en` del menu).

## Variables

- Se recolectan con `guardar_en` (en estados `entrada` o `menu`).
- Se muestran con llaves: `{nombre}`, `{servicio}`, `{dia}`, `{hora}`.
- Ejemplo: `"Perfecto {nombre}, tu {servicio} quedo el {dia} a las {hora}."`

## Reglas de oro para que se vea HUMANO

1. Escribe como hablarias tu, no como un robot. Frases cortas.
2. Usa el nombre de la persona cuando lo tengas: `{nombre}`.
3. Confirma lo que entendiste antes de cerrar (el paso `cita_confirmar`).
4. Ten un buen `no_entiendo`: amable, y recuerda las opciones.
5. Varia los saludos y cierres (eso lo afinamos en el motor con el toque de delays).

## Que sigue

Cuando termines de llenar `guion.yaml`, construimos el MOTOR que lo lee y te deja
chatear con el bot en tu terminal/navegador. Cero costo, cero WhatsApp todavia.
