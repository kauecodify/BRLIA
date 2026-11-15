
# BRLIA

Repositorio: https://github.com/kauecodify/BRLIA

Aplicacao de demonstracao: https://brlia.vercel.app

Arquivo: README.md

Versao: V2.1

Status: descricao de contrato e funcionamento; nao registra implantacao, execucao de containers, benchmark executado ou medicao de latencia.

---

## 1. Finalidade

BRLIA e um bureau de credito inteligente e motor de liquidacao instantanea B2B. A plataforma conecta fornecedores, compradores, instituicoes financeiras, ERPs, core banking, TMS e arranjos de pagamento para transformar credito futuro em liquidez imediata, sem exigir que o comprador abra mao do prazo comercial original.

O fornecedor recebe no mesmo ciclo de liquidacao. O comprador conserva o prazo negociado. A operacao e avaliada por modelo de risco explicavel, admitida em janela deterministica de 1 ms, compensada com outras operacoes da mesma janela, registrada em partidas dobradas e conciliada com um capital de abertura imutavel de R$ 100.000.000,00.

A captura de valor ocorre por taxas operacionais, spread de risco, servicos financeiros e, quando houver base legal e consentimento, monetizacao de dados agregados e anonimizados, nos termos da LGPD e do GDPR.

---

## 2. Principio de funcionamento

Tres definicoes organizam o produto:

- Genesis: capital pre-seed de R$ 100.000.000,00, representado como 10000000000 centavos, moeda BRL, escala 2, lancado em partidas dobradas e protegido contra alteracao.
- Pool: conjunto de operacoes admitidas em uma janela de 1 ms, agrupadas por pool_key, reduzido por netting multilateral a K lancamentos liquidos, com K <= N, e materializado em um unico evento pool.closed.v1.
- Co-localizacao: o motor executa junto ao servidor da empresa, em nuvem ou em servidor proprio, por meio de host-adapter, sem substituir o ERP, o core banking ou o TMS e sem reiniciar processos do host.

Em termos da diretriz de escopo adotada pelo repositorio, genesis, orquestracao, roteamento e pool compoem o nucleo escalavel, replicavel a custo marginal zero. Os arquivos runtime/modes.yaml, runtime/tuning.yaml, configs/jurisdictions/*.yaml e configs/pool/*.yaml compoem a camada configuravel. Carve-outs regulatorios especificos de um cliente ou de uma praca permanecem no orcamento de excecao, monitorados, tarifados e com vigencia definida. Escalar continua sendo a disciplina de isolar a excecao.

---

## 3. Fluxo operacional

1. O fornecedor registra uma venda a prazo para o comprador. O prazo comercial permanece registrado no sistema de origem.

2. O host-adapter admite a operacao pelo Unix Domain Socket /var/run/brlia/pool.sock, com fallback TCP somente sob mTLS/SPIFFE. O acoplamento e feito por scripts/attach.sh sem reiniciar o servidor da empresa, sem alterar codigo legado e sem exigir ingress publico.

3. O routing-engine classifica a intencao antes da orquestracao e publica a decisao (br, intl, fx ou br_intl) juntamente com o pool_key, composto por jurisdicao, moeda funcional, janela monotonica e sequencia.

4. O pool-engine admit a operacao em uma janela de 1 ms usando CLOCK_MONOTONIC_RAW. O pool_id e deterministico. Nenhum wall-clock, NTP, timestamp de banco, Redis ou PostgreSQL decide ordem nesse trajeto. O caminho quente e compilado em Rust com PyO3 ou em Go, com ring buffer MPMC lock-free e zero-copy; FastAPI atende somente /health, /ready, /metrics e /config em socket de controle separado.

5. O risk-engine calcula probabilidade de default, limite sugerido e rating interno. A decisao gera explicacao auditavel via SHAP e admite fallback deterministico por regras quando o modelo nao estiver carregado. O alvo configurado para a decisao de credito e < 200 ms, dominio distinto do SLO de compensacao da janela.

6. O compliance-screening aplica KYC, KYB, KYT, triagem OFAC/SDN, PEP, listas internas, FATF Recomendacao 16 / Travel Rule e, conforme a jurisdicao, MiCA, AMLD6, FinCEN, CRS, FATCA, W-9 e W-8BEN.

7. O treasury-service expoe liquidity_ceiling_minor = 10000000000 como teto de referencia. O pool consulta esse teto, mas nao debita Capital Social, nao muta seed/genesis.json e nao converte o capital de abertura em saldo bancario operacional.

8. O netting compensa operacoes distintas da mesma janela por jurisdicao e moeda funcional. Cada lancamento liquido carrega pool_id, window_seq, idempotency-key e a trilha das operacoes de origem. Fechada a janela, publica-se um unico pool.closed.v1 no outbox; o audit-trail grava pool_id e o hash da composicao em registro WORM.

9. O transaction-orchestrator consome pool.closed.v1, executa a saga com compensacao e aciona o escrow-manager, que mantem a retencao multimoeda ate a condicao de liberacao.

10. O settlement-engine liquida os lancamentos liquidos. No cenario nacional usa PIX, SPI, DICT, MED 2.0, Pix Automatico, SPB/STR e CIP, com idempotencia por endToEndId. No cenario internacional usa ISO 20022 pain.001, pacs.008 e camt.053, SWIFT gpi, ACH, Fedwire, SEPA/SCT Inst, FPS, CHAPS, FAST e PayNow. O fx-engine aplica PTAX, spread configuravel, IOF-FX, arredondamento bancario explicito e registra a cotacao usada em cada conversao.

11. O ledger e o multi-currency-ledger registram partidas dobradas em BRL, USD e EUR, sempre em unidades minimas inteiras. A moeda funcional e distinta da moeda de origem; a conversao nunca sobrescreve o lancamento original. A cadeia de hash permanece integrada ao audit-trail.

12. A tesouraria aplica o saldo de escrow conforme seed/treasury_policy.yaml, com referencia a CDI quando configurada, e registra o rendimento em conta propria, sem alterar o genesis. O recebimento futuro do comprador efetua a baixa da operacao e fecha o ciclo.

13. O reporting-regulatorio deriva e-Financeira, SCR, CCS, CRS e FATCA dos mesmos eventos do outbox, sem recomputar saldos.

14. As taxas operacionais, o spread de risco e os servicos financeiros sao apropriados por evento versionado. A monetizacao de dados depende de base legal, consentimento e pseudonimizacao no modo hybrid.

---

## 4. O pool em milissegundos

| Etapa | p50 | p99 | p99.9 | Restricao |
|---|---|---|---|---|
| admit: UDS -> ring -> pool_id | <= 0,15 ms | <= 1 ms | <= 2 ms | sem rede, sem fsync, sem sleep |
| close + netting + pool.closed.v1 | <= 0,8 ms | <= 3 ms | <= 5 ms | 1 evento por janela |
| pool.closed.v1 -> orchestrator | <= 2 ms | <= 10 ms | <= 20 ms | outbox assincrono |
| duracao da janela | 1 ms | 1 ms | 1 ms | CLOCK_MONOTONIC_RAW, sem drift |

Metricas obrigatorias: pool_admit_latency_seconds, pool_close_latency_seconds, pool_window_ops, pool_netting_ratio, pool_rejected_total. Spans: pool.admit, pool.close, pool.netting, host.attach.

Backpressure rejeita explicitamente com POOL_FULL e orienta retry com a mesma idempotency-key. E proibido descarte silencioso, overflow implicito ou duplo lancamento.

Nenhuma latencia foi medida nesta geracao. Os valores acima sao alvos configurados em configs/pool/slo.yaml e verificaveis posteriormente por make bench-pool, que executa tests/pool/bench_pool.py com 100.000 operacoes e histograma HDR, falhando em CI se o p99 de close + netting exceder 5 ms.

---

## 5. Capital pre-seed

Valor unico e exato: R$ 100.000.000,00.

- seed/genesis.json: amount_minor 10000000000, currency BRL, scale 2.
- seed/genesis_entries.sql: debito em Ativo Caixa/Bancos e credito em Patrimonio Liquido Capital Social / AFAC; soma de debitos igual a soma de creditos.
- Imutabilidade: hash encadeado no audit-trail, registro WORM, sem UPDATE ou DELETE por grant de banco; scripts/apply-seed.sh falha se o correlation_id ja existir.
- seed/verify_seed.py reconcilia genesis.json, ledger_entries e treasury-service e verifica que nenhum lancamento com pool_id tem natureza de capital.
- SEED_CAPITAL.md e CAP_TABLE.md documentam origem, data, instrumento, valuation pre-money, diluicao e destinacao a capital minimo, sempre com a formulacao "sujeito a validacao do regulador e da assessoria".

O genesis nao e saldo bancario real, nao e certificacao regulatoria e nao e liquidez automatica para o pool.

---

## 6. Co-localizacao com o servidor da empresa

| Modo | Onde executa | Artefato |
|---|---|---|
| sidecar | Kubernetes, junto ao pod da empresa | deploy/sidecar/k8s-sidecar-patch.yaml |
| daemonset | K3s ou edge, uma instancia por no | deploy/daemonset/k3s-daemonset.yaml |
| standalone | servidor proprio, systemd, bare-metal | deploy/onprem/systemd/brlia-agent.service |
| managed | nuvem, ECS, Cloud Run ou Container Apps | deploy/cloud/aws, deploy/cloud/gcp, deploy/cloud/azure |

A mesma imagem, o mesmo binario e o mesmo contrato gRPC atendem aos quatro modos; a diferenca fica em runtime/modes.yaml. Nuvem e servidor proprio sao modos de deploy, nao produtos distintos.

Preferencia de transporte: UDS em /var/run/brlia/pool.sock, grupo brlia, permissao 0660. Fallback TCP somente com mTLS. O host-adapter/egress_policy.yaml impoe local-first e outbound-only no modo hybrid: dados do cliente permanecem no host e apenas eventos pseudonimizados alcancam o control plane.

Em runtime/degraded-mode.yaml, a perda do control plane mantem WAL local por ate 60 s, com escrita fail-closed (503 POOL_DEGRADED), leitura fail-open e replay idempotente no reattach.

---

## 7. Cenario nacional e internacional

Nacional (BR): PIX, SPI, DICT, MED 2.0, Pix Automatico, SPB/STR, CIP, CCS, SCR, e-Financeira, validacao de CPF/CNPJ, Res. 80/2021, Res. 4.658/2018, PLD/FT e LGPD em configs/bacen/.

Internacional: ISO 20022 com XSD em configs/iso20022/, SWIFT gpi e correspondent banking, ACH/Fedwire, SEPA/SCT Inst com IBAN, FPS/CHAPS, FAST/PayNow, PTAX, IOF-FX, OFAC/SDN, PEP, KYC/KYB/KYT, FATF R.16, MiCA, AMLD6, FinCEN, CRS, FATCA, W-8BEN e W-9.

A matriz completa esta em JURISDICTIONS.md e em configs/jurisdictions/br.yaml, us.yaml, eu.yaml, uk.yaml e sg.yaml. O jurisdiction-engine carrega esses arquivos; o routing-engine decide antes da orquestracao.

---

## 8. Estrutura do repositorio

```text
brlia/
|-- index.html                          [MANTIDO] inalterado, byte a byte
|-- demo.html                           [MANTIDO]
|-- README.md                           [NOVO] este arquivo
|-- INFRASTRUCTURE.md                   [EXPANDIDO]
|-- QUICKSTART.md                       [EXPANDIDO]
|-- ARCHITECTURE_V2.md                  [MANTIDO]
|-- POOL_ENGINE.md                      [NOVO]
|-- COLOCATION.md                       [NOVO]
|-- REFACTORING_SUMMARY.md              [MANTIDO]
|-- SEED_CAPITAL.md                     [MANTIDO]
|-- CAP_TABLE.md                        [MANTIDO]
|-- JURISDICTIONS.md                    [MANTIDO]
|-- COMPLIANCE.md                       [EXPANDIDO]
|-- docker-compose.yml                  [EXPANDIDO] perfis br, intl, all, colocated
|-- docker-compose.seed.yml             [MANTIDO]
|-- docker-compose.colocated.yml        [NOVO]
|-- Makefile                            [EXPANDIDO]
|-- .env.example                        [EXPANDIDO]
|-- .gitignore                          [MANTIDO]
|-- infrastructure/
|   |-- host-adapter/
|   |   |-- uds/
|   |   |-- grpc/
|   |   |-- mtls/
|   |   |-- connectors/
|   |   |-- egress_policy.yaml
|   |-- routing-engine/
|   |-- pool-engine/
|   |   |-- core/
|   |   |-- window/
|   |   |-- netting/
|   |   |-- liquidity/
|   |   |-- clock/
|   |   |-- wal/
|   |   |-- backpressure/
|   |   |-- control/
|   |   |-- publish/
|   |-- risk-engine/
|   |-- compliance-screening/
|   |-- treasury-service/
|   |-- transaction-orchestrator/
|   |-- settlement-engine/
|   |-- escrow-manager/
|   |-- ledger/
|   |-- multi-currency-ledger/
|   |-- fx-engine/
|   |-- jurisdiction-engine/
|   |-- audit-trail/
|   |-- reporting-regulatorio/
|   |-- auth-service/
|   |-- notification-service/
|   |-- file-processor/
|-- seed/
|   |-- genesis.json
|   |-- genesis_entries.sql
|   |-- cap_table.json
|   |-- treasury_policy.yaml
|   |-- verify_seed.py
|-- deploy/
|   |-- sidecar/
|   |-- daemonset/
|   |-- onprem/
|   |-- cloud/
|   |-- hybrid/
|-- runtime/
|   |-- modes.yaml
|   |-- tuning.yaml
|   |-- degraded-mode.yaml
|-- configs/
|   |-- nginx/nginx.conf
|   |-- kubernetes/
|   |-- monitoring/prometheus.yml
|   |-- opentelemetry/
|   |-- bacen/
|   |-- iso20022/
|   |-- jurisdictions/
|   |-- pool/
|-- schemas/
|   |-- events/
|   |   |-- pool.closed.v1.json
|   |   |-- pool.admitted.v1.json
|   |-- ledger/
|-- scripts/
|   |-- start.sh
|   |-- stop.sh
|   |-- build.sh
|   |-- init-db.sql
|   |-- apply-seed.sh
|   |-- reconcile.sh
|   |-- migrate.sh
|   |-- attach.sh
|   |-- detach.sh
|   |-- bench-pool.sh
|-- tests/
|   |-- seed/
|   |-- pool/
|   |-- colocation/
|   |-- jurisdiction/
|   |-- fx/
|   |-- e2e/
```

---

## 9. Reconciliacao com o material de origem

| Item | Versao anterior | V2.1 neste repositorio | Tratamento |
|---|---|---|---|
| Marca e grafia | BRLIA com simbolo de registro, setas e imagem remota | BRLIA em texto ASCII/PT-BR | Simbolos removidos; fluxo numerado e documentos internos substituem o asset externo |
| Arvore | brlia-ai-backend/ com core, ml-engine, stream-processing, api-gateways | brlia/ com infrastructure, seed, deploy, runtime, configs, schemas, scripts, tests | Arvore V2.1 substitui a anterior; index.html e demo.html preservados |
| Nucleo | Java 17, Spring Boot 3, Spring Cloud, Resilience4j, gRPC | Python 3.12 + FastAPI + Pydantic v2 no control plane; Rust ou Go no hot path do pool | O contrato gRPC/Protocol Buffers e mantido; adaptadores de ERP, core banking e TMS ficam na fronteira em host-adapter/connectors, sem duplicar o nucleo |
| Stream | Kafka, Flink, Redis | Redpanda/Kafka com transactional outbox; pool-engine compilado; Redis fora do caminho quente | Flink e absorvido por routing-engine e pela janela de 1 ms; Redis permanece apenas para idempotencia distribuida |
| ML | TensorFlow, Scikit-Learn, XGBoost, SHAP, MLflow | risk-engine com modelo registrado, SHAP, MLflow e fallback deterministico por regras | Treino e registro permanecem; inferencia em producao usa fallback quando o modelo nao esta carregado |
| Latencia | < 200 ms por decisao | < 200 ms para decisao de credito; p99 <= 3 ms para close + netting | Dominios distintos, ambos configurados, nenhum medido nesta geracao |
| Mercado | "preparada para trilhões" | dimensionamento de capacidade do ledger, sem promessa de volume | Estimativas movidas para a Secao 10 com ressalva explicita |
| Licenca | texto nao reconhecido como instrumento de licenciamento | pendente de definicao pelo titular | Campo corrigido na Secao 17; recomenda-se MIT, Apache-2.0 ou licenca proprietaria antes de publicar |

---

## 10. Mercado enderecavel, em carater de referencia

- Credito total no Brasil: R$ 6 trilhões, estimativa de referencia.
- Credito corporativo: aproximadamente R$ 3 trilhões.
- Mercado de cartões: aproximadamente R$ 2,4 trilhões por ano.
- Exercicio de dimensionamento: 0,02% de R$ 1 trilhão corresponde a R$ 200 milhões de volume movimentado.

Esses numeros sao referencias de dimensionamento utilizadas no material de origem. Nao constituem projecao de receita, compromisso de captura, volume processado ou resultado auditado.

---

## 11. Comunicacao, seguranca e observabilidade

Contrato interno: gRPC + Protocol Buffers. REST/JSON aparece apenas no control plane, no index.html, na aplicacao de demonstracao e nos endpoints /health, /ready, /metrics e /config.

Seguranca: mTLS, OIDC/OAuth2, JWT, HSM, AES-256, SPIFFE no fallback TCP, escopos por jurisdicao e por modo de deploy. Segredos permanecem em variaveis de ambiente ou Secret do Kubernetes; .env.example nao contem segredos reais.

Observabilidade: OpenTelemetry, Prometheus, Grafana e Loki. Alem de latencia de predicao, taxa de aprovacao, taxa de fraude e SLA operacional, registram-se as metricas do pool e os spans pool.admit, pool.close, pool.netting e host.attach. Todo servico propaga trace_id.

---

## 12. Decisao auditavel

```json
{
  "decision": "REJECTED",
  "confidence": 0.93,
  "model_version": "credit-risk-2026.1",
  "trace_id": "7f3c9a12-4b80-4f1e-9d2c-1a6e5b8f0c37",
  "pool_id": "br-BRL-000000000001-0001",
  "explanation": [
    "Padrão de localização divergente",
    "Histórico recente incompatível",
    "Volume acima da média histórica"
  ]
}
```

A explicacao e gravada no audit-trail juntamente com pool_id, window_seq e o hash da composicao da janela, em registro WORM com retencao decenal.

---

## 13. Governanca de modelos

Data Lake -> Treinamento -> Validacao -> MLflow Registry -> Producao -> Monitoramento -> Retraining Automatico.

Monitoramentos: Data Drift, Concept Drift e Performance Drift. Fraude utiliza Monte Carlo Dropout, Isolation Forest, Autoencoders e Gradient Boosting, com estimativa de incerteza estatistica e controle de falsos positivos. Toda decisao automatizada produz explicacao auditavel; a ausencia do modelo carregado ativa o fallback deterministico, sem interromper a admissao no pool.

---

## 14. Como executar pelo operador

Os comandos abaixo sao instrucoes para execucao posterior. Nao foram executados na producao deste README.

```bash
docker compose -f docker-compose.colocated.yml up -d
make attach MODE=sidecar
make seed
make reconcile
make bench-pool
```

Verificacao do contrato gRPC de risco:

```bash
ghz --insecure --proto ./proto/risk.proto --call risk.RiskService/Predict localhost:50051
```

A geracao do repositorio nao instala dependencias, nao sobe containers, nao executa benchmark, nao abre porta publica no modo hybrid e nao altera o servidor da empresa.

---

## 15. Restricoes e validacao

- index.html permanece byte a byte identico a V1; demo.html e preservado.
- Nenhum emoji, box-drawing, seta decorativa ou marca de verificacao aparece em codigo, documentacao, commits, PR ou logs.
- Nao ha force-push. Se o remoto ja tiver historico, a entrega ocorre por branch feat/v2.1-pool-colocation e PR contra main.
- O genesis nao e debitado por lancamento com pool_id.
- Latencias sao alvos configurados ate que make bench-pool seja executado pelo operador.
- Nenhuma afirmacao de conformidade regulatoria e automatica: toda destinacao a capital minimo, todo reporting e todo tratamento transfronteirico permanecem sujeitos a validacao do regulador e da assessoria.
- Os criterios de aceite completos permanecem os do prompt V2.1 e sao verificados por make reconcile e make bench-pool; nenhum resultado e afirmado neste arquivo.

---

## 16. Roadmap

Fase 1: Bureau de Credito, API de Score e Dashboard Operacional. Materializada no risk-engine, no auth-service e em monitoring.

Fase 2: Liquidacao Instantanea, Escrow Digital e Antecipacao de Recebiveis. Materializada no pool-engine, no escrow-manager, no settlement-engine e no genesis de 100 milhoes.

Fase 3: Open Finance, Embedded Finance e Marketplace de Credito. Tratada como camada configuravel de conectores e escopos, nao como novo nucleo.

Fase 4: Internacionalizacao, America Latina e Tokenizacao de Recebiveis. Tratada por jurisdiction-engine, fx-engine, ISO 20022 e configs/jurisdictions, mantendo o core intacto.

---

## 17. Diferenciais tecnicos

- IA explicavel em tempo real com trilha WORM.
- Pool de 1 ms com netting multilateral antes da orquestracao.
- Co-localizacao hibrida sem restart do servidor da empresa.
- Genesis contabil imutavel reconciliado centavo a centavo.
- Mesmo binario para nuvem e servidor proprio.
- Arquitetura orientada a eventos com outbox, saga e idempotency-key obrigatoria.
- Nucleo escalavel separado de jurisdicoes configuraveis e excecoes vigiadas.

---

## 18. Licenca e titularidade

Copyright 2026, kauecodify.

````
