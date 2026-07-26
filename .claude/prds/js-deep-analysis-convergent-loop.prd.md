# JS 深度静态分析与循环收敛架构

## Problem

ARL-Next 当前采用一次性线性扫描模型：任务下发后执行单轮资产发现流水线，跑完即结束。然而实战中大量影子资产（JS 中的内部域名、证书 SAN 字段中的新域名、跳转链中的隐藏入口等）在第一轮扫描时并不在目标列表中，而是在扫描过程中才被发现。当前的做法是发现了也只记录入库，不会自动回收并展开下一轮扫描，导致单次任务的资产覆盖率远低于理论上可达的范围。

此外，现有 JS 分析能力仅依赖 WIH 做密钥正则匹配（身份证/手机号/AK/SK），缺乏对 API 端点、前端路由、多环境配置、管理后台路径等关键攻击面的提取能力，大量高价值暴露面被遗漏。

成本：安全研究人员需要手动将第一轮发现的新资产整理后再发起第二轮扫描，效率低、易遗漏、无法规模化。

## Evidence

- **实战案例**：用户在实际 SRC/攻防场景中遇到过"一轮扫描后 JS 中发现新资产但需要手动整理再发起第二轮"的情况
- **方法论支撑**：《怎么做好资产信息收集》系统化论述了"种子展开成网"的方法论，三件套之后的核心在于 JS 分析和循环收敛
- **工具验证**：jsrip（Python，786 行核心分析类）和 getfrontend（Python，~1200 行 Source Map 引擎）等成熟工具已验证这些技术可行，可直接移植核心算法
- **架构空白**：ARL-Next 当前任务流水线（domain.py / ip.py）是线性执行，无循环回收机制，这是已知的设计上的局限

## Users

- **Primary**：使用 ARL-Next 做资产侦察的安全研究人员、红队成员、SRC 漏洞挖掘者。他们的工作流是"下发任务 → 分析结果 → 发现新线索 → 再扫"，当前需要手动完成最后两步。
- **Secondary**：企业安全团队使用资产监控功能的管理员，循环收敛能提升监控任务对新增资产的发现率。
- **Not for**：只需一次性简单资产枚举（如查单个域名的子域名列表）的用户，他们不需要收敛循环的开销。

## Hypothesis

We believe **JS 深度静态分析 + 循环收敛架构** 将会 **提升单次任务的资产覆盖率和攻击面展开深度** 为 **ARL-Next 的安全研究人员用户**。

We'll know we're right when **启用收敛的任务比同等配置的线性任务多发现 50% 以上的有效资产（域名/IP/站点），且分析 JS 带来的 API 端点/路由/配置发现量是现有 WIH 的 3 倍以上**。

## Success Metrics

| Metric | Target | How measured |
|--------|--------|-------------|
| 单任务资产发现量增幅 | +50% | 对比同目标启用/未启用收敛的结果差异 |
| API 端点提取数 | ≥100/千站点 | `js_endpoint` 集合统计 |
| Source Map 检测覆盖率 | ≥30% 站点 | `js_sourcemap` 中 `map_accessible=true` 的占比 |
| 误报率 | ≤15% | 采样抽查 `js_endpoint` 中 `confidence=high` 条目的有效性 |
| 前端路由/配置发现 | ≥10条/百站点 | `js_route` / `js_config` 统计 |
| 向后兼容 | 无回归 | 未启用收敛的任务行为与之前完全一致 |

## Scope

**MVP** — 以下三项同时交付：

1. **JS 深度静态分析模块**
   - API 端点提取（从 fetch/axios/XHR/WebSocket/GraphQL 中提取 URL、方法、参数）
   - Source Map 检测（响应头 / `sourceMappingURL` / `.map` 追加，三路检测）
   - SPA 路由提取（Vue Router / React Router / Angular Router）
   - 敏感配置提取（多环境地址、baseURL、鉴权白名单、内部域名、第三方密钥）
   - 管理后台发现（admin 路径、权限字段、管理组件引用）
   - **不保存 Source Map 全量重建源码，仅记录 map_url 和从中提取的敏感内容**

2. **循环收敛架构**
   - 整轮批处理模式：每轮完整跑完 → 整体去重 → 判定收敛 → 再入下一轮
   - 种子源：JS 端点 / JS 内部域名 / 证书 SAN / 页面跳转 / Spider 结果 / DNS 记录
   - 收敛判定：轮次上限 + 最小新增数 + 新增占比，三者任一满足即停止
   - **默认关闭**，与现有行为完全兼容

3. **前端展示**
   - AssetSearch 新增 3 个 Tab：JS 接口 / Source Map / JS 配置
   - JsAnalysisReport.vue 分析报告页
   - TaskList.vue 新建任务增加"循环收敛"配置面板
   - TaskDetail.vue 增加 JS 分析摘要和收敛轮次日志

**Out of scope**

| 排除项 | 原因 |
|--------|------|
| 历史 URL 溯源（Wayback Machine） | 独立数据收集能力，后续再评估 |
| Bucket 对象存储检测 | 独立功能，非 JS 分析范畴 |
| Puppeteer JS 收集扩展 | 复用 Spider 结果 + getfrontend chunk 发现即可覆盖 |
| 流式收敛模式 | 复杂度高且收益不明确，整轮批处理已满足需求 |
| AI 辅助 JS 分析 | 当前阶段纯正则+规则已足够 |
| 全端口 0-65535 扫描 | 已有 `port_all.txt` 但不在本次范围内 |

## Delivery Milestones

| # | Milestone | Outcome | Status | Plan |
|---|-----------|---------|--------|------|
| 1 | 基础设施 | 数据模型 + 配置 + 匹配模式库就绪 | pending | — |
| 2 | JS 分析引擎 | 完整的 API 端点 / Source Map / 路由 / 配置 / 后台发现能力 | pending | — |
| 3 | 循环收敛 | 任务支持多轮批处理收敛，默认关闭 | pending | — |
| 4 | API + 前端 | 搜索结果 Tab + 分析报告页 + 任务配置界面 | pending | — |

## Open Questions

- [ ] 50% 资产发现量增幅的验证方式：是否需要在实施后用同一批目标跑对比测试？
- [ ] `js_config` 中发现的内部域名是自动作为新资产入库，还是只标记展示？需要明确流程
- [ ] 收敛循环的最大轮次默认值定为 3 轮是否合理？还是应该更保守（2 轮）？

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| JS 分析拖慢任务完成时间 | 中 | 中 | 设超时 600 秒/站点 + 默认关闭收敛；用户按需开启 |
| Source Map 下载触发目标告警 | 低 | 低 | 复用项目已有的代理配置和速率控制 |
| getfrontend chunk 发现算法误判 | 低 | 低 | 结果经 `js_endpoint` 置信度过滤后展示 |
| 循环收敛导致任务卡在无限循环 | 低 | 高 | 硬上限 max_rounds=10 + 每轮超时兜底 |
| 新增 MongoDB 集合增加存储 | 低 | 低 | `fnv_hash` 去重 + 临时文件自动清理 |

---
*Status: DRAFT — requirements only. Implementation planning pending via /plan.*
