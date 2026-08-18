"""Notificaciones al staff de KitraDep.

Avisa al equipo cuando pasa algo relevante: un paciente completa un
agendamiento, el bot deriva a humano (handoff), o se detecta una urgencia.

El canal por ahora es email (SMTP). Es opcional: si no hay configuracion
SMTP en el entorno, las notificaciones se registran en consola/log en vez
de enviarse (modo desarrollo). Asi el bot nunca se cae por falta de SMTP.

Diseno extensible: agregar un canal nuevo (WhatsApp interno, Slack, etc.)
es agregar una funcion _enviar_por_X y llamarla en notificar().
"""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText

import guardrails
from config import config


def _enviar_email(asunto: str, cuerpo: str) -> bool:
    """Envia un email via SMTP. Devuelve True si se envio."""
    if not config.notificaciones_activas:
        return False
    msg = MIMEText(cuerpo, _charset="utf-8")
    msg["Subject"] = asunto
    msg["From"] = config.smtp_user
    msg["To"] = config.notif_email_to
    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=15) as server:
            server.starttls()
            server.login(config.smtp_user, config.smtp_password)
            server.send_message(msg)
        return True
    except Exception as exc:  # pragma: no cover - depende de red/SMTP
        print(f"[notificaciones] Error enviando email: {type(exc).__name__}: {exc}")
        return False


def notificar(asunto: str, cuerpo: str) -> None:
    """Notifica al staff. Usa email si esta configurado; si no, log a consola.

    El cuerpo se enmascara de PII antes de loguear en consola (no antes de
    enviar por email, ya que el staff necesita los datos reales del paciente).
    """
    enviado = _enviar_email(asunto, cuerpo)
    if not enviado:
        # Modo desarrollo: mostramos el aviso enmascarado en consola.
        seguro = guardrails.enmascarar_pii(cuerpo)
        print("\n" + "=" * 60)
        print(f"[NOTIFICACION AL STAFF - no enviada, SMTP no configurado]")
        print(f"Asunto: {asunto}")
        print(seguro)
        print("=" * 60 + "\n")


# ---- helpers de alto nivel para eventos tipicos ---------------------------


def aviso_agendamiento(datos: str) -> None:
    notificar(
        asunto="[KitraDep Bot] Nuevo agendamiento",
        cuerpo=f"Un paciente completo el agendamiento por el bot:\n\n{datos}",
    )


def aviso_handoff(sesion_id: str, contexto: str = "") -> None:
    notificar(
        asunto="[KitraDep Bot] Derivacion a humano",
        cuerpo=(
            f"El bot derivo una conversacion a atencion humana.\n"
            f"Sesion: {sesion_id}\n{contexto}"
        ),
    )


def aviso_urgencia(sesion_id: str, mensaje: str = "") -> None:
    notificar(
        asunto="[KitraDep Bot] POSIBLE URGENCIA detectada",
        cuerpo=(
            f"El bot detecto una posible urgencia y derivo a emergencias.\n"
            f"Sesion: {sesion_id}\nMensaje: {mensaje}"
        ),
    )
