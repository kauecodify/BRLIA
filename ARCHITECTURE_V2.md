# ARCHITECTURE V2 (fonte normativa)

## 1. Posicao do documento

Este documento e a fonte normativa da arquitetura V2 e permanece valido na V2.1.
Em conflito entre documentos, prevalece a ordem: este arquivo, POOL_ENGINE.md,
COLOCATION.md, COMPLIANCE.md.

## 2. Principios

1. O genesis de R$ 100.000.000,00 (10000000000 minor units, BRL, scale 2) e imutavel.
2. O pool e o genesis compoem o nucleo escalavel. Os modos de deploy e as jurisdicoes
   compoem a camada configuravel. Os carve-outs de cada host ficam no orcamento de
   excecao, vigiados e com vigencia definida.
3. Toda escrita exige idempotency-key. Toda mudanca de estado passa por saga com
   compensacao e transactional outbox.
4. O caminho quente do pool-engine nao interpretado: nucleo compilado (Rust com
   binding PyO3), ring buffer MPMC lock-free, zero-copy, CLOCK_MONOTONIC_RAW.
5. Redis e PostgreSQL ficam fora do trajeto admit -> pool_id.
6. FastAPI e Python permanecem apenas no control plane.

## 3. Servicos

| Servico                     | Papel                                                            |
|-----------------------------|------------------------------------------------------------------|
| routing-engine              | decide br | intl | fx | br_intl e emite pool_key antes da orquestracao |
| pool-engine                 | janela de 1 ms, netting multilateral, pool.closed.v1            |
| transaction-orchestrator    | saga, outbox, consome pool.closed.v1                            |
| settlement-engine           | consome lancamentos liquidos do pool                            |
| ledger                      | partidas dobradas, hash-chain, genesis                          |
| multi-currency-ledger       | BRL/USD/EUR em minor units                                      |
| fx-engine                   | PTAX, spread, IOF-FX, trilha da cotacao                         |
| jurisdiction-engine         | br, us, eu, uk, sg, global                                      |
| treasury-service            | expoe liquidity_ceiling_minor = 10000000000 (somente leitura)   |
| risk-engine                 | scikit-learn com fallback deterministico por regras             |
| compliance-screening        | OFAC/SDN, PEP, KYC/KYB/KYT, Travel Rule                         |
| escrow-manager              | escrow multimoeda                                               |
| auth-service                | OIDC, mTLS, escopo por jurisdicao e por modo de deploy          |
| notification-service        | notificacoes operacionais                                       |
| file-processor              | ISO 20022, camt.053, CNAB, OFX                                  |
| audit-trail                 | WORM, hash encadeado, registra pool_id e hash da janela         |
| reporting-regulatorio       | BACEN, e-Financeira, CRS/FATCA, deriva do outbox                |
| host-adapter                | UDS preferencial, mTLS como fallback, conectores somente leitura |

## 4. Fluxo nominal

1. routing-engine publica decisao (br | intl | fx | br_intl) e pool_key
   = (jurisdicao, moeda_funcional, janela_monotonica, sequence).
2. pool-engine admite as pernas na janela de 1 ms, aplica netting multilateral
   entre operacoes distintas da mesma janela e publica um unico pool.closed.v1
   por janela no outbox.
3. transaction-orchestrator consome pool.closed.v1 e conduz a saga.
4. settlement-engine consome os lancamentos liquidos.
5. audit-trail grava pool_id e hash da composicao em WORM.
6. reporting-regulatorio deriva dos mesmos eventos, sem recomputar saldos.

## 5. Stack obrigatoria

Python 3.12, FastAPI, Pydantic v2, PostgreSQL 16 com particionamento e partidas
dobradas, Redpanda/Kafka com transactional outbox, Redis fora do caminho quente,
Docker multi-stage, Kubernetes, Prometheus, Grafana, OpenTelemetry.

## 6. Jurisdicoes

br, us, eu, uk, sg e global. Cada jurisdicao possui arquivo em
configs/jurisdictions/ e modulo em infrastructure/jurisdiction-engine/.
