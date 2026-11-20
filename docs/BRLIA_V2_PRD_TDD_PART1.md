# **BRLIA V2 - DOCUMENTO DE ESPECIFICAÇÃO DE PRODUTO E ARQUITETURA TÉCNICA (PRD + TDD)**

> **Versão:** 2.0.0  
> **Data:** 2024-11-20  
> **Classificação:** Confidencial - Apenas para uso interno e times autorizados  
> **Autor:** CTO Office - BRLIA  

---

## **ÍNDICE EXECUTIVO**

| Seção | Descrição |
|--------|-----------|
| 1 | Estratégia e Proposta de Valor (V2) |
| 2 | Arquitetura de Sistema e Engenharia de Baixa Latência |
| 3 | Contratos de API e Integração |
| 4 | Modelagem de Dados e Ledger Financeiro |
| 5 | Jornada do Usuário e Fluxo Operacional |
| 6 | Compliance, Segurança e Resolução Societária |
| 7 | Métricas de Sucesso |

---

## **1. ESTRATÉGIA E PROPOSTA DE VALOR (V2)**

### **1.1 Pitch Fornecedor: "Liquidez Atômica"**

#### **Problema do Fornecedor**
- **Dor principal:** Recebíveis com prazo médio de 30-90 dias
- **Custo de oportunidade:** Capital imobilizado = perda de giros de caixa
- **Burocracia atual:** Análise manual, documentação física, aprovação em 5-10 dias úteis
- **Risco:** Incerteza sobre pagamento, dependência do comprador

#### **Solução BRLIA V2**

```
LIQUIDEZ ATÔMICA - T+0 REAL
- Antecipação em MILISSEGUNDOS (p99 < 5ms)
- Sem burocracia: Upload NF -> Aprovação -> Liquidez automática
- Discrição total: Operação confidencial, sem exposição do comprador
- Custódia segregada: Recursos em escrow até liquidação final
- Taxa competitiva: Spread base CDI + risco calculado por IA
```

#### **Linguagem Técnica para Vendas B2B**

**Para CFOs/Financeiros:**
```
Reduza seu DSO (Days Sales Outstanding) de 60 para 0 dias com custódia segregada e auditável.
Nosso pool de liquidez com genesis de R$ 100MM garante execução atômica via splitpayments (LowDataESC).
Integração direta com seu ERP via Unix Domain Socket - sem API pública, sem exposição.
```

**Para CTOs/Engenheiros:**
```
Arquitetura orientada a eventos com:
- Pool engine em Rust (PyO3) - janela de 1ms determinística
- Transactional outbox + Saga pattern para consistência distribuída
- Idempotency key obrigatório em todas as escritas
- Integração nativa com splitpayments via gRPC/mTLS
- Co-location: executa junto ao seu servidor sem restart
```

#### **Diferenciais Competitivos**

| Feature | BRLIA V2 | Concorrente A | Concorrente B |
|---------|----------|---------------|---------------|
| Latência | **p99 < 5ms** | 2-5 segundos | 10-30 segundos |
| Integração | **UDS/mTLS** | REST HTTP | REST HTTP |
| Custódia | **Segregada + Imutável** | Comum | Comum |
| Auditoria | **Hash-chain WORM** | Logs simples | Logs simples |

---

### **1.2 Pitch Lender/Parceiro: "Settlement Segregado e Imutável"**

#### **Problema do Lender**
- **Risco de desvio:** Recursos podem ser misturados ou desviados
- **Falta de transparência:** Dificuldade em auditar destino dos fundos
- **Custo operacional:** Reconciliação manual de splits
- **Compliance:** Necessidade de rastreabilidade para Bacen/LGPD

#### **Solução BRLIA V2**

```
SETTLEMENT SEGREGADO E IMUTÁVEL
- Split executado NA CAMADA DE INFRAESTRUTURA
- Custódia segregada por contraparte (escrow multimoeda)
- Auditoria em TEMPO REAL via hash-chain + WORM
- Risco ZERO de desvio: LowDataESC splitpayments como fonte da verdade
- Revenue share automático via código (sem intervenção manual)
```

#### **Garantias para Lenders**

**1. Imutabilidade Financeira**
```sql
CREATE TABLE ledger_entries (
    id UUID PRIMARY KEY,
    pool_id VARCHAR(255) NOT NULL,
    transaction_id UUID NOT NULL,
    account_id UUID NOT NULL,
    amount_minor BIGINT NOT NULL,
    entry_type CHAR(4) NOT NULL,  -- DEBT/CRED
    hash VARCHAR(512) NOT NULL,
    previous_hash VARCHAR(512) NOT NULL,
    CONSTRAINT immutable_ledger CHECK (
        (SELECT SUM(CASE WHEN entry_type = 'DEBT' THEN amount_minor ELSE -amount_minor END) 
         FROM ledger_entries WHERE transaction_id = ledger_entries.transaction_id) = 0
    )
);
```

**2. Split Atômico via LowDataESC**
```typescript
interface SplitTransaction {
  id: string;
  originalAmount: number;
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

## **2. ARQUITETURA DE SISTEMA E ENGENHARIA DE BAIXA LATÊNCIA**

### **2.1 Arquitetura de Alto Nível**

```
BRLIA V2 - ARQUITETURA

  [Fornecedor]    [Comprador]    [Lender]    [ERP/legacy]
       |               |              |              |
       └───────────────┴──────────────┴──────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │   API Gateway /     │
         │   Load Balancer      │
         │   (NGINX)            │
         └────────────┬────────┘
                      │
         ┌────────────▼────────┐
         │   Control Plane      │
         │   (FastAPI)          │
         │   - Auth Service     │
         │   - File Processor   │
         │   - Risk Engine      │
         │   - Compliance       │
         └────────┬─────────────┘
                  │
         ┌────────▼────────┐
         │ Pool Engine      │  ← Janela 1ms (Rust/PyO3)
         │ (Netting)        │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │ Transaction      │
         │ Orchestrator     │  ← Saga Pattern
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │ Message Broker    │  ← Kafka/Redpanda
         │ (Outbox)         │
         └────────┬────────┘
                  │
   ┌──────────────┼──────────────┐
   │              │              │
   ▼              ▼              ▼
[Settlement]  [Ledger]      [Audit Trail]
[Engine]      [Double-Entry][WORM + Hash-chain]
   │              │              │
   └──────────────┼──────────────┘
                  │
         ┌────────▼────────┐
         │ LOWDATAESC       │
         │ splitpayments    │  ← Fonte da Verdade
         │ (BACEN/Iugu/     │
         │  Asaas/Efi)     │
         └─────────────────┘
```

### **2.2 Garantia de Latência em Milissegundos**

**Caminho Quente (Hot Path) - p99 < 5ms:**
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
```

**Otimizações:**
- **CLOCK_MONOTONIC_RAW:** Sem drift, sem NTP
- **Ring Buffer MPMC Lock-Free:** Zero-copy, sem lock
- **Zero-Copy Serialization:** Sem alocação de memória

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
      "bankCode": "104",
      "agency": "0001",
      "accountNumber": "12345678"
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
    "supplier": 94000000,
    "platformFee": 1000000,
    "buyerReserve": 2000000,
    "lenderCost": 3000000
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
  "errorMessage": "Gateway Iugu indisponível. Fundos retidos em escrow.",
  "escrowAccount": "ESCROW_BRLIA_FALLBACK",
  "retryInSeconds": 300
}
```

### **3.3 Webhook Integration**

**splitpayments -> BRLIA:**
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

## **4. MODELAGEM DE DADOS E LEDGER FINANCEIRO**

### **4.1 Schemas SQL**

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
    account_type VARCHAR(50) NOT NULL,
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
    INDEX idx_ledger_entry_hash (entry_hash),
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
    INDEX idx_audit_created_at (created_at),
    CONSTRAINT fk_transaction FOREIGN KEY (transaction_id) REFERENCES brlia.transactions(id) ON DELETE CASCADE
);
```

---

## **5. JORNADA DO USUÁRIO (UX) E FLUXO OPERACIONAL**

### **5.1 Fluxo em 5 Passos**

**Passo 1: Upload e OCR da NF**
- Upload PDF/XML da Nota Fiscal
- OCR extrai: CNPJ fornecedor/comprador, valor, vencimento, itens
- Validação de schema
- **Momento de Verdade:** "Documento processado com sucesso!" (20%)

**Passo 2: Análise de Risco e Compliance**
- Risk Engine (ML + SHAP) calcula score
- Compliance Screening (OFAC, PEP, KYC)
- Aprovação automática se score >= limite
- **Momento de Verdade:** "Análise concluída - Score: A (85/100)" (40%)

**Passo 3: Aprovação e Disparo do Split**
- Aprovação manual (se necessário)
- Pool Engine admite em janela de 1ms
- Transaction Orchestrator dispara split via splitpayments
- **Momento de Verdade:** "Processando split..." → "Split executado em 3ms" (60%)

**Passo 4: Confirmação do Settlement**
- splitpayments executa split atômico
- Webhook confirma sucesso
- Ledger registra partidas dobradas
- **Momento de Verdade:** "Liquidez confirmada!" (80%)

**Passo 5: Notificação e Fechamento**
- Notificação por email/SMS
- Dashboard atualizado
- Comprovante disponível para download
- **Momento de Verdade:** "Transação concluída!" (100%)

### **5.2 Componentes UI**

```typescript
// Estado da UI
type TransactionUIState = 
    | { type: 'IDLE' }
    | { type: 'UPLOADING', progress: number }
    | { type: 'PROCESSING_OCR', progress: number }
    | { type: 'ANALYZING_RISK', score: number }
    | { type: 'AWAITING_APPROVAL' }
    | { type: 'EXECUTING_SPLIT', latencyMs: number }
    | { type: 'SETTLING', progress: number }
    | { type: 'COMPLETED', data: TransactionCompletedData }
    | { type: 'FAILED', error: Error };

// Componente de Status
const SplitState = ({ latencyMs }) => (
    <div>
        <div className="spinner">⚡</div>
        <p>Processando split...</p>
        <p>Latência: {latencyMs}ms</p>
        <progress value={Math.min(latencyMs, 5)} max="5" />
    </div>
);

const CompletedState = ({ data }) => (
    <div>
        <div>✓</div>
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

## **6. COMPLIANCE, SEGURANÇA E RESOLUÇÃO SOCIETÁRIA**

### **6.1 Checklist Técnico-Jurídico (4 Passos)**

**Passo 1: SLA com LowDataESC**
- Disponibilidade: 99.95%
- Latência p99: < 5ms
- Throughput: 10.000 TPS
- Penalidades: Crédito de 10% por 0.01% abaixo do SLA

**Passo 2: Revenue Share Automático**
```yaml
revenueShare:
  platform:
    feePercentage: 0.01
    escrowAccount: "BRLIA_MAIN_ESCROW"
  lender:
    spreadPercentage: 0.03
    costAccount: "LENDER_FEE_ACCOUNT"
  buyer:
    reservePercentage: 0.02
    escrowAccount: "BUYER_RESERVE_POOL"
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
        const jsonData = JSON.stringify(data);
        const iv = crypto.randomBytes(16);
        const cipher = crypto.createCipheriv('aes-256-gcm', this.key, iv);
        let encrypted = cipher.update(jsonData, 'utf8', 'hex');
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
    getAnonymizedEntries(filter: LedgerFilter): AnonymizedLedgerEntry[] {
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
    
    async validateTransactionLimits(transaction: any): Promise<LimitValidationResult> {
        // Valida limites conforme Res. BCB 4.658/2018
    }
}
```

---

## **7. MÉTRICAS DE SUCESSO**

### **7.1 Métricas de Engenharia**

| Métrica | Descrição | Alvo | Ferramenta |
|---------|-----------|------|------------|
| p99 Latency | Latência do 99º percentil | **< 5ms** | Prometheus |
| Split Success Rate | Taxa de sucesso do split | **> 99.9%** | Prometheus |
| Idempotency Collision Rate | Taxa de colisões de idempotency key | **< 0.001%** | Prometheus |

**Implementação:**
```typescript
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
| Volume Total Processado | Valor total via split | **R$ 100MM/mês** | Metabase |
| CAC por Lender | Custo de aquisição | **< R$ 5.000** | CRM + BI |
| Taxa de Retenção | Fornecedores que retornam | **> 80%** | PostgreSQL |

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
    
    async getLenderCAC(period: DateRange): Promise<number> {
        const costs = await this.getMarketingAndSalesCosts(period);
        const newLenders = await this.getNewLenders(period);
        return newLenders > 0 ? costs / newLenders : 0;
    }
}
```

---

## **8. CONCLUSÃO**

### **8.1 Resumo da Arquitetura V2**

| Component | Tecnologia | SLA |
|-----------|------------|-----|
| API Gateway | NGINX | 99.95% |
| Pool Engine | Rust + PyO3 | p99 < 1ms |
| Transaction Orchestrator | Python | 99.9% |
| splitpayments | LowDataESC | p99 < 5ms |

### **8.2 Checklist de Entrega**

- [ ] Arquitetura documentada
- [ ] Contratos gRPC/REST definidos
- [ ] Schemas SQL implementados
- [ ] Cliente splitpayments
- [ ] Idempotência funcionando
- [ ] Saga Pattern implementado
- [ ] Ledger com partidas dobradas
- [ ] Audit Trail com hash-chain
- [ ] Compliance LGPD/Bacen
- [ ] Métricas configuradas
- [ ] UI em 5 passos
- [ ] Testes E2E
- [ ] Deploy Kubernetes

### **8.3 Roadmap**

| Fase | Duração | Entregáveis |
|------|---------|-------------|
| Core | 4 semanas | Pool Engine, Orchestrator, Ledger |
| Integração | 2 semanas | Cliente splitpayments, Webhooks |
| UX | 3 semanas | Frontend, Notificações |
| Compliance | 2 semanas | LGPD, Bacen, Auditoria |
| Monitoramento | 1 semana | Métricas, Alertas |
| Testes | 2 semanas | E2E, Benchmark |
| Deploy | 1 semana | Kubernetes, CI/CD |

---

> **Documento gerado em:** 2024-11-20
> **Versão:** 2.0.0
> **Classificação:** Confidencial

**"Liquidez em milissegundos, com custódia segregada e auditoria imutável."**
— BRLIA V2 Mission Statement
