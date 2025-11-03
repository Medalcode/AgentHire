FROM python:3.12-slim

WORKDIR /app

COPY agents/core/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY agents/core ./core
COPY agents/apply ./apply
COPY connectors ./connectors
COPY templates ./templates

RUN mkdir -p /app/outputs/screenshots

EXPOSE 8005
CMD ["uvicorn", "apply.main:app", "--host", "0.0.0.0", "--port", "8005", "--workers", "1"]
