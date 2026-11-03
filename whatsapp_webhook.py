"""Webhook de WhatsApp (Fase 4-B: Twilio Sandbox).

Twilio recibe el WhatsApp del paciente y hace un POST a /webhook con los
datos del mensaje (form-urlencoded: From, Body, NumMedia, ...). Aca:

1. Validamos la firma `X-Twilio-Signature` (prueba de que el POST viene de
   Twilio y no de cualquiera que conozca la URL).
2. Pasamos el texto al bot (la funcion `procesar` que entrega la webapp).
3. Respondemos con TwiML (XML) y Twilio le envia la respuesta al paciente.

No usa el paquete `twilio`: la firma y el TwiML son simples de armar a mano,
asi evitamos una dependencia mas.

Cuando Meta verifique el negocio se agrega aqui la variante Meta Cloud API
(GET con challenge + POST JSON); el resto del bot no cambia.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
from collections.abc import Callable
from xml.sax.saxutils import escape

from fastapi import APIRouter, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

log = logging.getLogger("kitradep.webhook")

# Twilio corta los mensajes de WhatsApp sobre 1600 caracteres.
MAX_CARACTERES = 1600

MENSAJE_SOLO_TEXTO = (
    "Por ahora solo puedo leer mensajes de texto 🙏 "
    "¿Me lo escribes, por favor?"
)


# ============================================================================
# Helpers puros (testeables sin servidor)
# ============================================================================


def firma_twilio(auth_token: str, url: str, params: dict[str, str]) -> str:
    """Calcula la firma que Twilio pone en `X-Twilio-Signature`.

    Algoritmo oficial: URL completa + cada parametro POST (ordenados por
    nombre) concatenado como nombre+valor, HMAC-SHA1 con el Auth Token,
    codificado en base64.
    """
    datos = url + "".join(k + params[k] for k in sorted(params))
    digest = hmac.new(auth_token.encode(), datos.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


def firma_valida(
    auth_token: str, url: str, params: dict[str, str], firma: str
) -> bool:
    """Compara en tiempo constante (evita ataques por tiempo de respuesta)."""
    esperada = firma_twilio(auth_token, url, params)
    return hmac.compare_digest(esperada, firma or "")


def partir_texto(texto: str, maximo: int = MAX_CARACTERES) -> list[str]:
    """Divide respuestas largas en trozos <= maximo, cortando en saltos de linea."""
    trozos: list[str] = []
    while len(texto) > maximo:
        corte = texto.rfind("\n", 0, maximo)
        if corte <= 0:
            corte = maximo
        trozos.append(texto[:corte].rstrip())
        texto = texto[corte:].lstrip()
    if texto:
        trozos.append(texto)
    return trozos


def twiml(texto: str) -> str:
    """Arma la respuesta TwiML. Texto vacio = no responder nada."""
    mensajes = "".join(
        f"<Message>{escape(t)}</Message>" for t in partir_texto(texto)
    )
    return f'<?xml version="1.0" encoding="UTF-8"?><Response>{mensajes}</Response>'


def sesion_id_whatsapp(remitente: str) -> str:
    """'whatsapp:+569...' -> 'wa:+569...' (una sesion por numero de telefono)."""
    return "wa:" + remitente.removeprefix("whatsapp:")


# ============================================================================
# Endpoint
# ============================================================================


def crear_router_webhook(
    procesar: Callable[[str, str], str],
    auth_token: str,
    url_publica: str,
) -> APIRouter:
    """Crea el endpoint POST /webhook.

    - procesar(sesion_id, texto) -> respuesta del bot.
    - auth_token: Auth Token de Twilio. Vacio = sin validar firma (solo para
      pruebas locales; en el servidor SIEMPRE debe estar configurado).
    - url_publica: URL exacta registrada en Twilio (ej:
      https://3-20-141-102.sslip.io/webhook). Hace falta porque detras de
      Caddy el bot ve la peticion como http://127.0.0.1:8765/webhook y la
      firma se calcula sobre la URL publica.
    """
    router = APIRouter()

    if not auth_token:
        log.warning("TWILIO_AUTH_TOKEN vacio: el webhook NO valida firmas.")

    @router.post("/webhook")
    async def webhook_twilio(request: Request) -> Response:
        form = await request.form()
        params = {k: str(v) for k, v in form.items()}

        if auth_token:
            url = url_publica or str(request.url)
            firma = request.headers.get("X-Twilio-Signature", "")
            if not firma_valida(auth_token, url, params, firma):
                log.warning("Firma de Twilio invalida; peticion rechazada.")
                return Response("Firma invalida", status_code=403)

        remitente = params.get("From", "")
        texto = params.get("Body", "").strip()
        if not remitente:
            return Response("Falta From", status_code=400)

        if not texto:
            # Audio, foto, sticker, ubicacion...
            respuesta = MENSAJE_SOLO_TEXTO if params.get("NumMedia", "0") != "0" else ""
        else:
            # procesar() llama a Gemini (bloqueante): va en un hilo aparte.
            respuesta = await run_in_threadpool(
                procesar, sesion_id_whatsapp(remitente), texto
            )

        return Response(twiml(respuesta), media_type="application/xml")

    return router
