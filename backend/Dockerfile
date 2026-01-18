# Use official Python runtime as base image
FROM python:3.12-slim

# Set working directory in container
WORKDIR /app

# System deps
# - curl is used by the container healthcheck
# - unixodbc(*) is needed for pyodbc (kept for optional MSSQL support)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        unixodbc \
        unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Optional: install Microsoft ODBC driver (only needed when DB_ENGINE=mssql).
# Default is off because AWS deployments typically use MySQL (DB_ENGINE=mysql).
ARG INSTALL_MSSQL_ODBC=false
RUN if [ "$INSTALL_MSSQL_ODBC" = "true" ]; then \
        set -eux; \
        apt-get update; \
        apt-get install -y --no-install-recommends gnupg; \
        curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg; \
        curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list; \
        apt-get update; \
        ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18; \
        apt-get clean; \
        rm -rf /var/lib/apt/lists/*; \
    fi

# Copy requirements first for better Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance directory for SQLite
RUN mkdir -p instance

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/stats || exit 1

# Run the application
CMD ["python", "run.py"]
