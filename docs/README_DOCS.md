# **Documentação do BRLIA V2**

> **Versão:** 2.0.0  
> **Data:** 2024-11-20  
> **Classificação:** Confidencial

---

## **ÍNDICE DE DOCUMENTOS**

### **1. Documentação Principal**

| Documento | Descrição | Localização |
|-----------|-----------|-------------|
| **PRD + TDD Completo** | Especificação completa de produto e arquitetura técnica | [BRLIA_V2_COMPLETE.md](./BRLIA_V2_COMPLETE.md) |
| **PRD + TDD (Parte 1)** | Versão detalhada - Parte 1 | [BRLIA_V2_PRD_TDD_PART1.md](./BRLIA_V2_PRD_TDD_PART1.md) |

### **2. Contratos de API**

| Documento | Descrição | Localização |
|-----------|-----------|-------------|
| **gRPC Contract** | Definição do serviço gRPC para splitpayments | [proto/splitpayments.proto](../proto/splitpayments.proto) |

### **3. Configurações**

| Documento | Descrição | Localização |
|-----------|-----------|-------------|
| **Config SplitPayments** | Configuração de integração com splitpayments | [configs/splitpayments/config.yaml](../configs/splitpayments/config.yaml) |

### **4. Implementações de Referência**

| Documento | Descrição | Localização |
|-----------|-----------|-------------|
| **Cliente SplitPayments** | Implementação TypeScript do cliente gRPC | [infrastructure/splitpayments/splitpayments.client.ts](../infrastructure/splitpayments/splitpayments.client.ts) |

---

## **ESTRUTURA DA DOCUMENTAÇÃO**

```
docs/
├── README_DOCS.md                    # Este arquivo
├── BRLIA_V2_COMPLETE.md               # Documento principal completo
├── BRLIA_V2_PRD_TDD_PART1.md          # Parte 1 do documento
└── snippets/                          # Trechos de código (opcional)

proto/
└── splitpayments.proto                # Contrato gRPC

configs/
└── splitpayments/
    └── config.yaml                    # Configuração da integração

infrastructure/
└── splitpayments/
    └── splitpayments.client.ts        # Cliente TypeScript
```

---

## **COMO USAR ESTA DOCUMENTAÇÃO**

### **Para CTOs e Arquitetos**

1. **Leia o [BRLIA_V2_COMPLETE.md](./BRLIA_V2_COMPLETE.md)** para entender:
   - Arquitetura de alto nível
   - Estratégia e proposta de valor
   - Garantias de sistema (atomicidade, idempotência, consistência)
   - Modelagem de dados
   - Fluxo operacional

2. **Analise o [proto/splitpayments.proto](../proto/splitpayments.proto)** para entender:
   - Contratos de API com LowDataESC
   - Mensagens e tipos de dados
   - Serviços disponíveis

3. **Consulte o [config.yaml](../configs/splitpayments/config.yaml)** para:
   - Configurações de integração
   - Timeouts e retries
   - Gateways disponíveis
   - Regras de split padrão

### **Para Desenvolvedores**

1. **Implemente o Pool Engine em Rust** usando:
   - [BRLIA_V2_COMPLETE.md - Seção 8.1](./BRLIA_V2_COMPLETE.md#81-pool-engine-rust)
   - Exemplos de código em Rust para CLOCK_MONOTONIC_RAW
   - Ring Buffer MPMC Lock-Free

2. **Desenvolva o Transaction Orchestrator** usando:
   - [BRLIA_V2_COMPLETE.md - Seção 8.2](./BRLIA_V2_COMPLETE.md#82-transactional-outbox-pattern)
   - [BRLIA_V2_COMPLETE.md - Seção 8.3](./BRLIA_V2_COMPLETE.md#83-saga-pattern)

3. **Integre com splitpayments** usando:
   - [splitpayments.client.ts](../infrastructure/splitpayments/splitpayments.client.ts)
   - [proto/splitpayments.proto](../proto/splitpayments.proto)
   - [config.yaml](../configs/splitpayments/config.yaml)

4. **Implemente o Ledger** usando:
   - [BRLIA_V2_COMPLETE.md - Seção 4.2](./BRLIA_V2_COMPLETE.md#42-implementação-do-double-entry-bookkeeping)
   - Schemas SQL em [BRLIA_V2_COMPLETE.md - Seção 4.1](./BRLIA_V2_COMPLETE.md#41-schemas-sql-tabelas-críticas)

### **Para Product Managers**

1. **Entenda a proposta de valor** em:
   - [BRLIA_V2_COMPLETE.md - Seção 1.1](./BRLIA_V2_COMPLETE.md#11-pitch-fornecedor-liquidez-atômica---t0-real)
   - [BRLIA_V2_COMPLETE.md - Seção 1.2](./BRLIA_V2_COMPLETE.md#12-pitch-lender-settlement-segregado-e-imutável)

2. **Acompanhe as métricas** em:
   - [BRLIA_V2_COMPLETE.md - Seção 7](./BRLIA_V2_COMPLETE.md#7-métricas-de-sucesso)

3. **Roadmap de implementação** em:
   - [BRLIA_V2_COMPLETE.md - Seção 11](./BRLIA_V2_COMPLETE.md#11-roadmap-de-implementação)

---

## **DOCUMENTOS EXTERNOS**

### **LowDataESC splitpayments**

- **Repositório:** [https://github.com/kauecodify/LOWDATAESC/tree/main/revenue-share/services/splitpayments](https://github.com/kauecodify/LOWDATAESC/tree/main/revenue-share/services/splitpayments)
- **Documentação:** [README.md](https://github.com/kauecodify/LOWDATAESC/blob/main/revenue-share/services/splitpayments/README.md)
- **API Reference:** Ver [proto/splitpayments.proto](../proto/splitpayments.proto)

### **BRLIA V2**

- **Repositório:** [https://github.com/kauecodify/BRLIA](https://github.com/kauecodify/BRLIA)
- **Arquitetura:** [ARCHITECTURE_V2.md](../ARCHITECTURE_V2.md)
- **Compliance:** [COMPLIANCE.md](../COMPLIANCE.md)
- **README:** [README.md](../README.md)

---

## **GLOSSÁRIO**

| Termo | Definição |
|-------|-----------|
| **Atomicidade** | Propriedade de uma transação ser executada completamente ou não ser executada |
| **Idempotência** | Propriedade de uma operação produzir o mesmo resultado quando executada múltiplas vezes |
| **Partidas Dobradas** | Sistema contábil onde cada transação afeta pelo menos duas contas (débito e crédito) |
| **Saga Pattern** | Padrão para gerenciar transações distribuídas com compensação |
| **Transactional Outbox** | Padrão para publicação confiável de eventos em sistemas distribuídos |
| **WORM** | Write Once, Read Many - Armazenamento imutável |
| **Hash-chain** | Cadeia de hashes onde cada hash depende do anterior, garantindo imutabilidade |
| **Co-location** | Execução do sistema junto ao servidor do cliente (sidecar, daemonset) |
| **UDS** | Unix Domain Socket - Comunicação inter-processos local |
| **mTLS** | Mutual TLS - Autenticação mútua via certificados |
| **Netting** | Compensação de débitos e créditos entre partes |
| **Escrow** | Conta de custódia onde fundos são retidos até condições serem atendidas |

---

## **CONTATOS**

| Área | Responsável | Email |
|------|-------------|-------|
| CTO Office | [CTO Name] | cto@brlia.com |
| Engenharia | [Eng Lead] | eng@brlia.com |
| Produto | [Product Lead] | produto@brlia.com |
| Compliance | [Compliance Lead] | compliance@brlia.com |
| LowDataESC | [SplitPayments Lead] | split-payment@lowdataesc.gov.br |

---

## **PRÓXIMOS PASSOS**

1. **Implementar o Pool Engine em Rust** (Prioridade 1)
2. **Desenvolver o Transaction Orchestrator com Saga Pattern** (Prioridade 1)
3. **Implementar o cliente gRPC para splitpayments** (Prioridade 1)
4. **Criar os schemas do banco de dados** (Prioridade 1)
5. **Desenvolver o Frontend com fluxo em 5 passos** (Prioridade 2)

Para mais detalhes, consulte o [Roadmap de Implementação](./BRLIA_V2_COMPLETE.md#11-roadmap-de-implementação).

---

> **"Liquidez em milissegundos, com custódia segregada e auditoria imutável."**
> — BRLIA V2 Mission Statement

**Documento gerado em:** 2024-11-20  
**Versão:** 2.0.0
