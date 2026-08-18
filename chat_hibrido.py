"""CLI para probar el router hibrido en la terminal.

Usa el backend LLM que indique la variable de entorno LLM_BACKEND:
    LLM_BACKEND=fake    (default) -> respuestas simuladas, sin internet
    LLM_BACKEND=gemini            -> Gemini real (requiere GEMINI_API_KEY)

Uso:
    python chat_hibrido.py
    LLM_BACKEND=gemini python chat_hibrido.py   (en tu PC personal)
"""

from __future__ import annotations

import sys

from router import Router, SesionChat


def main() -> None:
    print("=" * 66)
    router = Router.crear(handoff_contacto="Javiera (nuestra kine)")
    print(f"  Chat hibrido KitraDep - backend LLM: {router.backend}")
    print("  Escribi 'salir' para terminar.")
    print("=" * 66)

    sesion = SesionChat()

    # Saludo inicial del bot.
    saludo = router.manejar(sesion, "hola")
    print(f"\nKitra> {saludo}\n")

    while True:
        try:
            entrada = input("Tu> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nKitra> Que estes muy bien. Hasta pronto!")
            break

        if entrada.lower() in {"salir", "exit", "quit", "chao"}:
            print("Kitra> Que estes muy bien. Hasta pronto!")
            break

        if not entrada:
            continue

        respuesta = router.manejar(sesion, entrada)
        print(f"\nKitra> {respuesta}\n")


if __name__ == "__main__":
    sys.exit(main())
