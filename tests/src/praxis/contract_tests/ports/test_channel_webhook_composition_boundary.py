"""Stage 14 — composition-root boundary guard (LIVE; hoist landed).

``F-14-O6-COMPOSITION-HOIST-PENDING-01`` — RESOLVED at the Stage-14 Day-2 hoist.
The runtime composition (``build_runtime_gateway`` / ``compose_auth_quartet``)
was moved out of the ``mcp_server`` adapter into the neutral
``praxis.composition.runtime_gateway`` member, so ``webhook_app`` no longer
imports ``mcp_server``/FastMCP. The earlier wrong-direction arrow
``channels -> mcp_server -> FastMCP`` is gone.

This was an ``xfail(strict=True)`` fence while the arrow existed; it is now a
LIVE PASSING assertion and a permanent regression guard: no
``praxis.adapters.channels.*`` module may transitively import
``praxis.adapters.mcp_server.*`` (equivalently, ``webhook_app`` must not pull in
``fastmcp``). If a future change reintroduces the arrow, this test goes red.

NO ``@pytest.mark.no_waiver`` — a boundary guard, not a runtime invariant; the
14/9/23 pin is unaffected.
"""

from __future__ import annotations

import json
import subprocess
import sys

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
        f"fastmcp — the composition-root hoist regressed: {offenders}"
    )
