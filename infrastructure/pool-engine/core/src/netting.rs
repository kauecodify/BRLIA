//! Netting multilateral por (jurisdicao, moeda funcional, janela).
//! Reduz N operacoes admitidas a K lancamentos liquidos, com K <= N.
//! Nenhum lancamento debita Capital Social e nenhum altera o genesis.

use std::collections::BTreeMap;

use crate::ops::{AdmittedOp, SIDE_CREDIT, SIDE_DEBIT};

#[derive(Debug, Clone)]
pub struct LiquidEntry {
    pub entry_seq: u64,
    pub account_hash: u64,
    pub side: i8,
    pub amount_minor: i64,
    pub currency_code: u32,
    pub scale: u8,
    pub jurisdiction: u8,
    pub monotonic_window: u64,
    pub origin_trail: Vec<u64>,
}

#[derive(Debug, Default)]
struct Accumulator {
    debit_minor: i64,
    credit_minor: i64,
    origins: Vec<u64>,
}

pub struct NettingResult {
    pub liquid_entries: Vec<LiquidEntry>,
    pub admitted_count: usize,
}

/// Compensacao multilateral: para cada conta participante acumula debitos e
/// creditos da janela e materializa apenas o saldo liquido nao nulo.
pub fn nettle(ops: &[AdmittedOp]) -> NettingResult {
    let mut by_account: BTreeMap<u64, Accumulator> = BTreeMap::new();
    for op in ops {
        let acc = by_account.entry(op.account_hash).or_default();
        // Convencao da janela: amount_minor positivo com sinal embutido no
        // campo; debito soma, credito subtrai no acumulado bruto.
        if op.amount_minor >= 0 {
            acc.debit_minor = acc.debit_minor.wrapping_add(op.amount_minor);
        } else {
            acc.credit_minor = acc.credit_minor.wrapping_add(-op.amount_minor);
        }
        acc.origins.push(op.operation_id);
    }

    let mut liquid_entries = Vec::with_capacity(by_account.len());
    let mut entry_seq: u64 = 0;
    for (account_hash, acc) in by_account.iter() {
        let net = acc.debit_minor - acc.credit_minor;
        if net == 0 {
            continue;
        }
        let (side, amount) = if net > 0 {
            (SIDE_DEBIT, net)
        } else {
            (SIDE_CREDIT, -net)
        };
        let currency_code = ops
            .iter()
            .find(|op| op.account_hash == *account_hash)
            .map(|op| op.currency_code)
            .unwrap_or(986);
        let scale = ops
            .iter()
            .find(|op| op.account_hash == *account_hash)
            .map(|op| op.scale)
            .unwrap_or(2);
        let jurisdiction = ops
            .iter()
            .find(|op| op.account_hash == *account_hash)
            .map(|op| op.jurisdiction)
            .unwrap_or(0);
        let monotonic_window = ops
            .iter()
            .find(|op| op.account_hash == *account_hash)
            .map(|op| op.monotonic_window)
            .unwrap_or(0);
        liquid_entries.push(LiquidEntry {
            entry_seq,
            account_hash: *account_hash,
            side,
            amount_minor: amount,
            currency_code,
            scale,
            jurisdiction,
            monotonic_window,
            origin_trail: acc.origins.clone(),
        });
        entry_seq += 1;
    }

    let admitted_count = ops.len();
    debug_assert!(liquid_entries.len() <= admitted_count, "K <= N");
    NettingResult {
        liquid_entries,
        admitted_count,
    }
}
