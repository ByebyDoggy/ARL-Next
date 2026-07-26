"""
JS 深度静态分析 — 数据模型

对应文章第四章（二级业务目录）、第五章（前端反推后端）、第六章（影子资产）、第十一章（C端→B端串联）

所有模型类不继承 BaseInfo，参照 WihRecord 模式：
自包含类，dump_json() 返回 dict，__eq__/__hash__ 基于 fnv_hash 去重。
"""
import hashlib


def _fnv_hash(content):
    """生成去重哈希，参照 WihRecord 的 fnv_hash 模式"""
    raw = hashlib.md5(content.encode("utf-8")).hexdigest()
    return int(raw[:12], 16)


class JsEndpoint:
    """从 JS 中提取的 API 端点"""
    def __init__(self, task_id, site, js_url, method, url, path,
                 params=None, source=None, framework=None, confidence="medium"):
        self.task_id = task_id
        self.site = site
        self.js_url = js_url
        self.method = method.upper()
        self.url = url
        self.path = path
        self.params = params or []
        self.source = source or "unknown"
        self.framework = framework or ""
        self.confidence = confidence
        content_hash = "{}{}{}{}".format(task_id, url, method, js_url)
        self.fnv_hash = _fnv_hash(content_hash)

    def __eq__(self, other):
        if not isinstance(other, JsEndpoint):
            return False
        return self.fnv_hash == other.fnv_hash

    def __hash__(self):
        return self.fnv_hash

    def dump_json(self):
        return {
            "task_id": self.task_id,
            "site": self.site,
            "js_url": self.js_url,
            "method": self.method,
            "url": self.url,
            "path": self.path,
            "params": self.params,
            "source": self.source,
            "framework": self.framework,
            "confidence": self.confidence,
            "fnv_hash": str(self.fnv_hash),
        }


class JsSourceMap:
    """Source Map 检测结果。不保存全量重建源码，仅记录发现信息和从中提取的敏感内容"""
    def __init__(self, task_id, site, js_url, map_url, accessible=False,
                 detection_method=None, sensitive_findings=None):
        self.task_id = task_id
        self.site = site
        self.js_url = js_url
        self.map_url = map_url
        self.accessible = accessible
        self.detection_method = detection_method or "unknown"
        self.sensitive_findings = sensitive_findings or []
        content_hash = "{}{}{}".format(task_id, map_url, js_url)
        self.fnv_hash = _fnv_hash(content_hash)

    def __eq__(self, other):
        if not isinstance(other, JsSourceMap):
            return False
        return self.fnv_hash == other.fnv_hash

    def __hash__(self):
        return self.fnv_hash

    def dump_json(self):
        return {
            "task_id": self.task_id,
            "site": self.site,
            "js_url": self.js_url,
            "map_url": self.map_url,
            "map_accessible": self.accessible,
            "detection_method": self.detection_method,
            "sensitive_findings": self.sensitive_findings,
            "fnv_hash": str(self.fnv_hash),
        }


class JsRoute:
    """从 SPA 前端路由表中提取的业务页面路径"""
    def __init__(self, task_id, site, js_url, framework, routes=None):
        self.task_id = task_id
        self.site = site
        self.js_url = js_url
        self.framework = framework or ""
        self.routes = routes or []
        content_hash = "{}{}{}".format(task_id, js_url, framework)
        self.fnv_hash = _fnv_hash(content_hash)

    def __eq__(self, other):
        if not isinstance(other, JsRoute):
            return False
        return self.fnv_hash == other.fnv_hash

    def __hash__(self):
        return self.fnv_hash

    def dump_json(self):
        return {
            "task_id": self.task_id,
            "site": self.site,
            "js_url": self.js_url,
            "framework": self.framework,
            "routes": self.routes,
            "fnv_hash": str(self.fnv_hash),
        }


class JsConfigItem:
    """JS 中提取的敏感配置信息"""
    def __init__(self, task_id, site, js_url, config_type, key, value,
                 environment="unknown", source="pattern"):
        self.task_id = task_id
        self.site = site
        self.js_url = js_url
        self.config_type = config_type
        self.key = key
        self.value = value
        self.environment = environment
        self.source = source
        content_hash = "{}{}{}{}".format(task_id, config_type, key, value)
        self.fnv_hash = _fnv_hash(content_hash)

    def __eq__(self, other):
        if not isinstance(other, JsConfigItem):
            return False
        return self.fnv_hash == other.fnv_hash

    def __hash__(self):
        return self.fnv_hash

    def dump_json(self):
        return {
            "task_id": self.task_id,
            "site": self.site,
            "js_url": self.js_url,
            "config_type": self.config_type,
            "key": self.key,
            "value": self.value,
            "environment": self.environment,
            "source": self.source,
            "fnv_hash": str(self.fnv_hash),
        }


class JsReport:
    """JS 分析汇总报告（每个站点一份）"""
    def __init__(self, task_id, site, js_files_found=0, js_files_analyzed=0,
                 sourcemap_found=False, sourcemap_count=0, api_endpoints=0,
                 routes_found=0, config_items=0, internal_domains=None,
                 admin_panels=None, framework="", assessment=""):
        self.task_id = task_id
        self.site = site
        self.js_files_found = js_files_found
        self.js_files_analyzed = js_files_analyzed
        self.sourcemap_found = sourcemap_found
        self.sourcemap_count = sourcemap_count
        self.api_endpoints = api_endpoints
        self.routes_found = routes_found
        self.config_items = config_items
        self.internal_domains = internal_domains or []
        self.admin_panels = admin_panels or []
        self.framework = framework
        self.assessment = assessment

    def dump_json(self):
        return {
            "task_id": self.task_id,
            "site": self.site,
            "js_files_found": self.js_files_found,
            "js_files_analyzed": self.js_files_analyzed,
            "sourcemap_found": self.sourcemap_found,
            "sourcemap_count": self.sourcemap_count,
            "api_endpoints": self.api_endpoints,
            "routes_found": self.routes_found,
            "config_items": self.config_items,
            "internal_domains": self.internal_domains,
            "admin_panels": self.admin_panels,
            "framework": self.framework,
            "assessment": self.assessment,
        }
