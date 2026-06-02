FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e ".[dev]"

COPY . /app
