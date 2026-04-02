FROM python:3.12-slim

ARG APP_NAME
WORKDIR /app
ENV PYTHONPATH=src UV_LINK_MODE=copy APP_NAME=$APP_NAME

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
RUN pip install uv --no-cache-dir

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --extra $APP_NAME

COPY .env .
COPY src/$APP_NAME src/app
COPY src/clients src/clients
COPY src/config.py src/config.py

CMD sh -c 'if [ "$APP_NAME" = "frontend" ]; then \
    exec streamlit run src/frontend/main.py; else \
    exec uv run -m app.main; fi'
