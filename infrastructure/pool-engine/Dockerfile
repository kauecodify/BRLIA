# Estagio 1: nucleo Rust estatico e extensao PyO3
FROM rust:1.83-slim AS core-builder
WORKDIR /build
COPY core/ ./core/
RUN cd core && cargo build --release

# Estagio 2: extensao Python (PyO3)
FROM python:3.12-slim AS pyo3-builder
RUN pip install --no-cache-dir maturin
WORKDIR /build
COPY core/ ./core/
COPY python/ ./python/
COPY pyproject.toml ./
RUN maturin build --release --interpreter python3

# Estagio 3: runtime
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=core-builder /build/core/target/release/ /opt/brlia/bin/
COPY --from=pyo3-builder /build/target/wheels/*.whl /opt/brlia/wheels/
RUN pip install --no-cache-dir /opt/brlia/wheels/*.whl \
    && pip install --no-cache-dir fastapi uvicorn pydantic>=2
COPY window/ ./window/
COPY netting/ ./netting/
COPY liquidity/ ./liquidity/
COPY clock/ ./clock/
COPY wal/ ./wal/
COPY backpressure/ ./backpressure/
COPY control/ ./control/
COPY publish/ ./publish/
ENV PYTHONPATH=/app
ENV BRLIA_CONTROL_SOCKET=/var/run/brlia/control.sock
EXPOSE 9100
CMD ["python", "-m", "control.server"]
