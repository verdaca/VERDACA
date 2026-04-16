"""MAC integration adapters — arch §10.

Each adapter wraps a cross-stage contract:

  - :mod:`pi_mono` — Pi-Mono ``CostTracker.track_cost`` hot-path (arch §10.1)
  - :mod:`runtime` — Runtime ``AgentSpawner``, MCP shape guard, Path B outbox (arch §10.3)
  - :mod:`compression` — Forge F8 ``reasoning_preserved`` flag (arch §10.4)

MAC imports these via :data:`typing.Protocol` shapes so the MAC package
remains independently testable without installing the full Pi-Mono /
Runtime / Compression packages. The production wiring at step 6 + Stage 7
Pov Harness substitutes real instances by passing them to the MAC
controller's constructor — same interface, no code change.
"""
