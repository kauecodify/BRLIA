//! Relogio monotonic bruto. CLOCK_MONOTONIC_RAW e a unica fonte de ordem e de
//! boundario de janela. Wall-clock, timestamp de banco e NTP nao decidem ordem.

use std::time::Duration;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct MonotonicClock {
    tick_ns: u64,
}

impl MonotonicClock {
    pub fn new(tick_ns: u64) -> Self {
        MonotonicClock { tick_ns }
    }

    pub fn tick_ns(&self) -> u64 {
        self.tick_ns
    }

    pub fn now_ns(&self) -> u64 {
        let mut ts = libc::timespec {
            tv_sec: 0,
            tv_nsec: 0,
        };
        // CLOCK_MONOTONIC_RAW = 4 em Linux; nao avanca com NTP e nao dorme.
        unsafe {
            libc::clock_gettime(4, &mut ts);
        }
        (ts.tv_sec as u64).wrapping_mul(1_000_000_000).wrapping_add(ts.tv_nsec as u64)
    }

    pub fn window_index(&self, now_ns: u64) -> u64 {
        now_ns / self.tick_ns
    }

    pub fn window_start_ns(&self, window_index: u64) -> u64 {
        window_index.wrapping_mul(self.tick_ns)
    }

    pub fn window_deadline(&self, window_index: u64, watermark_ms: u64) -> Duration {
        Duration::from_nanos(
            self.window_start_ns(window_index)
                .wrapping_add(watermark_ms.wrapping_mul(1_000_000)),
        )
    }
}
