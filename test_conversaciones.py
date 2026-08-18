"""Test suite de conversaciones del router hibrido.

Corre una bateria de mensajes contra el Router usando el FakeLLM (offline)
y verifica que los guardrails y el pipeline funcionan. NO necesita internet
ni API key.

Uso:
    python test_conversaciones.py
"""

from __future__ import annotations

import os

# Forzamos backend fake para tests deterministas y offline.
os.environ["LLM_BACKEND"] = "fake"

import guardrails
from router import Router, SesionChat


# ============================================================================
# Casos de guardrails: (mensaje, riesgo esperado)
# ============================================================================

CASOS_GUARDRAIL = [
    ("me cai y no puedo mover la pierna", guardrails.Riesgo.EMERGENCIA),
    ("tengo un dolor insoportable en la rodilla", guardrails.Riesgo.EMERGENCIA),
    ("me duele la rodilla, sera menisco?", guardrails.Riesgo.MEDICO),
    ("que ejercicios me recomiendas para la espalda?", guardrails.Riesgo.MEDICO),
    ("quiero hablar con una persona", guardrails.Riesgo.HANDOFF),
    ("eres un bot?", guardrails.Riesgo.HANDOFF),
    ("que opinas del futbol?", guardrails.Riesgo.FUERA_TEMA),
    ("cuanto cuesta una sesion?", guardrails.Riesgo.NINGUNO),
    ("hola buenas tardes", guardrails.Riesgo.NINGUNO),
    ("a que hora atienden los sabados?", guardrails.Riesgo.NINGUNO),
]


# ============================================================================
# Casos de PII: (texto, debe_contener_marcador)
# ============================================================================

CASOS_PII = [
    ("mi rut es 12.345.678-9", "[RUT]"),
    ("llamame al +56 9 1234 5678", "[FONO]"),
    ("mi correo es juan@gmail.com", "[EMAIL]"),
]


def test_guardrails() -> tuple[int, int]:
    print("\n=== TEST: Guardrails (deteccion de riesgo) ===")
    ok = 0
    for mensaje, esperado in CASOS_GUARDRAIL:
        v = guardrails.evaluar(mensaje)
        passed = v.riesgo is esperado
        ok += passed
        marca = "OK " if passed else "XX "
        print(f"  {marca} [{v.riesgo.value:11}] (esperado: {esperado.value:11}) <- {mensaje}")
    print(f"  -> {ok}/{len(CASOS_GUARDRAIL)} correctos")
    return ok, len(CASOS_GUARDRAIL)


def test_pii() -> tuple[int, int]:
    print("\n=== TEST: Enmascarado de PII ===")
    ok = 0
    for texto, marcador in CASOS_PII:
        enmascarado = guardrails.enmascarar_pii(texto)
        passed = marcador in enmascarado
        ok += passed
        marca = "OK " if passed else "XX "
        print(f"  {marca} {texto!r} -> {enmascarado!r}")
    print(f"  -> {ok}/{len(CASOS_PII)} correctos")
    return ok, len(CASOS_PII)


def test_pipeline_completo() -> tuple[int, int]:
    print("\n=== TEST: Pipeline completo (router + FakeLLM + memoria) ===")
    router = Router.crear(handoff_contacto="Javiera")
    sesion = SesionChat()

    guion_prueba = [
        "hola",
        "cuanto cuesta la kinesiologia?",
        "tengo isapre",
        "a que hora atienden?",
        "me duele mucho, sera grave?",   # debe disparar guardrail medico
        "quiero hablar con alguien",     # debe disparar handoff
        "gracias!",
    ]

    ok = 0
    for msg in guion_prueba:
        respuesta = router.manejar(sesion, msg)
        tiene_respuesta = bool(respuesta and respuesta.strip())
        ok += tiene_respuesta
        marca = "OK " if tiene_respuesta else "XX "
        print(f"  {marca} Tu> {msg}")
        print(f"      Kitra> {respuesta}")
    print(f"  -> {ok}/{len(guion_prueba)} turnos con respuesta")
    print(f"  -> memoria acumulada: {len(sesion.historial)} turnos")
    return ok, len(guion_prueba)


def main() -> None:
    print("=" * 66)
    print("  TEST SUITE - Chatbot KitraDep (backend: FakeLLM, offline)")
    print("=" * 66)

    total_ok = 0
    total = 0
    for fn in (test_guardrails, test_pii, test_pipeline_completo):
        ok, n = fn()
        total_ok += ok
        total += n

    print("\n" + "=" * 66)
    print(f"  RESULTADO GLOBAL: {total_ok}/{total} checks OK")
    print("=" * 66)
    if total_ok != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
