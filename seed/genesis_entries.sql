-- Genesis de abertura: R$ 100.000.000,00 em partidas dobradas.
-- Idempotente: falha se correlation_id ja existir.
BEGIN;

INSERT INTO ledger_entries (
  correlation_id, entry_id, account, account_name, side,
  amount_minor, currency, scale, nature, pool_id, entry_hash, created_at
)
SELECT
  v.correlation_id, v.entry_id, v.account, v.account_name, v.side,
  v.amount_minor, v.currency, v.scale, v.nature, NULL, v.entry_hash, v.created_at
FROM (VALUES
  (
    'seed-genesis-0000000000000001',
    'seed-entry-0000000000000001',
    '1.1.1.01',
    'Ativo Circulante - Caixa/Bancos',
    'D',
    10000000000::bigint,
    'BRL',
    2,
    'capital',
    encode(digest('seed-genesis-0000000000000001|seed-entry-0000000000000001|1.1.1.01|D|10000000000', 'sha256'), 'hex'),
    TIMESTAMPTZ '2025-01-01T00:00:00Z'
  ),
  (
    'seed-genesis-0000000000000001',
    'seed-entry-0000000000000002',
    '2.1.1.01',
    'Patrimonio Liquido - Capital Social (AFAC)',
    'C',
    10000000000::bigint,
    'BRL',
    2,
    'capital',
    encode(digest('seed-genesis-0000000000000001|seed-entry-0000000000000002|2.1.1.01|C|10000000000', 'sha256'), 'hex'),
    TIMESTAMPTZ '2025-01-01T00:00:00Z'
  )
) AS v(
  correlation_id, entry_id, account, account_name, side,
  amount_minor, currency, scale, nature, entry_hash, created_at
)
WHERE NOT EXISTS (
  SELECT 1 FROM ledger_entries
  WHERE correlation_id = 'seed-genesis-0000000000000001'
);

DO $$
DECLARE
  v_debit  bigint;
  v_credit bigint;
  v_count  int;
BEGIN
  SELECT COALESCE(SUM(amount_minor), 0) INTO v_debit
  FROM ledger_entries
  WHERE correlation_id = 'seed-genesis-0000000000000001' AND side = 'D';

  SELECT COALESCE(SUM(amount_minor), 0) INTO v_credit
  FROM ledger_entries
  WHERE correlation_id = 'seed-genesis-0000000000000001' AND side = 'C';

  SELECT COUNT(*) INTO v_count
  FROM ledger_entries
  WHERE correlation_id = 'seed-genesis-0000000000000001';

  IF v_count = 0 THEN
    RAISE EXCEPTION 'apply-seed: genesis ausente';
  END IF;

  IF v_debit <> v_credit OR v_debit <> 10000000000 THEN
    RAISE EXCEPTION 'apply-seed: partidas dobradas nao fecham (D=%, C=%)', v_debit, v_credit;
  END IF;
END $$;

COMMIT;
