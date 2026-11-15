# pool-engine

Motor de janelas de 1 ms com netting multilateral. O hot path (admit -> ring
MPMC lock-free -> pool_id e close + netting -> pool.closed.v1) vive no nucleo
compilado em core/ (Rust com binding PyO3). FastAPI atende somente /health,
/ready, /metrics e /config em socket de controle separado.

## Diretorios

- core/: nucleo Rust. ring.rs (MPMC lock-free, zero-copy), clock.rs
  (CLOCK_MONOTONIC_RAW), pool.rs (janela, pool_id deterministico),
  netting.rs (compensacao multilateral), sha256.rs (hash de composicao).
- window/: janela de 1 ms, watermark e pool_id deterministico.
- netting/: compensacao multilateral por moeda e jurisdicao.
- liquidity/: le liquidity_ceiling_minor; nunca debita genesis.
- clock/: fachada CLOCK_MONOTONIC_RAW para control plane e testes.
- wal/: WAL local, fsync diferido, replay idempotente.
- backpressure/: rejeicao explicita POOL_FULL; descarte silencioso proibido.
- control/: control plane FastAPI em socket separado.
- publish/: um pool.closed.v1 por janela para o outbox.

## Restricoes

- Redis e PostgreSQL proibidos em core/, window/, netting/ e clock/.
- Sem sleep, GC, fsync ou rede na admissao.
- Nenhum wall-clock decide ordem ou pool_id.

## Build

    cd core && cargo build --release
    maturin develop --release

O SLO e limite configurado (configs/pool/slo.yaml); medicao apenas via
make bench-pool pelo operador.
