FROM python:3.12-slim AS runtime
WORKDIR /app
COPY uds/ ./uds/
COPY grpc/ ./grpc/
COPY mtls/ ./mtls/
COPY connectors/ ./connectors/
COPY agent.py wal_local.py ./
ENV PYTHONPATH=/app
ENV BRLIA_UDS_PATH=/var/run/brlia/pool.sock
CMD ["python", "agent.py"]
