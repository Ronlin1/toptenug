FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY services/core/pyproject.toml ./pyproject.toml
RUN uv sync --no-dev --no-install-project
COPY services/core ./
RUN uv sync --no-dev
EXPOSE 8080
CMD ["uv","run","fastapi","run","app/main.py","--host","0.0.0.0","--port","8080"]
