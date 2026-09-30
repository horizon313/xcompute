"""Hardware digital twin: Roofline-style analytical predictor."""


class Hardware:
    def __init__(self, mem_bw_gbs, peak_gflops, ram_gb, os_reserved_gb=3.0):
        self.mem_bw_gbs = mem_bw_gbs
        self.peak_gflops = peak_gflops
        self.ram_gb = ram_gb
        self.os_reserved_gb = os_reserved_gb

    @classmethod
    def from_profile(cls, prof):
        """Build the twin from hardware_profile.json (see twin/profiler.py)."""
        return cls(
            mem_bw_gbs=prof.get("mem_bw_gbs_multi") or prof["mem_bw_gbs_single"],
            peak_gflops=prof.get("peak_gflops_estimate") or 1.0,
            ram_gb=prof.get("ram_gb") or 8.0,
        )

    @property
    def usable_ram_gb(self):
        return max(self.ram_gb - self.os_reserved_gb, 0)


def predict_time_s(hw, flops, bytes_moved):
    """Lower bound on runtime: max(compute time, memory time)."""
    compute = flops / (hw.peak_gflops * 1e9)
    memory = bytes_moved / (hw.mem_bw_gbs * 1e9)
    return max(compute, memory)


def bound_type(hw, flops, bytes_moved):
    ridge = hw.peak_gflops / hw.mem_bw_gbs  # flops per byte
    intensity = flops / bytes_moved if bytes_moved else float("inf")
    return "compute-bound" if intensity >= ridge else "memory-bound"


def predict_decode_tokens_per_s(hw, model_gb):
    """LLM decoding is memory-bound: each token reads all weights once."""
    if model_gb > hw.usable_ram_gb:
        return None  # does not fit, would swap
    return hw.mem_bw_gbs / model_gb  # upper bound
