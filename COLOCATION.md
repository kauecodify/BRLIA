# COLOCATION

## 1. Posicionamento

O motor deixa de ser um servico remoto e passa a rodar co-localizado com o
servidor da empresa (nuvem ou servidor proprio), junto ao ERP, ao core banking
ou ao TMS, sem substitui-los, sem reinicia-los e sem alterar seu codigo.

## 2. Modos de deploy

BRLIA_DEPLOY_MODE admite quatro valores. Mesma imagem, mesmo binario, mesmo
contrato gRPC; a diferenca esta apenas em runtime/modes.yaml.

| Modo       | Superficie                         | Descricao                                  |
|------------|------------------------------------|--------------------------------------------|
| sidecar    | Kubernetes, container no mesmo pod | UDS local, sem ingress publico             |
| daemonset  | K3s e edge, um agente por no       | UDS no host, egress outbound-only          |
| standalone | systemd em servidor proprio        | agente nativo, socket em /var/run/brlia    |
| managed    | AWS ECS, GCP Cloud Run, Azure Container Apps | sem UDS, gRPC com mTLS obrigatorio |

## 3. host-adapter

- Roda junto ao server da empresa.
- Caminho preferencial: Unix Domain Socket em /var/run/brlia/pool.sock,
  permissao 0660, grupo brlia.
- Fallback TCP somente com mTLS e identidade SPIFFE.
- Conectores erp, core-banking, tms e pix-api operam somente leitura.
- attach.sh acopla o agente sem reiniciar o processo do host, sem alterar
  codigo do host, sem ingress publico e sem migracao de dados.
- detach.sh drena a janela corrente, fecha o WAL e desacopla.

## 4. Politica de egress

egress_policy.yaml define local-first e outbound-only no modo hybrid: dados de
cliente permanecem no host; somente eventos pseudonimizados alcancam o control
plane. Nenhuma porta publica e aberta no modo hybrid.

## 5. Modo degradado

runtime/degraded-mode.yaml: sem control plane, o host-adapter mantem WAL local
por ate 60 s. Escrita fail-closed com 503 POOL_DEGRADED; leitura fail-open;
replay idempotente no reattach, sem duplicidade por idempotency-key. Perda
silenciosa e duplo lancamento sao proibidos.

## 6. Orcamento de excecao

Carve-outs de cada host (por exemplo, connector de leitura com atraso conhecido
ou janela estendida em hardware restrito) sao registrados no orcamento de
excecao, vigiados por metrica e com vigencia definida; expiram automaticamente.
