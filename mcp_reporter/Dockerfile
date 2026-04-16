ARG BUILD_FROM=ghcr.io/home-assistant/base:latest
FROM ${BUILD_FROM}

WORKDIR /app

RUN apk add --no-cache python3 py3-pip

COPY app/pyproject.toml app/README.md /app/
COPY app/src /app/src

RUN pip3 install --break-system-packages --no-cache-dir /app

COPY rootfs /

RUN chmod +x /etc/services.d/mcp-report/run
