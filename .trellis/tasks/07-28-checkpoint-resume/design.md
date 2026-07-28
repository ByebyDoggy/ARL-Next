# Checkpoint/Resume 设计

## 目标

ARL 域名资产发现任务支持步骤级 checkpoint，停止后可 resume 续跑。

## 核心改动

### 1. Task 文档新增 checkpoint 字段

```python
checkpoint = {
    "completed_steps": ["domain_brute", "dns_query_plugin", ...],  # 已完成步骤
    "current_round": 1,                # 当前轮次
    "round_seeds": ["ninebot.com"],     # 本轮目标种子
    "original_target": "ninebot.com",   # 原始目标（不变）
    "converged": False,                 # 是否已收敛
}
```

### 2. DomainTask 改造

```
run():
  for round_num in 1..max_rounds:
    domain_fetch()
    search_engines()
    start_ip_fetch()
    start_site_fetch()
    start_find_vhost()
    start_poc_run()
    start_wih_domain_update()
    JS analysis
    收敛判定
```

每个步骤改为：
```python
if "domain_brute" not in self.completed_steps:
    self.domain_brute()
    self.checkpoint("domain_brute")
```

### 3. Resume API

```
POST /api/task/resume/<task_id>
  → 检查 task.status == "stop"
  → 读取 checkpoint 字段
  → 新建 celery 任务
  → 设置 status = "resumed"
  → DomainTask 从 checkpoint 恢复中间状态
```

### 4. 中间状态重建

| 对象 | 重建来源 |
|------|---------|
| domain_info_list | domain 集合 `task_id` 查询 |
| ip_info_list | ip + service 集合 |
| cert_map | cert 集合 |
| site_list | site 集合 |
| ipv4_map | domain 集合 A 记录 |
| cc._all_known | domain 集合（去重） |

## 涉及文件

- `backend/app/routes/task.py` — 新增 resume 路由
- `backend/app/tasks/domain.py` — 步骤 checkpoint 和 resume 逻辑
- `backend/app/modules/__init__.py` — 新增状态常量
- `backend/app/celerytask.py` — 注册 resume_task
