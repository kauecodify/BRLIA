# **BRLIA V2 - DOCUMENTO DE ESPECIFICAÇÃO COMPLETO (PRD + TDD)**

> **Versão:** 2.0.0  
> **Data:** 2024-11-20  
> **Autor:** CTO Office - BRLIA  
> **Classificação:** Confidencial

---

## **SUMÁRIO EXECUTIVO**

Este documento é o **PRD (Product Requirements Document) + TDD (Technical Design Document)** completo para o **BRLIA V2**, um sistema de antecipação de recebíveis B2B de alta performance com **liquidez em milissegundos** e **split atômico** via integração com o módulo `splitpayments` do **LowDataESC**.

### **Diferenciais Competitivos**

| Feature | BRLIA V2 | Mercado |
|---------|----------|---------|
| **Latência** | p99 < 5ms | 2-30 segundos |
| **Atomicidade** | Split executado na infraestrutura | Manual |
| **Custódia** | Segregada + Imutável | Comum |
| **Auditoria** | Hash-chain WORM | Logs simples |
| **Integração** | UDS/mTLS (Co-location) | REST HTTP |

---

## **1. ESTRATÉGIA E PROPOSTA DE VALOR (V2)**

### **1.1 Pitch Fornecedor: "Liquidez Atômica - T+0 Real"**

**Problema:**
- Recebíveis com prazo médio de 30-90 dias
- Capital imobilizado = perda de giros de caixa
- Burocracia: 5-10 dias úteis para aprovação

**Solução BRLIA V2:**
```
✓ Antecipação em MILISSEGUNDOS (p99 < 5ms)
✓ Sem burocracia: Upload NF → Aprovação → Liquidez automática
✓ Discrição total: Operação confidencial
✓ Custódia segregada: Recursos em escrow até liquidação
✓ Taxa competitiva: Spread base CDI + risco calculado por IA
```

**Linguagem para Vendas:**
- **CFOs:** "Reduza seu DSO de 60 para 0 dias com custódia segregada e auditável"
- **CTOs:** "Arquitetura orientada a eventos com Pool Engine em Rust (1ms) + Saga Pattern"
- **Engenheiros:** "Integração via UDS/mTLS, co-location sem restart do servidor"

### **1.2 Pitch Lender: "Settlement Segregado e Imutável"**

**Problema:**
- Risco de desvio de recursos
- Falta de transparência na auditoria
- Reconciliação manual de splits

**Solução BRLIA V2:**
```
✓ Split executado NA CAMADA DE INFRAESTRUTURA (LowDataESC splitpayments)
✓ Custódia segregada por contraparte (escrow multimoeda)
✓ Auditoria em TEMPO REAL via hash-chain + WORM
✓ Risco ZERO de desvio: splitpayments como fonte da verdade
✓ Revenue share automático via código
```

**Garantias para Lenders:**
```typescript
// Garantia de atomicidade no split
interface SplitTransaction {
  originalAmount: number;  // R$ 100.00
  splitRules: {
    platformFee: { percentage: 0.01, destination: "BRLIA_ESCROW" };
    buyerReserve: { percentage: 0.02, destination: "BUYER_ESCROW" };
    lenderCost: { percentage: 0.03, destination: "LENDER_ACCOUNT" };
    supplierNet: { percentage: 0.94, destination: "SUPPLIER_ACCOUNT" };
  };
  // Garantia: SUM(splitRules.*.percentage) == 1.0
}
```

---

## **2. ARQUITETURA DE SISTEMA**

### **2.1 Arquitetura de Alto Nível**

```
┌─────────────────────────────────────────────────────────────────────┐
│                              BRLIA V2                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Fornecedor]    [Comprador]    [Lender]    [ERP/legacy]          │
│       │               │              │              │                │
│       └───────────────┴──────────────┴──────────────┘               │
│                                  │                                   │
│                    ┌─────────────▼─────────────┐                     │
│                    │     API Gateway / Load    │                     │
│                    │        Balancer (NGINX)    │                     │
│                    └─────────────┬─────────────┘                     │
│                                  │                                   │
│                    ┌─────────────▼─────────────┐                     │
│                    │   Control Plane (FastAPI) │                     │
│                    │   - Auth Service (OIDC)   │                     │
│                    │   - File Processor (OCR)  │                     │
│                    │   - Risk Engine (ML/SHAP) │                     │
│                    │   - Compliance Screening  │                     │
│                    └─────────────┬─────────────┘                     │
│                                  │                                   │
│         ┌────────────────────────┼────────────────────────┐         │
│         │                        │                        │         │
│         ▼                        ▼                        ▼         │
│  ┌──────────────┐        ┌──────────────┐        ┌─────────────┐  │
│  │ Pool Engine   │        │ Transaction  │        │ Treasury    │  │
│  │ (Rust/PyO3)   │        │ Orchestrator │        │ Service     │  │
│  │ - Janela 1ms  │        │ - Saga       │        │ - Genesis    │  │
│  │ - Netting     │        │ - Outbox     │        │   R$100MM   │  │
│  └──────┬───────┘        └──────┬───────┘        └─────────────┘  │
│         │                        │                               │
│         └────────────────────────┼────────────────────────┘          │
│                                  │                               │
│                    ┌─────────────▼─────────────┐                     │
│                    │   Message Broker           │                     │
│                    │   (Redpanda/Kafka)         │                     │
│                    │   - pool.closed.v1         │                     │
│                    └─────────────┬─────────────┘                     │
│                                  │                                   │
│         ┌────────────────────────┼────────────────────────┐         │
│         │                        │                        │         │
│         ▼                        ▼                        ▼         │
│  ┌──────────────┐        ┌──────────────┐        ┌─────────────┐  │
│  │ Settlement   │        │ Ledger       │        │ Audit Trail │  │
│  │ Engine       │        │ (Partidas    │        │ (WORM +     │  │
│  │ - PIX/SPB    │        │   Dobradas)  │        │  Hash-chain)│  │
│  │ - ISO 20022  │        │ - Multi-     │        │ - S3        │  │
│  │ - SWIFT gpi  │        │   Currency   │        │             │  │
│  └──────────────┘        └──────────────┘        └─────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    LOWDATAESC splitpayments                     ││
│  │  (Fonte da Verdade)                                            ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        ││
│  │  │ BACEN API    │  │ Iugu Adapter │  │ Asaas Adapter│        ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘        ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### **2.2 Caminho Quente (Hot Path) - p99 < 5ms**

```
UDS (/var/run/brlia/pool.sock)
       │
       ▼
  Ring Buffer MPMC Lock-Free (p50: 0.15ms, p99: 1ms)
       │
       ▼
  Pool Engine (Admit + Netting + Close) (p50: 0.8ms, p99: 3ms)
       │
       ▼
  Transactional Outbox (Kafka) (p50: 2ms, p99: 10ms)
       │
       ▼
  splitpayments (LowDataESC) (p99: < 5ms)
       │
       ▼
  Gateway (BACEN/Iugu/Asaas/Efi)
```

**Otimizações:**
- **CLOCK_MONOTONIC_RAW:** Sem drift, sem NTP
- **Ring Buffer MPMC Lock-Free:** Zero-copy, sem lock
- **Zero-Copy Serialization:** Sem alocação de memória

### **2.3 Estratégia de Fallback e Idempotência**

**Cenários de Falha:**

| Cenário | Detecção | Ação | Garantia |
|---------|----------|------|----------|
| splitpayments falha | Timeout gRPC | Rollback via Saga | Dinheiro não some/duplica |
| Kafka indisponível | Producer error | Retry com backoff | Mensagem não perdida |
| PostgreSQL indisponível | Connection error | Fail-closed + WAL | Consistência mantida |
| Duplo clique | Idempotency key | Verifica Redis | Operação 1x |

**Fluxo de Recuperação:**
```
1. BRLIA envia split para splitpayments
2. splitpayments falha no gateway
3. splitpayments retém fundos em escrow
4. BRLIA recebe webhook ESCROW_RETAINED
5. BRLIA agenda retry automático
6. Após sucesso, fundos liberados
```

---

## **3. CONTRATOS DE API E INTEGRAÇÃO**

### **3.1 gRPC Contract (splitpayments.proto)**

```protobuf
syntax = "proto3";

package brlia.splitpayments.v1;

message CreateSplitRequest {
    string idempotency_key = 1;
    string transaction_id = 2;
    string pool_id = 3;
    uint64 amount_minor = 4;
    Currency currency = 5;
    DestinationAccount supplier_account = 7;
    DestinationAccount platform_fee_account = 8;
    DestinationAccount buyer_reserve_account = 9;
    DestinationAccount lender_cost_account = 10;
    repeated SplitRule split_rules = 11;
}

message CreateSplitResponse {
    string split_id = 1;
    string transaction_id = 2;
    string status = 3;
    string split_hash = 4;
    map<string, uint64> split_amounts = 6;
    string gateway = 7;
    string gateway_transaction_id = 8;
}

service SplitPaymentsService {
    rpc CreateSplit(CreateSplitRequest) returns (CreateSplitResponse);
    rpc GetSplitStatus(GetSplitStatusRequest) returns (GetSplitStatusResponse);
}
```

### **3.2 JSON Payloads**

**Request (Create Split):**
```json
{
  "idempotencyKey": "brlia:split:uuid-v4",
  "transactionId": "550e8400-e29b-41d4-a716-446655440000",
  "poolId": "br-BRL-000000000001-0001",
  "amountMinor": 100000000,
  "currency": "BRL",
  "referenceId": "NF-2024-0012345",
  "supplierAccount": {
    "accountType": "PIX",
    "pixAccount": {
      "keyType": "CNPJ",
      "keyValue": "12345678901234",
      "holderName": "FORNECEDOR LTDA"
    }
  },
  "platformFeeAccount": {
    "accountType": "BANK",
    "bankAccount": {
      "bankCode": "104", "agency": "0001", "accountNumber": "12345678"
    }
  },
  "splitRules": [
    {"description": "Taxa plataforma", "percentage": 0.01},
    {"description": "Reserva comprador", "percentage": 0.02},
    {"description": "Custo capital", "percentage": 0.03},
    {"description": "Líquido fornecedor", "percentage": 0.94}
  ]
}
```

**Response (Success):**
```json
{
  "splitId": "split-550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED",
  "splitHash": "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  "splitAmounts": {
    "supplier": 94000000, "platformFee": 1000000,
    "buyerReserve": 2000000, "lenderCost": 3000000
  },
  "gateway": "BACEN_SPLIT_API",
  "latencyMs": 3
}
```

**Response (Escrow Fallback):**
```json
{
  "splitId": "split-550e8400-e29b-41d4-a716-446655440000",
  "status": "ESCROW_RETAINED",
  "errorCode": "GATEWAY_UNAVAILABLE",
  "errorMessage": "Gateway indisponível. Fundos retidos em escrow.",
  "escrowAccount": "ESCROW_BRLIA_FALLBACK",
  "retryInSeconds": 300
}
```

### **3.3 Webhook (splitpayments → BRLIA)**

```json
{
  "eventId": "evt-uuid",
  "eventType": "SPLIT_COMPLETED",
  "splitId": "split-uuid",
  "transactionId": "txn-uuid",
  "timestamp": "2024-11-20T14:30:45.123456Z",
  "data": {
    "amountMinor": 100000000,
    "splitAmounts": {"supplier": 94000000, "platformFee": 1000000, ...},
    "gateway": "BACEN_SPLIT_API"
  },
  "signature": "sha256-hmac:abc123..."
}
```

---

## **4. MODELAGEM DE DADOS**

### **4.1 Schemas SQL (Tabelas Críticas)**

**Transactions:**
```sql
CREATE TABLE brlia.transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pool_id VARCHAR(255) NOT NULL,
    transaction_hash VARCHAR(512) NOT NULL UNIQUE,
    supplier_id UUID NOT NULL,
    buyer_id UUID NOT NULL,
    lender_id UUID,
    original_amount_minor BIGINT NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'BRL',
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    risk_score DECIMAL(5,4),
    risk_rating VARCHAR(20),
    split_id UUID,
    split_status VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    settled_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    
    INDEX idx_transactions_pool_id (pool_id),
    INDEX idx_transactions_supplier_id (supplier_id),
    INDEX idx_transactions_status (status),
    INDEX idx_transactions_hash (transaction_hash),
    CONSTRAINT positive_amount CHECK (original_amount_minor > 0)
);
```

**Ledger Entries (Double-Entry):**
```sql
CREATE TABLE brlia.ledger_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL,
    pool_id VARCHAR(255),
    split_id UUID,
    account_id UUID NOT NULL,
    account_code VARCHAR(50) NOT NULL,
    account_type VARCHAR(50) NOT NULL,  -- ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
    amount_minor BIGINT NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'BRL',
    entry_type CHAR(4) NOT NULL,  -- DEBT or CRED
    counterparty_id UUID,
    counterparty_type VARCHAR(50),
    description TEXT,
    entry_hash VARCHAR(512) NOT NULL,
    previous_hash VARCHAR(512) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    
    INDEX idx_ledger_transaction_id (transaction_id),
    INDEX idx_ledger_account_id (account_id),
    CONSTRAINT fk_transaction FOREIGN KEY (transaction_id) REFERENCES brlia.transactions(id),
    CONSTRAINT valid_entry_type CHECK (entry_type IN ('DEBT', 'CRED')),
    CONSTRAINT non_zero_amount CHECK (amount_minor != 0)
);

-- Valida Partidas Dobradas
CREATE OR REPLACE FUNCTION validate_double_entry()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT SUM(CASE WHEN entry_type = 'DEBT' THEN amount_minor ELSE -amount_minor END)
        FROM brlia.ledger_entries WHERE transaction_id = NEW.transaction_id) != 0 THEN
        RAISE EXCEPTION 'Double entry violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Audit Logs (WORM):**
```sql
CREATE TABLE brlia.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID,
    pool_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    before_data JSONB,
    after_data JSONB,
    status VARCHAR(50),
    error_message TEXT,
    created_by UUID,
    created_by_type VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    log_hash VARCHAR(512) NOT NULL,
    previous_hash VARCHAR(512) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    
    INDEX idx_audit_transaction_id (transaction_id),
    INDEX idx_audit_action (action),
    CONSTRAINT fk_transaction FOREIGN KEY (transaction_id) REFERENCES brlia.transactions(id) ON DELETE CASCADE
);
```

**Split Rules:**
```sql
CREATE TABLE brlia.split_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    version INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    rules JSONB NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    
    CONSTRAINT valid_percentages CHECK (
        (SELECT SUM((value::text)::decimal) FROM jsonb_each_text(rules) 
         WHERE key LIKE '%Percentage') = 1.0
    )
);
```

### **4.2 Implementação do Double-Entry Bookkeeping**

```typescript
// ledger/ledger.service.ts
class LedgerService {
    async createEntriesForAdvance(transaction: any, splitResult: any) {
        const entries = [];
        
        // 1. Débito: Recebível do Comprador (Ativo)
        entries.push({
            transactionId: transaction.id,
            accountCode: 'ASSET_RECEIVABLE',
            accountType: 'ASSET',
            amountMinor: transaction.original_amount_minor,
            entryType: 'DEBT',
            counterpartyId: transaction.buyer_id,
            counterpartyType: 'BUYER'
        });
        
        // 2. Crédito: Antecipação ao Fornecedor (Passivo)
        entries.push({
            transactionId: transaction.id,
            accountCode: 'LIABILITY_ADVANCE',
            accountType: 'LIABILITY',
            amountMinor: splitResult.splitAmounts.supplier,
            entryType: 'CRED',
            counterpartyId: transaction.supplier_id,
            counterpartyType: 'SUPPLIER'
        });
        
        // 3. Crédito: Taxa da Plataforma (Receita)
        entries.push({
            transactionId: transaction.id,
            accountCode: 'REVENUE_FEE',
            accountType: 'REVENUE',
            amountMinor: splitResult.splitAmounts.platformFee,
            entryType: 'CRED',
            counterpartyType: 'PLATFORM'
        });
        
        // 4. Crédito: Reserva do Comprador (Passivo)
        entries.push({
            transactionId: transaction.id,
            accountCode: 'LIABILITY_RESERVE',
            accountType: 'LIABILITY',
            amountMinor: splitResult.splitAmounts.buyerReserve,
            entryType: 'CRED',
            counterpartyId: transaction.buyer_id,
            counterpartyType: 'BUYER'
        });
        
        // 5. Crédito: Custo do Capital (Despesa)
        entries.push({
            transactionId: transaction.id,
            accountCode: 'EXPENSE_CAPITAL_COST',
            accountType: 'EXPENSE',
            amountMinor: splitResult.splitAmounts.lenderCost,
            entryType: 'CRED',
            counterpartyId: transaction.lender_id,
            counterpartyType: 'LENDER'
        });
        
        // Valida: Débito = Crédito
        const totalDebit = entries
            .filter(e => e.entryType === 'DEBT')
            .reduce((sum, e) => sum + e.amountMinor, 0);
        const totalCredit = entries
            .filter(e => e.entryType === 'CRED')
            .reduce((sum, e) => sum + e.amountMinor, 0);
        
        if (totalDebit !== totalCredit) {
            throw new Error(`Double entry violation: ${totalDebit} != ${totalCredit}`);
        }
        
        return this.saveEntries(entries);
    }
}
```

---

## **5. JORNADA DO USUÁRIO (UX)**

### **5.1 Fluxo em 5 Passos**

**Passo 1: Upload e OCR da NF**
- Upload PDF/XML da Nota Fiscal
- OCR extrai: CNPJ, valor, vencimento, itens
- Validação de schema
- **Momento de Verdade:** ✓ "Documento processado com sucesso!" (20%)

**Passo 2: Análise de Risco e Compliance**
- Risk Engine (ML + SHAP) calcula score
- Compliance Screening (OFAC, PEP, KYC)
- **Momento de Verdade:** 🛡️ "Score: A (85/100)" (40%)

**Passo 3: Aprovação e Disparo do Split**
- Aprovação manual/automática
- Pool Engine admite em janela de 1ms
- Transaction Orchestrator dispara split
- **Momento de Verdade:** ⚡ "Split executado em 3ms" (60%)

**Passo 4: Confirmação do Settlement**
- splitpayments executa split atômico
- Webhook confirma sucesso
- Ledger registra partidas dobradas
- **Momento de Verdade:** 💰 "Liquidez confirmada!" (80%)

**Passo 5: Notificação e Fechamento**
- Notificação por email/SMS
- Dashboard atualizado
- Comprovante disponível
- **Momento de Verdade:** 🎉 "Transação concluída!" (100%)

### **5.2 Componentes UI (React/TypeScript)**

```typescript
// Estados da UI
type TransactionUIState = 
    | { type: 'IDLE' }
    | { type: 'UPLOADING', progress: number }
    | { type: 'PROCESSING_OCR', progress: number }
    | { type: 'ANALYZING_RISK', score: number }
    | { type: 'EXECUTING_SPLIT', latencyMs: number }
    | { type: 'COMPLETED', data: TransactionData }
    | { type: 'FAILED', error: Error };

// Componente de Status do Split
const SplitState = ({ latencyMs }) => (
    <div className="split-state">
        <div className="spinner">⚡</div>
        <p>Processando split...</p>
        <p className="latency">Latência: {latencyMs}ms</p>
        <progress value={Math.min(latencyMs, 5)} max="5" />
    </div>
);

// Componente de Conclusão
const CompletedState = ({ data }) => (
    <div className="completed-state">
        <div className="check-icon">✓</div>
        <h2>Liquidez confirmada!</h2>
        <p>Valor líquido: R$ {data.netAmount.toLocaleString('pt-BR')}</p>
        <p>Latência: {data.latencyMs}ms</p>
        <button onClick={() => downloadReceipt(data.transactionId)}>
            Baixar comprovante
        </button>
    </div>
);
```

---

## **6. COMPLIANCE, SEGURANÇA E IP**

### **6.1 Checklist Técnico-Jurídico (4 Passos)**

**Passo 1: SLA com LowDataESC**
- Disponibilidade: 99.95%
- Latência p99: < 5ms
- Throughput: 10.000 TPS
- Penalidades: Crédito de 10% por 0.01% abaixo do SLA

**Passo 2: Revenue Share Automático**
```yaml
revenueShare:
  platform: { feePercentage: 0.01, escrowAccount: "BRLIA_MAIN_ESCROW" }
  lender: { spreadPercentage: 0.03, costAccount: "LENDER_FEE_ACCOUNT" }
  buyer: { reservePercentage: 0.02, escrowAccount: "BUYER_RESERVE_POOL" }
```

**Passo 3: Proteção de IP**
- Pool Engine: Trade Secret
- Risk Engine: Trade Secret + Patent Pending
- Split Orchestrator: Trade Secret
- Dados: Confidential (10 anos de retenção)

**Passo 4: Seguro e Garantias**
- Responsabilidade Civil: R$ 50MM
- Cibernéítico: R$ 20MM
- Garantia para Lenders: Fundos segregados + reembolso em 24h

### **6.2 LGPD e Bacen no Código**

**Criptografia de Dados Sensíveis:**
```typescript
class EncryptionService {
    encryptSensitiveData(data: any): EncryptedData {
        const iv = crypto.randomBytes(16);
        const cipher = crypto.createCipheriv('aes-256-gcm', this.key, iv);
        let encrypted = cipher.update(JSON.stringify(data), 'utf8', 'hex');
        encrypted += cipher.final('hex');
        return {
            ciphertext: encrypted,
            iv: iv.toString('hex'),
            authTag: cipher.getAuthTag().toString('hex')
        };
    }
}
```

**Anonimização no Ledger:**
```typescript
class AnonymizedLedgerService {
    getAnonymizedEntries(filter: LedgerFilter) {
        return entries.map(entry => ({
            ...entry,
            counterpartyHash: crypto
                .createHash('sha256')
                .update(entry.counterpartyId + SALT)
                .digest('hex')
                .substring(0, 16)
        }));
    }
}
```

**Validação Bacen:**
```typescript
class BacenComplianceService {
    async validateDocument(document: string, type: 'CPF' | 'CNPJ'): Promise<boolean> {
        if (type === 'CPF') return this.validateCPF(document);
        return this.validateCNPJ(document);
    }
    
    async generateRegulatoryReport(type: 'e-Financeira' | 'SCR', period: DateRange) {
        // Gera relatórios conforme normativas Bacen
    }
}
```

---

## **7. MÉTRICAS DE SUCESSO**

### **7.1 Métricas de Engenharia**

| Métrica | Descrição | Alvo | Ferramenta |
|---------|-----------|------|------------|
| **p99 Latency** | Latência do 99º percentil | **< 5ms** | Prometheus |
| **Split Success Rate** | Taxa de sucesso do split | **> 99.9%** | Prometheus |
| **Idempotency Collision Rate** | Taxa de colisões | **< 0.001%** | Prometheus |
| **Pool Throughput** | Transações por segundo | **> 10.000 TPS** | Prometheus |
| **Netting Ratio** | Razão de netting | **> 0.7** | Prometheus |

**Implementação:**
```typescript
// metrics.service.ts
class MetricsService {
    splitLatencyHistogram = prometheus.createHistogram({
        name: 'brlia_split_latency_seconds',
        buckets: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 2, 5]
    });
    
    splitSuccessCounter = prometheus.createCounter({
        name: 'brlia_split_success_total',
        labelNames: ['gateway']
    });
    
    splitFailureCounter = prometheus.createCounter({
        name: 'brlia_split_failure_total',
        labelNames: ['gateway', 'error_code']
    });
}
```

### **7.2 Métricas de Negócio**

| Métrica | Descrição | Alvo | Ferramenta |
|---------|-----------|------|------------|
| **Volume Total Processado** | Valor total via split | **R$ 100MM/mês** | Metabase |
| **CAC por Lender** | Custo de aquisição | **< R$ 5.000** | CRM + BI |
| **Taxa de Retenção** | Fornecedores que retornam | **> 80%** | PostgreSQL |
| **Receita por Transação** | Receita média | **> 1%** | Ledger |
| **Margem de Contribuição** | Margem após custos | **> 40%** | Contabilidade |

**Implementação:**
```typescript
class BusinessMetricsService {
    async getTotalSplitVolume(period: DateRange): Promise<number> {
        const result = await db.query(`
            SELECT SUM(amount_minor) as total
            FROM brlia.transactions
            WHERE split_status = 'COMPLETED'
            AND created_at BETWEEN $1 AND $2
        `, [period.start, period.end]);
        return Number(result[0]?.total || 0);
    }
}
```

---

## **8. IMPLEMENTAÇÃO TÉCNICA DETALHADA**

### **8.1 Pool Engine (Rust)**

```rust
// pool-engine/src/main.rs
mod clock;
mod ring_buffer;
mod netting;

use std::sync::Arc;
use tokio::sync::Mutex;

#[tokio::main]
async fn main() {
    let clock = clock::MonotonicClock::new();
    let buffer = Arc::new(Mutex::new(ring_buffer::RingBuffer::new()));
    let pool_engine = window::PoolEngine::new(clock, buffer);
    pool_engine.start_workers(4).await;
    tokio::signal::ctrl_c().await.expect("Failed to listen for ctrl-c");
}
```

**CLOCK_MONOTONIC_RAW:**
```rust
pub struct MonotonicClock {
    start_ns: u64,
}

impl MonotonicClock {
    pub fn now_ns(&self) -> u64 {
        unsafe {
            let mut ts = libc::timespec { tv_sec: 0, tv_nsec: 0 };
            libc::clock_gettime(libc::CLOCK_MONOTONIC_RAW, &mut ts);
            (ts.tv_sec as u64) * 1_000_000_000 + (ts.tv_nsec as u64)
        }
    }
    
    pub fn window_id(&self) -> u64 {
        self.now_ns() / 1_000_000  // Janela de 1ms
    }
}
```

**Ring Buffer MPMC Lock-Free:**
```rust
const BUFFER_SIZE: usize = 1024 * 1024; // 1M slots

pub struct RingBuffer<T> {
    buffer: UnsafeCell<[Option<T>; BUFFER_SIZE]>,
    head: AtomicUsize,
    tail: AtomicUsize,
}

impl<T> RingBuffer<T> {
    pub fn push(&self, item: T) -> Result<(), &'static str> {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Acquire);
        
        if (head + 1) % BUFFER_SIZE == tail {
            return Err("Buffer full");
        }
        
        unsafe {
            let buffer = &mut *self.buffer.get();
            buffer[head] = Some(item);
        }
        
        self.head.store((head + 1) % BUFFER_SIZE, Ordering::Release);
        Ok(())
    }
}
```

### **8.2 Transactional Outbox Pattern**

```typescript
// outbox.service.ts
class TransactionalOutbox {
    async publish(
        aggregateType: string,
        aggregateId: string,
        eventType: string,
        payload: any,
    ): Promise<void> {
        const queryRunner = this.dataSource.createQueryRunner();
        await queryRunner.connect();
        await queryRunner.startTransaction();
        
        try {
            // 1. Insere no outbox
            await queryRunner.manager.insert(OutboxEvent, {
                aggregate_type: aggregateType,
                aggregate_id: aggregateId,
                event_type: eventType,
                payload,
                status: 'PENDING',
                created_at: new Date(),
            });
            
            // 2. Publica no Kafka
            await this.producer.send({
                topic: 'outbox-events',
                messages: [{
                    key: `${aggregateType}:${aggregateId}`,
                    value: JSON.stringify({ aggregateType, aggregateId, eventType, payload }),
                }],
            });
            
            await queryRunner.commitTransaction();
        } catch (error) {
            await queryRunner.rollbackTransaction();
            throw error;
        } finally {
            await queryRunner.release();
        }
    }
}
```

### **8.3 Saga Pattern**

```typescript
// saga.orchestrator.ts
class SagaOrchestrator {
    async executeSaga<T>(
        initialContext: T,
        steps: SagaStep<T>[],
        sagaName: string,
    ): Promise<T> {
        const executedSteps: string[] = [];
        let context = initialContext;
        
        for (const step of steps) {
            try {
                context = await step.execute(context);
                executedSteps.push(step.name);
                
                await this.outbox.publish({
                    aggregateType: 'Saga',
                    aggregateId: context.transactionId,
                    eventType: `SagaStepCompleted.${step.name}`,
                    payload: context,
                });
            } catch (error) {
                // Compensação em ordem reversa
                for (let i = executedSteps.length - 1; i >= 0; i--) {
                    const stepName = executedSteps[i];
                    const step = steps.find(s => s.name === stepName);
                    if (step) {
                        await step.compensate(context);
                    }
                }
                throw error;
            }
        }
        
        return context;
    }
}
```

### **8.4 Cliente splitpayments (gRPC)**

```typescript
// splitpayments.client.ts
@Injectable()
export class SplitPaymentsClient implements OnModuleInit {
    @Client({
        transport: Transport.GRPC,
        options: {
            url: process.env.SPLITPAYMENTS_GRPC_URL,
            package: 'brlia.splitpayments.v1',
            protoPath: join(__dirname, 'proto/splitpayments.proto'),
            tls: {
                cert: process.env.GRPC_CLIENT_CERT,
                key: process.env.GRPC_CLIENT_KEY,
                ca: process.env.GRPC_CA_CERT,
            },
        },
    })
    private client: ClientGrpc;
    
    async createSplit(request: CreateSplitRequest): Promise<CreateSplitResponse> {
        return lastValueFrom(this.client.getService('SplitPaymentsService').createSplit(request));
    }
}
```

### **8.5 Webhook Handler**

```typescript
// splitpayments.webhook.controller.ts
@Controller('webhooks/splitpayments')
export class SplitPaymentsWebhookController {
    @Post()
    async handleWebhook(
        @Headers('X-Splitpayments-Signature') signature: string,
        @Headers('X-Splitpayments-Event-Type') eventType: string,
        @Body() payload: any,
    ) {
        // 1. Validar assinatura
        await this.validateSignature(signature, payload);
        
        // 2. Processar evento
        switch (eventType) {
            case 'SPLIT_COMPLETED':
                await this.handleSplitCompleted(payload);
                break;
            case 'SPLIT_FAILED':
                await this.handleSplitFailed(payload);
                break;
            case 'ESCROW_RETAINED':
                await this.handleEscrowRetained(payload);
                break;
        }
        
        // 3. Auditar
        await this.auditService.log({
            action: `WEBHOOK_${eventType}`,
            entityType: 'SplitTransaction',
            entityId: payload.splitId,
            data: payload,
        });
        
        return { status: 'processed' };
    }
}
```

### **8.6 Idempotência**

```typescript
// idempotency.service.ts
@Injectable()
export class IdempotencyService {
    private readonly redis: Redis;
    
    async checkAndSet(key: string, value: any): Promise<{ isNew: boolean; existing?: any }> {
        const existing = await this.redis.get(key);
        if (existing) {
            return { isNew: false, existing: JSON.parse(existing) };
        }
        await this.redis.setex(key, 86400, JSON.stringify(value));
        return { isNew: true };
    }
    
    generateKey(prefix: string, request: any): string {
        const payloadHash = crypto
            .createHash('sha256')
            .update(JSON.stringify(request))
            .digest('hex');
        return `${prefix}:${payloadHash}`;
    }
}
```

---

## **9. DEPLOY E INFRAESTRUTURA**

### **9.1 Dockerfile (Pool Engine)**

```dockerfile
FROM rust:1.70 as builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
RUN apt-get update && apt-get install -y pkg-config libssl-dev
RUN cargo build --release

FROM debian:bullseye-slim
WORKDIR /app
COPY --from=builder /app/target/release/pool-engine .
COPY config.yaml .
EXPOSE 8080
ENTRYPOINT ["./pool-engine"]
```

### **9.2 Kubernetes Deployment**

```yaml
# pool-engine/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pool-engine
spec:
  replicas: 4
  selector:
    matchLabels:
      app: brlia
      component: pool-engine
  template:
    metadata:
      labels:
        app: brlia
        component: pool-engine
    spec:
      containers:
        - name: pool-engine
          image: brlia/pool-engine:v2.0.0
          resources:
            limits:
              cpu: "2"
              memory: "1Gi"
            requests:
              cpu: "1"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8080
            initialDelaySeconds: 30
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: pool-engine
spec:
  selector:
    app: brlia
    component: pool-engine
  ports:
    - name: http
      port: 80
      targetPort: 8080
  type: ClusterIP
```

### **9.3 Helm Chart**

```yaml
# charts/brlia/values.yaml
poolEngine:
  enabled: true
  replicaCount: 4
  image:
    repository: brlia/pool-engine
    tag: v2.0.0
  resources:
    limits:
      cpu: 2
      memory: 1Gi
    requests:
      cpu: 1
      memory: 512Mi

postgresql:
  enabled: true
  auth:
    username: brlia
    password: "brlia-secret"
    database: brlia
  primary:
    persistence:
      size: 100Gi

kafka:
  enabled: true
  replicaCount: 3
  persistence:
    size: 200Gi

prometheus:
  enabled: true
grafana:
  enabled: true
```

---

## **10. CI/CD**

### **10.1 GitHub Actions Workflow**

```yaml
# .github/workflows/ci-cd.yaml
name: BRLIA V2 CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: brlia
          POSTGRES_PASSWORD: brlia-test
          POSTGRES_DB: brlia-test
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
          
      - run: npm ci
      - run: pip install -r requirements.txt
      - run: cargo fetch
      
      - run: npm run lint
      - run: npm run type-check
      - run: npm run test:unit
      - run: cargo test --workspace
      - run: npm run test:integration
      - run: npm run test:e2e

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          file: pool-engine/Dockerfile
          push: true
          tags: ghcr.io/${{ github.repository }}/pool-engine:${{ github.sha }}

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-helm@v3
      - run: |
          helm upgrade --install brlia-v2 ./charts/brlia \
            --namespace brlia-staging \
            --create-namespace \
            --values ./charts/brlia/values-staging.yaml

  deploy-production:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-helm@v3
      - run: |
          helm upgrade --install brlia-v2 ./charts/brlia \
            --namespace brlia-production \
            --create-namespace \
            --values ./charts/brlia/values-production.yaml
```

---

## **11. ROADMAP DE IMPLEMENTAÇÃO**

| Fase | Duração | Entregáveis | Prioridade |
|------|---------|-------------|------------|
| **Fase 1: Core** | 4 semanas | Pool Engine, Transaction Orchestrator, Ledger | ⭐⭐⭐⭐⭐ |
| **Fase 2: Integração** | 2 semanas | Cliente splitpayments, Webhooks | ⭐⭐⭐⭐⭐ |
| **Fase 3: UX** | 3 semanas | Frontend (5 passos), Notificações | ⭐⭐⭐⭐ |
| **Fase 4: Compliance** | 2 semanas | LGPD, Bacen, Auditoria | ⭐⭐⭐⭐ |
| **Fase 5: Monitoramento** | 1 semana | Métricas, Alertas, Dashboards | ⭐⭐⭐ |
| **Fase 6: Testes** | 2 semanas | Testes E2E, Benchmark, Load Testing | ⭐⭐⭐⭐ |
| **Fase 7: Deploy** | 1 semana | Kubernetes, Co-location, CI/CD | ⭐⭐⭐ |

---

## **12. CHECKLIST DE ENTREGA**

- [ ] **Arquitetura:** Documentação completa (este documento)
- [ ] **API:** Contratos gRPC e REST definidos
- [ ] **Banco de Dados:** Schemas SQL implementados
- [ ] **Pool Engine:** Implementado em Rust
- [ ] **Transaction Orchestrator:** Saga Pattern implementado
- [ ] **Cliente splitpayments:** gRPC + REST + Retry
- [ ] **Idempotência:** Mecanismo funcionando
- [ ] **Ledger:** Partidas dobradas validadas
- [ ] **Audit Trail:** Hash-chain implementado
- [ ] **Compliance:** LGPD e Bacen aplicados
- [ ] **Webhooks:** Handler implementado
- [ ] **UI:** Fluxo em 5 passos
- [ ] **Testes:** Unitários, Integração, E2E
- [ ] **Monitoramento:** Métricas configuradas
- [ ] **Deploy:** Kubernetes + Helm
- [ ] **CI/CD:** GitHub Actions

---

## **13. CONCLUSÃO**

O **BRLIA V2** representa uma evolução significativa em relação ao piloto manual, oferecendo:

1. **Liquidez em milissegundos** (p99 < 5ms) via integração nativa com o `splitpayments` do LowDataESC
2. **Split atômico** executado na camada de infraestrutura, garantindo consistência
3. **Custódia segregada** com auditoria imutável via hash-chain + WORM
4. **Arquitetura de alta performance** com Pool Engine em Rust e janela de 1ms
5. **Compliance completo** com LGPD, Bacen e normativas financeiras

**Próximos Passos:**
1. Iniciar implementação do **Pool Engine em Rust**
2. Desenvolver o **Transaction Orchestrator com Saga Pattern**
3. Implementar o **cliente gRPC para splitpayments**
4. Criar os **schemas do banco de dados**
5. Desenvolver o **Frontend com fluxo em 5 passos**

---

> **"Liquidez em milissegundos, com custódia segregada e auditoria imutável."**
> — BRLIA V2 Mission Statement

**Documento gerado em:** 2024-11-20  
**Versão:** 2.0.0  
**Classificação:** Confidencial  
**Próxima revisão:** 2025-01-20
