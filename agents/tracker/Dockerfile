FROM python:3.12-slim

WORKDIR /app

COPY agents/core/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY agents/core ./core
COPY agents/tracker ./tracker

EXPOSE 8006
CMD ["uvicorn", "tracker.main:app", "--host", "0.0.0.0", "--port", "8006", "--workers", "2"]
