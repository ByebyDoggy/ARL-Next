# 前端 JS 深度静态分析 — 开发计划

> **对应文章**：《怎么做好资产信息收集》— 第 4/5/6/11 章  
> **优先级**：P0（投资回报最高）  
> **原则**：搜索并阅读成熟工具源码，将核心算法直接整合进项目原生 Python 代码，不通过子进程调用外部项目  

---

## 一、背景与目标

### 1.1 当前项目能力

ARL-Next 已具备的 JS 分析能力：

| 模块 | 能力 | 局限 |
|------|------|------|
| **WIH (Web Info Hunter)** | Go 二进制，下载站点 JS 文件，按规则提取 AK/SK/身份证/JWT/手机号等敏感信息 | 只做正则匹配，**不提取 API 端点、不分析架构、不解析 Source Map** |
| **webAnalyze** | 通过 Puppeteer 调用 Wappalyzer，识别前端框架/技术栈 | 只做指纹识别，**不深入 JS 内容** |
| **siteUrlSpider** | 爬取站点 URL（JS/CSS/Document）并去重 | 只收集 URL，**不做内容分析** |

### 1.2 目标

新增 **JS 深度静态分析** 能力，覆盖文章以下章节：

- **第四章（二级业务目录）**：从 JS 中读取 API 端点、解析 Swagger、读取前端路由表
- **第五章（从前端反推后端）**：API 全表提取、鉴权逻辑反推、多环境地址提取、Source Map 检测
- **第六章（影子资产）**：JS 中残留的内部域名、硬编码配置提取
- **第十一章（C 端→B 端串联）**：JS 中搜索 admin 路由、管理接口发现、权限字段提取

### 1.3 预期产出

| 产出 | 说明 |
|------|------|
| JS 文件收集器 | 从目标站点批量发现/下载 JS bundle |
| API 端点提取器 | 从 JS 中提取 fetch/XHR/axios 等请求的 URL、方法、参数 |
| Source Map 探测器 | 检测并下载 .map 文件，还原原始源码 |
| SPA 路由提取器 | 从 Vue/React/Angular 路由配置中提取业务页面路径 |
| 敏感配置提取器 | 多环境地址、鉴权配置、硬编码密钥 |
| 管理后台发现器 | JS 中 admin/manage/console 路径及权限字段检测 |
| 前端架构报告 | 汇总以上分析，生成结构化报告 |

---

## 二、成熟工具源码调研与核心算法提取

### 2.1 调研结论

搜索了 GitHub / npm / PyPI 等渠道，评估了多个候选工具。**最终决定：不通过子进程调用外部项目，而是直接读取两个高价值工具的核心源码，将算法提取并整合进项目原生 Python 代码中。**

选中两个工具作为"源码参考"：

| 工具 | 语言 | 核心能力 | 代码规模 | 提取内容 |
|------|------|---------|---------|---------|
| **jsrip** | Python | API端点提取 + 密钥检测 + 智能分析 + 误报过滤 | ~2500行 | `analyzer.py` 核心分析类 + 匹配模式 |
| **getfrontend** | Python | Source Map 发现 + 重建 + webpack/vite chunk 解析 | ~1200行 | Source Map 检测 + 现代框架 chunk 发现算法 |

### 2.2 jsrip 源码核心提取（analyzer.py）

**仓库**：[mouteee/jsrip](https://github.com/mouteee/jsrip)（Python 99.4%）  
**核心文件**：`core/analyzer.py`（786行）

**提取的核心类与算法**：

| 类/函数 | 功能 | 代码位置 |
|---------|------|---------|
| `JSAnalyzer` | JS 分析主类 | 全文核心 |
| `_find_secrets()` | 基于 patterns 字典的正则匹配密钥检测 | analyzer.py |
| `_find_sensitive_assignments()` | 检测 const/let/var 敏感变量赋值 | analyzer.py |
| `_find_config_objects()` | 检测对象字面量中的敏感配置键 | analyzer.py |
| `_find_env_leaks()` | 检测 process.env 环境变量泄漏 | analyzer.py |
| `_find_dom_storage()` | 检测 localStorage/sessionStorage 敏感存储 | analyzer.py |
| `_find_endpoints()` | 提取 fetch/axios/XHR API 端点 | analyzer.py |
| `_is_false_positive()` | 多层误报过滤 | analyzer.py |
| `_assess_confidence()` | 三档置信度评估（基于关键词+Shannon熵） | analyzer.py |
| `_calculate_entropy()` | Shannon 熵计算 | analyzer.py |
| `_deduplicate_by_content()` | 基于 SHA256 去重 | analyzer.py |
| `FETCH_URL_RE` | HTTP 客户端正则（fetch/axios/jQuery/XMLHttpRequest） | analyzer.py |
| `SENSITIVE_VAR_NAMES` | 敏感变量名正则 | analyzer.py |
| `VAR_ASSIGNMENT_RE` / `OBJ_PROPERTY_RE` | 变量赋值与对象属性提取 | analyzer.py |
| `ENV_LEAK_RE` / `DOM_STORAGE_RE` | 环境变量与 DOM 存储提取 | analyzer.py |

### 2.3 getfrontend 源码核心提取（getfrontend.py）

**仓库**：[zb3/getfrontend](https://github.com/zb3/getfrontend)（Python 100%，~1200行）  
**核心文件**：`getfrontend.py`（单一文件）

**提取的核心类与算法**：

| 类/方法 | 功能 | 说明 |
|---------|------|------|
| `Crawler.handle_js()` | JS 文件处理主入口，触发 Source Map 检测 | getfrontend.py:290 |
| `Crawler.handle_header_sourcemaps()` | 从 HTTP 响应头 `SourceMap`/`X-SourceMap` 检测 | getfrontend.py:335 |
| `Crawler.handle_content_sourcemaps()` | 从 JS 内容中检测 `sourceMappingURL=`（URL + inline base64） | getfrontend.py:342 |
| `Crawler.fetch_and_handle_srcmap()` | 下载并解析 .map 文件 | getfrontend.py:394 |
| `Crawler.handle_srcmap_data()` | 解析 version 3 Source Map JSON，提取 sources + sourcesContent | getfrontend.py:439 |
| `Crawler.find_webpack_chunk_info()` | webpack chunk 发现（runtime 解析） | getfrontend.py:588 |
| `Crawler.find_vite_chunks()` | Vite chunk 发现（__vite__fileDeps / __vite__mapDeps） | getfrontend.py:502 |
| `Crawler.find_federated_modules()` | Module Federation 远程模块发现 | getfrontend.py:805 |
| `Crawler.find_import_references()` | 静态 import() / from 引用发现 | getfrontend.py:1055 |
| `FArchive` | 重建源码的归档/保存类 | getfrontend.py:60 |
| `Client` | HTTP 请求客户端（超时/重试） | getfrontend.py:109 |

**Source Map 检测三路策略**（直接移植）：
1. JS 文件末尾 `//# sourceMappingURL=xxx.map` 正则匹配
2. HTTP 响应头 `SourceMap` / `X-SourceMap` 字段
3. 自动尝试请求 `{js_url}.map`（追加 .map 后缀）

### 2.4 其他参考工具（未选但值得关注）

| 工具 | 说明 |
|------|------|
| **anastasis** | Node.js AST 级别端点提取，其 MCP Server 可作为后续增强 |
| **@js-recon/js-recon** | 全流水线 SPA 分析 + OpenAPI 重建，MCP 集成 |
| **FerretJS** | 与 jsrip 功能重叠，有 Cloudflare 绕过可参考 |

### 2.5 综合结论

**采用"源码整合"策略**：
1. 将 jsrip 的 `JSAnalyzer` 类核心逻辑（API 端点提取 + 密钥检测 + 智能分析 + 误报过滤）移植到项目原生 Python 模块中
2. 将 getfrontend 的 Source Map 检测 + webpack/vite/Next.js chunk 发现算法移植到项目原生 Python 模块中
3. 自定义实现 SPA 路由提取 / 多环境地址检测 / 管理后台发现
4. 所有代码使用项目现有的 Logger、Config、MongoDB 等基础设施
5. **不产生任何子进程调用**，完全在项目进程内执行

---

## 三、架构设计

### 3.1 总体架构

```
┌─────────────────────────────────────────────────────┐
│                 现有任务流水线 (Celery)                │
├─────────────────────────────────────────────────────┤
│  Domain Task -> Port Scan -> HTTP Probe -> WIH ... │
│                                        |            │
│                            新增: JS 深度分析步骤      │
│  ┌──────────────────────────────────────────────┐   │
│  │           JS Analysis Service                  │   │
│  │                                              │   │
│  │  ┌─────────────────┐  ┌──────────────────┐  │   │
│  │  │  JS File Collector│  │  SourceMap        │  │   │
│  │  │  (复用 Puppeteer)  │  │  Detector         │  │   │
│  │  └────────┬────────┘  │  (移植 getfrontend) │  │   │
│  │           |            └────────┬─────────┘  │   │
│  │           |                     |            │   │
│  │           v                     v            │   │
│  │  ┌────────────────────────────────────────┐  │   │
│  │  │     API Endpoint Extractor              │  │   │
│  │  │     (移植 jsrip JSAnalyzer 核心)         │  │   │
│  │  └────────────────┬───────────────────────┘  │   │
│  │                    |                         │   │
│  │  ┌────────────────────────────────────────┐  │   │
│  │  |      Custom Python Analyzers            │  │   │
│  │  |  ┌────────┐ ┌────────┐ ┌────────────┐  │  │   │
│  │  |  | SPA    | | Multi- | | Admin Path |  │  │   │
│  │  |  | Router | | Env    | | Detector   |  │  │   │
│  │  |  └────────┘ | Config| └────────────┘  │  │   │
│  │  |             └────────┘                 │  │   │
│  │  └────────────────────────────────────────┘  │   │
│  └──────────────────────┬────────────────────────┘  │
│                         |                           │
│                     MongoDB                           │
│              (js_endpoint / js_sourcemap /            │
│               js_route / js_config / js_report)       │
└─────────────────────────────────────────────────────────┘
```

### 3.2 进程内执行

所有分析代码均在 **Celery Worker 进程内直接执行**，无需子进程调用：

- `JSAnalyzer` 类直接 import 使用，接收 JS 文件路径列表
- Source Map 检测使用 requests 库直接 HTTP 请求，不启动外部浏览器
- 自定义分析器使用纯 Python 正则 + 逻辑，零外部依赖
- **不需要扩展 Puppeteer，不需要启动额外浏览器实例**

### 3.3 与现有系统的关系

| 现有组件 | 关系 |
|---------|------|
| **WIH (infoHunter)** | **保留**。jsrip 移植的密钥检测作为 WIH 的**互补验证**。WIH 覆盖中文场景（身份证/手机号），jsrip 覆盖 1600+ 全球服务和智能分析（变量赋值/配置对象/环境变量泄漏）。两者使用不同 `record_type` 前缀（`wih_` vs `jsrip_`），**各自独立入库不做合并去重**，前端可筛选展示 |
| **siteUrlSpider** | **核心 JS URL 来源**。爬虫结果中的 `.js` 文件 URL 直接送入 JS 分析引擎 |
| **getfrontend 算法** | **弥补懒加载盲区**。从入口 JS 内容中静态发现 webpack/vite chunk URL，无需浏览器 |
| **webAnalyze** | **保留**，专注框架指纹，不参与 JS 静态分析 |
| **Celery 任务链** | **扩展**，在域名任务/IP 任务中增加 `js_analysis` 步骤 |

---

## 四、数据模型

### 4.1 新增 MongoDB 集合

#### Collection: `js_endpoint`

从 JS 中提取的 API 端点。

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | String | 任务 ID |
| `site` | String | 所属站点 URL |
| `js_url` | String | 发现该端点的 JS 文件 URL |
| `method` | String | HTTP 方法 (GET/POST/PUT/DELETE 等) |
| `url` | String | API 端点 URL (绝对路径) |
| `path` | String | API 端点路径 (相对路径，如 /api/v1/user/list) |
| `params` | Array | 提取的参数列表 |
| `source` | String | 来源 (fetch/axios/ajax/etc) |
| `framework` | String | 目标框架 (如 Spring Boot / Express) |
| `confidence` | String | 可信度 (high/medium/low) |
| `fnv_hash` | Number | 去重哈希 |
| `create_time` | Datetime | 发现时间 |

索引：`{task_id: 1, fnv_hash: 1}`, `{url: 1}`

#### Collection: `js_sourcemap`

Source Map 检测结果。**不保存全量重建源码**，仅记录发现信息和从中提取的有价值内容。需要时可从 `map_url` 重新下载。

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | String | 任务 ID |
| `site` | String | 所属站点 URL |
| `js_url` | String | 原始 JS 文件 URL |
| `map_url` | String | Source Map URL（可重下） |
| `map_accessible` | Boolean | 是否可访问（这本身即安全信号） |
| `detection_method` | String | 发现方式 (header/content_url/tail_append/inline) |
| `sensitive_findings` | Array | 从源码中提取出的敏感内容列表 |
| `create_time` | Datetime | 发现时间 |

索引：`{task_id: 1}`

#### Collection: `js_route`

从 SPA 前端路由表中提取的业务页面路径。

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | String | 任务 ID |
| `site` | String | 所属站点 URL |
| `js_url` | String | 发现路由的 JS 文件 URL |
| `framework` | String | 前端框架 (vue-router/react-router/angular) |
| `routes` | Array | 路由列表 [ { path, name, component, requires_auth, roles } ] |
| `create_time` | Datetime | 发现时间 |

索引：`{task_id: 1}`

#### Collection: `js_config`

JS 中提取的敏感配置信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | String | 任务 ID |
| `site` | String | 所属站点 URL |
| `js_url` | String | 发现配置的 JS 文件 URL |
| `config_type` | String | 配置类型 (env/endpoint/auth/api_key/internal_domain) |
| `key` | String | 配置键名 |
| `value` | String | 配置值 |
| `environment` | String | 所属环境 (prod/test/dev/internal) |
| `source` | String | 发现方式 (regex/pattern) |
| `fnv_hash` | Number | 去重哈希 |
| `create_time` | Datetime | 发现时间 |

索引：`{task_id: 1, fnv_hash: 1}`

#### Collection: `js_report`

JS 分析汇总报告（每个站点一份）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | String | 任务 ID |
| `site` | String | 站点 URL |
| `js_files_found` | Integer | 发现的 JS 文件数 |
| `js_files_analyzed` | Integer | 已分析的 JS 文件数 |
| `sourcemap_found` | Boolean | 是否发现 Source Map |
| `sourcemap_count` | Integer | Source Map 数量 |
| `api_endpoints` | Integer | API 端点数量 |
| `routes_found` | Integer | 前端路由数量 |
| `config_items` | Integer | 敏感配置数量 |
| `internal_domains` | Array | 发现的内部域名列表 |
| `admin_panels` | Array | 发现的管理后台路径列表 |
| `framework` | String | 检测到的前端框架 |
| `assessment` | String | 安全评估摘要 |
| `create_time` | Datetime | 分析完成时间 |

索引：`{task_id: 1, site: 1}`

### 4.2 数据模型模块

新建 `backend/app/modules/jsAnalysis.py`：

```python
class JsEndpoint:
    """JS 中提取的 API 端点"""
    def __init__(self, task_id, site, js_url, method, url, path,
                 params=None, source=None, framework=None, confidence="medium"):
        ...

class JsSourceMap:
    """Source Map 检测结果。不保存全量源码，仅记录发现信息和提取出的敏感内容"""
    def __init__(self, task_id, site, js_url, map_url, accessible=False,
                 detection_method=None, sensitive_findings=None):
        ...

class JsRoute:
    """SPA 前端路由"""
    def __init__(self, task_id, site, js_url, framework, routes=None):
        ...

class JsConfigItem:
    """JS 中提取的敏感配置"""
    def __init__(self, task_id, site, js_url, config_type, key, value,
                 environment="unknown"):
        ...

class JsReport:
    """JS 分析汇总报告"""
    def __init__(self, task_id, site, js_files_found=0, ...):
        ...
```

---

## 五、模块设计

### 5.1 服务层：`backend/app/services/js_analysis/`

```
js_analysis/
  __init__.py              # 统一入口
  collector.py             # JS 文件收集器
  analyzer.py              # 核心分析引擎（移植 jsrip JSAnalyzer）
  soucemap.py             # Source Map 检测器（移植 getfrontend 核心）
  route_analyzer.py        # SPA 路由分析器（自定义）
  config_extractor.py      # 敏感配置提取器（自定义）
  admin_detector.py        # 管理后台发现器（自定义）
  report_generator.py      # 汇总报告生成器
  patterns.py              # 匹配模式库（含 api_patterns, secret_patterns 等）
```

### 5.2 模块职责

#### `collector.py` — JS 文件收集（无需 Puppeteer）

| 方法 | 说明 |
|------|------|
| `collect_from_spider(task_id)` | **主要来源**。从 `siteUrlSpider` 爬虫结果中提取 `.js` 文件 URL |
| `discover_chunks(entry_js_content, base_url)` | **弥补懒加载盲区**。移植 getfrontend 的 webpack `find_webpack_chunk_info` / Vite `find_vite_chunks` 算法，从入口 JS 中静态发现所有 chunk URL |
| `download_js(url)` | 用 requests 下载单个 JS 文件到本地临时目录 |
| `deduplicate(js_files)` | 按 SHA256 内容哈希去重（移植 jsrip `_deduplicate_by_content`） |

**输入**：任务 ID（从数据库读 Spider 结果）  
**输出**：JS 文件列表（含 URL、本地路径、大小、内容哈希）

#### `analyzer.py` — 核心分析引擎（移植 jsrip JSAnalyzer）

直接移植 `core/analyzer.py` 的 `JSAnalyzer` 类，修改点：
- 替换 `from .patterns import patterns` 为项目本地 `patterns.py`
- 替换日志输出为项目 `utils.get_logger()`
- 去掉 `jsbeautifier` 依赖（改为可选）
- 输出格式调整为直接返回 Python dict 而非写入文件
- 增加 `source` 字段追踪每个发现的来源

**移植的检测能力**：

| 检测方法 | 移植来源 | 说明 |
|---------|---------|------|
| `find_secrets()` | jsrip `_find_secrets` | 对 JS 内容运行所有 patterns 正则，提取匹配值 |
| `find_sensitive_assignments()` | jsrip `_find_sensitive_assignments` | 检测 const/let/var 中敏感变量名的赋值 |
| `find_config_objects()` | jsrip `_find_config_objects` | 检测对象字面量中的敏感键值对 |
| `find_env_leaks()` | jsrip `_find_env_leaks` | 检测 process.env.xxx 引用和回退值泄漏 |
| `find_dom_storage()` | jsrip `_find_dom_storage` | 检测 localStorage/sessionStorage 敏感键值 |
| `find_endpoints()` | jsrip `_find_endpoints` | 提取 API HTTP 端点 URL |
| `is_false_positive()` | jsrip `_is_false_positive` | 多层误报过滤 |
| `assess_confidence()` | jsrip `_assess_confidence` | Shannon 熵 + 关键词三档置信度 |

**提取的 HTTP 客户端模式**（移植自 jsrip 正则）：

| 模式 | 正则 |
|------|------|
| fetch() | `fetch\(['"]([^'"]+)['"]` |
| axios.get/post/put | `axios\.(get\|post\|put\|delete)\(['"]([^'"]+)['"]` |
| XMLHttpRequest | `xhr\.open\(['"](GET\|POST)['"],\s*['"]([^'"]+)['"]` |
| $.ajax | `\$\.ajax\(\{[^}]*url:\s*['"]([^'"]+)['"]` |
| WebSocket | `new WebSocket\(['"]([^'"]+)['"]` |
| GraphQL | `gql\`...\`` 或 (query\|mutation)\s+\w+ |

**误报过滤层级**（移植自 jsrip）：

| 层级 | 规则 | 说明 |
|------|------|------|
| 1 | 长度检查 | <8 或 >512 字符丢弃 |
| 2 | 占位符模式 | YOUR_API_KEY / CHANGE_ME / TODO / REPLACE_ME 等 |
| 3 | 已知安全值 | content-type / authorization / GET/POST 等 |
| 4 | CSS 颜色 | #xxx / #xxxxxx 格式 |
| 5 | 版本号 | 1.2.3 / v2.0.0 格式 |
| 6 | 压缩变量名 | 单字母或 <=4 字符标识符 |
| 7 | camelCase 标识符 | 看起来像函数名/类名的值 |
| 8 | URL 路径 | `/path/to/file` 格式 |
| 9 | 纯数字 | isdigit() |
| 10 | 重复字符 | set.len <= 2 且长度 >= 8 |
| 11 | 文件路径 | /usr/ /var/ /etc/ ./node_modules/ 等前缀 |
| 12 | JS 表达式 | function() / return / module. 等关键词 |

#### `soucemap.py` — Source Map 检测（移植 getfrontend）

直接移植 getfrontend 的相关算法，简化后作为 Python 类。**不保存全量重建源码**，仅记录发现信息和从中扫描出的敏感内容：

```python
class SourceMapDetector:
    def detect_from_js_content(self, content, js_url):
        """
        三路检测 Source Map:
        1. 正则匹配 sourceMappingURL=xxx.map（URL + inline base64）
        2. 尝试请求 {js_url}.map
        返回 JsSourceMap 对象（含 map_url、是否可访问等）
        """
        ...

    def detect_from_headers(self, headers, js_url):
        """
        从 HTTP 响应头检测 SourceMap / X-SourceMap
        返回 JsSourceMap 对象
        """
        ...

    def extract_sensitive_from_sourcemap(self, map_data):
        """
        解析 .map JSON（version 3），从 sourcesContent 中扫描：
        - 硬编码密钥/Token
        - 原始注释（TODO/内部信息）
        - 原始变量名/API 路径
        - 内部域名
        返回 sensitive_findings 列表
        （不保留全量 sourcesContent）
        """
        ...
```

#### `route_analyzer.py` — SPA 路由分析（自定义）

**支持的框架与匹配模式**：

| 框架 | 匹配模式 |
|------|---------|
| Vue Router | `path:\s*['"]([^'"]+)['"]` + `routes:\s*\[` |
| React Router | `<Route path=['"]([^'"]+)['"]` + `element=` |
| Angular Router | `path:\s*['"]([^'"]+)['"]` + `loadChildren:` |
| 通用 SPA | `router\.push\|navigate\|go\(['"]([^'"]+)['"]` |

**输出**：路由路径列表 + 路由元数据（meta/roles/permissions）+ 业务页面清单

#### `config_extractor.py` — 敏感配置提取（自定义）

| 类型 | 正则 | 示例 |
|------|------|------|
| 多环境地址 | `(prod\|test\|dev\|staging\|internal)URL:\s*['"]https?://` | `prodAPI: "https://api.example.com"` |
| baseURL | `baseURL\|baseUrl:\s*['"]([^'"]+)['"]` | `baseURL: "https://test-api.example.com"` |
| 鉴权白名单 | `whiteList\|noAuth\|publicPath` | `noAuth: ["/api/public", "/health"]` |
| 内部域名 | `\.internal\b\|10\.\|172\.\|192\.168` | `backend: "http://10.0.1.5:8080"` |
| 第三方密钥 | `appId\|client_secret:\s*['"]([^'"]+)['"]` | `wxAppId: "wx1234567890"` |

#### `admin_detector.py` — 管理后台发现（自定义）

**检测策略**：
1. JS 内容中搜索 admin/manage/console/backend/dashboard/ops 等路径字符串
2. 检测权限判断逻辑：`if (user.role === 'admin')` / `user.isAdmin` / `permissions.includes`
3. 检测管理员相关组件引用（AdminPanel / AdminLayout / Dashboard 等）
4. 检测 API 路径中的 admin/manage 前缀

#### `report_generator.py` — 汇总报告生成

聚合一个站点的所有 JS 分析结果，生成 `js_report` 文档。

### 5.3 任务层：集成到 Celery 流水线

#### 新任务函数（`backend/app/tasks/js_analysis.py`）

```python
def js_analysis(sites, task_id):
    """
    对站点列表执行完整的 JS 深度分析（进程内执行，无子进程）
    
    流程：
    1. collector.collect(sites)          -> 收集 JS 文件
    2. analyzer.analyze(js_files)        -> 移植自 jsrip 的核心分析
    3. soucemap.detect(js_files)         -> 移植自 getfrontend 的 Source Map 检测
    4. route_analyzer.analyze(js_files)  -> 自定义 SPA 路由分析
    5. config_extractor.extract(js_files) -> 自定义敏感配置提取
    6. admin_detector.detect(js_files)   -> 自定义管理后台发现
    7. report_generator.generate()       -> 生成汇总报告
    8. 全部结果写入 MongoDB
    """
```

#### 集成到现有任务

**域名任务**（`domain.py`）中新增步骤（复用 Spider 结果，无需 Puppeteer）：
```
Brute -> Resolver -> PortScan -> HTTP probe ->
  WIH -> Fingerprint -> FileLeak -> Spider ->
  JS Analysis (新, 读 Spider 结果中的 JS URL) -> Nuclei -> Screenshot
```

**IP 任务**（`ip.py`）中新增步骤：
```
PortScan -> Service detect -> Cert ->
  Site find -> WIH ->
  JS Analysis (新, 读 siteUrlSpider 结果中的 JS URL) -> Nuclei
```

#### 调度配置

```yaml
JS_ANALYSIS:
  ENABLED: true
  CONCURRENCY: 3              # 并发站点数
  TIMEOUT: 600                # 单个站点超时（秒）
  SOURCEMAP_ENABLED: true     # 是否启用 Source Map 分析
  ROUTE_ANALYSIS: true        # 是否启用路由分析
  ADMIN_DETECT: true          # 是否启用管理后台发现
  MAX_JS_PER_SITE: 50         # 每个站点最多分析的 JS 数
  MAX_JS_SIZE_MB: 5           # 单个 JS 文件大小限制
```

---

## 六、API 设计

### 6.1 新增路由

| 路由 | 方法 | 功能 |
|------|------|------|
| `/api/js_endpoint/` | GET | 查询 API 端点列表 |
| `/api/js_endpoint/` | DELETE | 删除 API 端点记录 |
| `/api/js_sourcemap/` | GET | 查询 Source Map 结果 |
| `/api/js_route/` | GET | 查询前端路由 |
| `/api/js_config/` | GET | 查询敏感配置 |
| `/api/js_report/` | GET | 查询分析报告 |
| `/api/task/{id}/js_report/` | GET | 按任务获取 JS 分析报告 |

### 6.2 API 文件

新建 `backend/app/routes/js_analysis.py`，按项目现有模式（Flask-RESTX）实现。

### 6.3 前端资产搜索新增 Tab

在 `AssetSearch.vue` 中新增 Tab：

| Tab 键 | 显示名 | 数据源 |
|--------|-------|-------|
| js_endpoint | JS 接口 | `/api/js_endpoint/` |
| js_sourcemap | Source Map | `/api/js_sourcemap/` |
| js_config | JS 配置 | `/api/js_config/` |

---

## 七、前端设计

### 7.1 新增页面组件

在 `frontend/src/views/` 下新增 `JsAnalysisReport.vue`，功能：
- JS 文件统计（总数/已分析数）
- API 端点清单（方法标签、路径、来源 JS 文件、可信度）
- Source Map 状态（可访问/不可访问、重建文件列表）
- 前端路由列表
- 敏感配置列表（按环境分组：prod/test/dev/internal）
- 管理后台发现标记
- 安全评估摘要

### 7.2 修改现有页面

**AssetSearch.vue**：在 Tab 列表中追加 3 个新 Tab。

**TaskDetail.vue**：在任务详情中新增 JS 分析结果区块，展示该任务的 JS 分析统计摘要。

### 7.3 搜索字段设计

| Tab | 字段 | 类型 | 选项 |
|-----|------|------|------|
| JS 接口 | 站点 | 输入 | 模糊匹配 |
| | 方法 | 下拉 | GET/POST/PUT/DELETE/PATCH |
| | URI | 输入 | 模糊匹配 |
| | 可信度 | 下拉 | high/medium/low |
| Source Map | 站点 | 输入 | 模糊匹配 |
| | 是否可访问 | 下拉 | true/false |
| JS 配置 | 站点 | 输入 | 模糊匹配 |
| | 配置类型 | 下拉 | env/endpoint/auth/api_key/internal_domain |
| | 环境 | 下拉 | prod/test/dev/internal |

---

## 八、循环收敛架构

### 8.1 背景

ARL-Next 当前的任务模型是**线性扫描**：

```
任务下发 → 域名爆破 → 端口扫描 → HTTP探测 → 指纹识别 → 
  WIH → 文件泄漏 → Spider → JS分析 → Nuclei → 截图 → [结束]
```

一轮跑完即结束。但实战中大量影子资产（如 JS 中发现的内部域名、证书 SAN 字段中的新域名、历史归档中挖掘的 URL）**在第一轮扫描时并不在目标列表中**，而是在扫描过程中才被发现。当前的做法是：发现了也只记录入库，**不会自动回收并展开下一轮扫描**。

### 8.2 设计目标

引入**循环收敛架构**，使单次任务具备"发现→回收→再发现"的自动迭代能力。采用**整轮批处理模式**：每轮完整扫描全部完成后，再进行整体去重和收敛判定，判定通过后才进入下一轮增量扫描。不采用流式触发（即不会在扫描过程中发现一个种子就立即触发下一轮扫描），以确保去重准确性和实现简洁性。

```
                      ┌─────────────────────────────────┐
                      │         第 N 轮增量扫描           │
                      │  (仅新种子: 端口+HTTP+指纹+JS)   │
                      └────────────┬────────────────────┘
                                   │
          ┌────────────────────────┴───────────────────────┐
          │              种子提取 & 去重                    │
          │  JS端点 / 证书SAN / 页面跳转 / Spider结果       │
          └────────────────────────┬───────────────────────┘
                                   │
          ┌────────────────────────┴───────────────────────┐
          │             收敛判定                            │
          │  ① 轮次 ≥ max_rounds?                          │
          │  ② 新增资产占比 < threshold?                   │
          │  ③ 新增资产数量 < min_new?                     │
          └────────────────────────┬───────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │ 未收敛 (①②③均不满足)      │ 已收敛 (任一满足)
                    │ → 送增量队列继续下一轮       │ → 输出结果
                    └──────────────┘              └──────────────┘
```

### 8.3 种子源定义

种子是"可独立作为扫描目标的新资产"。每轮扫描结束后，从以下来源提取种子：

| 种子源 | 提取内容 | 对应模块 |
|--------|---------|---------|
| **JS 端点分析** | JS 中提取的 API URL 中的新域名/新 IP | `js_analysis.analyzer` |
| **JS 内部域名** | JS 中发现的 internal/.dev/.local 域名 | `js_analysis.config_extractor` |
| **证书 SAN 字段** | SSL 证书 Subject Alternative Name 中的域名 | `services.fetchCert` |
| **页面跳转** | HTTP 30x 跳转链中的新 URL | `services.fetchSite` |
| **Spider 结果** | 爬虫发现的新子域名/新路径中的域名 | `services.siteUrlSpider` |
| **DNS 记录** | 新解析出的 A 记录/CNAME 中的 IP/域名 | `services.resolverDomain` |

### 8.4 配置项

新增任务级配置，默认行为与现有完全一致（1 轮=线性扫描）：

```yaml
# 任务策略配置（每个任务独立）
POLICY:
  # 循环收敛配置
  CONVERGENCE:
    ENABLED: false           # 默认关闭，兼容现有行为
    MAX_ROUNDS: 3            # 最大收敛轮次 (1=线性)
    MIN_NEW_ASSETS: 5        # 最小新增资产数，低于此值认为收敛
    NEW_RATIO_THRESHOLD: 0.05  # 新增占比阈值，低于 5% 认为收敛
    SEED_SOURCES:             # 启用的种子源
      - js_endpoint           # JS 中的 API 端点
      - js_internal_domain    # JS 中的内部域名
      - cert_san              # 证书 SAN 字段
      - page_redirect         # 页面跳转
      - spider                # 爬虫结果
      - dns_record            # DNS 新记录
```

前端任务创建界面中新增"循环收敛"开关及参数设置（默认收起）。

### 8.5 核心算法

```python
def run_convergent_task(initial_targets, options):
    """
    循环收敛任务主算法
    
    输入：
        initial_targets: 初始目标列表
        options: 任务配置（含收敛参数）
    
    返回：
        all_assets: 全部已发现资产（去重后）
        rounds_log: 每轮统计日志
    """
    max_rounds = options.get('convergence_max_rounds', 1)
    min_new = options.get('convergence_min_new', 5)
    ratio_threshold = options.get('convergence_ratio', 0.05)
    enabled = options.get('convergence_enabled', False)
    
    # 如果未启用收敛，直接执行单轮线性扫描
    if not enabled or max_rounds <= 1:
        return linear_scan(initial_targets, options)
    
    all_assets = set()        # 全局资产池（所有轮次累计，去重后）
    all_results = {}           # 全部结果（含每轮发现）
    rounds_log = []            # 每轮统计
    
    # 整轮批处理模式：每轮完整跑完 → 整体去重 → 判定收敛 → 再入下一轮
    for round_num in range(1, max_rounds + 1):
        logger.info(f"=== 收敛扫描 第 {round_num}/{max_rounds} 轮 ===")
        
        if round_num == 1:
            # 第 1 轮：对初始目标执行完整扫描
            targets = initial_targets
        else:
            # 第 N 轮：仅对增量新种子执行扫描（整轮去重后才进入）
            targets = new_seeds
            if not targets:
                logger.info("无新增种子，提前收敛")
                break
        
        # 执行本轮完整扫描（端口+HTTP+指纹+JS分析+Spider 等，全部完成才下一步）
        round_results = execute_scan_round(targets, options, round_num)
        
        # [整轮完成后] 将本轮结果合并到全局资产池
        merge_results(all_results, round_results)
        
        # [整轮完成后] 提取本轮新种子并进行整体去重
        new_seeds = extract_seeds_from_results(round_results)
        new_seeds = filter_against_pool(new_seeds, all_assets)
        
        # [整轮完成后] 更新全局资产池
        all_assets.update(round_results.get_all_assets())
        
        # [整轮完成后] 收敛判定
        total_assets = len(all_assets)
        new_count = len(new_seeds)
        new_ratio = new_count / total_assets if total_assets > 0 else 1.0
        
        rounds_log.append({
            'round': round_num,
            'new_assets': new_count,
            'total_assets': total_assets,
            'new_ratio': round(new_ratio, 4),
            'converged': False
        })
        
        logger.info(f"第 {round_num} 轮完成: 新增 {new_count}, 总量 {total_assets}, "
                    f"占比 {new_ratio:.2%}")
        
        # 收敛条件：整轮跑完后，任一条满足即停止循环
        if round_num >= 2:  # 至少跑两轮才判断收敛
            if new_count < min_new:
                logger.info(f"新增资产 {new_count} < {min_new}，判定收敛")
                rounds_log[-1]['converged'] = True
                break
            if new_ratio < ratio_threshold:
                logger.info(f"新增占比 {new_ratio:.2%} < {ratio_threshold:.2%}，判定收敛")
                rounds_log[-1]['converged'] = True
                break
    
    # 去重全局结果，写入数据库
    final_results = deduplicate_all(all_results)
    save_to_database(final_results)
    
    return all_assets, rounds_log
```

### 8.6 增量扫描优化

从第 2 轮起，不需要完整重跑所有扫描步骤，只需要对**新种子执行精简流水线**：

| 步骤 | 第 1 轮（完整） | 第 N 轮（增量） |
|------|---------------|----------------|
| 域名爆破 | ✅ 全量字典 | ❌ 跳过（只有新域名才进入，不需要再爆子域名） |
| DNS 查询插件 | ✅ 11 个数据源 | ❌ 跳过 |
| AltDNS 组合 | ✅ 已有域名排列 | ❌ 跳过 |
| 端口扫描 | ✅ 按配置 | ✅ 只扫新 IP |
| HTTP 存活探测 | ✅ 全量 | ✅ 只扫新站点 |
| 指纹识别 | ✅ 全量 | ✅ 只扫新站点 |
| WIH / JS 分析 | ✅ 全量 | ✅ 只扫新站点（JS 分析是新种子的关键来源） |
| 文件泄漏 | ✅ 全量 | ✅ 只扫新站点 |
| Spider 爬虫 | ✅ 全量 | ⚠️ 有限爬取（新域名首页 + JS 提取） |
| Nuclei 扫描 | ✅ 全量 | ✅ 只扫新站点 |
| 种子提取 | ✅ 所有渠道 | ✅ 所有渠道（可能再诞生下一代种子） |

### 8.7 与 JS 分析的关系

JS 深度分析是循环收敛架构中**最重要的种子源**之一：

- **第 1 轮** JS 分析可能发现：`api.internal.target.com`、`test-admin.target.com`、`https://10.0.1.5:8080`
- 这些新域名/IP 不在初始目标列表中，被提取为种子
- **第 2 轮**增量扫描这些新种子，又会从这些新站点的 JS 中发现更多资产
- 这就形成了"种子→展开→新种子→再展开"的迭代效应

### 8.8 前端配置

任务创建界面新增配置区域（默认收起）：

```
□ 启用循环收敛 (默认关闭)
  最大轮次: [3]       (1-10)
  最小新增数: [5]     (1-1000)
  新增占比阈值: [5%]  (1-50%)
  
  种子源:
  ☑ JS 端点分析
  ☑ JS 内部域名
  ☑ 证书 SAN 字段
  ☑ 页面跳转
  ☑ 爬虫结果
```

---

## 九、实施路线图

### Phase 1 — 基础设施（2-3天）

| 步骤 | 文件 | 说明 |
|------|------|------|
| 1.1 | `modules/jsAnalysis.py` | 新建数据模型 (JsEndpoint/JsSourceMap/JsRoute/JsConfigItem/JsReport)，Source Map 模型**不保存全量源码** |
| 1.2 | `services/js_analysis/patterns.py` | 移植 jsrip 的核心正则 + 自定义匹配模式 |
| 1.3 | 配置项 | config.yaml 新增 JS_ANALYSIS 配置段 |
| 1.4 | `services/js_analysis/collector.py` | JS 文件收集器，**复用 Spider 结果** + 移植 getfrontend chunk 发现算法，**不需要扩展 Puppeteer** |

### Phase 2 — JS 收集 + 核心分析引擎移植（3-4天）

| 步骤 | 文件 | 说明 |
|------|------|------|
| 2.1 | `services/js_analysis/collector.py` | JS 文件收集器 |
| 2.2 | `services/js_analysis/analyzer.py` | **移植 jsrip JSAnalyzer 核心类**：find_secrets / find_endpoints / find_sensitive_assignments / find_config_objects / find_env_leaks / find_dom_storage + is_false_positive + assess_confidence |
| 2.3 | `services/js_analysis/__init__.py` | 统一入口 |

### Phase 3 — Source Map + 自定义分析器（3-4天）

| 步骤 | 文件 | 说明 |
|------|------|------|
| 3.1 | `services/js_analysis/soucemap.py` | **移植 getfrontend** Source Map 发现 + 解析算法 |
| 3.2 | `services/js_analysis/route_analyzer.py` | SPA 路由分析器（Vue/React/Angular 框架匹配） |
| 3.3 | `services/js_analysis/config_extractor.py` | 多环境地址/密钥配置提取 |
| 3.4 | `services/js_analysis/admin_detector.py` | 管理后台路径 + 权限字段检测 |
| 3.5 | `services/js_analysis/report_generator.py` | 汇总报告生成器 |

### Phase 4 — 循环收敛架构（2-3天）

| 步骤 | 文件 | 说明 |
|------|------|------|
| 4.1 | `services/convergence.py` | 循环收敛控制器：种子提取(JS端点/证书SAN/跳转/Spider)、去重比对、收敛判定算法 |
| 4.2 | `config.yaml.example` + `config.py` | 新增 `CONVERGENCE` 配置段和加载逻辑 |
| 4.3 | `tasks/domain.py` | 重构任务入口：支持 `max_rounds` 循环，第1轮全量/第N轮增量 |
| 4.4 | `tasks/ip.py` | 重构任务入口：同上 |
| 4.5 | `services/commonTask.py` | 增加种子提取和收敛判定的通用基类方法 |
| 4.6 | `frontend/TaskList.vue` | 任务创建界面增加"循环收敛"折叠面板 |
| 4.7 | `frontend/TaskDetail.vue` | 任务详情增加收敛轮次日志展示 |

### Phase 5 — API + 前端（3-4天）

| 步骤 | 文件 | 说明 |
|------|------|------|
| 5.1 | `tasks/js_analysis.py` | JS 分析 Celery 任务 |
| 5.2 | `routes/js_analysis.py` | 新增 5 个 REST API |
| 5.3 | `routes/__init__.py` | 注册新路由 |
| 5.4 | `AssetSearch.vue` | 新增 3 个 Tab |
| 5.5 | `JsAnalysisReport.vue` | 新建分析报告页 |
| 5.6 | `TaskDetail.vue` | 扩展 JS 分析摘要 |

---

## 十、工程文件变更清单

### 新增文件（14个）

| 文件路径 | 说明 | 源码参考 |
|---------|------|---------|
| `backend/app/modules/jsAnalysis.py` | JS 分析数据模型 | — |
| `backend/app/services/convergence.py` | **循环收敛控制器**：种子提取/去重/收敛判定 | 自定义，核心新架构 |
| `backend/app/services/js_analysis/__init__.py` | 统一入口 | — |
| `backend/app/services/js_analysis/collector.py` | JS 文件收集器，**复用 Spider 结果** + chunk 发现，**无需 Puppeteer** | — |
| `backend/app/services/js_analysis/analyzer.py` | **核心分析引擎** | **移植 jsrip `core/analyzer.py` JSAnalyzer 类** |
| `backend/app/services/js_analysis/patterns.py` | 匹配模式库 | **移植 jsrip 核心正则 + 自定义模式** |
| `backend/app/services/js_analysis/soucemap.py` | Source Map 检测器。**不保存全量源码**，仅记录发现信息和敏感内容 | **移植 getfrontend 三路检测算法** |
| `backend/app/services/js_analysis/route_analyzer.py` | SPA 路由分析器 | 自定义 |
| `backend/app/services/js_analysis/config_extractor.py` | 敏感配置提取器 | 自定义 |
| `backend/app/services/js_analysis/admin_detector.py` | 管理后台发现器 | 自定义 |
| `backend/app/services/js_analysis/report_generator.py` | 汇总报告生成器 | 自定义 |
| `backend/app/tasks/js_analysis.py` | JS 分析 Celery 任务 | — |
| `backend/app/routes/js_analysis.py` | JS 分析 API 路由 | — |
| `frontend/src/views/JsAnalysisReport.vue` | JS 分析报告页 | — |

### 修改文件（9个）

| 文件路径 | 变更内容 |
|---------|---------|
| `backend/app/config.yaml.example` | 新增 `JS_ANALYSIS` + `CONVERGENCE` 配置段 |
| `backend/app/config.py` | 加载 JS_ANALYSIS + CONVERGENCE 配置 |
| `backend/app/routes/__init__.py` | 注册新路由 |
| `backend/app/tasks/domain.py` | 重构为**循环收敛模式**，每轮结束后提取种子并判断是否下一轮 |
| `backend/app/tasks/ip.py` | 重构为**循环收敛模式** |
| `backend/app/services/commonTask.py` | 增加种子提取和收敛判断通用方法 |
| `frontend/src/views/TaskList.vue` | 新建任务界面增加"循环收敛"配置区域 |
| `frontend/src/views/AssetSearch.vue` | 新增 3 个 Tab |
| `frontend/src/views/TaskDetail.vue` | 增加 JS 分析摘要 + 收敛轮次日志

### 零新增 Python 依赖

jsrip 的 `JSAnalyzer` 仅使用 `re`, `math`, `hashlib`, `os`, `json`, `collections` 等标准库。  
getfrontend 的 Source Map 检测逻辑使用 `requests`（项目已有）+ `re`, `json`, `base64`（标准库）。  
**项目不需要安装任何新的 pip 包。**

---

## 十一、测试计划

### 单元测试

| 测试目标 | 测试内容 | 测试数据 |
|---------|---------|---------|
| `analyzer.find_endpoints()` | 从模拟 JS 中提取 fetch/axios/XHR 端点的准确性 | 含 5 种 HTTP 调用的模拟 JS 片段 |
| `analyzer.find_secrets()` | 正则匹配密钥（AK/SK/Token 等） | 含各种密钥格式的模拟 JS |
| `analyzer.find_sensitive_assignments()` | 检测敏感变量赋值 | const apiKey = "xxx" 模式 |
| `analyzer.find_env_leaks()` | 检测 process.env 泄漏 | process.env 引用 + 回退值 |
| `analyzer.is_false_positive()` | 误报过滤各层级有效性 | 12 种误报场景分别测试 |
| `soucemap.detect()` | Source Map 三路检测 | 含 sourceMappingURL 的模拟 JS |
| `route_analyzer.analyze()` | Vue/React 路由提取 | Vue/React 路由配置片段 |
| `config_extractor.extract()` | 多环境地址/密钥配置提取 | 含 baseURL/env 配置的模拟 JS |
| `admin_detector.detect()` | admin 路径和权限字段检测 | 含 admin 路由/权限判断的模拟 JS |
| `modules/jsAnalysis.py` | 数据模型序列化/反序列化 | 各模型构造和 JSON 输出 |

### 测试代码示例

```python
# test_analyzer.py — 移植自 jsrip 的核心测试逻辑

SAMPLE_JS_WITH_ENDPOINTS = """
const api = axios.create({baseURL: 'https://api.example.com'});
api.get('/v1/user/list').then(res => {});
api.post('/v1/order/create', {name: 'test'});
fetch('https://admin.example.com/manage/user/delete/123', {method: 'DELETE'});
const ws = new WebSocket('wss://ws.example.com/socket');
"""

def test_find_endpoints():
    """验证 API 端点提取器能正确识别多种 HTTP 客户端调用"""
    analyzer = JsAnalyzer()
    results = analyzer.find_endpoints(SAMPLE_JS_WITH_ENDPOINTS)
    assert len(results) >= 4
    # 检查 axios GET
    assert any(r['method'] == 'GET' and '/v1/user/list' in r['path'] for r in results)
    # 检查 axios POST
    assert any(r['method'] == 'POST' and '/v1/order/create' in r['path'] for r in results)
    # 检查 fetch DELETE
    assert any(r['method'] == 'DELETE' for r in results)
    # 检查 WebSocket
    assert any('ws.example.com' in r['url'] for r in results)


SAMPLE_JS_WITH_SECRETS = """
const apiKey = 'sk-1234567890abcdef1234567890abcdef';
const config = {
    secretKey: 'my-secret-key-12345',
    databaseUrl: 'postgresql://user:password@localhost:5432/db'
};
const token = localStorage.getItem('auth_token');
"""

def test_find_secrets():
    """验证密钥检测能发现硬编码的 API Key 和 Secret"""
    analyzer = JsAnalyzer()
    secrets = analyzer.find_secrets(SAMPLE_JS_WITH_SECRETS)
    assert len(secrets) > 0
    # 应发现 apiKey 赋值
    assert any('apiKey' in s['context'] and 'sk-' in s['value'] for s in secrets)


SAMPLE_JS_WITH_SOURCEMAP = """
//# sourceMappingURL=/js/app.js.map
console.log('hello');
"""

def test_sourcemap_detection():
    """验证 Source Map 检测能正确识别 sourceMappingURL"""
    detector = SourceMapDetector()
    result = detector.detect_from_content(
        SAMPLE_JS_WITH_SOURCEMAP,
        js_url="https://example.com/js/app.js"
    )
    assert result is not None
    assert result.map_url == "https://example.com/js/app.js.map"
```

---

## 十二、安全注意事项

1. **文件大小限制**：单个 JS 文件分析限制 5MB，防止 OOM
2. **超时控制**：每个站点 JS 分析总超时 600 秒，防止 Celery Worker 阻塞
3. **进程内安全**：所有分析代码在 Worker 进程内执行，无子进程注入风险
4. **去重机制**：所有提取结果使用 FNV 哈希 + SHA256 内容哈希双重去重
5. **临时文件清理**：下载的 JS 文件和重建源码在任务完成后自动清理
6. **Source Map 请求限制**：对 .map 请求设置频率限制，避免被目标封 IP

---

## 十三、扩展性设计

### MCP 集成

JS 分析结果可通过已有的 MCP Server 暴露，支持 AI Agent 查询：

```json
{
  "name": "js_analyze_site",
  "description": "对指定站点执行 JS 深度分析，返回 API 端点、路由等",
  "parameters": { "url": "string", "depth": "string" }
}
```

### 后续增强方向

- **anastasis MCP Server**：作为独立补充，提供更深层的 AST 级别分析
- **AI 辅助分析**：使用 LLM 对混淆 JS 进行语义理解
- **定时重分析**：对资产定期重新执行 JS 分析，检测新增/变更的端点
- **动态分析**：通过 Puppeteer 点击/滚动触发懒加载 JS 后分析

---

## 十四、参考资源

### 源码参考来源

| 工具 | 用途 | 仓库 | 核心提取文件 |
|------|------|------|------------|
| **jsrip** | 密钥检测 + API端点提取 + 误报过滤 | https://github.com/mouteee/jsrip | `core/analyzer.py`（786行） |
| **getfrontend** | Source Map 发现 + webpack/vite/Next.js chunk 解析 | https://github.com/zb3/getfrontend | `getfrontend.py`（~1200行） |

### 项目现有相关代码参考

| 路径 | 说明 |
|------|------|
| `backend/app/services/infoHunter.py` | 现有 WIH 服务 (JS 密钥提取 Go 二进制) |
| `backend/app/dicts/wih_rules.yml` | WIH 匹配规则配置 |
| `backend/app/services/webAnalyze.py` | Puppeteer 分析服务 |
| `backend/app/services/siteUrlSpider.py` | URL 爬虫服务 |
| `backend/app/tasks/domain.py` | 域名任务流水线（参考集成位置） |
| `backend/app/routes/assetWih.py` | WIH 数据路由（参考 API 模式） |
| `frontend/src/views/AssetSearch.vue` | 资产搜索页（参考 Tab 模式） |
