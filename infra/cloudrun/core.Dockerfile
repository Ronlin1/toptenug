FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY services/core/pyproject.toml ./pyproject.toml
RUN uv sync --no-dev
COPY services/core ./
ENV PORT=8080
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
