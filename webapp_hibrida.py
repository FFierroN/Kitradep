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

import hashlib
import hmac
import re
import uuid
import webbrowser
from html import escape
from pathlib import Path

import uvicorn
from fastapi import Cookie, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import guardrails
import notificaciones
from config import config
from db import Database
from ratelimit import MENSAJE_LIMITE, RateLimiter
from router import Router, SesionChat
from whatsapp_webhook import crear_router_webhook

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
# Clave de acceso (solo si SIMULADOR_CLAVE esta configurada, ej: en Vercel)
# ============================================================================

PAGINA_CLAVE = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KitraDep - Acceso</title><style>
body{margin:0;min-height:100vh;display:grid;place-items:center;font-family:-apple-system,Segoe UI,Roboto,sans-serif;
background:linear-gradient(160deg,#0f1c1a,#13211f 50%,#0b1413);color:#e9f5f2}
form{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);padding:32px;border-radius:20px;width:300px;text-align:center}
.logo{width:52px;height:52px;border-radius:14px;margin:0 auto 14px;display:grid;place-items:center;font-weight:700;font-size:22px;
background:linear-gradient(135deg,#25d366,#128c7e)}
h1{font-size:20px;margin:0 0 6px}p{font-size:13px;color:#9fc2bb;margin:0 0 18px}
input{width:100%;box-sizing:border-box;padding:12px 14px;border-radius:12px;border:1px solid rgba(255,255,255,.2);
background:rgba(0,0,0,.25);color:#fff;font-size:15px;outline:none}
button{margin-top:12px;width:100%;padding:12px;border:none;border-radius:12px;background:#25d366;color:#fff;font-size:15px;font-weight:600;cursor:pointer}
.error{color:#ff8a80;font-size:13px;margin-top:10px}</style></head><body>
<form method="get"><div class="logo">K</div><h1>Simulador de Kitra</h1>
<p>Ingresa la clave que te compartió el equipo de KitraDep.</p>
<input name="clave" type="password" placeholder="Clave de acceso" autofocus required>
<button type="submit">Entrar</button>__ERROR__</form></body></html>"""


def _firma_acceso(clave: str) -> str:
    """Valor de la cookie: un hash, para no guardar la clave tal cual."""
    return hashlib.sha256(f"kitradep:{clave}".encode()).hexdigest()


@app.middleware("http")
async def exigir_clave(request: Request, call_next):
    clave = config.simulador_clave
    if not clave or request.url.path == "/health":
        return await call_next(request)

    esperada = _firma_acceso(clave)
    if hmac.compare_digest(request.cookies.get("acceso", ""), esperada):
        return await call_next(request)

    intento = request.query_params.get("clave")
    if intento is not None and hmac.compare_digest(intento, clave):
        resp = RedirectResponse(request.url.path, status_code=303)
        resp.set_cookie("acceso", esperada, max_age=60 * 60 * 24 * 30,
                        httponly=True, samesite="lax")
        return resp

    error = '<div class="error">Clave incorrecta</div>' if intento is not None else ""
    return HTMLResponse(PAGINA_CLAVE.replace("__ERROR__", error), status_code=401)


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


def _obtener_sesion(sid: str | None, canal: str = "web") -> tuple[str, SesionChat]:
    """Devuelve (sid, SesionChat), rehidratando historial desde la DB."""
    if sid and sid in SESIONES:
        return sid, SESIONES[sid]

    if not sid:
        sid = uuid.uuid4().hex

    sesion = SesionChat()
    # Rehidratar memoria desde la DB (si la sesion ya existia).
    sesion.historial = DB.cargar_historial(sid, limite=config.max_turnos_memoria)
    SESIONES[sid] = sesion
    DB.asegurar_sesion(sid, canal=canal)
    return sid, sesion


def procesar_mensaje(sid: str, sesion: SesionChat, texto: str) -> str:
    """Pipeline comun a todos los canales (web, WhatsApp).

    Rate limit -> router -> persistencia -> auditoria/notificaciones.
    Devuelve el texto de respuesta del bot.
    """
    # Rate limiting anti-abuso.
    if not LIMITER.permitido(sid):
        DB.registrar_evento("rate_limit", "sesion excedio limite", sesion_id=sid)
        return MENSAJE_LIMITE

    # Procesar via router.
    r = ROUTER.manejar_detallado(sesion, texto)

    # Persistir.
    DB.guardar_mensaje(sid, "user", texto)
    DB.guardar_mensaje(sid, "assistant", r.texto)

    # Auditoria + notificaciones segun el riesgo detectado.
    if r.riesgo is not guardrails.Riesgo.NINGUNO:
        DB.registrar_evento("guardrail", f"{r.riesgo.value}: {texto}", sesion_id=sid)
    if r.notificar_staff:
        if r.riesgo is guardrails.Riesgo.EMERGENCIA:
            notificaciones.aviso_urgencia(sid, texto)
        elif r.riesgo is guardrails.Riesgo.HANDOFF:
            notificaciones.aviso_handoff(sid)
        elif r.datos_agendamiento:
            notificaciones.aviso_agendamiento(r.datos_agendamiento)
            DB.registrar_evento("agendamiento", "paciente completo datos", sesion_id=sid)

    return r.texto


def procesar_whatsapp(sid: str, texto: str) -> str:
    """Adaptador para el webhook: una sesion por numero de telefono."""
    sid, sesion = _obtener_sesion(sid, canal="whatsapp")
    return procesar_mensaje(sid, sesion, texto)


app.include_router(
    crear_router_webhook(
        procesar=procesar_whatsapp,
        auth_token=config.twilio_auth_token,
        url_publica=config.webhook_url_publica,
    )
)


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

    respuesta = procesar_mensaje(sid, sesion, texto_limpio)

    fragmento = TEMPLATES.get_template("_burbujas.html").render(
        burbujas=[
            {"autor": "usuario", "html": renderizar_texto(texto_limpio)},
            {"autor": "bot", "html": renderizar_texto(respuesta)},
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
