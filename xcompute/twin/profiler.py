"""Measure this machine (stdlib only) and save a Hardware Profile.

Run:  python3 -m xcompute.twin.profiler
Writes hardware_profile.json in the current folder (per-machine, do not commit).
"""
import json
import os
import platform
import subprocess
import time


def _sysctl(name):
    try:
        return subprocess.check_output(
            ["sysctl", "-n", name], stderr=subprocess.DEVNULL, universal_newlines=True
        ).strip()
    except Exception:
        return None


def read_ram_gb():
    v = _sysctl("hw.memsize")
    if v and v.isdigit():
        return int(v) / 1024 ** 3
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024 ** 3
    except (ValueError, OSError, AttributeError):
        return None


def read_cpu_info():
    brand = _sysctl("machdep.cpu.brand_string") or platform.processor() or platform.machine()
    phys = _sysctl("hw.physicalcpu")
    freq = _sysctl("hw.cpufrequency")
    feats = ((_sysctl("machdep.cpu.features") or "") + " " +
             (_sysctl("machdep.cpu.leaf7_features") or "")).upper()
    return {
        "brand": brand,
        "physical_cores": int(phys) if phys and phys.isdigit() else (os.cpu_count() or 1),
        "logical_cores": os.cpu_count() or 1,
        "base_ghz": int(freq) / 1e9 if freq and freq.isdigit() else None,
        "has_avx": "AVX1.0" in feats or " AVX " in (" " + feats + " "),
        "has_avx2": "AVX2" in feats,
        "has_fma": "FMA" in feats,
    }


def estimate_peak_gflops(cpu):
    """Peak FP32 GFLOPS = cores x GHz x flops/cycle/core (rough, ignores turbo)."""
    if not cpu["base_ghz"] or platform.machine() in ("arm64", "aarch64"):
        return None
    if cpu["has_avx2"] and cpu["has_fma"]:
        fpc = 32
    elif cpu["has_avx"]:
        fpc = 16
    else:
        fpc = 8
    return round(cpu["physical_cores"] * cpu["base_ghz"] * fpc, 1)


def _worker(seconds):
    src = bytearray(32 * 1024 * 1024)
    moved = 0
    t0 = time.perf_counter()
    end = t0 + seconds
    while time.perf_counter() < end:
        bytes(src)  # read + write
        moved += 2 * len(src)
    return moved / (time.perf_counter() - t0) / 1e9


def measure_mem_bw_single_gbs(seconds=0.6):
    return _worker(seconds)


def measure_mem_bw_multi_gbs(workers=None, seconds=0.6):
    """Sum of per-process copy rates, approximates the multi-core bandwidth."""
    import multiprocessing as mp
    workers = workers or os.cpu_count() or 1
    with mp.Pool(workers) as pool:
        rates = pool.map(_worker, [seconds] * workers, chunksize=1)
    return sum(rates)


def profile():
    cpu = read_cpu_info()
    ram = read_ram_gb()
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": cpu,
        "ram_gb": round(ram, 2) if ram else None,
        "mem_bw_gbs_single": round(measure_mem_bw_single_gbs(), 2),
        "mem_bw_gbs_multi": round(measure_mem_bw_multi_gbs(), 2),
        "peak_gflops_estimate": estimate_peak_gflops(cpu),
        "note": "Estimates for calibrating the twin. Compare with real runs and correct.",
    }


if __name__ == "__main__":
    p = profile()
    with open("hardware_profile.json", "w", encoding="utf-8") as f:
        json.dump(p, f, indent=2, ensure_ascii=False)
    print(json.dumps(p, indent=2, ensure_ascii=False))
    print("\nSaved: hardware_profile.json")
