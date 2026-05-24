"""Stage 11 H#1 JSON-RPC golden probe from the frozen CAI stdio snapshot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SNAPSHOT_ROOT = Path("reference/spike-mcp-server-snapshot-d93f71a")
STDIO_SOURCE = SNAPSHOT_ROOT / "src" / "stdio.ts"
GOLDEN_FIXTURE = Path("fixtures/mcp_jsonrpc_golden/cai_stdio_initialize.jsonl")
STDIO_SHA256 = "23e550582c17ffaa9442fd1d1031b29af25014cdb8a2817699496fee406f4a34"
INITIALIZE_BYTES = (
    b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":'
    b'{"protocolVersion":"2025-06-18","capabilities":{},'
    b'"clientInfo":{"name":"verdaca-stage11-probe","version":"0.1.0"}}}'
)
INITIALIZED_BYTES = (
    b'{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_mcp_jsonrpc_golden_fixture_is_pinned_to_snapshot_stdio_source() -> None:
    source = Path(__file__).resolve().parents[4] / STDIO_SOURCE
    actual_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    fixture = _load_jsonl(Path(__file__).resolve().parents[4] / GOLDEN_FIXTURE)

    assert actual_hash == STDIO_SHA256
    assert fixture[0] == {
        "kind": "metadata",
        "source_snapshot": "spike-mcp-server-snapshot-d93f71a",
        "source_file": "src/stdio.ts",
        "source_file_sha256": STDIO_SHA256,
        "transport": "stdio",
        "protocol": "json-rpc-2.0",
        "capture_policy": "snapshot-derived",
    }
    assert "StdioServerTransport" in source.read_text(encoding="utf-8")
    assert "createCaiMcpServer" in source.read_text(encoding="utf-8")


def test_mcp_jsonrpc_golden_replay_bytes_are_byte_identical() -> None:
    fixture = _load_jsonl(Path(__file__).resolve().parents[4] / GOLDEN_FIXTURE)
    frames = [entry for entry in fixture if entry["kind"] == "frame"]
    replay = [entry["bytes"].encode("utf-8") for entry in frames]

    assert replay == [INITIALIZE_BYTES, INITIALIZED_BYTES]

    initialize = json.loads(replay[0])
    initialized = json.loads(replay[1])
    assert initialize["jsonrpc"] == "2.0"
    assert initialize["method"] == "initialize"
    assert initialized == {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }
