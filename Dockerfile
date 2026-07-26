FROM ghcr.io/astral-sh/uv:0.11.32 AS uv

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=uv /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY . .
RUN DJANGO_DEBUG=false \
    DJANGO_SECRET_KEY=build-only-not-used-at-runtime \
    python manage.py collectstatic --noinput

RUN mkdir -p /app/media \
    && addgroup --system internflow \
    && adduser --system --ingroup internflow internflow \
    && chown -R internflow:internflow /app

USER internflow

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
