# Cai Coaching MCP Server — Spike

MCP (Model Context Protocol) server exposing Cai's coaching capabilities to enterprise AI platforms: CoPilot, ChatGPT Enterprise, Claude Desktop.

**See [FINDINGS.md](./FINDINGS.md) for the full spike report.**

## Quick Start

```bash
npm install
npm run build
```

### stdio transport (Claude Desktop / Claude Code / MCP Inspector)

```bash
npm run start:stdio
```

### Streamable HTTP transport (Azure Functions / remote)

```bash
npm run start:http
# Server at http://127.0.0.1:3000/mcp
# Health check at http://127.0.0.1:3000/health
```

### Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector node dist/stdio.js
# Opens http://localhost:6274
```

## What's Exposed

| Type | Name | Description |
|------|------|-------------|
| Tool | `single-turn-advice` | Coaching response for a leadership question |
| Tool | `book-session` | Book a coaching session (ai/human/hybrid) |
| Resource | `coaching://model` | Complete coaching methodology overview |
| Resource | `coaching://territories` | 12 coaching territory modules |
| Resource | `coaching://territories/{id}` | Individual territory detail |
| Resource | `coaching://signals` | 7 coaching signal types |
| Resource | `coaching://phases` | 7-phase coaching arc |
| Prompt | `coaching-question` | Structured coaching question template |

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "cai-coaching": {
      "command": "node",
      "args": ["<path-to-spike>/dist/stdio.js"]
    }
  }
}
```

## Stack

- TypeScript + `@modelcontextprotocol/sdk` v1.29.0
- Zod schema validation
- stdio + Streamable HTTP (stateless) transports
- Stub backend (production: connects to Cai coaching API on Azure Functions)
