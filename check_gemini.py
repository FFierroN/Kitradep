"""Diagnostico de Gemini: verifica la key y lista los modelos disponibles.

Util cuando el bot devuelve 'NotFound' o 'API key not valid': te dice si la
key es valida y QUE modelos acepta tu cuenta, para poner uno correcto en
GEMINI_MODEL (los nombres de modelo cambian y algunos se retiran).

Uso (con el .venv activo y el .env con tu GEMINI_API_KEY):
    python check_gemini.py
"""

import os

from dotenv import load_dotenv

load_dotenv()
import google.generativeai as genai

key = os.getenv("GEMINI_API_KEY", "")
print("Key detectada:", (key[:6] + "..." + key[-4:]) if key else "VACIA")
print("Largo de la key:", len(key))
print("Modelo en .env:", os.getenv("GEMINI_MODEL", "(no seteado)"))

genai.configure(api_key=key)
print("\n--- Modelos que tu key PUEDE usar (soportan generateContent) ---")
try:
    for m in genai.list_models():
        if "generateContent" in getattr(m, "supported_generation_methods", []):
            print("  ", m.name)
except Exception as e:  # noqa: BLE001 - queremos ver el error real
    print("ERROR:", type(e).__name__, "-", e)
