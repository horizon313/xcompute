import os
import unittest

from xcompute.core.registry import Registry
from xcompute.router.memory import StrategyMemory
from xcompute.twin.roofline import Hardware, predict_decode_tokens_per_s, bound_type

PLUGINS = os.path.join(os.path.dirname(__file__), "..", "plugins")


class Tests(unittest.TestCase):
    def test_registry_scan_and_disable(self):
        r = Registry()
        r.scan(PLUGINS)
        self.assertIn("backend.cpu", r.capabilities())
        self.assertIsNotNone(r.load("cpu_backend"))
        self.assertTrue(r.instances["cpu_backend"].health())
        r.disable("cpu_backend")
        self.assertNotIn("backend.cpu", r.capabilities())

    def test_twin(self):
        hw = Hardware(mem_bw_gbs=100, peak_gflops=3600, ram_gb=8)
        self.assertEqual(predict_decode_tokens_per_s(hw, 4.0), 25.0)
        self.assertIsNone(predict_decode_tokens_per_s(hw, 8.0))
        self.assertEqual(bound_type(hw, flops=1e6, bytes_moved=1e9), "memory-bound")

    def test_strategy_memory(self):
        m = StrategyMemory()
        w = {"model": "x"}
        m.record(w, "a", 1.0, 2.0)
        m.record(w, "b", 1.0, 1.0)
        self.assertEqual(m.best(w), ("b", 1.0))
        self.assertIsNotNone(m.twin_error())


if __name__ == "__main__":
    unittest.main()
