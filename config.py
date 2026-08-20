"""Configuracion centralizada del bot.

Lee variables de entorno (y opcionalmente un archivo .env) y las expone
como un objeto tipado. Un solo lugar para toda la config: nada de os.getenv
desperdigado por el codigo (principio DRY).

Si python-dotenv esta instalado, carga .env automaticamente. Si no, usa
solo las variables de entorno del sistema (util en produccion/Docker).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).parent


def _cargar_dotenv() -> None:
    """Carga .env si python-dotenv esta disponible. Silencioso si no."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)


_cargar_dotenv()


def _bool(valor: str | None, default: bool = False) -> bool:
    if valor is None:
        return default
    return valor.strip().lower() in {"1", "true", "yes", "si", "on"}


def _int(valor: str | None, default: int) -> int:
    try:
        return int(valor) if valor is not None else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Config:
    """Configuracion inmutable del bot, poblada desde el entorno."""

    # --- LLM ---
    llm_backend: str          # 'fake' | 'gemini'
    gemini_api_key: str
    gemini_model: str

    # --- Persistencia ---
    db_path: Path

    # --- Servidor web ---
    host: str
    puerto: int
    abrir_navegador: bool

    # --- Comportamiento del bot ---
    handoff_contacto: str
    max_turnos_memoria: int

    # --- Rate limiting (anti-abuso) ---
    rate_limit_mensajes: int   # mensajes permitidos...
    rate_limit_ventana_s: int  # ...por esta ventana de tiempo (segundos)

    # --- Notificaciones al staff ---
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    notif_email_to: str

    @classmethod
    def cargar(cls) -> "Config":
        return cls(
            llm_backend=os.getenv("LLM_BACKEND", "fake").lower().strip(),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            db_path=Path(os.getenv("DB_PATH", str(BASE_DIR / "data" / "kitradep.db"))),
            host=os.getenv("HOST", "127.0.0.1"),
            puerto=_int(os.getenv("PUERTO"), 8765),
            abrir_navegador=_bool(os.getenv("ABRIR_NAVEGADOR"), True),
            handoff_contacto=os.getenv("HANDOFF_CONTACTO", "nuestro equipo"),
            max_turnos_memoria=_int(os.getenv("MAX_TURNOS_MEMORIA"), 20),
            rate_limit_mensajes=_int(os.getenv("RATE_LIMIT_MENSAJES"), 30),
            rate_limit_ventana_s=_int(os.getenv("RATE_LIMIT_VENTANA_S"), 60),
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=_int(os.getenv("SMTP_PORT"), 587),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            notif_email_to=os.getenv("NOTIF_EMAIL_TO", ""),
        )

    @property
    def notificaciones_activas(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.notif_email_to)


# Instancia global (se carga una vez al importar).
config = Config.cargar()
