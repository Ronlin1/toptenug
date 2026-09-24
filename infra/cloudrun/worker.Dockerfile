FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY services/core/pyproject.toml ./pyproject.toml
RUN uv sync --no-dev --no-install-project
COPY services/core ./
RUN uv sync --no-dev
ENTRYPOINT ["uv","run","toptenug"]
