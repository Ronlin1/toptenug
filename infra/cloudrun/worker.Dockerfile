FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY services/core/pyproject.toml ./pyproject.toml
RUN uv sync --no-dev
COPY services/core ./
ENTRYPOINT ["uv", "run", "toptenug"]
CMD ["--help"]
