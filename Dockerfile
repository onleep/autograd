FROM python:3.12-slim

ARG APP_NAME
WORKDIR /app
ENV PYTHONPATH=src

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
RUN pip install uv --no-cache-dir

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --extra $APP_NAME

COPY .env .
COPY src/$APP_NAME src/app
COPY src/clients src/clients
COPY src/config.py src/config.py

CMD ["uv", "run", "-m", "app.main"]
