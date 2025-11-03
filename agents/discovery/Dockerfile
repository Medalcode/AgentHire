FROM python:3.12-slim

# Instalar dependencias del sistema para WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements del core y del agente
COPY agents/core/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copiar código
COPY agents/core ./core
COPY agents/discovery ./discovery
COPY connectors ./connectors
COPY templates ./templates
COPY prompts ./prompts

RUN mkdir -p /app/outputs/cvs /app/outputs/cover_letters /app/outputs/screenshots

EXPOSE 8001

CMD ["uvicorn", "discovery.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
