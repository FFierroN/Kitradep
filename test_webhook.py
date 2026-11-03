"""Tests del webhook de WhatsApp (Twilio).

Offline: no llama a Twilio ni a Gemini. Simula los POST que haria Twilio
llamando a la app FastAPI directamente (ASGI), sin servidor ni httpx.

Uso:
    python test_webhook.py
"""

from __future__ import annotations

import asyncio
from urllib.parse import urlencode

from fastapi import FastAPI

from whatsapp_webhook import (
    MENSAJE_SOLO_TEXTO,
    crear_router_webhook,
    firma_twilio,
    firma_valida,
    partir_texto,
    sesion_id_whatsapp,
    twiml,
)

TOKEN = "token_de_prueba"
URL = "https://ejemplo.sslip.io/webhook"


def _post(app: FastAPI, params: dict[str, str], firma: str | None) -> tuple[int, str]:
    """Hace un POST form-urlencoded a /webhook y devuelve (status, cuerpo)."""
    cuerpo = urlencode(params).encode()
    headers = [(b"content-type", b"application/x-www-form-urlencoded")]
    if firma is not None:
        headers.append((b"x-twilio-signature", firma.encode()))
    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": "POST", "scheme": "http", "path": "/webhook", "raw_path": b"/webhook",
        "query_string": b"", "headers": headers,
        "server": ("127.0.0.1", 8765), "client": ("127.0.0.1", 5000),
    }
    salida: dict = {"status": 0, "body": b""}

    async def receive():
        return {"type": "http.request", "body": cuerpo, "more_body": False}

    async def send(msg):
        if msg["type"] == "http.response.start":
            salida["status"] = msg["status"]
        elif msg["type"] == "http.response.body":
            salida["body"] += msg.get("body", b"")

    asyncio.run(app(scope, receive, send))
    return salida["status"], salida["body"].decode()


def _app(auth_token: str = TOKEN) -> tuple[FastAPI, list]:
    """App minima con el webhook y un 'bot' falso que registra las llamadas."""
    llamadas: list[tuple[str, str]] = []

    def procesar(sid: str, texto: str) -> str:
        llamadas.append((sid, texto))
        return f"eco: {texto}"

    app = FastAPI()
    app.include_router(crear_router_webhook(procesar, auth_token, URL))
    return app, llamadas


def _check(nombre: str, passed: bool, res: list[bool]) -> None:
    res.append(passed)
    print(f"  {'OK ' if passed else 'XX '} {nombre}")


def test_helpers() -> tuple[int, int]:
    print("\n=== TEST: Helpers del webhook ===")
    res: list[bool] = []
    # Ejemplo oficial de https://www.twilio.com/docs/usage/security
    oficial = {"CallSid": "CA1234567890ABCDE", "Caller": "+14158675310",
               "Digits": "1234", "From": "+14158675310", "To": "+18005551212"}
    _check("firma = ejemplo oficial de Twilio",
           firma_twilio("12345", "https://example.com/myapp.php?foo=1&bar=2", oficial)
           == "L/OH5YylLD5NRKLltdqwSvS0BnU=", res)

    params = {"From": "whatsapp:+56911112222", "Body": "hola"}
    f = firma_twilio(TOKEN, URL, params)
    _check("firma correcta se acepta", firma_valida(TOKEN, URL, params, f), res)
    _check("firma con otro token se rechaza",
           not firma_valida("otro", URL, params, f), res)
    _check("firma con cuerpo alterado se rechaza",
           not firma_valida(TOKEN, URL, {**params, "Body": "chao"}, f), res)
    _check("firma vacia se rechaza", not firma_valida(TOKEN, URL, params, ""), res)

    _check("sesion por numero: whatsapp:+569.. -> wa:+569..",
           sesion_id_whatsapp("whatsapp:+56911112222") == "wa:+56911112222", res)

    largo = ("linea de texto\n" * 200).strip()
    trozos = partir_texto(largo)
    _check("texto largo se parte en trozos <= 1600",
           len(trozos) > 1 and all(len(t) <= 1600 for t in trozos), res)

    x = twiml("Hola <Kitra> & co")
    _check("TwiML escapa caracteres XML",
           "<Message>Hola &lt;Kitra&gt; &amp; co</Message>" in x, res)
    _check("texto vacio -> TwiML sin mensajes",
           twiml("").endswith("<Response></Response>"), res)

    ok = sum(res)
    print(f"  -> {ok}/{len(res)} correctos")
    return ok, len(res)


def test_endpoint() -> tuple[int, int]:
    print("\n=== TEST: Endpoint POST /webhook ===")
    res: list[bool] = []
    params = {"From": "whatsapp:+56911112222", "Body": "Hola, atienden Fonasa?",
              "NumMedia": "0"}

    app, llamadas = _app()
    status, cuerpo = _post(app, params, firma_twilio(TOKEN, URL, params))
    _check("POST firmado -> 200", status == 200, res)
    _check("respuesta del bot va dentro de <Message>",
           "<Message>eco: Hola, atienden Fonasa?</Message>" in cuerpo, res)
    _check("el bot recibe sesion wa:+numero y el texto",
           llamadas == [("wa:+56911112222", "Hola, atienden Fonasa?")], res)

    app, llamadas = _app()
    status, _ = _post(app, params, "firma-falsa")
    _check("firma falsa -> 403 y el bot no se ejecuta",
           status == 403 and not llamadas, res)

    app, llamadas = _app()
    status, _ = _post(app, params, None)
    _check("sin firma -> 403", status == 403 and not llamadas, res)

    foto = {"From": "whatsapp:+56911112222", "Body": "", "NumMedia": "1"}
    app, llamadas = _app()
    status, cuerpo = _post(app, foto, firma_twilio(TOKEN, URL, foto))
    _check("foto/audio sin texto -> aviso 'solo texto' sin llamar al bot",
           status == 200 and "solo puedo leer" in cuerpo and not llamadas, res)

    app, llamadas = _app(auth_token="")
    status, cuerpo = _post(app, params, None)
    _check("sin TWILIO_AUTH_TOKEN (modo local) -> acepta sin firma",
           status == 200 and len(llamadas) == 1, res)

    ok = sum(res)
    print(f"  -> {ok}/{len(res)} correctos")
    return ok, len(res)


def main() -> None:
    assert MENSAJE_SOLO_TEXTO
    resultados = [test_helpers(), test_endpoint()]
    ok = sum(r[0] for r in resultados)
    total = sum(r[1] for r in resultados)
    print(f"\n=== TOTAL: {ok}/{total} ===")
    raise SystemExit(0 if ok == total else 1)


if __name__ == "__main__":
    main()
