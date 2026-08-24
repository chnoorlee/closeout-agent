FROM node:24-alpine AS frontend-build

WORKDIR /workspace/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PORT=8080

WORKDIR /app
RUN addgroup --system closeout && adduser --system --ingroup closeout closeout

COPY --from=ghcr.io/astral-sh/uv:0.11.2 /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md ./
COPY backend ./backend
COPY --from=frontend-build /workspace/backend/static ./backend/static
RUN uv sync --locked --no-dev --no-editable --no-cache

ENV PATH="/app/.venv/bin:$PATH"

USER closeout
EXPOSE 8080

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
