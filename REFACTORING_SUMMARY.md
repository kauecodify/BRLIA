# REFACTORING SUMMARY (historico da V1)

## 1. V1

A V1 consolidou o repositorio inicial em uma estrutura de servicos sob
infrastructure/, com control plane Python 3.12 e FastAPI, PostgreSQL 16 com
partidas dobradas, outbox transacional e seed de capital de R$ 100.000.000,00.

## 2. V2

A V2 estabeleceu a fonte normativa em ARCHITECTURE_V2.md, a matriz de
jurisdicoes, o fx-engine com PTAX e trilha de cotacao, o multi-currency-ledger
em minor units e o reporting derivado do outbox.

## 3. V2.1

A V2.1 desloca o motor para co-localizacao com o servidor da empresa em quatro
modos de deploy (sidecar, daemonset, standalone, managed), introduz o
host-adapter com UDS preferencial e mTLS como fallback, e define o pool como
janela deterministica de 1 ms com netting multilateral em nucleo compilado
fora do interpretador Python. Redis e PostgreSQL ficam proibidos no trajeto de
admissao; a persistencia passa a ser assincrona via outbox e WAL local.

## 4. Contrato preservado

O genesis de R$ 100.000.000,00 permanece imutavel e verificado contra qualquer
lancamento do pool; index.html segue byte a byte; a geracao nao instala
dependencias, nao sobe containers e nao executa benchmark.
