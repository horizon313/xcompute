# XCompute

Adaptive compute optimizer with a hardware digital twin.

Simulate first, benchmark last: predict performance with a cheap model of the
hardware, then only measure the few best candidates.

## Status
v0.1 skeleton (zero dependencies, standard library only):
- `xcompute/core`: plugin Registry + Capability Graph (add / remove / disable modules)
- `xcompute/twin`: hardware profiler + Roofline predictor
- `xcompute/router`: Strategy Memory (SQLite)
- `plugins/`: manifest-based plugins (example: `cpu_backend`)

## Quick start
```bash
python3 -m xcompute.twin.profiler     # measure this machine
python3 -m unittest discover tests    # run tests
```

## Principles
- Small stable core, everything else is a plugin
- Language-neutral manifests (Python first, Rust/WASM later)
- Self-evolution only changes strategies, never core code; always with rollback
- Local first, zero cost

See `NOTES.md` for progress.
