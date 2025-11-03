FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libcairo2 libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY agents/core/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY agents/core ./core
COPY agents/cover_letter ./cover_letter
COPY templates ./templates
COPY prompts ./prompts

RUN mkdir -p /app/outputs/cover_letters

EXPOSE 8004
CMD ["uvicorn", "cover_letter.main:app", "--host", "0.0.0.0", "--port", "8004", "--workers", "2"]
