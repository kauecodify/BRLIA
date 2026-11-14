# SEED CAPITAL

## 1. Identificacao

| Campo            | Valor                                                       |
|------------------|-------------------------------------------------------------|
| Valor            | R$ 100.000.000,00                                           |
| amount_minor     | 10000000000                                                 |
| Moeda            | BRL                                                         |
| Scale            | 2                                                           |
| Instrumento      | Integralizacao de capital social em moeda nacional (AFAC)   |
| Data de referencia | Definida pelo ato societario registravel                  |
| Pre-money        | N/A para pre-seed; consulte CAP_TABLE.md                    |
| Correlation id   | seed-genesis-0000000000000001                               |

## 2. Origem

Aporte inicial dos socios fundadores, integralizado em especie, destinado a
formacao de capital de giro e garantias operacionais. A origem dos recursos e
documentada nos instrumentos societarios e comprovantes bancarios do emissor.

Todo registro de valor, data, instrumento, pre-money, diluicao e capital minimo
neste documento e declarativo e permanece sujeito a validacao do regulador e da
assessoria.

## 3. Contabilidade

Lancamento de abertura em partidas dobradas:

- Debito: Ativo Circulante, Caixa/Bancos, 10000000000 minor units.
- Credito: Patrimonio Liquido, Capital Social (AFAC), 10000000000 minor units.

A soma dos debitos e igual a soma dos creditos. O arquivo seed/genesis_entries.sql
materializa o par contabil e seed/genesis.json fixa o valor unico.

## 4. Imutabilidade

1. O genesis nao admite UPDATE nem DELETE; os grants do banco nao incluem essas
   operacoes para a role operacional.
2. apply-seed.sh e idempotente: falha se correlation_id ja existir.
3. O audit-trail encadeia o hash do genesis em WORM.
4. Nenhum lancamento do pool tem natureza de capital; verify_seed.py valida que
   nenhum pool mutou o genesis.

## 5. Capital minimo

O capital minimo operacional por jurisdicao e parametro de configs/jurisdictions/
e de treasury_policy.yaml. Qualquer ajuste e sujeito a validacao do regulador e
da assessoria.
