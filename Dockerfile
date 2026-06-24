# ---- Build stage ----
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

RUN pip install --no-cache-dir build && \
    python -m build --wheel && \
    python -m build --sdist

# ---- Runtime stage ----
FROM python:3.12-slim

RUN groupadd -r kuksa && useradd -r -g kuksa -d /app -s /sbin/nologin kuksa

WORKDIR /app

COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

USER kuksa

EXPOSE 8765

ENTRYPOINT ["kuksa-mcp"]
CMD []
