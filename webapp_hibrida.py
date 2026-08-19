"""WebApp HIBRIDA - simula WhatsApp usando el router hibrido.

A diferencia de webapp.py (que usa el motor de estados puro), esta webapp
usa el Router: guardrails + memoria + LLM (fake o gemini). Ademas:
  - Persiste conversaciones en SQLite (sobreviven reinicios).
  - Rate limiting por sesion (anti-abuso).
  - Notifica al staff en handoff / urgencia.
  - Endpoint /health para monitoreo (UptimeRobot).

No toca webapp.py: ambas coexisten para poder comparar.

Uso:
    python webapp_hibrida.py
    LLM_BACKEND=gemini python webapp_hibrida.py   (en tu PC con API key)
"""

from __future__ import annotations

import re
import uuid
import webbrowser
from html import escape
from pathlib import Path

import uvicorn
from fastapi import Cookie, FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import guardrails
import notificaciones
from config import config
from db import Database
from ratelimit import MENSAJE_LIMITE, RateLimiter
from router import Router, SesionChat

BASE_DIR = Path(__file__).parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="KitraDep - Simulador WhatsApp (Hibrido)")

# Recursos compartidos (se crean una vez al arrancar).
ROUTER = Router.crear(handoff_contacto=config.handoff_contacto)
DB = Database(config.db_path)
LIMITER = RateLimiter(
    max_mensajes=config.rate_limit_mensajes,
    ventana_s=config.rate_limit_ventana_s,
)

# Memoria en RAM por sesion (se rehidrata desde la DB al reconectar).
SESIONES: dict[str, SesionChat] = {}


# ============================================================================
# Helpers
# ============================================================================

_URL_RE = re.compile(r"(https?://\S+)")
_BOLD_RE = re.compile(r"\*(.+?)\*", re.DOTALL)


def renderizar_texto(texto: str) -> str:
    """Convierte *bold* -> <strong> y URLs -> <a>. Escapa HTML del usuario."""
    escapado = escape(texto)
    con_bold = _BOLD_RE.sub(r"<strong>\1</strong>", escapado)
    con_links = _URL_RE.sub(
        r'<a href="\1" target="_blank" rel="noopener">\1</a>', con_bold
    )
    return con_links.replace("\n", "<br>")


def _obtener_sesion(sid: str | None) -> tuple[str, SesionChat]:
    """Devuelve (sid, SesionChat), rehidratando historial desde la DB."""
    if sid and sid in SESIONES:
        return sid, SESIONES[sid]

    if not sid:
        sid = uuid.uuid4().hex

    sesion = SesionChat()
    # Rehidratar memoria desde la DB (si la sesion ya existia).
    sesion.historial = DB.cargar_historial(sid, limite=config.max_turnos_memoria)
    SESIONES[sid] = sesion
    DB.asegurar_sesion(sid, canal="web")
    return sid, sesion


# ============================================================================
# Endpoints
# ============================================================================


@app.get("/", response_class=HTMLResponse)
def index(sid: str | None = Cookie(default=None)):
    sid, sesion = _obtener_sesion(sid)

    # Si es sesion nueva sin historial, saludo inicial del bot.
    if not sesion.historial:
        r = ROUTER.manejar_detallado(sesion, "hola")
        DB.guardar_mensaje(sid, "user", "hola")
        DB.guardar_mensaje(sid, "assistant", r.texto)

    historial = [
        {"autor": t.rol, "html": renderizar_texto(t.texto)}
        for t in sesion.historial
    ]
    html = TEMPLATES.get_template("index.html").render(
        nombre_bot="Kitra",
        historial=historial,
    )
    resp = HTMLResponse(html)
    resp.set_cookie("sid", sid, httponly=True, samesite="lax")
    return resp


@app.post("/mensaje", response_class=HTMLResponse)
def mensaje(texto: str = Form(...), sid: str | None = Cookie(default=None)):
    sid, sesion = _obtener_sesion(sid)
    texto_limpio = texto.strip()
    if not texto_limpio:
        return HTMLResponse("")

    # Rate limiting anti-abuso.
    if not LIMITER.permitido(sid):
        DB.registrar_evento("rate_limit", "sesion excedio limite", sesion_id=sid)
        fragmento = TEMPLATES.get_template("_burbujas.html").render(
            burbujas=[
                {"autor": "usuario", "html": renderizar_texto(texto_limpio)},
                {"autor": "bot", "html": renderizar_texto(MENSAJE_LIMITE)},
            ]
        )
        return HTMLResponse(fragmento)

    # Procesar via router.
    r = ROUTER.manejar_detallado(sesion, texto_limpio)

    # Persistir.
    DB.guardar_mensaje(sid, "user", texto_limpio)
    DB.guardar_mensaje(sid, "assistant", r.texto)

    # Auditoria + notificaciones segun el riesgo detectado.
    if r.riesgo is not guardrails.Riesgo.NINGUNO:
        DB.registrar_evento(
            "guardrail", f"{r.riesgo.value}: {texto_limpio}", sesion_id=sid
        )
    if r.notificar_staff:
        if r.riesgo is guardrails.Riesgo.EMERGENCIA:
            notificaciones.aviso_urgencia(sid, texto_limpio)
        elif r.riesgo is guardrails.Riesgo.HANDOFF:
            notificaciones.aviso_handoff(sid)
        elif r.datos_agendamiento:
            notificaciones.aviso_agendamiento(r.datos_agendamiento)
            DB.registrar_evento("agendamiento", "paciente completo datos", sesion_id=sid)

    fragmento = TEMPLATES.get_template("_burbujas.html").render(
        burbujas=[
            {"autor": "usuario", "html": renderizar_texto(texto_limpio)},
            {"autor": "bot", "html": renderizar_texto(r.texto)},
        ]
    )
    resp = HTMLResponse(fragmento)
    resp.set_cookie("sid", sid, httponly=True, samesite="lax")
    return resp


@app.post("/reset", response_class=HTMLResponse)
def reset(sid: str | None = Cookie(default=None)):
    if sid:
        SESIONES.pop(sid, None)
        DB.borrar_sesion(sid)
    resp = HTMLResponse('<meta http-equiv="refresh" content="0; url=/">')
    resp.delete_cookie("sid")
    return resp


@app.get("/health")
def health():
    """Healthcheck para monitoreo (UptimeRobot). Verifica DB accesible."""
    try:
        n = DB.contar("sesiones")
        return JSONResponse(
            {
                "status": "ok",
                "backend_llm": ROUTER.backend,
                "sesiones": n,
            }
        )
    except Exception as exc:  # pragma: no cover
        return JSONResponse(
            {"status": "error", "detalle": type(exc).__name__}, status_code=500
        )


# ============================================================================
# Arranque
# ============================================================================


def main() -> None:
    url = f"http://{config.host}:{config.puerto}"
    print("=" * 66)
    print(f"  Simulador web HIBRIDO KitraDep en {url}")
    print(f"  Backend LLM: {ROUTER.backend}  |  DB: {config.db_path}")
    print("  Ctrl+C para detener")
    print("=" * 66)
    if config.abrir_navegador:
        webbrowser.open(url)
    uvicorn.run(app, host=config.host, port=config.puerto, log_level="warning")


if __name__ == "__main__":
    main()
