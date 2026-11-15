"""Diagnostico do relogio monotonic bruto (control plane)."""

from clock import CLOCK_NAME, now_ns, window_index

if __name__ == "__main__":
    first = now_ns()
    print(f"clock={CLOCK_NAME} now_ns={first} window={window_index(first)}")
