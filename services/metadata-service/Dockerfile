FROM python:3.11-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Base deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        unixodbc \
        unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Optional: install Microsoft ODBC driver (only needed when DB_ENGINE=mssql)
ARG INSTALL_MSSQL_ODBC=false
RUN if [ "$INSTALL_MSSQL_ODBC" = "true" ]; then \
        set -eux; \
        apt-get update; \
        apt-get install -y --no-install-recommends gnupg; \
        curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg; \
        echo "deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list; \
        apt-get update; \
        ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18; \
        apt-get clean; \
        rm -rf /var/lib/apt/lists/*; \
    fi

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 5002

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

CMD ["python", "app/metadata_service.py"]
