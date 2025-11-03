FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libcairo2 libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY agents/core/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY agents/core ./core
COPY agents/cv_generator ./cv_generator
COPY templates ./templates
COPY prompts ./prompts

RUN mkdir -p /app/outputs/cvs

EXPOSE 8003
CMD ["uvicorn", "cv_generator.main:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "2"]
