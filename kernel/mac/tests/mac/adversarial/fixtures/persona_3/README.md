# Persona 3 Adversarial Corpus — Rotation README

Per arch §10.2 rotation protocol. This corpus is split into:

- **`public/`** — visible in the repo. Red-teamers and external auditors
  can study these prompts. Target minimum: 3 prompts at step 5 (stubs);
  Stage 7 POV Harness replaces with real adversarial content.

- **`rotating/`** — replaced every **4 weeks**. Not intended for external
  audit; tests only verify the directory exists with a valid manifest and
  at least 3 prompts. Stage 7 POV Harness owns the rotation cadence and
  content generation.

## Rotation cadence

- Every 4 weeks, the entire `rotating/` corpus is replaced by a new set.
- The replacement date is recorded in `rotating/ROTATION.yaml`.
- Old rotating prompts are NOT promoted to `public/` — they are archived
  out of band (step 5 does not implement the archive; Stage 7 does).

## File format

Each prompt is a plain-text file with a front-matter header:

```
target_gate:R5 strategy:manufactured_dissent

[prompt body follows, one or more paragraphs]
```

The `target_gate` is the R1..R12 identifier the producer is trying to
game. The `strategy` is a short canonical name for the gaming approach.

## Step 5 stubs

Step 5 ships placeholder `.txt` files with minimal front-matter and
one-paragraph bodies, sufficient to satisfy `MAC-T-ADV-P3-01` fixture
inventory (no_waiver deterministic, allow-list entry #15) and
`MAC-T-ADV-ROTATION-01..03`. Real adversarial content is Stage 7 POV
Harness territory.

## Out-of-scope at step 5

Per v0.3 test-strategy §10.3 out-of-scope declaration, the following
are NOT in the Persona 3 corpus:

- Jailbreak prompts
- PII leakage attempts
- Copyright-infringement tests

These are deferred to Stage 6 or a separate RFC. Do not add them to
this corpus.
