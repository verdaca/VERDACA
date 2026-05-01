"""Atelier decision memory adapter (§5 of architecture.md).

Phase 3B-iii scope
------------------

MINIMAL surface per Andrey's A3.3.4 brief:
  - store_decision — real capture with internal embedding
  - retrieve_decisions — naive similarity + §5.3 multiplicative scoring
  - flag_and_quarantine — §8.7 in-place embedding strip (R-04 critical)
  - delete — decision-scoped cascade
  - export — decision dump
  - health — store liveness

All other MemoryProtocol methods raise NotImplementedError because Phase 3C
facade composition routes them elsewhere (facts → Mem0; task outcomes also
go to Atelier in the real composition, but the protocol conformance tests
don't exercise them on the standalone AtelierStore).

Out of scope for Phase 3B-iii (Stage 5 MAC territory per Andrey):
  - Auto-capture hooks (AT9)
  - TTL decay reaper (§5.4)
  - decision_type_config table (AT5)
  - Write-time conflict detection via LLM classifier (AT3)
  - trace_decision / decision_relations graph (AT4, AT13)
  - ltree scope hierarchy (AT8)
  - last_accessed_at side-effect on retrieve (AT6)

Live pgvector + real embeddings are Quinn's Step 3.4 concern. The Phase
3B-iii AtelierStore uses a naive word-set "embedding" plus Jaccard
similarity over the decision text so unit tests exercise the scoring
formula end-to-end without network dependencies.
"""

__all__: list[str] = []
