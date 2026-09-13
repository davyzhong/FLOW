FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.10 /uv /usr/local/bin/uv
RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium chromium-sandbox fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY services/api/pyproject.toml services/api/uv.lock ./
COPY services/api/src ./src
COPY services/api/config ./services/api/config
COPY services/api/migrations ./migrations
COPY services/api/alembic.ini ./alembic.ini
COPY templates/excel/flow_v1_contract.yaml ./templates/excel/flow_v1_contract.yaml
COPY config/intake ./config/intake
COPY config/metrics ./config/metrics
COPY config/statements ./config/statements
COPY config/analysis ./config/analysis
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH" \
    FLOW_CHROMIUM_PATH="/usr/bin/chromium" \
    FLOW_CHROMIUM_NO_SANDBOX="1"
RUN useradd --create-home --uid 10001 flow && chown -R flow:flow /app
USER flow
CMD ["uvicorn", "flow_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
