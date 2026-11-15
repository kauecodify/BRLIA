# host-adapter

Agente que roda JUNTO ao server da empresa (ERP, core banking ou TMS), sem
substitui-lo, sem reinicia-lo e sem alterar seu codigo.

## Transportes

- uds/: Unix Domain Socket em /var/run/brlia/pool.sock, 0660, grupo brlia.
  Caminho preferencial.
- grpc/: contrato AdmitOperation, PoolClosed, Reconcile (pool.proto), unico
  nos quatro modos de deploy.
- mtls/: fallback TCP somente com mTLS e identidade SPIFFE.

## Conectores

connectors/: erp, core-banking, tms e pix-api, todos somente leitura. Escrita
no host e proibida e levanta PermissionError.

## Politicas

- egress_policy.yaml: local-first, outbound-only; dados de cliente permanecem
  no host; somente eventos pseudonimizados saem.
- Modo degradado: WAL local por ate 60 s (wal_local.py), escrita fail-closed
  com 503 POOL_DEGRADED, leitura fail-open, replay idempotente por
  idempotency-key no reattach.

## Operacao

    sudo ../scripts/attach.sh --mode standalone
    sudo ../scripts/detach.sh
