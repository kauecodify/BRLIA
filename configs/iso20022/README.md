# ISO 20022

Mensagens usadas pelo file-processor e pelo settlement-engine:

- pain.001: instrucao de debito direto.
- pacs.008: transferencia creditica entre instituicoes.
- camt.053: extrato bancario.

Os arquivos XSD neste diretorio sao envelopes de integracao: referenciam o
conjunto esquematico oficial ISO 20022 (head.001 e as mensagens correspondentes)
e devem ser substituidos, em homologacao, pelos XSD oficiais publicados pelo
padrao ISO 20022, sem alteracao dos consumidores.
