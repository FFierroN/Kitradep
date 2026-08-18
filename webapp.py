"""WebApp del chatbot - simula WhatsApp en el navegador.

Corre local, sin hosting, sin costo. Ideal para demos internas y para
que los kinesiologos de KitraDep vean el bot antes de conectarlo a
WhatsApp real.

Uso:
    python webapp.py
    python webapp.py --puerto 8765 --no-abrir
"""

from __future__ import annotations

import argparse
import re
import uuid
import webbrowser
from pathlib import Path

import uvicorn
from fastapi import Cookie, FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from motor_core import RUTA_GUION_DEFAULT, ConversacionCore, Guion

BASE_DIR = Path(__file__).parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ============================================================================
# App y sesiones en memoria
# ============================================================================

app = FastAPI(title="KitraDep - Simulador WhatsApp")

# Cargamos el guion una vez al arrancar.
GUION: Guion = Guion.cargar(RUTA_GUION_DEFAULT)

# session_id -> {"conv": ConversacionCore, "historial": list[dict]}
# Cada item del historial es {"autor": "bot"|"usuario", "texto": str}.
SESIONES: dict[str, dict] = {}


def _nueva_sesion() -> tuple[str, dict]:
    """Crea una sesion nueva y ejecuta el turno inicial del bot."""
    sid = uuid.uuid4().hex
    conv = ConversacionCore(guion=GUION)
    mensajes_bot = conv.turno_bot()
    historial = [{"autor": "bot", "texto": m} for m in mensajes_bot]
    SESIONES[sid] = {"conv": conv, "historial": historial}
    return sid, SESIONES[sid]


def _obtener_sesion(sid: str | None) -> tuple[str, dict]:
    if sid and sid in SESIONES:
        return sid, SESIONES[sid]
    return _nueva_sesion()


# ============================================================================
# Renderizado (formateo estilo WhatsApp del texto)
# ============================================================================

_URL_RE = re.compile(r"(https?://\S+)")
_BOLD_RE = re.compile(r"\*(.+?)\*", re.DOTALL)


def renderizar_texto(texto: str) -> str:
    """Convierte *bold* -> <strong> y URLs -> <a>. Sin HTML raw del usuario."""
    from html import escape

    escapado = escape(texto)
    con_bold = _BOLD_RE.sub(r"<strong>\1</strong>", escapado)
    con_links = _URL_RE.sub(
        r'<a href="\1" target="_blank" rel="noopener">\1</a>', con_bold
    )
    # Mantener saltos de linea.
    return con_links.replace("\n", "<br>")


# ============================================================================
# Endpoints
# ============================================================================


@app.get("/", response_class=HTMLResponse)
def index(sid: str | None = Cookie(default=None)):
    sid, sesion = _obtener_sesion(sid)
    html = TEMPLATES.get_template("index.html").render(
        nombre_bot=GUION.config.get("nombre_bot", "Chatbot"),
        historial=[
            {"autor": m["autor"], "html": renderizar_texto(m["texto"])}
            for m in sesion["historial"]
        ],
    )
    response = HTMLResponse(html)
    response.set_cookie("sid", sid, httponly=True, samesite="lax")
    return response


@app.post("/mensaje", response_class=HTMLResponse)
def mensaje(
    texto: str = Form(...),
    sid: str | None = Cookie(default=None),
):
    """Endpoint HTMX: recibe un mensaje del usuario y devuelve las burbujas
    nuevas (usuario + respuestas del bot) como fragmento HTML."""
    sid, sesion = _obtener_sesion(sid)
    conv: ConversacionCore = sesion["conv"]

    texto_limpio = texto.strip()
    if not texto_limpio:
        return HTMLResponse("")

    # Registrar mensaje del usuario en historial.
    sesion["historial"].append({"autor": "usuario", "texto": texto_limpio})

    # Procesar y registrar respuestas del bot.
    respuestas = conv.turno_usuario(texto_limpio)
    for r in respuestas:
        sesion["historial"].append({"autor": "bot", "texto": r})

    # Devolver solo el fragmento con las burbujas nuevas.
    fragmento = TEMPLATES.get_template("_burbujas.html").render(
        burbujas=[
            {"autor": "usuario", "html": renderizar_texto(texto_limpio)},
            *[{"autor": "bot", "html": renderizar_texto(r)} for r in respuestas],
        ]
    )
    response = HTMLResponse(fragmento)
    response.set_cookie("sid", sid, httponly=True, samesite="lax")
    return response


@app.post("/reset", response_class=HTMLResponse)
def reset(sid: str | None = Cookie(default=None)):
    """Reinicia la conversacion (nueva sesion desde cero)."""
    if sid and sid in SESIONES:
        del SESIONES[sid]
    # Devolvemos un pequeno script HTMX que recarga la pagina.
    response = HTMLResponse('<meta http-equiv="refresh" content="0; url=/">')
    response.delete_cookie("sid")
    return response


# ============================================================================
# CLI
# ============================================================================


def parsear_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulador web del bot KitraDep.")
    parser.add_argument("--puerto", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--no-abrir",
        action="store_true",
        help="No abrir el navegador automaticamente.",
    )
    return parser.parse_args()


def main() -> None:
    args = parsear_args()
    url = f"http://{args.host}:{args.puerto}"
    print("=" * 66)
    print(f"  Simulador web KitraDep corriendo en {url}")
    print("  Ctrl+C para detener")
    print("=" * 66)
    if not args.no_abrir:
        webbrowser.open(url)
    uvicorn.run(app, host=args.host, port=args.puerto, log_level="warning")


if __name__ == "__main__":
    main()
