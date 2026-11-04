"""Punto de entrada para Vercel.

Vercel busca la app FastAPI en archivos con nombres estandar (app.py,
main.py, index.py...). Aca solo re-exportamos la webapp hibrida, que es la
que usa el simulador. En el PC y en el servidor AWS se sigue corriendo
`python webapp_hibrida.py` como siempre.
"""

from webapp_hibrida import app  # noqa: F401
