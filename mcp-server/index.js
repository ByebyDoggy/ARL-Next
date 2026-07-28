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
        name: "submit_task",
        description: "下发资产发现任务。支持完整参数控制：域名爆破（可选 test/top1000/top10/subdomainer 类型）、端口扫描（test/top100/top1000/all/custom）、服务识别、站点识别/截图、JS信息提取(web_info_hunter)、文件泄露、SSL证书、Host碰撞(findvhost)等。",
        inputSchema: {
          type: "object",
          properties: {
            name: { type: "string", description: "任务名称" },
            target: { type: "string", description: "目标域名或IP，多个用逗号/换行分隔" },
            domain_brute: { type: "boolean", description: "启用域名爆破 (默认 true)" },
            domain_brute_type: { type: "string", enum: ["test", "top1000", "top10", "subdomainer"], description: "域名爆破字典类型 (默认 test)" },
            port_scan_type: { type: "string", enum: ["test", "top100", "top1000", "all", "custom"], description: "端口扫描类型 (默认 test)" },
            port_scan: { type: "boolean", description: "启用端口扫描 (默认 true)" },
            service_detection: { type: "boolean", description: "服务识别" },
            service_brute: { type: "boolean", description: "服务弱口令爆破" },
            os_detection: { type: "boolean", description: "操作系统识别" },
            site_identify: { type: "boolean", description: "站点指纹识别" },
            site_capture: { type: "boolean", description: "站点截图" },
            site_spider: { type: "boolean", description: "站点爬虫" },
            file_leak: { type: "boolean", description: "文件泄露检测" },
            search_engines: { type: "boolean", description: "搜索引擎调用" },
            arl_search: { type: "boolean", description: "ARL 历史查询碰撞" },
            alt_dns: { type: "boolean", description: "DNS字典智能生成" },
            ssl_cert: { type: "boolean", description: "SSL 证书获取" },
            dns_query_plugin: { type: "boolean", description: "域名查询插件" },
            skip_scan_cdn_ip: { type: "boolean", description: "跳过CDN IP扫描" },
            findvhost: { type: "boolean", description: "Host 碰撞" },
            web_info_hunter: { type: "boolean", description: "WEB JS 信息提取" },
            npoc_service_detection: { type: "boolean", description: "服务(Python)识别" },
            nuclei_scan: { type: "boolean", description: "Nuclei 漏洞扫描" },
            wih: { type: "boolean", description: "WIH Web感染检测" },
          },
          required: ["name", "target"],
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

      if (name === "submit_task") {
        const payload = { name: toolArgs.name, target: toolArgs.target };
        const boolFields = ["domain_brute", "port_scan", "service_detection", "service_brute",
          "os_detection", "site_identify", "site_capture", "site_spider", "file_leak",
          "search_engines", "arl_search", "alt_dns", "ssl_cert", "dns_query_plugin",
          "skip_scan_cdn_ip", "findvhost", "web_info_hunter", "npoc_service_detection",
          "nuclei_scan", "wih"];
        for (const field of boolFields) {
          if (toolArgs[field] !== undefined) payload[field] = toolArgs[field];
        }
        if (toolArgs.domain_brute_type) payload.domain_brute_type = toolArgs.domain_brute_type;
        if (toolArgs.port_scan_type) payload.port_scan_type = toolArgs.port_scan_type;

        const response = await apiClient.post("/task/", payload);
        return { content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }] };
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
  // 注意：不使用 express.json()，因为 MCP SDK 的 handlePostMessage 通过 raw stream 读取请求体

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
