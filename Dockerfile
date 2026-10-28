FROM python:3.11-slim

# ecCodes C library: needed to read GRIB files
RUN apt-get update \
 && apt-get install -y --no-install-recommends libeccodes0 \
 && rm -rf /var/lib/apt/lists/*

# dbt in its own virtual environment, so its dependencies never clash with ours
RUN python -m venv /opt/dbt-venv \
 && /opt/dbt-venv/bin/pip install --no-cache-dir dbt-postgres==1.7.9

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a normal user, not root (good security practice)
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "scripts.scheduler"]