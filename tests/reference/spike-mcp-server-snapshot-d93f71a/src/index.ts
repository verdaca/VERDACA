/**
 * Cai Coaching MCP Server — Default entry point (stdio)
 *
 * Defaults to stdio transport for broadest MCP client compatibility.
 * Use src/http.ts for Streamable HTTP transport.
 */
export { createCaiMcpServer } from './server.js';

// Default: run stdio transport
import './stdio.js';
