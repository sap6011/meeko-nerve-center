#!/usr/bin/env node

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { config } from './config.js';
import { createChargeSchema, createCharge, getChargeSchema, getCharge } from './tools/index.js';

// Create MCP server
const server = new McpServer({
  name: config.serverName,
  version: config.serverVersion,
});

// Register tools
server.tool(
  'create-charge',
  'Generate a Coinbase Commerce payment link',
  createChargeSchema,
  createCharge
);

server.tool(
  'get-charge',
  'Retrieve details of an existing Coinbase Commerce charge',
  getChargeSchema,
  getCharge
);

async function main() {
  // Start with stdio transport
  const transport = new StdioServerTransport();
  
  try {
    // Verify API key is present
    if (!config.coinbaseCommerceApiKey) {
      console.error('Error: COINBASE_COMMERCE_API_KEY is not defined in environment variables');
      process.exit(1);
    }

    // Connect to transport
    await server.connect(transport);
    console.error('Coinbase Commerce MCP Server running on stdio');
  } catch (error) {
    console.error('Error starting MCP server:', error);
    process.exit(1);
  }
}

// Start the server
main().catch((error) => {
  console.error('Fatal error in main():', error);
  process.exit(1);
});