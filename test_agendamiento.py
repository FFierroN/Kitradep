"""Tests del flujo de agendamiento (recolector determinista).

Cubre: deteccion de intenciones (agendar, "si", "ya agende", "por aca"),
validacion de campos (RUT modulo 11, email, telefono, prevision, franja),
lectura de datos en un solo mensaje, cancelacion, el link de AgendaPro, el
control de invitaciones (no insistir) y la integracion via el Router
(con FakeLLM, offline).

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
    ok += _check(agendamiento._norm_franja("mañana temprano").startswith("Mañana"),
                 "normaliza franja a AM")

    print(f"  -> {ok}/{total} correctos")
    return ok, total


def test_detectores() -> tuple[int, int]:
    print("\n=== TEST: Detectores (si / ya agende / por aca / invitacion) ===")
    casos = [
        (agendamiento.es_afirmativo("Sí, dale!"), "'Sí, dale!' es afirmativo"),
        (agendamiento.es_afirmativo("ok"), "'ok' es afirmativo"),
        (not agendamiento.es_afirmativo("si, pero cuanto cuesta?"),
         "'si, pero cuanto cuesta?' NO es afirmativo (es pregunta)"),
        (not agendamiento.es_afirmativo("me duele la rodilla"), "dolor NO es afirmativo"),
        (agendamiento.ya_agendo("Listo, ya agendé para el martes"), "detecta 'ya agendé'"),
        (agendamiento.ya_agendo("listo!"), "detecta 'listo!'"),
        (not agendamiento.ya_agendo("quiero agendar"), "'quiero agendar' NO es 'ya agendé'"),
        (agendamiento.prefiere_chat("no me abre el link"), "detecta 'no me abre el link'"),
        (agendamiento.prefiere_chat("agéndame por aquí mejor"), "detecta 'por aquí' (con tilde)"),
        (agendamiento.es_invitacion("¿Te parece si agendamos tu evaluación? 📅"),
         "detecta invitación del bot"),
        (not agendamiento.es_invitacion("Estamos en San Miguel 📍"), "ubicación NO es invitación"),
        (agendamiento.quitar_invitacion("Atendemos hasta las 21 hrs. ¿Te gustaría agendar?")
         == "Atendemos hasta las 21 hrs.", "quita solo la frase de invitación"),
        (not agendamiento.hay_senal_interes("ahora me duele"), "'ahora' NO es señal de interés"),
        (agendamiento.hay_senal_interes("¿qué horarios tienen?"), "'horarios' SÍ es señal"),
        (agendamiento.detectar_intencion("Agéndame porfa"), "intención con tilde"),
    ]
    ok = sum(_check(c, d) for c, d in casos)
    print(f"  -> {ok}/{len(casos)} correctos")
    return ok, len(casos)


def test_recolector() -> tuple[int, int]:
    print("\n=== TEST: Datos en un solo mensaje ===")
    ok = 0
    total = 0

    ag = Agendamiento()
    lista = ag.iniciar()
    total += 1
    ok += _check(all(c.linea in lista for c in agendamiento.CAMPOS),
                 "la lista inicial trae todos los campos")

    # Plantilla completada, sin prevision.
    r = ag.procesar(
        "📝 Nombre: ana soto\n🆔 RUT: 11.111.111-1\n"
        "📧 Correo electrónico: ana@correo.cl\n📞 Número de contacto: 9 8765 4321\n"
        "🏥 Previsión de salud (Fonasa, Isapre, Particular):\n"
        "🏠 Dirección (opcional):\n🕐 ¿Prefieres mañana o tarde?: tarde"
    )
    total += 1
    ok += _check(not r.completado and "Previsión" in r.texto
                 and "Nombre" not in r.texto,
                 "plantilla incompleta -> pide SOLO lo que falta")
    r = ag.procesar("fonasa")
    total += 1
    ok += _check(r.completado, "con el dato faltante se completa")
    total += 1
    ok += _check(r.datos_staff is not None and "11.111.111-1" in r.datos_staff
                 and "FONASA" in r.datos_staff and "Ana Soto" in r.datos_staff
                 and "Dirección: -" in r.datos_staff,
                 "resumen para staff normalizado (dirección opcional vacía)")

    # Todo en una linea, sin rotulos.
    ag = Agendamiento()
    r = ag.procesar("Juan Pérez, 12.345.678-5, juan@gmail.com, +56 9 1234 5678, "
                    "isapre, en la mañana")
    total += 1
    ok += _check(r.completado and "Juan Pérez" in (r.datos_staff or "")
                 and "Mañana" in (r.datos_staff or ""),
                 "todo en una línea sin rótulos se entiende")

    # Datos invalidos -> avisa el error y no los guarda.
    ag = Agendamiento()
    r = ag.procesar("RUT: 12.345.678-9\nCorreo: juan@")
    total += 1
    ok += _check("RUT no me cuadra" in r.texto and "correo no parece" in r.texto
                 and "rut" not in ag.datos, "datos inválidos -> explica el error")

    # Un saludo no se confunde con un nombre.
    ag = Agendamiento()
    ag.procesar("buenas tardes")
    total += 1
    ok += _check("nombre" not in ag.datos, "'buenas tardes' NO se toma como nombre")

    ag = Agendamiento()
    r = ag.procesar("cancelar")
    total += 1
    ok += _check(r.cancelado and not r.completado, "cancelacion aborta el flujo")

    print(f"  -> {ok}/{total} correctos")
    return ok, total


def test_router_integracion() -> tuple[int, int]:
    print("\n=== TEST: Integracion via Router (link, datos, gracias) ===")
    ok = 0
    total = 0
    router = Router.crear(handoff_contacto="Javiera")

    # Pide agendar -> link de AgendaPro.
    s = SesionChat()
    router.manejar_detallado(s, "hola")
    r = router.manejar_detallado(s, "quiero agendar una hora")
    total += 1
    ok += _check(agendamiento.LINK_AGENDA in r.texto and s.link_enviado,
                 "intención -> envía link de AgendaPro")
    r = router.manejar_detallado(s, "listo, ya agendé")
    total += 1
    ok += _check("gracias por agendar" in r.texto.lower(),
                 "'ya agendé' -> agradecimiento + tips")

    # "Si" a una invitacion del bot -> link.
    s = SesionChat()
    router.manejar_detallado(s, "tengo fonasa")
    total += 1
    ok += _check(s.ultima_fue_invitacion, "el bot invitó (valores Fonasa)")
    r = router.manejar_detallado(s, "sí, dale")
    total += 1
    ok += _check(agendamiento.LINK_AGENDA in r.texto, "'sí' a la invitación -> link")

    # Prefiere por chat -> lista de datos -> completa -> notifica.
    r = router.manejar_detallado(s, "no me abre el link, me agendan por aquí?")
    total += 1
    ok += _check(s.agenda is not None and "RUT" in r.texto,
                 "'no me abre el link' -> pide datos en un mensaje")
    r = router.manejar_detallado(s, "¿y tienen estacionamiento?")
    total += 1
    ok += _check(s.agenda is not None and "RUT" not in r.texto,
                 "pregunta en medio -> responde sin perder el agendamiento")
    r = router.manejar_detallado(
        s, "Ana Soto, 11.111.111-1, ana@correo.cl, 9 8765 4321, particular, mañana")
    total += 1
    ok += _check(r.notificar_staff and r.datos_agendamiento is not None
                 and s.agenda is None, "al completar, notifica al staff y cierra")

    # Emergencia aborta un agendamiento en curso.
    s = SesionChat()
    router.manejar_detallado(s, "quiero agendar")
    router.manejar_detallado(s, "no puedo con el link")
    total += 1
    ok += _check(s.agenda is not None, "agendamiento por chat iniciado")
    r = router.manejar_detallado(s, "me cai y no puedo mover la pierna")
    total += 1
    ok += _check(s.agenda is None and r.riesgo.value == "emergencia",
                 "emergencia aborta la agenda en curso")

    print(f"  -> {ok}/{total} correctos")
    return ok, total


def test_no_insistir() -> tuple[int, int]:
    print("\n=== TEST: No insistir con agendar ===")
    ok = 0
    total = 0
    router = Router.crear(handoff_contacto="Javiera")
    s = SesionChat()

    r = router.manejar_detallado(s, "tengo fonasa")
    total += 1
    ok += _check(agendamiento.es_invitacion(r.texto), "1ra invitación permitida")

    # Sigue consultando sin responder a la invitacion. El FakeLLM invita
    # siempre que oye "isapre": el router debe impedirlo.
    invitaciones = 0
    for msg in ["donde quedan?", "y si tengo isapre tambien?", "atienden sabados?"]:
        r = router.manejar_detallado(s, msg)
        invitaciones += agendamiento.es_invitacion(r.texto)
    total += 1
    ok += _check(invitaciones == 0,
                 "no vuelve a invitar mientras el paciente sigue preguntando")
    total += 1
    ok += _check(s.invitaciones == 1, "contador de invitaciones = 1")

    # Despues de esperar, con señal de interés, puede volver a invitar.
    router.manejar_detallado(s, "tengo isapre")
    total += 1
    ok += _check(s.invitaciones == 2, "tras esperar 4 mensajes puede re-invitar")

    # Despues del link, nunca mas invita.
    s2 = SesionChat()
    router.manejar_detallado(s2, "quiero agendar")
    r = router.manejar_detallado(s2, "tengo isapre")
    total += 1
    ok += _check(not agendamiento.es_invitacion(r.texto),
                 "con el link ya enviado no vuelve a invitar")

    print(f"  -> {ok}/{total} correctos")
    return ok, total


def main() -> None:
    print("=" * 66)
    print("  TEST SUITE - Agendamiento KitraDep (offline)")
    print("=" * 66)
    total_ok = 0
    total = 0
    for fn in (test_intencion, test_validaciones, test_detectores,
               test_recolector, test_router_integracion, test_no_insistir):
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
