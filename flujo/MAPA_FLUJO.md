# Mapa del flujo - KitraDep (Fase 1)

> Este es el "arbol" de la conversacion. Cada caja es un ESTADO.
> Las flechas son las OPCIONES que llevan de un estado a otro.
> Nueva version: refleja la bifurcacion clave FONASA vs ISAPRE/PARTICULAR.

```
                          +---------------------+
                          |       INICIO        |
                          |  (saludo + menu)    |
                          +----------+----------+
                                     |
       +-------------+---------------+---------------+----------------+
       |             |               |               |                |
       v             v               v               v                v
   [1] FAQ       [2] AGENDAR     [3] INFO        [4] HABLAR       [0] SALIR
   (submenu)     (flujo largo)   CONTACTO        CON HUMANO       (despedida)
       |             |
       v             v
  +----------+   +-----------------------------------------------------------+
  | FAQ menu |   |                FLUJO DE AGENDAR CITA                       |
  +---+------+   |                                                            |
      |          |  0) Tiene orden medica? (Si/No) - informativo              |
   1  |  2 3 4   |     -> Si -> "envia foto cuando te contactemos"            |
   +--+--+--+--+ |     -> continua igual                                      |
   |  |  |  |    |                                                            |
   v  v  v  v    |  1) Explicacion 1-a-1 + evaluacion inicial                 |
 hor ubi ser prec|                                                            |
             |   |  2) *** BIFURCACION *** Cual es tu prevision?              |
             v   |     - Fonasa                                               |
        pide prev|     - Isapre                                               |
        y bifurca|     - Particular                                           |
             |   |                                                            |
         +---+---+                                                            |
         |       |                                                            |
         v       v   3) Muestra VALORES segun prevision y pide plan:          |
       fonasa isapre  - Fonasa: $20k / $100k / $180k + aclaracion "no adher"  |
                      - Isapre/Part: $25k / $115k / $230k + "damos boleta"    |
                      -> guarda {plan}                                        |
                                                                              |
                   4) Preferencia horario: AM (Javiera/Jaime)                 |
                      / PM (Francisco/Valentina) / cualquiera                 |
                      -> guarda {horario_pref}                                |
                                                                              |
                   5) Pide DATOS en un solo mensaje:                          |
                      Nombre, RUT, Correo, Contacto, Prevision, Direccion     |
                      -> guarda {datos}                                       |
                                                                              |
                   6) Confirmar resumen (Si -> OK / No -> vuelve al inicio)   |
                                                                              |
                   7) OK: cierre + tips (ropa comoda, bicicletero, pago) +    |
                      link Maps + link autogestion Encuadrado                 |
                      "un kine te contactara para confirmar dia/hora"         |
                   +--------------------------------------------------+


   ESTADOS ESPECIALES (pueden dispararse en cualquier momento):
   - NO_ENTIENDO      : cuando el usuario escribe algo fuera de las opciones.
   - DESPEDIDA        : cierre amable de la conversacion.
   - HUMANO           : mensaje de "te derivo con un kinesiologo".
   - FUERA_DE_HORARIO : auto-mensaje si esta fuera de L-V 8-21 / Sab 9-13.
```

## Tipos de estado que usamos

1. **menu**: muestra un mensaje + opciones numeradas. Segun lo que elige el usuario,
   salta a otro estado. Puede tener `guardar_en` para guardar el valor elegido.
2. **entrada** (input): hace una pregunta y GUARDA lo que responde el usuario en una
   variable. Luego avanza al siguiente estado.
3. **mensaje**: solo muestra un texto y avanza (o termina si `ir_a: fin`).

## Variables recolectadas en el flujo de cita

| Variable | Que guarda | Ejemplo |
|---|---|---|
| `{prevision}` | Prevision del paciente | "Fonasa" / "Isapre" / "Particular" |
| `{plan}` | Modalidad elegida (sesiones + precio) | "Pack 10 sesiones Fonasa ($180.000)" |
| `{horario_pref}` | Preferencia AM / PM | "AM" |
| `{datos}` | Bloque completo de datos del paciente | (todo el texto pegado) |

Estas se pueden inyectar en cualquier mensaje con llaves, ej:
`"Perfecto! Prevision: {prevision}, plan: {plan}"`.

## Diferencia clave con la version anterior

| Antes | Ahora |
|---|---|
| "Servicio" era Fonasa/Isapre/Otro (mal modelado) | Servicio es unico; **prevision** bifurca precios |
| Solo pedia dia + hora + nombre | Pide prevision + plan + preferencia horaria + datos completos |
| No mencionaba orden medica | Pregunta explicitamente al inicio del agendamiento |
| Bot "cerraba" la cita solo | Bot recolecta info y avisa "un kine confirma slot exacto" |
| Sin aclaracion Fonasa | Aclara: "no somos centro adherido, valor preferencial" |
| Sin mencion de reembolso | Isapre: "damos boleta para reembolso" |
| Sin post-cita | Cierre con tips (ropa comoda, bicicletero, pago) + Maps + link autogestion |
