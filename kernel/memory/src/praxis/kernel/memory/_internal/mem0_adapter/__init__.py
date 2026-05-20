"""Mem0 integration adapter (§4 of architecture.md).

Wraps the mem0ai pip dependency behind a typed boundary so:
  - raw dicts from Mem0 never cross into application code (§4.5 #2)
  - tenant scoping is injected and validated (§4.5 #3)
  - Mem0 exception types are translated into Praxis-typed exceptions (§4.5 #4)
  - PII redaction happens at the write boundary (§4.5 #5)
  - every call is observed via telemetry + cost events (§4.5 #7)

Phase 3B-ii scope
-----------------

- `Mem0ClientProtocol` — the minimal structural shape of the vendor client
  we depend on. Production construction uses `mem0.Memory.from_config(cfg)`;
  tests inject an in-memory fake. Dependency injection means the adapter
  is testable without a live Mem0 backend (pgvector, API keys, etc.) per
  Andrey's 3B-ii(a) authorization for mocked tests.

- `Mem0Adapter` — implements the full `MemoryProtocol` surface. The
  FACT-shaped methods (`store_fact`, `retrieve_facts`, parts of `delete`
  and `export`) do real work against the injected client. The
  non-fact-shaped methods (`store_task_outcome`, `store_decision`,
  `retrieve_similar_tasks`, `retrieve_decisions`, `flag_and_quarantine`)
  raise `NotImplementedError` — they are routed to other backends
  (Atelier, Beads) by the Phase 3C facade composition. Those methods
  exist on the adapter for signature conformance only so Mem0Adapter
  passes the protocol harness.

- `pii.py` — stub PII redactor. Real implementation is TBD
  (architecture §4.5 references "same redactor as seed corpus ingest"
  which lives elsewhere). The stub normalizes inputs so the write path
  is exercised end-to-end.

Follow-up work for Quinn (Step 3.4)
-----------------------------------

- Live-backend integration tests against a real Mem0 instance with
  pgvector. The mocked round-trip tests here prove adapter LOGIC, not
  Mem0 behavior correctness. Quinn's coverage suite should add at least
  one integration test per fact-shaped method against live Mem0.
"""

__all__: list[str] = []
