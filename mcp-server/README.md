# 🤖 ARL-Next MCP Server

> 为 AI 助手量身定制的 ARL 资产侦察灯塔系统接口，让大模型（如 Cursor, Claude, Antigravity）无缝接管安全运营。
> 支持 **stdio**（默认）和 **SSE** 两种传输模式。

---

## ⚡ 极速接入

本服务已全面容器化，无需配置 Node.js 依赖。推荐使用一键复制功能：

💡 **快捷方式**：登录 ARL-Next 首页，点击右上角 **「AI 助手接入 (MCP)」** 复制您的专属配置。

---

## 🔌 传输模式选择

### 模式一：Stdio（默认，短生命周期）

适用于 **Claude Desktop、Cursor** 等支持进程启动的 AI 客户端。每次工具调用拉起一个容器，调用结束后销毁。

**手动配置示例**（添加至您的 AI 客户端 `mcpServers` 节点）：

```json
"ARL-Next": {
  "command": "docker",
  "args": [
    "run", "-i", "--rm",
    "-e", "ARL_HOST",
    "-e", "ARL_TOKEN",
    "arl-next-mcp:latest"
  ],
  "env": {
    "ARL_HOST": "https://[您的服务器IP或域名]:5000",
    "ARL_TOKEN": "您的_API_TOKEN"
  }
}
```
*注：初次使用需先构建本地镜像：在 `mcp-server` 目录下执行 `docker build -t arl-next-mcp:latest .`。*

### 模式二：SSE（持久化 HTTP 服务，推荐）

#### 架构说明

MCP Server 与 ARL 项目部署在**同一台 VPS 的 Docker 网络**中，通过 SSE 协议为远程客户端提供服务：

```
AI 客户端 (Cursor/Claude Desktop/etc.)
       │  SSE over HTTPS
       ▼
VPS ┌─────────────────────────────────────────┐
    │  arl-frontend  (端口 5173)               │
    │  arl-web       (内网 arl-web:5000)       │
    │  arl-mcp       (端口 3100) ← MCP Server  │
    │                     └─ 连接内网 ARL API   │
    └─────────────────────────────────────────┘
```

#### 部署方式

**步骤 1：在 VPS 上构建镜像**

```bash
# 进入项目目录（VPS 上已拉取代码）
cd ~/ARL-Next/mcp-server
docker build -t arl-next-mcp:latest .
```

**步骤 2：启动 SSE 容器（加入 ARL Docker 网络）**

```bash
docker run -d --name arl-next-mcp \
  --network arl-next-prod_arl-net \
  -p 3100:3100 \
  -e ARL_HOST=http://arl-web:5000 \
  -e ARL_TOKEN="您的_API_TOKEN" \
  -e SSE=true \
  -e PORT=3100 \
  arl-next-mcp:latest
```

> **关键说明：**
> - `--network arl-next-prod_arl-net` 让 MCP 容器与 ARL 服务同网络，可直接通过容器名访问
> - `ARL_HOST=http://arl-web:5000` 指向 Docker 内网的 ARL Web 服务
> - `ARL_TOKEN` 需与 ARL 系统的 API Token 一致（即登录后生成的 Token）

**步骤 3：验证部署**

```bash
curl http://localhost:3100/health
# 返回: {"status":"ok","mode":"sse","activeSessions":0,"tools":6}
```

#### 客户端配置

从 ARL 前端页面（右上角「AI 助手接入」）选择 **HTTP (SSE)** 模式，复制生成的配置。URL 已自动内嵌 Token 鉴权：

```json
"ARL-Next": {
  "url": "http://[VPS-IP]:3100/sse?token=您的_API_TOKEN"
}
```

> **安全说明：** SSE 端点的 `/sse` 接口会验证 `token` 参数，无效 Token 返回 401。Token 通过 URL 传递，建议在生产环境使用 HTTPS 反向代理保护外层连接。**健康检查 `/health` 无需鉴权。**

#### 本地开发启动

```bash
# 直接运行
node index.js --sse

# 或通过环境变量
SSE=true node index.js

# 指定端口（默认 3100）
PORT=3200 node index.js --sse

# 通过 npm script
npm run start:sse
```

---

## 🛠️ 核心能力矩阵 (Tools)

AI 助手已自动掌握以下 6 大核心技能，支持智能化分页与纠错：

### 🔍 资产与漏洞分析
- **`search_assets`** 资产检索：全方位搜寻站点、IP、域名、证书及服务指纹。 *(例: "查一下开了 nginx 的站点")*
- **`search_vulns`** 漏洞查询：精准检索安全漏洞，支持按严重级别过滤。 *(例: "最近有哪些高危漏洞？")*
- **`get_tasks`** 任务监控：实时跟进扫描任务的进度与状态。 *(例: "看看有没有失败的任务")*
- **`get_dashboard_summary`** 运行概览：一键生成全盘资产、任务与漏洞统计大盘。 *(例: "给我一份今日战报")*

### 🏢 商业/备案情报 (ICP)
- **`search_icp_tasks`** ICP 任务追踪：查询企业备案拉取任务进度。 *(例: "某某公司的ICP查完没？")*
- **`search_icp_assets`** 子资产挖掘：深挖小程序、公众号、快应用等扩展资产。 *(例: "列出那个任务查到的所有公众号")*

---

## 💡 常见 AI 客户端配置路径

| 客户端 | 配置入口 / 文件路径 |
| :--- | :--- |
| **Claude Desktop** | **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`<br>**Win**: `%APPDATA%\Claude\claude_desktop_config.json` |
| **Cursor** | 面板：`Settings` -> `Features` -> `MCP` -> `+ Add new MCP server` |
| **Antigravity** | **全局**: `~/.gemini/config/mcp.json`<br>**项目**: `.gemini/mcp.json` |
| **Codex** | **全局**: `~/.codex/config.toml` (在 `[mcp_servers.arl-next]` 节点添加) |
| **Windsurf / Trae** | 面板：`Settings` -> `AI` -> `MCP Servers` -> `Add Server`（选择 SSE 模式，填写 url） |

---

## 📚 API 参考

开发者需要直接对接后端 API？
ARL-Next 提供开箱即用的 OpenAPI (Swagger) 交互式文档：
👉 访问地址：`https://[您的服务器IP或域名]:5173/api/doc`

---

## 📦 构建与开发

```bash
# 安装依赖
npm install

# Stdio 模式启动（默认）
npm start

# SSE 模式启动
npm run start:sse

# 构建 Docker 镜像
docker build -t arl-next-mcp:latest .
```
