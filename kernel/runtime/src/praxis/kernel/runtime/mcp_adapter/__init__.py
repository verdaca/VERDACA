"""Praxis Runtime MCP Tool Adapter.

Wraps the official `mcp` Python SDK. Public surface:
  client.py       — MCPToolClient, normalize_mcp_error, is_transient_error
  transport.py    — transport helpers (stdio, HTTP)
  version_guard.py — SDK shape regression guard
"""
