#!/usr/bin/env node

const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require("@modelcontextprotocol/sdk/types.js");
const axios = require("axios");
const https = require("https");

// ============================================================
// 启动模式判断
// ============================================================
const args = process.argv.slice(2);
const isSseMode = args.includes("--sse") || process.env.SSE === "true" || process.env.SSE === "1";
const PORT = parseInt(process.env.PORT || "3100", 10);

// ============================================================
// 环境变量验证
// ============================================================
const host = process.env.ARL_HOST;
const envToken = process.env.ARL_TOKEN;

if (!host || !envToken) {
  console.error("Error: Environment variables ARL_HOST and ARL_TOKEN are required.");
  process.exit(1);
}

// ============================================================
// 载荷裁剪 & 响应格式化（纯函数，无状态）
// ============================================================
function trimPayload(data) {
  if (data === null || data === undefined) return data;
  if (Array.isArray(data)) {
    return data.map(trimPayload);
  } else if (typeof data === "object") {
    const trimmed = {};
    for (const [key, value] of Object.entries(data)) {
      if (["body", "header", "headers", "favicon", "raw_data", "html", "icon", "cert_raw", "ssl_cert"].includes(key)) continue;
      if (typeof value === "string" && value.length > 500) {
        trimmed[key] = value.substring(0, 500) + "...[TRUNCATED]";
      } else {
        trimmed[key] = trimPayload(value);
      }
    }
    return trimmed;
  }
  return data;
}

function formatResponse(responseData) {
  const trimmed = trimPayload(responseData);
  let resultStr = JSON.stringify(trimmed, null, 2);
  if (responseData && responseData.page && responseData.size && responseData.total !== undefined) {
    const totalPages = Math.ceil(responseData.total / responseData.size) || 1;
    resultStr += `\n\n[System Note: 当前显示第 ${responseData.page} 页，共 ${totalPages} 页 (总计 ${responseData.total} 条数据)。]`;
  }
  return resultStr;
}

// ============================================================
// API 客户端工厂（每会话独立，使用该会话的 Token）
// ============================================================
function createApiClient(token) {
  return axios.create({
    baseURL: `${host}/api`,
    headers: { "Token": token },
    timeout: 10000,
    httpsAgent: new https.Agent({ rejectUnauthorized: false, keepAlive: true }),
  });
}

// ============================================================
// MCP Server 工厂（每会话独立）
// ============================================================
function createMcpServer(token) {
  const apiClient = createApiClient(token);
  const server = new Server(
    { name: "arl-next-mcp", version: "1.0.0" },
    { capabilities: { tools: {} } }
  );

  // ---------- 工具定义 ----------
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
      {
        name: "search_assets",
        description:
          "在 ARL-Next 资产库中搜索发现的资产。支持查询网站(site)、IP、域名(domain)、证书(cert)、开放端口/服务(service)。必需参数: assetType。支持 query 模糊搜索。",
        inputSchema: {
          type: "object",
          properties: {
            assetType: { type: "string", enum: ["site", "ip", "domain", "cert", "service"], description: "资产类型" },
            query: { type: "string", description: "模糊搜索关键词" },
            page: { type: "number", description: "页码 (默认 1)" },
            size: { type: "number", description: "单页数据量 (默认 10，最大 50)" },
          },
          required: ["assetType"],
        },
      },
      {
        name: "search_vulns",
        description: "搜索安全漏洞，支持按严重级别过滤或模糊搜索。",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "漏洞名称模糊搜索" },
            vuln_severity: { type: "string", enum: ["critical", "high", "medium", "low"], description: "严重级别" },
            page: { type: "number", description: "页码 (默认 1)" },
            size: { type: "number", description: "单页数据量 (默认 10，最大 50)" },
          },
        },
      },
      {
        name: "get_dashboard_summary",
        description: "获取 ARL 系统运行状态与统计大盘数据。",
        inputSchema: { type: "object", properties: {} },
      },
      {
        name: "get_tasks",
        description: "获取最近的资产发现与漏洞扫描任务列表。",
        inputSchema: {
          type: "object",
          properties: {
            page: { type: "number", description: "页码 (默认 1)" },
            size: { type: "number", description: "单页数据量 (默认 10)" },
          },
        },
      },
      {
        name: "search_icp_tasks",
        description: "查询 ICP 备案信息拉取及企业架构分析任务。",
        inputSchema: {
          type: "object",
          properties: {
            name: { type: "string", description: "任务名称过滤" },
            target: { type: "string", description: "目标公司过滤" },
            status: { type: "string", description: "任务状态" },
            page: { type: "number", description: "页码 (默认 1)" },
            size: { type: "number", description: "单页数据量 (默认 10)" },
          },
        },
      },
      {
        name: "search_icp_assets",
        description: "深度挖掘 ICP 任务获取的子资产数据（公众号、小程序、商标等）。",
        inputSchema: {
          type: "object",
          properties: {
            task_id: { type: "string", description: "ICP 任务 ID" },
            query_type: {
              type: "string",
              enum: ["web", "app", "mapp", "kapp", "invest", "trademark", "wechat", "weibo"],
              description: "查询子维度",
            },
            page: { type: "number", description: "页码 (默认 1)" },
            size: { type: "number", description: "单页数据量 (默认 10，最大 50)" },
          },
          required: ["query_type"],
        },
      },
    ],
  }));

  // ---------- 工具执行 ----------
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: toolArgs } = request.params;

    try {
      if (name === "search_assets") {
        const { assetType, query, page = 1, size = 10 } = toolArgs;
        if (!["site", "ip", "domain", "cert", "service"].includes(assetType)) {
          return { content: [{ type: "text", text: `Error: Invalid assetType '${assetType}'` }], isError: true };
        }
        const response = await apiClient.get(`/${assetType}/`, { params: { page, size: Math.min(size, 50), query } });
        return { content: [{ type: "text", text: formatResponse(response.data) }] };
      }

      if (name === "search_vulns") {
        const { query, vuln_severity, page = 1, size = 10 } = toolArgs;
        const response = await apiClient.get("/vuln/", { params: { page, size: Math.min(size, 50), query, vuln_severity } });
        return { content: [{ type: "text", text: formatResponse(response.data) }] };
      }

      if (name === "get_dashboard_summary") {
        const [statsRes, sysinfoRes] = await Promise.all([
          apiClient.get("/dashboard/stats"),
          apiClient.get("/dashboard/sysinfo"),
        ]);
        return { content: [{ type: "text", text: JSON.stringify({ stats: statsRes.data, sysinfo: sysinfoRes.data }, null, 2) }] };
      }

      if (name === "get_tasks") {
        const { page = 1, size = 10 } = toolArgs;
        const response = await apiClient.get("/task/", { params: { page, size } });
        return { content: [{ type: "text", text: formatResponse(response.data) }] };
      }

      if (name === "search_icp_tasks") {
        const { page = 1, size = 10, name: taskName, target, status } = toolArgs;
        const response = await apiClient.get("/icp/task", { params: { page, size, name: taskName, target, status } });
        return { content: [{ type: "text", text: formatResponse(response.data) }] };
      }

      if (name === "search_icp_assets") {
        const { task_id, query_type, page = 1, size = 10 } = toolArgs;
        if (!["web", "app", "mapp", "kapp", "invest", "trademark", "wechat", "weibo"].includes(query_type)) {
          return { content: [{ type: "text", text: `Error: Invalid query_type '${query_type}'` }], isError: true };
        }
        const response = await apiClient.get("/icp/asset", { params: { page, size: Math.min(size, 50), task_id, query_type } });
        return { content: [{ type: "text", text: formatResponse(response.data) }] };
      }

      throw new Error(`Unknown tool: ${name}`);
    } catch (error) {
      return {
        content: [{ type: "text", text: `API Request Failed: ${error.message}\n${error.response?.data ? JSON.stringify(error.response.data) : ""}` }],
        isError: true,
      };
    }
  });

  return server;
}

// ============================================================
// Stdio 模式
// ============================================================
async function runStdio() {
  const server = createMcpServer(envToken);
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("ARL-Next MCP Server running on stdio transport");
}

// ============================================================
// SSE 模式（每会话独立 Server + 独立 Token）
// ============================================================
async function runSse() {
  const express = require("express");
  const cors = require("cors");
  const { SSEServerTransport } = require("@modelcontextprotocol/sdk/server/sse.js");

  const app = express();
  app.use(cors());
  app.use(express.json());

  // 存储活跃会话 { sessionId -> { server, transport } }
  const sessions = {};

  // ---------- Token 鉴权中间件（通过 ARL API 实时验证）----------
  function authMiddleware(req, res, next) {
    const token = req.query.token || (req.headers.authorization && req.headers.authorization.replace(/^Bearer\s+/i, ""));
    if (!token) {
      return res.status(401).json({ error: "Unauthorized: missing token" });
    }

    // 用客户端提交的 Token 请求 ARL API 验证有效性
    const validator = axios.create({
      baseURL: `${host}/api`,
      headers: { "Token": token },
      timeout: 5000,
      httpsAgent: new https.Agent({ rejectUnauthorized: false }),
    });

    validator.get("/dashboard/stats").then((resp) => {
      // ARL API 统一返回 HTTP 200，鉴权结果在 body.code 中
      if (resp.data && resp.data.code === 200) {
        req.clientToken = token;
        return next();
      }
      return res.status(401).json({ error: "Unauthorized: invalid token" });
    }).catch((err) => {
      // ARL 网络不可达时回退到环境变量比对
      if (token === envToken) {
        req.clientToken = token;
        return next();
      }
      return res.status(503).json({ error: "ARL backend unreachable and token fallback failed" });
    });
  }

  // ---------- SSE 端点 ----------
  app.get("/sse", authMiddleware, async (req, res) => {
    const transport = new SSEServerTransport("/messages", res);
    const sessionServer = createMcpServer(req.clientToken);

    sessions[transport.sessionId] = { server: sessionServer, transport };
    res.on("close", () => {
      delete sessions[transport.sessionId];
      sessionServer.close();
    });

    await sessionServer.connect(transport);
  });

  // ---------- 消息端点 ----------
  app.post("/messages", async (req, res) => {
    const sessionId = req.query.sessionId;
    const session = sessions[sessionId];
    if (session) {
      await session.transport.handlePostMessage(req, res);
    } else {
      res.status(400).json({ error: "Session not found" });
    }
  });

  // ---------- 健康检查 ----------
  app.get("/health", (_req, res) => {
    res.json({
      status: "ok",
      mode: "sse",
      activeSessions: Object.keys(sessions).length,
      tools: 6,
    });
  });

  await new Promise((resolve, reject) => {
    app.listen(PORT, (err) => {
      if (err) return reject(err);
      resolve();
    });
  });

  console.error(`ARL-Next MCP Server running on SSE transport → http://localhost:${PORT}/sse`);
  console.error(`  Health check → http://localhost:${PORT}/health`);
}

// ============================================================
// 启动入口
// ============================================================
if (isSseMode) {
  runSse().catch((error) => {
    console.error("Fatal error running MCP server in SSE mode:", error);
    process.exit(1);
  });
} else {
  runStdio().catch((error) => {
    console.error("Fatal error running MCP server:", error);
    process.exit(1);
  });
}
