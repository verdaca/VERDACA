# Changelog — praxis-adapter-tonl

Adapter for `praxis.ports.serialization.SerializationPort`. In-tree wrap of
the kernel TONL substrate at `praxis.kernel.compression.tonl` per ADR-9.2-V2
v0.2 corrigendum. ADR-9.2-V4 Pi-Mono precedent shape (in-tree adapter
wrapping kernel module; single implementation, two consumers — kernel
`compression/orchestrator.py` + this adapter).

## v0.1.0 — 2026-04-28 — Initial in-tree adapter wrapping kernel TONL substrate per ADR-9.2-V2 v0.2 corrigendum.

- Adapter delegates `encode` / `decode` primitives to `praxis.kernel.compression.tonl.encode` / `praxis.kernel.compression.tonl.decode`. Substrate API surface (encode/decode primitives) ≥ port contract requirement; mapping table at 9.4.2 preload Item 7.3 confirmed composition.
- Adapter authors **port-level** `can_decode_version` and `fuzz_roundtrip` on top of substrate (not delegated; substrate does not provide these — they are Verdaca-port concerns per port-contracts.md v0.2 §2.3).
- `EncodedBytes` wrapper sets `encoding_format="tonl-v0.1.0"` and `encoded_schema_version=payload.schema_version` (binding contract per M-T-SER-ENCODE-TONL-01). Adapter encodes a 3-key dict `{body, payload_kind, schema_version}` to TONL text via the kernel substrate; decode reconstructs `SerializablePayload` from the dict.
- Kernel TONL exception → port error taxonomy mapping: `TONLValidationError` / `TONLTypeError` / `TONLSecurityError` → `ContractViolation` (with appropriate `violation_class`); `TONLParseError` (raised at decode) → `ContractViolation` with `violation_class="value"`. `TONLError` base never raised directly in adapter code; subclasses are exhaustive.

### Discipline-preserved invariants

- Adapter does NOT import any upstream `tonl` package — upstream `tonl-dev/tonl` is TypeScript-only with zero Python source (9.4.2 preload Item 7.1 evidence). Codename "TONL" persists as the kernel substrate's package name (`praxis.kernel.compression.tonl`), not as an upstream Python import target.
- Kernel TONL stays put serving compression-layer duty per its Stage-2 purpose. 12 in-kernel `praxis.kernel.compression.tonl.*` consumer sites (orchestrator + tests) are compression-layer consumers, not Serialization-port consumers — they stay where they are. 9.4.7 atomic-PR scope at this seam: standard restructure only, no kernel-compression touch.
- Adapter never authors a substrate replacement — composition only. If the kernel substrate's API surface ever shifts, adapter needs concurrent update (per ADR-9.2-V2 v0.2 §Consequences "negative" entry).

### Agent-initiative additive decisions (per 9.4.1 precedent — surfaced for Cleo 9.6 supply-chain review)

- `SerializationPort` is `@runtime_checkable` on the port-package side at `ports/src/praxis/ports/serialization.py`. Mirrors the 9.4.1 `VersionedStatePort` runtime_checkable decision (documented at `adapters/beads/src/praxis/adapters/beads/changelog.md` v0.1.0). Adapter `on_init()` performs `isinstance(self, SerializationPort)` self-check as the §2.2 lifecycle contract self-check (per executor playbook §9.C addendum; precedent: 9.4.1 API_VERSION ClassVar bug).
- `TONLAdapter.API_VERSION` ClassVar mirrors the Protocol's `API_VERSION` ClassVar. Required for `runtime_checkable` Protocol data-attribute conformance (per 9.4.1 lesson — static syntax check insufficient; live `isinstance(adapter, SerializationPort)` is load-bearing).
- `__init__` exposes `supported_schema_versions: set[int] | None = None` (defaults to `{1}`). `can_decode_version(N)` returns `N in self._supported_versions`. This is the simplest implementation that satisfies M-T-SER-EVO-01..04 trigger semantics without importing a Migrator-style chain registry; tests register additional versions via constructor parameter when needed (e.g. `TONLAdapter(supported_schema_versions={1, 2})` for evolution tests).
- `__init__` exposes `default_correlation_id: str | None = None` (UUID4 fallback per-instance), mirroring the 9.4.1 BeadsAdapter `__init__` user-authorized refinement (option b).
- `RoundtripFuzzReport.correlation_id` is derived deterministically from `seed` via `f"fuzz-seed-{seed}"`. Required for M-T-SER-FUZZ-02 deterministic-report invariant (same `(sample_count, seed)` invoked twice → identical DTO). Documented agent-initiative — the port contract specifies report shape but not how `correlation_id` is generated; deterministic seed-derivation is the natural fit for a seeded harness.
- Fuzz sample generator (`_fuzz_sample`) emits **only** `bool` / `int` / `str` / `None` / `list` / `dict` values — excludes `float` (kernel TONL `_encode_value` rejects floats with `TONLValidationError` per `kernel/compression/.../tonl/encode.py:64-67`). Sample generator includes Unicode strings and nested edge cases for M-T-SER-FUZZ-03 adversarial coverage.

### Out of scope at v0.1.0 (Stage 10 / future-stage debt)

- msgspec substitute adapter (Stage 10 per ADR-9.2-V2 v0.2 §Decision msgspec line). msgspec MAC-Ts (M-T-SER-ENCODE-MSGSPEC-01 / M-T-SER-DECODE-MSGSPEC-01) deferred.
- Schema-evolution migration chain. v0.1.0 supports only same-version decode (`encoded_schema_version == expected_schema_version` else `SchemaEvolutionFailure`). Full forward-migration support routes through future `Migrator` consumption pattern (analogous to Versioned State port's migrate flow).
- Streaming encode/decode. Port contract is sync/non-streaming; kernel substrate has `encode_stream`/`decode_stream` available but they're out of port scope at 9.4.2.
