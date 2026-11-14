//! Janela deterministica de 1 ms, pool_id deterministico e evento de
//! fechamento. pool_key = (jurisdicao, moeda funcional, janela monotonic,
//! sequence).

use crate::clock::MonotonicClock;
use crate::netting::{nettle, LiquidEntry, NettingResult};
use crate::ops::AdmittedOp;
use crate::sha256::sha256_hex;

pub struct PoolClosedEvent {
    pub pool_id: String,
    pub jurisdiction: String,
    pub functional_currency: String,
    pub monotonic_window: u64,
    pub sequence: u64,
    pub window_seq: u64,
    pub admitted_ops: usize,
    pub liquid_entries: Vec<LiquidEntry>,
    pub composition_hash: String,
}

pub struct WindowManager {
    clock: MonotonicClock,
    watermark_ms: u64,
    max_ops_per_window: usize,
    sequence: u64,
    pending: Vec<AdmittedOp>,
    current_window: u64,
}

pub enum AdmitError {
    WindowFull,
}

impl WindowManager {
    pub fn new(tick_ns: u64, watermark_ms: u64, max_ops_per_window: usize) -> Self {
        WindowManager {
            clock: MonotonicClock::new(tick_ns),
            watermark_ms,
            max_ops_per_window,
            sequence: 0,
            pending: Vec::with_capacity(max_ops_per_window),
            current_window: 0,
        }
    }

    pub fn clock(&self) -> &MonotonicClock {
        &self.clock
    }

    /// Admite uma operacao na janela corrente. Sem rede, sem fsync, sem sleep.
    pub fn admit(&mut self, op: AdmittedOp) -> Result<u64, AdmitError> {
        let now = self.clock.now_ns();
        let window = self.clock.window_index(now);
        if window != self.current_window && !self.pending.is_empty() {
            self.close(window);
        }
        self.current_window = window;
        if self.pending.len() >= self.max_ops_per_window {
            return Err(AdmitError::WindowFull);
        }
        self.pending.push(op);
        Ok(window)
    }

    /// Fecha a janela corrente: netting, pool_id deterministico e um unico
    /// evento de fechamento por janela.
    pub fn close(&mut self, next_window: u64) -> Option<PoolClosedEvent> {
        if self.pending.is_empty() {
            self.current_window = next_window;
            return None;
        }
        let ops: Vec<AdmittedOp> = std::mem::replace(
            &mut self.pending,
            Vec::with_capacity(self.max_ops_per_window),
        );
        let monotonic_window = self.current_window;
        let jurisdiction = ops[0].jurisdiction;
        let currency_code = ops[0].currency_code;
        let sequence = self.sequence;
        self.sequence = self.sequence.wrapping_add(1);
        self.current_window = next_window;

        let NettingResult {
            liquid_entries,
            admitted_count,
        } = nettle(&ops);

        let composition_hash = composition_hash(&ops, monotonic_window);
        let pool_id = pool_id_from(
            jurisdiction,
            currency_code,
            monotonic_window,
            sequence,
            &composition_hash,
        );

        Some(PoolClosedEvent {
            pool_id,
            jurisdiction: jurisdiction_code_to_string(jurisdiction),
            functional_currency: currency_code_to_string(currency_code),
            monotonic_window,
            sequence,
            window_seq: monotonic_window,
            admitted_ops: admitted_count,
            liquid_entries,
            composition_hash,
        })
    }

    pub fn watermark_ms(&self) -> u64 {
        self.watermark_ms
    }
}

pub fn composition_hash(ops: &[AdmittedOp], monotonic_window: u64) -> String {
    let mut hasher_input: Vec<u8> = Vec::with_capacity(ops.len() * 32);
    hasher_input.extend_from_slice(&monotonic_window.to_be_bytes());
    let mut sorted: Vec<&AdmittedOp> = ops.iter().collect();
    sorted.sort_by_key(|op| (op.operation_id, op.idempotency_hash));
    for op in sorted {
        hasher_input.extend_from_slice(&op.operation_id.to_be_bytes());
        hasher_input.extend_from_slice(&op.idempotency_hash.to_be_bytes());
        hasher_input.extend_from_slice(&op.amount_minor.to_be_bytes());
        hasher_input.extend_from_slice(&op.account_hash.to_be_bytes());
    }
    sha256_hex(&hasher_input)
}

pub fn pool_id_from(
    jurisdiction: u8,
    currency_code: u32,
    monotonic_window: u64,
    sequence: u64,
    composition_hash: &str,
) -> String {
    let mut input = Vec::with_capacity(40);
    input.extend_from_slice(&[jurisdiction]);
    input.extend_from_slice(&currency_code.to_be_bytes());
    input.extend_from_slice(&monotonic_window.to_be_bytes());
    input.extend_from_slice(&sequence.to_be_bytes());
    input.extend_from_slice(composition_hash.as_bytes());
    format!("pool-{}", sha256_hex(&input))
}

pub fn jurisdiction_code_to_string(code: u8) -> String {
    match code {
        0 => "br".to_string(),
        1 => "us".to_string(),
        2 => "eu".to_string(),
        3 => "uk".to_string(),
        4 => "sg".to_string(),
        _ => "global".to_string(),
    }
}

pub fn currency_code_to_string(code: u32) -> String {
    match code {
        986 => "BRL".to_string(),
        840 => "USD".to_string(),
        978 => "EUR".to_string(),
        826 => "GBP".to_string(),
        702 => "SGD".to_string(),
        _ => format!("C{}", code),
    }
}
