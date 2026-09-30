"""Measure this machine (stdlib only) to build a Hardware Profile."""
import json
import os
import platform
import time


def measure_mem_bw_gbs(size_mb=64, repeats=5):
    src = bytearray(size_mb * 1024 * 1024)
    best = 0.0
    for _ in range(repeats):
        t = time.perf_counter()
        dst = bytes(src)  # read + write
        dt = time.perf_counter() - t
        best = max(best, 2 * len(src) / dt / 1e9)
    del dst
    return best


def measure_py_ops_per_s(n=2000000):
    t = time.perf_counter()
    x = 0
    for i in range(n):
        x += i * 2
    return n / (time.perf_counter() - t)


def profile():
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "mem_bw_gbs_measured": round(measure_mem_bw_gbs(), 2),
        "py_ops_per_s": int(measure_py_ops_per_s()),
        "note": "single-thread stdlib estimate; use it to calibrate the twin, not as peak",
    }


if __name__ == "__main__":
    print(json.dumps(profile(), indent=2, ensure_ascii=False))
