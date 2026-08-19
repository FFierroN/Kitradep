"""Tests del flujo de agendamiento (recolector determinista).

Cubre: deteccion de intencion, validacion de campos (RUT modulo 11, email,
telefono, prevision, franja), reintentos ante datos invalidos, cancelacion,
y la integracion end-to-end via el Router (con FakeLLM, offline).

Uso:
    python test_agendamiento.py
"""

from __future__ import annotations

import os

os.environ["LLM_BACKEND"] = "fake"

import agendamiento
from agendamiento import Agendamiento
from router import Router, SesionChat


def _check(cond: bool, desc: str) -> int:
    print(f"  {'OK ' if cond else 'XX '} {desc}")
    return int(cond)


def test_intencion() -> tuple[int, int]:
    print("\n=== TEST: Deteccion de intencion de agendar ===")
    positivos = [
        "quiero agendar",
        "si, quiero una hora",
        "me agendas una sesion?",
        "necesito agendar mi evaluacion",
        "dale, agendemos",
        "quiero sacar hora",
    ]
    negativos = [
        "a que hora atienden?",
        "cuanto cuesta?",
        "hola buenas",
        "me duele la rodilla",
        "donde quedan?",
    ]
    ok = 0
    for m in positivos:
        ok += _check(agendamiento.detectar_intencion(m), f"intencion SI: {m!r}")
    for m in negativos:
        ok += _check(not agendamiento.detectar_intencion(m), f"intencion NO: {m!r}")
    total = len(positivos) + len(negativos)
    print(f"  -> {ok}/{total} correctos")
    return ok, total


def test_validaciones() -> tuple[int, int]:
    print("\n=== TEST: Validacion y normalizacion de campos ===")
    ok = 0
    total = 0

    casos = [
        # (funcion, valor, es_valido)
        (agendamiento._validar_nombre, "Juan Perez", True),
        (agendamiento._validar_nombre, "Juan", False),
        (agendamiento._validar_nombre, "Juan3 Perez", False),
        (agendamiento._validar_rut, "12.345.678-5", True),   # DV valido
        (agendamiento._validar_rut, "12.345.678-9", False),  # DV invalido
        (agendamiento._validar_rut, "hola", False),
        (agendamiento._validar_correo, "juan@gmail.com", True),
        (agendamiento._validar_correo, "juan@", False),
        (agendamiento._validar_fono, "9 1234 5678", True),
        (agendamiento._validar_fono, "12345", False),
        (agendamiento._validar_prevision, "tengo isapre", True),
        (agendamiento._validar_prevision, "no se", False),
        (agendamiento._validar_franja, "en la tarde", True),
        (agendamiento._validar_franja, "cuando sea", False),
    ]
    for fn, valor, valido in casos:
        total += 1
        resultado_ok = (fn(valor) is None) == valido
        ok += _check(resultado_ok, f"{fn.__name__}({valor!r}) valido={valido}")

    # Normalizaciones clave.
    total += 1
    ok += _check(agendamiento._norm_rut("123456785") == "12.345.678-5",
                 "normaliza RUT con puntos y guion")
    total += 1
    ok += _check(agendamiento._norm_prevision("con fonasa") == "FONASA",
                 "normaliza prevision a etiqueta")
    total += 1
    ok += _check(agendamiento._norm_franja("mañana temprano").startswith("Manana"),
                 "normaliza franja a AM")

    print(f"  -> {ok}/{total} correctos")
    return ok, total


def test_flujo_completo() -> tuple[int, int]:
    print("\n=== TEST: Recolector end-to-end (feliz + reintento) ===")
    ok = 0
    total = 0

    ag = Agendamiento()
    primera = ag.iniciar()
    total += 1
    ok += _check("nombre" in primera.lower(), "primera pregunta pide nombre")

    # Nombre invalido -> repite; luego valido.
    r = ag.procesar("Juan")
    total += 1
    ok += _check(not r.completado and "nombre" in r.texto.lower(),
                 "nombre invalido repite la pregunta")
    r = ag.procesar("Juan Perez")
    total += 1
    ok += _check("rut" in r.texto.lower(), "tras nombre valido pide RUT")

    # RUT invalido -> repite; luego valido.
    r = ag.procesar("12.345.678-9")
    total += 1
    ok += _check("rut" in r.texto.lower() and not r.completado,
                 "RUT invalido repite la pregunta")
    r = ag.procesar("12.345.678-5")
    total += 1
    ok += _check("correo" in r.texto.lower(), "tras RUT valido pide correo")

    r = ag.procesar("juan@gmail.com")
    r = ag.procesar("9 1234 5678")
    total += 1
    ok += _check("prevision" in r.texto.lower(), "tras telefono pide prevision")
    r = ag.procesar("tengo isapre")
    total += 1
    ok += _check("manana" in r.texto.lower() or "tarde" in r.texto.lower(),
                 "tras prevision pide franja")
    r = ag.procesar("en la tarde")

    total += 1
    ok += _check(r.completado, "flujo completado")
    total += 1
    ok += _check(r.datos_staff is not None
                 and "12.345.678-5" in r.datos_staff
                 and "ISAPRE" in r.datos_staff,
                 "resumen para staff con datos normalizados")

    # Cancelacion.
    ag2 = Agendamiento()
    ag2.iniciar()
    r = ag2.procesar("cancelar")
    total += 1
    ok += _check(r.cancelado and not r.completado, "cancelacion aborta el flujo")

    print(f"  -> {ok}/{total} correctos")
    return ok, total


def test_router_integracion() -> tuple[int, int]:
    print("\n=== TEST: Integracion via Router (guardrails + agenda + LLM) ===")
    ok = 0
    total = 0
    router = Router.crear(handoff_contacto="Javiera")
    sesion = SesionChat()

    # Conversacion normal -> LLM, sin agenda.
    router.manejar_detallado(sesion, "hola")
    total += 1
    ok += _check(sesion.agenda is None, "saludo no dispara agendamiento")

    # Intencion -> arranca recoleccion.
    r = router.manejar_detallado(sesion, "quiero agendar una hora")
    total += 1
    ok += _check(sesion.agenda is not None and "nombre" in r.texto.lower(),
                 "intencion arranca la recoleccion")

    # Completar datos.
    for msg in ["Ana Soto", "11.111.111-1", "ana@correo.cl",
                "9 8765 4321", "particular", "manana"]:
        r = router.manejar_detallado(sesion, msg)
    total += 1
    ok += _check(r.notificar_staff and r.datos_agendamiento is not None,
                 "al completar, notifica al staff con datos")
    total += 1
    ok += _check(sesion.agenda is None, "recolector se cierra al completar")

    # Guardrail de emergencia aborta una agenda en curso.
    sesion2 = SesionChat()
    router.manejar_detallado(sesion2, "quiero agendar")
    total += 1
    ok += _check(sesion2.agenda is not None, "agenda iniciada")
    r = router.manejar_detallado(sesion2, "me cai y no puedo mover la pierna")
    total += 1
    ok += _check(sesion2.agenda is None and r.riesgo.value == "emergencia",
                 "emergencia aborta la agenda en curso")

    print(f"  -> {ok}/{total} correctos")
    return ok, total


def main() -> None:
    print("=" * 66)
    print("  TEST SUITE - Agendamiento KitraDep (offline)")
    print("=" * 66)
    total_ok = 0
    total = 0
    for fn in (test_intencion, test_validaciones,
               test_flujo_completo, test_router_integracion):
        o, n = fn()
        total_ok += o
        total += n
    print("\n" + "=" * 66)
    print(f"  RESULTADO GLOBAL: {total_ok}/{total} checks OK")
    print("=" * 66)
    if total_ok != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
