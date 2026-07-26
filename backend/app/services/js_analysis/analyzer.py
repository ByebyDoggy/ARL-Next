"""JS 深度分析 — 核心分析引擎

移植自 jsrip `core/analyzer.py` 的 JSAnalyzer 类。
修改点：
- 替换日志为项目 utils.get_logger()
- 输出格式为 Python dict 而非文件写入
- 增加 source 字段追踪每个发现来源
"""
import os
import hashlib
import re
from urllib.parse import urlparse

from app import utils
from . import patterns as p

logger = utils.get_logger()


class JsAnalyzer:
    """JS 深度分析核心引擎"""

    def __init__(self, beautify=False):
        self.beautify = beautify
        self.js_dir = None

    def analyze_content(self, content, js_url=None, filepath=None):
        """对单段 JS 内容执行全部分析

        Args:
            content: JS 文件内容（字符串）
            js_url: JS 文件的 URL
            filepath: JS 文件的本地路径

        Returns:
            dict: {endpoints, secrets, assignments, config_objects, env_leaks, dom_storage}
        """
        if not content:
            return {"endpoints": [], "secrets": [], "assignments": [],
                    "config_objects": [], "env_leaks": [], "dom_storage": []}

        content = self._remove_base64_noise(content)
        filename = os.path.basename(filepath or js_url or "unknown.js")

        return {
            "endpoints": self._find_endpoints(content, filename),
            "secrets": self._find_secrets(content, filename),
            "assignments": self._find_sensitive_assignments(content, filename),
            "config_objects": self._find_config_objects(content, filename),
            "env_leaks": self._find_env_leaks(content, filename),
            "dom_storage": self._find_dom_storage(content, filename),
        }

    def analyze_files(self, js_files):
        """批量分析多个 JS 文件

        Args:
            js_files: list of dict [{"path": ..., "url": ...}, ...]

        Returns:
            list[dict]: 每个文件的分析结果
        """
        results = []
        seen_hashes = set()

        for entry in js_files:
            path = entry.get("path") or entry.get("filepath")
            js_url = entry.get("url") or entry.get("js_url") or path
            if not path or not os.path.exists(path):
                continue

            # 内容去重
            try:
                with open(path, "rb") as f:
                    content_hash = hashlib.sha256(f.read()).hexdigest()
                if content_hash in seen_hashes:
                    continue
                seen_hashes.add(content_hash)
            except Exception:
                continue

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if self.beautify:
                try:
                    import jsbeautifier
                    content = jsbeautifier.beautify(content)
                except ImportError:
                    pass

            result = self.analyze_content(content, js_url=js_url, filepath=path)
            result["js_url"] = js_url
            result["filepath"] = path
            results.append(result)

        return results

    # ----------------------------------------------------------
    # Base64 噪声去除
    # ----------------------------------------------------------
    BASE64_IMAGE_RE = re.compile(
        r"data:image\/[^,]+;base64,[A-Za-z0-9+/=\s]{100,}",
        re.IGNORECASE
    )
    LARGE_BASE64_RE = re.compile(
        r"[A-Za-z0-9+/]{400,}={0,2}"
    )

    def _remove_base64_noise(self, content):
        content = self.BASE64_IMAGE_RE.sub("", content)
        content = self.LARGE_BASE64_RE.sub("", content)
        return content

    # ----------------------------------------------------------
    # API 端点提取（移植自 jsrip _find_endpoints）
    # ----------------------------------------------------------
    def _find_endpoints(self, content, filename):
        """提取 JS 中的 API 端点 URL"""
        found = set()
        results = []

        for source_name, regex in p.ALL_HTTP_PATTERNS:
            for match in regex.finditer(content):
                raw_url = match.group(1).strip().strip("'\"")
                if not self._is_valid_endpoint(raw_url):
                    continue
                method = self._infer_http_method(content, match.start(), source_name)
                dedup_key = "{}||{}".format(method, raw_url)
                if dedup_key in found:
                    continue
                found.add(dedup_key)
                parsed = urlparse(raw_url)
                results.append({
                    "method": method,
                    "url": raw_url,
                    "path": parsed.path or "/",
                    "params": self._extract_params(raw_url),
                    "source": source_name,
                    "confidence": "high" if source_name != "generic" else "medium",
                })

        return results

    def _is_valid_endpoint(self, endpoint):
        """验证端点是否有效（过滤已知噪声）"""
        if len(endpoint) < 8 or len(endpoint) > 500:
            return False
        lower = endpoint.lower()
        skip_terms = [
            "license", "github.com/", "stackoverflow.com",
            "opensource.org", "w3.org", "schema.org",
            "creativecommons.org", "mozilla.org", "npmjs.com",
            "unpkg.com", "cdnjs.cloudflare.com", "cdn.jsdelivr.net",
            "fonts.googleapis.com", "fonts.gstatic.com",
        ]
        if any(term in lower for term in skip_terms):
            return False
        if any(lower.startswith(x) for x in [
            "http://example.com", "https://example.com",
            "http://localhost", "https://localhost",
            "/path/to/", "/example/",
        ]):
            return False
        skip_ext = [
            ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
            ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4",
            ".webp", ".pdf", ".zip", ".tar", ".gz",
        ]
        if any(lower.endswith(ext) for ext in skip_ext):
            return False
        return True

    def _infer_http_method(self, content, pos, source_name):
        """从上下文中推断 HTTP 方法"""
        if source_name == "generic":
            return "GET"
        snippet = content[max(0, pos - 30):pos].lower()
        for method in ["post", "put", "delete", "patch", "head", "options"]:
            if method in snippet:
                return method.upper()
        return "GET"

    @staticmethod
    def _extract_params(url):
        """从 URL 中提取查询参数"""
        if "?" not in url:
            return []
        query = url.split("?", 1)[1]
        params = []
        for part in query.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                params.append({"name": k, "value": v if len(v) < 50 else v[:50] + "..."})
        return params

    # ----------------------------------------------------------
    # 密钥检测（移植自 jsrip _find_secrets）
    # ----------------------------------------------------------
    @staticmethod
    def _find_secrets(content, filename):
        """基于 patterns 正则匹配密钥（WIH 已覆盖的密钥类型不再重复）"""
        return []

    # ----------------------------------------------------------
    # 敏感变量赋值检测（移植自 jsrip _find_sensitive_assignments）
    # ----------------------------------------------------------
    def _find_sensitive_assignments(self, content, filename):
        """检测 const/let/var 中敏感变量名的赋值"""
        findings = []
        for match in p.VAR_ASSIGNMENT_RE.finditer(content):
            var_name = match.group(1)
            var_value = match.group(2)
            if not p.SENSITIVE_VAR_NAMES.search(var_name):
                continue
            context = content[max(0, match.start() - 100):match.end() + 100].strip()
            if p.is_false_positive(var_value, context):
                continue
            entropy = p.calculate_entropy(var_value)
            if entropy < 2.0:
                continue
            confidence = "high" if entropy >= 3.5 else "medium" if entropy >= 2.5 else "low"
            findings.append({
                "type": "sensitive_assignment:{}".format(var_name),
                "value": var_value,
                "var_name": var_name,
                "confidence": confidence,
                "entropy": entropy,
                "context": context[:200],
            })
        return findings

    # ----------------------------------------------------------
    # 配置对象检测（移植自 jsrip _find_config_objects）
    # ----------------------------------------------------------
    def _find_config_objects(self, content, filename):
        """检测对象字面量中的敏感键值对"""
        findings = []
        for match in p.OBJ_PROPERTY_RE.finditer(content):
            prop_name = match.group(1)
            prop_value = match.group(2)
            if not p.SENSITIVE_VAR_NAMES.search(prop_name):
                continue
            context = content[max(0, match.start() - 100):match.end() + 100].strip()
            if p.is_false_positive(prop_value, context):
                continue
            entropy = p.calculate_entropy(prop_value)
            if entropy < 2.5:
                continue
            confidence = "high" if entropy >= 3.5 else "medium"
            findings.append({
                "type": "config_object:{}".format(prop_name),
                "key": prop_name,
                "value": prop_value,
                "confidence": confidence,
                "entropy": entropy,
                "context": context[:200],
            })
        return findings

    # ----------------------------------------------------------
    # 环境变量泄漏检测（移植自 jsrip _find_env_leaks）
    # ----------------------------------------------------------
    def _find_env_leaks(self, content, filename):
        """检测 process.env 引用和回退值泄漏"""
        findings = []
        sensitive_patterns = [
            "KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL",
            "AUTH", "PRIVATE", "API", "DATABASE", "DB_",
            "STRIPE", "AWS", "REDIS", "MONGO", "SMTP",
        ]
        for match in p.ENV_LEAK_RE.finditer(content):
            env_var = match.group(1)
            if not any(pat in env_var.upper() for pat in sensitive_patterns):
                continue
            context = content[max(0, match.start() - 100):match.end() + 300].strip()
            # 检查是否有回退值（硬编码默认值）
            fallback_match = re.search(
                r"process\.env\." + re.escape(env_var) +
                r"\s*\|\|\s*['\"]([^'\"]{8,256})['\"]",
                content[max(0, match.start() - 20):match.end() + 300]
            )
            if fallback_match:
                fallback_value = fallback_match.group(1)
                if not p.is_false_positive(fallback_value, context):
                    entropy = p.calculate_entropy(fallback_value)
                    findings.append({
                        "type": "env_fallback:{}".format(env_var),
                        "env_var": env_var,
                        "value": fallback_value,
                        "confidence": "high" if entropy >= 3.5 else "medium",
                        "entropy": entropy,
                        "context": context[:200],
                    })
            else:
                findings.append({
                    "type": "env_reference:{}".format(env_var),
                    "env_var": env_var,
                    "value": "process.env.{}".format(env_var),
                    "confidence": "info",
                    "entropy": 0.0,
                    "context": context[:200],
                })
        return findings

    # ----------------------------------------------------------
    # DOM 存储检测（移植自 jsrip _find_dom_storage）
    # ----------------------------------------------------------
    def _find_dom_storage(self, content, filename):
        """检测 localStorage/sessionStorage 敏感键值"""
        findings = []
        sensitive_keys = [
            "token", "key", "secret", "auth", "session", "jwt",
            "password", "credential", "api", "access",
        ]
        for match in p.DOM_STORAGE_RE.finditer(content):
            storage_key = match.group(1)
            storage_value = match.group(2) if match.lastindex and match.group(2) else None
            if not any(sk in storage_key.lower() for sk in sensitive_keys):
                continue
            context = content[max(0, match.start() - 100):match.end() + 100].strip()
            if storage_value and not p.is_false_positive(storage_value, context):
                entropy = p.calculate_entropy(storage_value)
                findings.append({
                    "type": "dom_storage_value:{}".format(storage_key),
                    "key": storage_key,
                    "value": storage_value,
                    "confidence": "medium" if entropy >= 3.0 else "low",
                    "entropy": entropy,
                    "context": context[:200],
                })
            else:
                findings.append({
                    "type": "dom_storage_key:{}".format(storage_key),
                    "key": storage_key,
                    "value": storage_key,
                    "confidence": "info",
                    "entropy": 0.0,
                    "context": context[:200],
                })
        return findings
