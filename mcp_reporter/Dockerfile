ARG BUILD_FROM
FROM ${BUILD_FROM}

WORKDIR /app

COPY app/pyproject.toml app/README.md /app/
COPY app/src /app/src

RUN pip install --no-cache-dir /app

COPY rootfs /

RUN chmod +x /etc/services.d/mcp-report/run
