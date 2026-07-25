FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for WeasyPrint/cairo if needed
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY agents/core/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all agents code
COPY agents /app/agents

# Run from inside agents/ so it can import core, discovery, etc.
WORKDIR /app/agents
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
