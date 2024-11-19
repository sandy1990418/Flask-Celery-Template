FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    sqlite3\
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/db
RUN mkdir -p /app/src

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY config.yaml .
COPY db/. ./db/
COPY src/. ./src/
COPY .git .
COPY .pre-commit-config.yaml .

ENV PYTHONPATH=/app

RUN find /app/db -name "*.db" -type f -delete

RUN chmod -R 777 /app/db
