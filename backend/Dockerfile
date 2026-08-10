FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY worker ./worker
COPY alembic.ini ./
COPY alembic ./alembic

RUN pip install --no-cache-dir .

FROM base AS development

RUN pip install --no-cache-dir ".[dev]"

COPY tests ./tests

FROM base AS production

RUN addgroup --system app && adduser --system --ingroup app app

USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
