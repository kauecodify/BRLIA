//! Ring buffer MPMC lock-free com slots pre-alocados e copia zero para
//! operacoes de tamanho fixo. Baseado no desenho de fila bounded MPMC com
//! sequencia por slot (Vyukov). Sem alocacao no push e no pop.

use std::cell::UnsafeCell;
use std::sync::atomic::{AtomicUsize, Ordering};

use crate::ops::AdmittedOp;

struct Slot {
    sequence: AtomicUsize,
    value: UnsafeCell<AdmittedOp>,
}

pub struct MpmcRing {
    buffer: Box<[Slot]>,
    mask: usize,
    enqueue_pos: AtomicUsize,
    dequeue_pos: AtomicUsize,
}

unsafe impl Sync for MpmcRing {}
unsafe impl Send for MpmcRing {}

pub enum PushError {
    Full,
}

impl MpmcRing {
    pub fn new(capacity: usize) -> Self {
        assert!(capacity.is_power_of_two(), "capacidade deve ser potencia de 2");
        let buffer: Vec<Slot> = (0..capacity)
            .map(|i| Slot {
                sequence: AtomicUsize::new(i),
                value: UnsafeCell::new(AdmittedOp::empty()),
            })
            .collect();
        MpmcRing {
            buffer: buffer.into_boxed_slice(),
            mask: capacity - 1,
            enqueue_pos: AtomicUsize::new(0),
            dequeue_pos: AtomicUsize::new(0),
        }
    }

    pub fn capacity(&self) -> usize {
        self.mask + 1
    }

    /// Insere sem copiar estruturas proprias: a operacao cabe em um slot de
    /// tamanho fixo e e escrita diretamente no slot (zero-copy).
    pub fn push(&self, op: AdmittedOp) -> Result<(), PushError> {
        let mut pos = self.enqueue_pos.load(Ordering::Relaxed);
        loop {
            let slot = unsafe { &*self.buffer.get_unchecked(pos & self.mask) };
            let seq = slot.sequence.load(Ordering::Acquire);
            let diff = seq as isize - pos as isize;
            if diff == 0 {
                if self
                    .enqueue_pos
                    .compare_exchange_weak(pos, pos + 1, Ordering::Relaxed, Ordering::Relaxed)
                    .is_ok()
                {
                    unsafe {
                        *slot.value.get() = op;
                        slot.sequence.store(pos + 1, Ordering::Release);
                    }
                    return Ok(());
                }
            } else if diff < 0 {
                return Err(PushError::Full);
            } else {
                pos = self.enqueue_pos.load(Ordering::Relaxed);
            }
        }
    }

    pub fn pop(&self) -> Option<AdmittedOp> {
        let mut pos = self.dequeue_pos.load(Ordering::Relaxed);
        loop {
            let slot = unsafe { &*self.buffer.get_unchecked(pos & self.mask) };
            let seq = slot.sequence.load(Ordering::Acquire);
            let diff = seq as isize - (pos + 1) as isize;
            if diff == 0 {
                if self
                    .dequeue_pos
                    .compare_exchange_weak(pos, pos + 1, Ordering::Relaxed, Ordering::Relaxed)
                    .is_ok()
                {
                    let value = unsafe { *slot.value.get() };
                    slot.sequence.store(pos.wrapping_add(self.capacity()), Ordering::Release);
                    return Some(value);
                }
            } else if diff < 0 {
                return None;
            } else {
                pos = self.dequeue_pos.load(Ordering::Relaxed);
            }
        }
    }

    pub fn len(&self) -> usize {
        let enq = self.enqueue_pos.load(Ordering::Acquire);
        let deq = self.dequeue_pos.load(Ordering::Acquire);
        enq.wrapping_sub(deq)
    }
}
