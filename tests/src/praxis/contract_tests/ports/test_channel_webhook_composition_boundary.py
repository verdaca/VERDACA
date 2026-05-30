"""Stage 14 Phase-0.6 O-6 — composition-root hoist boundary guardrail.

``F-14-O6-COMPOSITION-HOIST-PENDING-01`` — an executable fence for the deferred
composition-root hoist (the HARD MERGE-GATE, not this commit).

On this demo branch ``webhook_app`` wires its gateway through
``praxis.adapters.mcp_server.composition`` (``build_runtime_gateway`` /
``compose_auth_quartet``). That is the WRONG-DIRECTION arrow
``channels -> mcp_server -> FastMCP``: ``composition.py`` carries the contract
to "hoist to a dedicated neutral member when channels wire", which has NOT
happened yet. The arrow is tolerable on a local demo branch but MUST NOT reach
main (Winston⇄Murat 2026-05-30).

This test ASSERTS the desired POST-HOIST state — that no
``praxis.adapters.channels.*`` module transitively imports
``praxis.adapters.mcp_server.*`` (equivalently, ``webhook_app`` does not pull in
``fastmcp``). It therefore FAILS TODAY BY DESIGN and is marked
``xfail(strict=True)``:

  - today  → assertion fails → ``xfailed`` (expected; the fence is armed).
  - after the hoist lands → assertion passes → ``xpassed`` → strict xfail turns
    that into a CI FAILURE, forcing the hoist author to flip this marker to a
    live assertion. That is the fence screaming at the next channel author.

NO ``@pytest.mark.no_waiver`` — this is an xfail guardrail, not a runtime
invariant, so the 14/9/23 pin (no_waiver == 14) is unaffected.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

# Probe script: import the channel package in a CLEAN interpreter and report any
# mcp_server / fastmcp modules that got transitively pulled in.
_PROBE = """
import json, sys
import praxis.adapters.channels.webhook_app  # noqa: F401
offenders = sorted(
    m for m in sys.modules
    if m == "fastmcp" or m.startswith("fastmcp.")
    or m == "praxis.adapters.mcp_server"
    or m.startswith("praxis.adapters.mcp_server.")
)
print(json.dumps(offenders))
"""


@pytest.mark.xfail(
    strict=True,
    reason=(
        "F-14-O6-COMPOSITION-HOIST-PENDING-01: webhook_app wires through "
        "praxis.adapters.mcp_server.composition (wrong-direction "
        "channels->mcp_server->FastMCP arrow). composition.py's 'hoist to a "
        "dedicated neutral member when channels wire' contract is not yet "
        "satisfied; flips green only when the hoist merge-gate lands."
    ),
)
def test_channels_do_not_transitively_import_mcp_server_subtree() -> None:
    result = subprocess.run(
        [sys.executable, "-c", _PROBE],
        capture_output=True,
        text=True,
        check=True,
    )
    offenders = json.loads(result.stdout.strip().splitlines()[-1])
    assert offenders == [], (
        "channels.webhook_app transitively imports the mcp_server subtree / "
        f"fastmcp (hoist not yet landed): {offenders}"
    )
