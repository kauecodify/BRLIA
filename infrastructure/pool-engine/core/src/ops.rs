//! Operacao admitida. Estrutura de tamanho fixo, Copy, para permitir slots
//! pre-alocados e copia zero no ring buffer.

#[derive(Debug, Clone, Copy)]
pub struct AdmittedOp {
    pub operation_id: u64,
    pub idempotency_hash: u64,
    pub jurisdiction: u8,
    pub leg: u8,
    pub amount_minor: i64,
    pub account_hash: u64,
    pub currency_code: u32,
    pub scale: u8,
    pub monotonic_window: u64,
    pub sequence: u64,
    pub trace_hash: u64,
    pub _pad: [u64; 2],
}

impl AdmittedOp {
    pub fn empty() -> Self {
        AdmittedOp {
            operation_id: 0,
            idempotency_hash: 0,
            jurisdiction: 0,
            leg: 0,
            amount_minor: 0,
            account_hash: 0,
            currency_code: 0,
            scale: 2,
            monotonic_window: 0,
            sequence: 0,
            trace_hash: 0,
            _pad: [0; 2],
        }
    }
}

pub const LEG_PIX: u8 = 0;
pub const LEG_FX: u8 = 1;
pub const LEG_ESCROW: u8 = 2;
pub const LEG_LEDGER: u8 = 3;

pub const SIDE_DEBIT: i8 = 0;
pub const SIDE_CREDIT: i8 = 1;
