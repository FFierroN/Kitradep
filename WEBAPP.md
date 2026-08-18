# WebApp - Simulador WhatsApp local

Web local que se ve como WhatsApp y usa el `motor_core` del bot.
100% gratis, 0 tramites, ideal para demos internas y para mostrarle
el bot a los kinesiologos de KitraDep antes de conectarlo a WhatsApp
real.

## Como correrlo

```bash
# Desde la carpeta chatbot/
python webapp.py

# Con otras opciones:
python webapp.py --puerto 8765
python webapp.py --host 0.0.0.0        # accesible desde otros equipos de tu red
python webapp.py --no-abrir            # no abre el navegador automatico
```

Se abre el navegador en http://127.0.0.1:8765. Podes hablarle al bot
como si fuera WhatsApp real.

## Arquitectura

```
webapp.py
+-- FastAPI app
+-- GET  /              -> renderiza index.html con historial de la sesion
+-- POST /mensaje       -> HTMX: recibe mensaje, devuelve burbujas nuevas
+-- POST /reset         -> borra la sesion y recarga

Sesiones en memoria: {session_id: ConversacionCore + historial}
Session ID en cookie httpOnly (samesite lax).
```

## Templates

- `templates/index.html` -> pantalla completa estilo WhatsApp
- `templates/_burbuja.html` -> una burbuja (bot o usuario)
- `templates/_burbujas.html` -> lista de burbujas (fragmento HTMX)

## Estilo WhatsApp

- Tailwind CSS via CDN.
- Colores: header verde oscuro (#075e54), boton enviar verde brillante
  (#25d366), burbuja bot blanca, burbuja usuario verde clarito (#d9fdd3).
- Fondo con el patron sutil tipico de WhatsApp.
- Indicador "escribiendo..." con 3 puntos animados mientras el bot procesa.

## Que hace este simulador vs WhatsApp real

| Feature | Simulador | WhatsApp real (Fase 4) |
|---|---|---|
| Interfaz visual identica | Si | Si (nativa) |
| Envio/recepcion mensajes | Si (localhost) | Si (via Twilio/Meta) |
| Formato bold *texto* | Si (renderiza <strong>) | Si (nativo WA) |
| Links clickeables | Si | Si |
| Fotos/audios | No | Si |
| Multiples usuarios simultaneos | Si (por cookie) | Si (por numero) |
| Persistencia entre reinicios | No (memoria) | Depende (BD) |
| Costo | 0 | ~USD 0-15/mes |
| Setup | 15 min | Horas a semanas |

## Sesiones

Cada visitante recibe una cookie `sid` con un uuid. Se mantiene su
estado de conversacion en memoria hasta que:
- Toque el boton "Reiniciar" (borra la sesion).
- Se detenga el servidor (todas las sesiones se pierden).

Para pruebas locales alcanza y sobra. Cuando pasemos a produccion
(Fase 4) esto va a ser SQLite/Postgres.

## Comandos globales

Igual que la CLI, funcionan desde el input del chat:
- `menu` / `inicio` / `reset` -> vuelve al estado inicial
- `salir` / `chao` -> despedida

## Que NO hace (por ahora)

- No persiste conversaciones al reiniciar (por diseno).
- No tiene autenticacion (localhost, no expuesto a internet).
- No maneja media (solo texto).
- No tiene notificaciones al staff (Fase 4.5).
