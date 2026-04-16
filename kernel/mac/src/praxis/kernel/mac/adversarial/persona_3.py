"""Persona 3 gaming corpus loader — benchmark-questions.md §4 Persona 3.

Per benchmark §4 Persona 3: the adversary is a rational actor who
knows MAC's rubric and tries to game each gate by surface-level
mimicry. MAC resists via structural properties (Req-F two-step,
manufactured-dissent Req-C cap, section routing) that can't be
bypassed with surface text alone.

The corpus is split into two sets per arch §10.2 rotation protocol:

  - **public/** — visible in the repo. Red-teamers can study.
    Minimum 3 prompts at step 5 (stubs); Stage 7 POV Harness replaces
    with real adversarial content.
  - **rotating/** — replaced every N weeks (documented in the README).
    Minimum 3 prompts at step 5 (stubs).

``MAC-T-ADV-P3-01`` (allow-list entry #15, ``no_waiver`` deterministic)
asserts both directories exist and each carries ≥3 gaming prompts.
``MAC-T-ADV-ROTATION-01..03`` assert the rotation protocol invariants.

Binding anchors:
  - mac/benchmark-questions.md §4 Persona 3 (adversarial persona)
  - mac/architecture.md §12.6 Adversarial Corpus
  - mac/architecture.md §10.2 Rotation Protocol
  - mac/test-strategy.md v0.3 §10.1 MAC-T-ADV-P3-01..05
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Persona3Prompt:
    """A single gaming prompt in the Persona 3 corpus.

    ``target_gate`` is the gate the producer is trying to game
    (e.g., ``"R5"`` for manufactured dissent, ``"R11"`` for
    single-scenario-disguised-as-multi). ``prompt`` is the actual
    gaming text the producer would emit.
    """

    prompt_id: str
    target_gate: str
    strategy: str  # e.g., "manufactured_dissent", "single_scenario_bias"
    prompt: str


class Persona3CorpusLoader:
    """Load Persona 3 gaming prompts from the fixtures directory.

    Step 5 reads ``.txt`` files from ``public/`` and ``rotating/``,
    parses minimal front-matter (``target_gate``, ``strategy``) from
    the first line, and returns :class:`Persona3Prompt` instances.
    Stage 7 POV Harness may extend to a richer format (YAML / JSON).
    """

    def __init__(self, fixtures_root: Path) -> None:
        self._root = fixtures_root

    @property
    def public_dir(self) -> Path:
        return self._root / "public"

    @property
    def rotating_dir(self) -> Path:
        return self._root / "rotating"

    def load_public(self) -> list[Persona3Prompt]:
        return self._load_from(self.public_dir)

    def load_rotating(self) -> list[Persona3Prompt]:
        return self._load_from(self.rotating_dir)

    def _load_from(self, directory: Path) -> list[Persona3Prompt]:
        prompts: list[Persona3Prompt] = []
        if not directory.exists():
            return prompts
        for txt_file in sorted(directory.glob("*.txt")):
            text = txt_file.read_text(encoding="utf-8")
            lines = text.splitlines()
            if not lines:
                continue
            # Front-matter: first line "target_gate:R{N} strategy:NAME"
            header = lines[0].strip()
            target_gate = ""
            strategy = ""
            for token in header.split():
                if token.startswith("target_gate:"):
                    target_gate = token.split(":", 1)[1]
                elif token.startswith("strategy:"):
                    strategy = token.split(":", 1)[1]
            prompt_body = "\n".join(lines[1:]).strip()
            prompts.append(
                Persona3Prompt(
                    prompt_id=txt_file.stem,
                    target_gate=target_gate,
                    strategy=strategy,
                    prompt=prompt_body,
                )
            )
        return prompts


__all__ = (
    "Persona3CorpusLoader",
    "Persona3Prompt",
)
