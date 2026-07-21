# Evaluator-only acceptance oracles

These tests are copied into the isolated project only after the agent has
finished. They are never included in model context. A standard benchmark task
without an oracle fails closed rather than treating a clean no-op as correct.

