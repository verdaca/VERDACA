"""Verdaca port Protocols + DTOs + shared error taxonomy.

Per `_bmad-output/implementation-artifacts/verdaca/stage9/ports-architecture.md`
v0.2 (RATIFIED 2026-04-18) + v0.3 corrigendum (§4.1 namespace) + v0.4
corrigendum (ADR-9.2-V3 vendor-pattern flip).

Six ports land progressively across Stage 9.4 sub-stages:
    9.4.1 — versioned_state (Beads in-tree per ADR-9.2-V3 v0.4)
    9.4.2 — serialization (TONL submodule per ADR-9.2-V2)
    9.4.3 — memory (Mem0 + Letta dual-adapter per ADR-9.2-V1)
    9.4.4 — cost_meter (Pi-Mono in-tree per ADR-9.2-V4)
    9.4.5 — llm_proxy (RTK + LiteLLM dual-adapter per ADR-9.2-V5)
    9.4.6 — compaction (Forge sidecar OR in-tree-stub per ADR-9.2-V6, G-1 gated)

Closed-contract substance is inherited from
`_bmad-output/implementation-artifacts/verdaca/stage9/port-contracts.md` v0.2.
This package introduces zero new contract substance.
"""

__version__ = "0.1.0"
