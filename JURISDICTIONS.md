# JURISDICTIONS

## 1. Escopo

A camada configuravel de jurisdicoes cobre br, us, eu, uk, sg e global. Cada
jurisdicao possui arquivo declarativo em configs/jurisdictions/ e modulo
carregador em infrastructure/jurisdiction-engine/.

## 2. Matriz

| Jurisdicao | Moeda funcional | Sistemas de pagamento           | Reporting           | Capital minimo |
|------------|-----------------|----------------------------------|---------------------|----------------|
| br         | BRL             | PIX, SPB/STR                     | BACEN, e-Financeira | Configuravel   |
| us         | USD             | ACH, Fedwire, RTP                | FinCEN, CRS/FATCA   | Configuravel   |
| eu         | EUR             | SEPA, SCT Inst                   | MiCA, AMLD6, CRS    | Configuravel   |
| uk         | GBP             | FPS, CHAPS                       | FCA reporting       | Configuravel   |
| sg         | SGD             | FAST, PayNow                     | MAS reporting       | Configuravel   |
| global     | Multi           | SWIFT gpi                        | CRS/FATCA           | Configuravel   |

## 3. Regras

1. A jurisdicao integra pool_key e determina a particao de netting.
2. Requisitos de dados e residencia por modo de deploy estao em COMPLIANCE.md.
3. Carve-outs por host e por jurisdicao ficam no orcamento de excecao, com
   vigencia definida e monitoramento obrigatorio.
4. Nenhuma afirmacao de conformidade automatica e feita nesta geracao.
