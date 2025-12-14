FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app


RUN apt-get update \
 && apt-get install -y --no-install-recommends procps curl \
 && rm -rf /var/lib/apt/lists/*

# poetry
RUN pip install --no-cache-dir poetry

# deps (кешируется слоем)
COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-root

# code
COPY . /app