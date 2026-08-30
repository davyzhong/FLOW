FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.10 /uv /usr/local/bin/uv
WORKDIR /app
COPY services/api/pyproject.toml services/api/uv.lock ./
COPY services/api/src ./src
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"
RUN useradd --create-home --uid 10001 flow && chown -R flow:flow /app
USER flow
CMD ["uvicorn", "flow_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
