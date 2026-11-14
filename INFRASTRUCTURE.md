# INFRASTRUCTURE

## 1. Composicao

O docker-compose.yml raiz define mais de 30 servicos com perfis br, intl, all e
colocated. O docker-compose.seed.yml isola o bootstrap do capital. O
docker-compose.colocated.yml sobe o motor co-localizado com UDS e sem ingress
publico.

## 2. Perfis

| Perfil     | Conteudo                                                      |
|------------|---------------------------------------------------------------|
| br         | jurisdicao BR: PIX, SPB, BACEN reporting                      |
| intl       | jurisdicoes internacionais: ISO 20022, FX, screening          |
| all        | uniao de br e intl                                            |
| colocated  | pool-engine e host-adapter co-localizados, UDS, sem ingress   |

## 3. Servicos de plataforma

- PostgreSQL 16: particionamento por janela e partidas dobradas.
- Redpanda/Kafka: transactional outbox e eventos versionados.
- Redis: idempotencia distribuida fora do caminho quente.
- Prometheus + Grafana: pool_admit_latency_seconds, pool_close_latency_seconds,
  pool_window_ops, pool_netting_ratio, pool_rejected_total; alertas de p99,
  POOL_FULL e capital minimo.
- OpenTelemetry: spans pool.admit, pool.close, pool.netting, host.attach.

## 4. Imagens

Docker multi-stage em todos os servicos. O pool-engine produz binario estatico
do nucleo compilado (Rust com binding PyO3). build.sh executa multi-arch e
inclui o binario do pool.

## 5. Restricoes de execucao

A geracao do repositorio nao executa docker compose, nao instala dependencias e
nao executa benchmark. O operador executa make up, make seed, make bench-pool.
