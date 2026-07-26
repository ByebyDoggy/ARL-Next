"""Source Map 检测器

移植自 getfrontend 的核心算法。不保存全量重建源码，仅记录发现信息和从中扫描出的敏感内容。
"""
import json
import re
import requests
from urllib.parse import urljoin

from app import utils
from . import patterns as p

logger = utils.get_logger()


class SourceMapDetector:
    """Source Map 三路检测器"""

    def __init__(self, timeout=15, proxies=None):
        self.timeout = timeout
        self.proxies = proxies or {}
        self._fetched_map_cache = {}

    def detect_from_content(self, content, js_url):
        """从 JS 内容中检测 Source Map 引用

        三路检测:
        1. 正则匹配 sourceMappingURL=xxx.map
        2. inline base64 编码的 sourceMappingURL
        3. 尝试请求 {js_url}.map

        Returns:
            dict 或 None
        """
        if not content or not js_url:
            return None

        # 方式 1: URL 格式 sourceMappingURL
        for match in re.finditer(p.SOURCEMAP_URL_RE, content):
            map_path = match.group(1).strip()
            map_url = urljoin(js_url, map_path)
            return self._try_fetch_map(map_url, js_url, "content_url")

        # 方式 2: inline base64
        inline_match = re.search(
            r"sourceMappingURL=data:application/json;base64,([A-Za-z0-9+/=]+)",
            content,
        )
        if inline_match:
            try:
                import base64
                map_content = base64.b64decode(inline_match.group(1)).decode("utf-8")
                findings = self._scan_source_content(map_content, js_url)
                return {
                    "task_id": "",
                    "site": js_url,
                    "js_url": js_url,
                    "map_url": "inline:base64",
                    "map_accessible": True,
                    "detection_method": "inline",
                    "sensitive_findings": findings,
                }
            except Exception:
                pass

        # 方式 3: 尝试追加 .map
        return self.detect_by_append(js_url)

    def detect_from_headers(self, headers, js_url):
        """从 HTTP 响应头检测 SourceMap / X-SourceMap"""
        if not headers or not js_url:
            return None
        for header_name in p.SOURCEMAP_HEADER_NAMES:
            map_url = headers.get(header_name)
            if map_url:
                full_url = urljoin(js_url, map_url)
                return self._try_fetch_map(full_url, js_url, "header")
        return None

    def detect_by_append(self, js_url):
        """尝试请求 {js_url}.map"""
        if js_url in self._fetched_map_cache:
            return None
        map_url = js_url + ".map"
        return self._try_fetch_map(map_url, js_url, "tail_append", check_only=True)

    def _try_fetch_map(self, map_url, js_url, method, check_only=False):
        """尝试下载并解析 .map 文件"""
        if map_url in self._fetched_map_cache:
            return None
        self._fetched_map_cache[map_url] = True

        try:
            resp = requests.get(
                map_url, timeout=self.timeout, proxies=self.proxies,
                verify=False, headers={"User-Agent": utils.get_ua()},
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            findings = self._scan_source_content(json.dumps(data), js_url)

            return {
                "task_id": "",
                "site": js_url,
                "js_url": js_url,
                "map_url": map_url,
                "map_accessible": True,
                "detection_method": method,
                "sensitive_findings": findings,
            }
        except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
            logger.debug("sourcemap fetch failed {}: {}".format(map_url, e))
            return None

    @staticmethod
    def _scan_source_content(map_text, source_url):
        """从 Source Map 内容中扫描敏感信息"""
        findings = []
        try:
            data = json.loads(map_text)
        except json.JSONDecodeError:
            return findings

        sources_content = data.get("sourcesContent") or []
        sources = data.get("sources") or []

        sensitive_keywords = [
            "api_key", "apikey", "secret", "password", "token",
            "private_key", "internal", "TODO", "FIXME", "HACK",
            "bypass", "backdoor", "debug", "test", "admin",
        ]

        for i, content in enumerate(sources_content):
            if not content:
                continue
            source_name = sources[i] if i < len(sources) else "unknown"
            for keyword in sensitive_keywords:
                if keyword.lower() in content.lower():
                    for line_num, line in enumerate(content.split("\n"), 1):
                        if keyword.lower() in line.lower():
                            findings.append({
                                "source_file": source_name,
                                "line": line_num,
                                "keyword": keyword,
                                "snippet": line.strip()[:120],
                            })
                            break
        return findings
