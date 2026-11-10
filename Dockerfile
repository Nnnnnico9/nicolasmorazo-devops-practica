# Imagen de la API REST de la Tienda Online (Práctica 2)
FROM python:3.12-slim

# Evita ficheros .pyc y fuerza que los logs salgan sin buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# 1) Dependencias primero: esta capa se cachea mientras requirements.txt no cambie
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Código fuente
COPY src/ ./src/

# 3) Usuario sin privilegios propietario del código, con permisos de lectura/ejecución
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app \
    && chmod -R u+rwX,go-w /app
USER appuser

WORKDIR /app/src/Tienda_online
EXPOSE 8000

# 4) Comando de inicio: escucha en todas las interfaces para ser accesible desde fuera
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
