//! Nucleo compilado do pool-engine BRLIA.
//!
//! Hot path: UDS -> ring MPMC lock-free -> pool_id. Sem interpretador Python,
//! sem GC, sem fsync, sem sleep e sem rede neste crate. FastAPI permanece
//! apenas no control plane (modulo control/ do pacote Python).

pub mod clock;
pub mod netting;
pub mod ops;
pub mod pool;
pub mod ring;
pub mod sha256;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use clock::MonotonicClock;
use netting::LiquidEntry;
use ops::AdmittedOp;
use pool::{composition_hash as core_composition_hash, pool_id_from, WindowManager};

#[pyclass]
pub struct PyWindowManager {
    inner: WindowManager,
}

#[pymethods]
impl PyWindowManager {
    #[new]
    #[pyo3(signature = (tick_ns = 1_000_000, watermark_ms = 5, max_ops_per_window = 4096))]
    fn new(tick_ns: u64, watermark_ms: u64, max_ops_per_window: usize) -> Self {
        PyWindowManager {
            inner: WindowManager::new(tick_ns, watermark_ms, max_ops_per_window),
        }
    }

    /// Admite uma operacao e retorna o indice monotonic da janela.
    fn admit(
        &mut self,
        operation_id: u64,
        idempotency_hash: u64,
        jurisdiction: u8,
        leg: u8,
        amount_minor: i64,
        account_hash: u64,
        currency_code: u32,
        scale: u8,
        sequence: u64,
        trace_hash: u64,
    ) -> PyResult<u64> {
        let op = AdmittedOp {
            operation_id,
            idempotency_hash,
            jurisdiction,
            leg,
            amount_minor,
            account_hash,
            currency_code,
            scale,
            monotonic_window: 0,
            sequence,
            trace_hash,
            _pad: [0; 2],
        };
        self.inner.admit(op).map_err(|_| {
            PyValueError::new_err("POOL_FULL: janela cheia; retry com a mesma idempotency-key")
        })
    }

    /// Fecha a janela corrente e retorna o evento pool.closed.v1 como dicionario.
    fn close(&mut self, next_window: u64) -> Option<PyObject> {
        Python::with_gil(|py| {
            self.inner.close(next_window).map(|event| {
                let entries: Vec<PyObject> = event
                    .liquid_entries
                    .iter()
                    .map(|entry| entry_to_dict(py, entry))
                    .collect();
                let dict = pyo3::types::PyDict::new(py);
                dict.set_item("pool_id", event.pool_id).ok();
                dict.set_item("jurisdiction", event.jurisdiction).ok();
                dict.set_item("functional_currency", event.functional_currency)
                    .ok();
                dict.set_item("monotonic_window", event.monotonic_window).ok();
                dict.set_item("sequence", event.sequence).ok();
                dict.set_item("window_seq", event.window_seq).ok();
                dict.set_item("admitted_ops", event.admitted_ops).ok();
                dict.set_item("liquid_entries", entries).ok();
                dict.set_item("composition_hash", event.composition_hash).ok();
                dict.into()
            })
        })
    }

    fn watermark_ms(&self) -> u64 {
        self.inner.watermark_ms()
    }

    fn now_ns(&self) -> u64 {
        self.inner.clock().now_ns()
    }
}

fn entry_to_dict(py: Python, entry: &LiquidEntry) -> PyObject {
    let dict = pyo3::types::PyDict::new(py);
    dict.set_item("entry_seq", entry.entry_seq).ok();
    dict.set_item("account_hash", entry.account_hash).ok();
    dict.set_item("side", if entry.side == ops::SIDE_DEBIT { "D" } else { "C" })
        .ok();
    dict.set_item("amount_minor", entry.amount_minor).ok();
    dict.set_item("currency_code", entry.currency_code).ok();
    dict.set_item("scale", entry.scale).ok();
    dict.set_item("jurisdiction", entry.jurisdiction).ok();
    dict.set_item("monotonic_window", entry.monotonic_window).ok();
    dict.set_item("origin_trail", entry.origin_trail.clone()).ok();
    dict.into()
}

#[pyfunction]
fn monotonic_now_ns() -> u64 {
    MonotonicClock::new(1_000_000).now_ns()
}

#[pyfunction]
fn window_index_of(now_ns: u64, tick_ns: u64) -> u64 {
    MonotonicClock::new(tick_ns).window_index(now_ns)
}

#[pyfunction]
fn compute_pool_id(
    jurisdiction: u8,
    currency_code: u32,
    monotonic_window: u64,
    sequence: u64,
    composition_hash: &str,
) -> String {
    pool_id_from(
        jurisdiction,
        currency_code,
        monotonic_window,
        sequence,
        composition_hash,
    )
}

#[pyfunction]
fn compute_composition_hash(ops: Vec<(u64, u64, i64, u64)>, monotonic_window: u64) -> String {
    let admitted: Vec<AdmittedOp> = ops
        .iter()
        .map(|(operation_id, idempotency_hash, amount_minor, account_hash)| AdmittedOp {
            operation_id: *operation_id,
            idempotency_hash: *idempotency_hash,
            jurisdiction: 0,
            leg: 0,
            amount_minor: *amount_minor,
            account_hash: *account_hash,
            currency_code: 986,
            scale: 2,
            monotonic_window,
            sequence: 0,
            trace_hash: 0,
            _pad: [0; 2],
        })
        .collect();
    core_composition_hash(&admitted, monotonic_window)
}

#[pymodule]
fn brlia_pool_core(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PyWindowManager>()?;
    module.add_function(wrap_pyfunction!(monotonic_now_ns, module)?)?;
    module.add_function(wrap_pyfunction!(window_index_of, module)?)?;
    module.add_function(wrap_pyfunction!(compute_pool_id, module)?)?;
    module.add_function(wrap_pyfunction!(compute_composition_hash, module)?)?;
    Ok(())
}
