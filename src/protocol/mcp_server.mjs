#!/usr/bin/env node
/**
 * MCP stdio server: proxies ECP FastAPI tools (resolve, execute, feedback, search, provenance).
 *
 * Env:
 *   ECP_BASE_URL   - default http://127.0.0.1:8080
 *   ECP_API_KEY    - optional x-ecp-api-key header for API auth
 *   ECP_USER_ID    - optional default x-ecp-user-id header
 *   ECP_DEPARTMENT - optional x-ecp-department
 *   ECP_ROLE       - optional x-ecp-role
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import * as z from "zod";

const BASE = (process.env.ECP_BASE_URL || "http://127.0.0.1:8080").replace(/\/$/, "");

function baseHeaders() {
  const h = { "Content-Type": "application/json", Accept: "application/json" };
  if (process.env.ECP_API_KEY) h["x-ecp-api-key"] = process.env.ECP_API_KEY;
  if (process.env.ECP_USER_ID) h["x-ecp-user-id"] = process.env.ECP_USER_ID;
  if (process.env.ECP_DEPARTMENT) h["x-ecp-department"] = process.env.ECP_DEPARTMENT;
  if (process.env.ECP_ROLE) h["x-ecp-role"] = process.env.ECP_ROLE;
  return h;
}

function withIdentityHeaders({ user_id, department, role } = {}) {
  const headers = { ...baseHeaders() };
  if (user_id !== undefined) headers["x-ecp-user-id"] = user_id;
  if (department !== undefined) headers["x-ecp-department"] = department;
  if (role !== undefined) headers["x-ecp-role"] = role;
  return headers;
}

function jsonText(obj) {
  return { content: [{ type: "text", text: JSON.stringify(obj, null, 2) }] };
}

async function api(path, { method = "GET", body, headers = {} } = {}) {
  const url = `${BASE}${path}`;
  const r = await fetch(url, {
    method,
    headers: { ...baseHeaders(), ...headers },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await r.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text, status: r.status };
  }
  if (!r.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string"
      ? detail
      : detail !== undefined
        ? JSON.stringify(detail)
        : r.statusText;
    const err = new Error(message);
    err.status = r.status;
    err.body = data;
    throw err;
  }
  return data;
}

const mcpServer = new McpServer({
  name: "enterprise-context-platform",
  version: "3.0.0",
});

mcpServer.registerTool(
  "resolve_concept",
  {
    description: "Resolve a business concept to canonical definitions and an execution plan (ECP POST /api/v1/resolve).",
    inputSchema: {
      concept: z.string().describe("Natural language concept, e.g. APAC revenue last quarter"),
      user_id: z.string().optional().describe("Overrides ECP_USER_ID for this call"),
      department: z.string().optional(),
      role: z.string().optional(),
    },
  },
  async ({ concept, user_id, department, role }) => {
    const headers = withIdentityHeaders({ user_id, department, role });
    const data = await api("/api/v1/resolve", {
      method: "POST",
      body: { concept, user_context: null },
      headers,
    });
    return jsonText(data);
  },
);

mcpServer.registerTool(
  "execute_metric",
  {
    description: "Execute a stored resolution against the semantic layer (ECP POST /api/v1/execute).",
    inputSchema: {
      resolution_id: z.string(),
      parameters: z.record(z.string(), z.any()).optional().default({}),
      user_id: z.string().optional(),
      department: z.string().optional(),
      role: z.string().optional(),
    },
  },
  async ({ resolution_id, parameters, user_id, department, role }) => {
    const data = await api("/api/v1/execute", {
      method: "POST",
      body: { resolution_id, parameters: parameters || {} },
      headers: withIdentityHeaders({ user_id, department, role }),
    });
    return jsonText(data);
  },
);

mcpServer.registerTool(
  "report_feedback",
  {
    description: "Report feedback on a resolution (ECP POST /api/v1/feedback).",
    inputSchema: {
      resolution_id: z.string(),
      feedback: z.enum(["accepted", "corrected", "rejected"]),
      correction_details: z.string().optional().default(""),
      user_id: z.string().optional(),
      department: z.string().optional(),
      role: z.string().optional(),
    },
  },
  async ({ resolution_id, feedback, correction_details, user_id, department, role }) => {
    const data = await api("/api/v1/feedback", {
      method: "POST",
      body: {
        resolution_id,
        feedback,
        correction_details: correction_details || "",
      },
      headers: withIdentityHeaders({ user_id, department, role }),
    });
    return jsonText(data);
  },
);

mcpServer.registerTool(
  "search_context",
  {
    description: "Search the context registry (ECP POST /api/v1/search).",
    inputSchema: {
      query: z.string(),
      asset_types: z.array(z.string()).optional().default([]),
      limit: z.number().int().min(1).max(100).optional().default(10),
      user_id: z.string().optional(),
      department: z.string().optional(),
      role: z.string().optional(),
    },
  },
  async ({ query, asset_types, limit, user_id, department, role }) => {
    const data = await api("/api/v1/search", {
      method: "POST",
      body: { query, asset_types: asset_types || [], limit: limit ?? 10 },
      headers: withIdentityHeaders({ user_id, department, role }),
    });
    return jsonText(data);
  },
);

mcpServer.registerTool(
  "get_provenance",
  {
    description: "Fetch provenance for a resolution id (ECP GET /api/v1/provenance/{id}).",
    inputSchema: {
      resolution_id: z.string(),
      user_id: z.string().optional(),
      department: z.string().optional(),
      role: z.string().optional(),
    },
  },
  async ({ resolution_id, user_id, department, role }) => {
    const data = await api(`/api/v1/provenance/${encodeURIComponent(resolution_id)}`, {
      headers: withIdentityHeaders({ user_id, department, role }),
    });
    return jsonText(data);
  },
);

async function main() {
  const transport = new StdioServerTransport();
  await mcpServer.connect(transport);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
