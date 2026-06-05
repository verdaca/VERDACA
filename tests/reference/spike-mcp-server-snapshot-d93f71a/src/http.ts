/**
 * Cai Coaching MCP Server — Streamable HTTP transport
 *
 * Use this for remote deployment (Azure Functions, Container Apps, standalone).
 * Stateless mode suitable for serverless environments.
 *
 * Launch: npx tsx src/http.ts
 * Test: curl -X POST http://localhost:3000/mcp -H "Content-Type: application/json" ...
 */

import { createServer } from 'node:http';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { createCaiMcpServer } from './server.js';

const PORT = parseInt(process.env.PORT ?? '3000', 10);

async function main() {
  const httpServer = createServer(async (req, res) => {
    // Health check endpoint
    if (req.url === '/health' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok', server: 'cai-coaching-mcp', version: '0.1.0' }));
      return;
    }

    // MCP endpoint — new server instance per request (stateless, serverless-compatible)
    if (req.url === '/mcp') {
      const server = createCaiMcpServer();
      const transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: undefined, // Stateless — suitable for serverless
      });
      await server.connect(transport);
      await transport.handleRequest(req, res);
      return;
    }

    // 404 for everything else
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found. MCP endpoint is at /mcp' }));
  });

  httpServer.listen(PORT, '127.0.0.1', () => {
    console.error(`Cai Coaching MCP Server (HTTP) listening on http://127.0.0.1:${PORT}/mcp`);
    console.error(`Health check: http://127.0.0.1:${PORT}/health`);
  });

  process.on('SIGINT', () => {
    console.error('Shutting down...');
    httpServer.close();
    process.exit(0);
  });
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
