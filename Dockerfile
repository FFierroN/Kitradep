# Dockerfile del bot KitraDep (webapp hibrida)
# ----------------------------------------------------------------------------
# Build:  docker build -t kitradep-bot .
# Run:    docker run -p 8765:8765 --env-file .env -v kitradep_data:/app/data kitradep-bot
# ----------------------------------------------------------------------------

FROM python:3.12-slim

# No generar .pyc, output sin buffer (mejores logs en contenedor).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PUERTO=8765 \
    ABRIR_NAVEGADOR=0

WORKDIR /app

# Instalar dependencias primero (mejor cache de capas).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del codigo.
COPY . .

# Carpeta de datos persistente (montar como volumen).
RUN mkdir -p /app/data

EXPOSE 8765

# Healthcheck nativo de Docker (complementa a UptimeRobot).
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8765/health').status==200 else 1)"

CMD ["python", "webapp_hibrida.py"]
