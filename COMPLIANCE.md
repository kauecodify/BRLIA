# COMPLIANCE

## 1. Escopo

Este documento descreve controles de conformidade e residencia de dados por modo
de deploy. A geracao do repositorio nao afirma conformidade regulatoria automatica.

## 2. Residencia de dados por modo de deploy

| Modo       | Dados de cliente            | Eventos pseudonimizados      | Base normativa relevante         |
|------------|-----------------------------|------------------------------|----------------------------------|
| sidecar    | permanecem no host/pod      | saem para o control plane    | LGPD                             |
| daemonset  | permanecem no no            | saem para o control plane    | LGPD, politicas do no            |
| standalone | permanecem no servidor      | saem para o control plane    | LGPD                             |
| managed    | permanecem na regiao cloud  | saem para o control plane    | LGPD, GDPR, contratual da nuvem  |
| hybrid     | permanecem no host (local-first) | outbound-only, pseudonimizados | LGPD, GDPR             |

Regras:

1. Dados de cliente (titular, documento, contraparte) nao deixam o host em
   nenhum modo. Somente eventos pseudonimizados sao exportados.
2. Pseudonimizacao: identificadores diretos sao substituidos por hashes com
   sal por host; o sal permanece no host.
3. Base legal, finalidade e retencao por categoria sao declaradas em
   configs/jurisdictions/*.yaml.
4. Direitos do titular (acesso, correcao, eliminacao, portabilidade) sao
   atendidos no host; o control plane retem apenas pseudonimos.

## 3. Brasil

- PIX SPI/DICT/MED 2.0/Pix Automatico com idempotencia por endToEndId.
- SPB/STR, CIP, CCS.
- Res. BCB 80/2021 (arranjos de pagamento), Res. 4.658/2018 (cambio),
  PLD/FT (Lei 9.613/1998 e Res. BCB), LGPD (Lei 13.709/2018).
- e-Financeira, SCR. Reporting derivado do outbox, sem recomputar saldos.

## 4. Internacional

- ISO 20022: pain.001, pacs.008, camt.053 com XSD em configs/iso20022/.
- SWIFT gpi, ACH/Fedwire, SEPA/SCT Inst com IBAN, FPS/CHAPS, FAST/PayNow.
- FATF R.16/Travel Rule, OFAC/SDN, PEP, KYC/KYB/KYT.
- MiCA/AMLD6 (UE), FinCEN (US), CRS/FATCA, W-8BEN/W-9.

## 5. Genesis e capital

O genesis de R$ 100.000.000,00 e imutavel, com hash encadeado em WORM. Nenhum
lancamento com pool_id tem natureza de capital. Documentacao de capital usa a
formulacao "sujeito a validacao do regulador e da assessoria".

## 6. Trilhas

- audit-trail: WORM com hash encadeado; registra pool_id e hash da janela.
- Toda escrita exige idempotency-key; replay nao produz duplo lancamento.
