FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY ../requirements.txt .
COPY ../.env .
COPY ../run.py .
COPY ../config.yaml .
COPY ../src/. ./src/

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

CMD ["python", "run.py"]
