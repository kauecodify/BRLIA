# POOL ENGINE

## 1. Definicao normativa

Pool e o conjunto de operacoes admitidas dentro de uma janela deterministica de
1 ms, agrupadas por pool_key = (jurisdicao, moeda_funcional, janela_monotonica,
sequence). O routing-engine emite pool_key antes da orquestracao. Todas as pernas
de uma mesma operacao (PIX, FX, escrow, ledger) entram na mesma janela. O netting
ocorre entre operacoes distintas da mesma janela, reduzindo N operacoes admitidas
a K lancamentos liquidos, com K <= N.

"Gerar o pool" significa materializar pool_id, composicao, K lancamentos liquidos
e o unico evento pool.closed.v1 por janela, entregue ao outbox.

O pool nao e fila, nao e batch, nao e cache Redis, nao e saldo bancario e nao
muta o genesis.

## 2. Janela e relogio

- Duracao da janela: 1 ms, fixada em runtime/tuning.yaml (tick_ms: 1).
- clock/ usa CLOCK_MONOTONIC_RAW. Nenhum wall-clock, nenhum timestamp de banco e
  nenhum NTP decide ordem ou pool_id.
- pool_id e deterministico: funcao da pool_key e do hash da composicao ordenada.
- watermark_ms define a tolerancia de fechamento; a janela fecha por tick ou por
  watermark, o que ocorrer primeiro.

## 3. Admissao

- Caminho: UDS -> ring buffer MPMC lock-free -> pool_id.
- Sem rede, sem fsync, sem sleep, sem GC e sem chamada interpretada no trajeto.
- Redis e PostgreSQL sao proibidos entre admit e pool_id. A varredura estatica
  de core/, window/, netting/ e clock/ deve comprovar ausencia de cliente de rede.
- Sem espaco no ring buffer, backpressure rejeita com POOL_FULL e orienta retry
  com a mesma idempotency-key. Descarte silencioso e proibido.

## 4. Netting

- Agrupamento por (jurisdicao, moeda_funcional, janela).
- Compensacao multilateral: cada participante acumula debitos e creditos na
  janela e o resultado liquido e materializado em K lancamentos, K <= N.
- Cada lancamento liquido carrega pool_id, window_seq, idempotency-key e a
  trilha das operacoes de origem.
- Nenhum lancamento do pool debita Capital Social ou altera genesis.json. A
  liquidez referencia liquidity_ceiling_minor do treasury-service.

## 5. Publicacao

- Um unico pool.closed.v1 por janela, versionado em schemas/events/, entregue ao
  transactional outbox de forma assincrona.
- O audit-trail grava pool_id e hash da composicao em WORM.
- Persistencia local via WAL com fsync diferido e replay idempotente.

## 6. SLO (limites configuraveis, nunca medidos na geracao)

| Etapa                                  | p50      | p99    | p99.9  | Restricao                          |
|----------------------------------------|----------|--------|--------|------------------------------------|
| admit: UDS -> ring -> pool_id          | <=0,15ms | <=1ms  | <=2ms  | sem rede, sem fsync, sem sleep     |
| close + netting + pool.closed.v1       | <=0,8ms  | <=3ms  | <=5ms  | 1 evento por janela                |
| pool.closed.v1 -> orchestrator         | <=2ms    | <=10ms | <=20ms | outbox assincrono                  |
| duracao da janela                      | 1ms      | 1ms    | 1ms    | CLOCK_MONOTONIC_RAW, sem drift     |

Falha de CI se p99 de close + netting exceder 5 ms em tests/pool/bench_pool.py
com 100.000 operacoes e histograma HDR. Execucao: make bench-pool.

## 7. Metricas e spans

- Metricas: pool_admit_latency_seconds, pool_close_latency_seconds,
  pool_window_ops, pool_netting_ratio, pool_rejected_total.
- Spans: pool.admit, pool.close, pool.netting, host.attach.

## 8. Control plane

FastAPI atende somente /health, /ready, /metrics e /config em socket de controle
separado do hot path. Se o SLO nao for cumprido com a implementacao escolhida, a
implementacao e trocada; o SLO nunca e relaxado.
