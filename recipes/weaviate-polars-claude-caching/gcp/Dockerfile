# Multi-stage Sovereign Production Dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runner

WORKDIR /app
# Security: Run as unprivileged non-root user
RUN addgroup --system --gid 1001 appgroup && adduser --system --uid 1001 --ingroup appgroup appuser

COPY --from=builder /root/.local /home/appuser/.local
COPY pipeline.py sample_data.csv ./

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    DATA_RESIDENCY=europe-west4

USER appuser

EXPOSE 8080
CMD ["python", "pipeline.py"]

