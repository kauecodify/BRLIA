# QUICKSTART

## 1. Pre-requisitos

Docker, Docker Compose, Make. Nenhum segredo em arquivo; use variaveis de
ambiente a partir de .env.example.

## 2. Subir a plataforma

    make up PROFILE=all

## 3. Aplicar o seed de capital

    make seed
    make reconcile

O genesis e de R$ 100.000.000,00 (10000000000 minor units, BRL, scale 2),
imutavel. apply-seed.sh e idempotente e falha se correlation_id ja existir.

## 4. Co-localizar em um host

    sudo ./scripts/attach.sh --mode standalone

O attach nao reinicia o processo do host e nao altera codigo do ERP, do core
banking ou do TMS. O caminho preferencial e o UDS /var/run/brlia/pool.sock.

## 5. Desacoplar

    sudo ./scripts/detach.sh

Drena a janela corrente, fecha o WAL e desacopla; o replay no reattach e
idempotente.

## 6. Benchmark do pool

    make bench-pool

Executa tests/pool/bench_pool.py com 100.000 operacoes e histograma HDR. A CI
falha se o p99 de close + netting exceder 5 ms. Os valores do SLO sao limites
configurados em configs/pool/slo.yaml; nenhuma latencia e afirmada antes da
execucao pelo operador.

## 7. Migracao de banco

    make migrate
