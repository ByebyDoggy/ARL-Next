"""敏感配置提取器（自定义）

从 JS 中提取多环境地址、baseURL、鉴权白名单、内部域名、第三方密钥。
"""
from . import patterns as p


class ConfigExtractor:
    """JS 敏感配置提取器"""

    def analyze(self, content, js_url=None):
        """从 JS 内容中提取敏感配置

        Returns:
            list[dict]: [{config_type, key, value, environment, source}]
        """
        if not content:
            return []

        findings = []

        # 1. 多环境地址
        for match in p.MULTI_ENV_URL_RE.finditer(content):
            url = match.group(1)
            findings.append({
                "config_type": "endpoint",
                "key": match.group(0).split(":")[0].strip(),
                "value": url,
                "environment": self._infer_env(url),
                "source": "multi_env_url",
            })

        # 2. baseURL / baseUrl
        for match in p.BASE_URL_RE.finditer(content):
            url = match.group(1)
            findings.append({
                "config_type": "endpoint",
                "key": "baseURL",
                "value": url,
                "environment": self._infer_env(url),
                "source": "base_url",
            })

        # 3. 鉴权白名单
        if p.AUTH_WHITELIST_RE.search(content):
            findings.append({
                "config_type": "auth",
                "key": "auth_whitelist",
                "value": "auth whitelist/rules found in JS",
                "environment": "unknown",
                "source": "auth_whitelist",
            })

        # 4. 内部域名 / 内网 IP
        for match in p.INTERNAL_DOMAIN_RE.finditer(content):
            domain = match.group(2)
            findings.append({
                "config_type": "internal_domain",
                "key": "internal_host",
                "value": domain,
                "environment": "internal",
                "source": "internal_domain",
            })

        # 5. 第三方密钥引用
        for match in p.THIRD_PARTY_KEY_RE.finditer(content):
            key_value = match.group(1)
            if not p.is_false_positive(key_value):
                findings.append({
                    "config_type": "api_key",
                    "key": match.group(0).split(":")[0].strip(),
                    "value": key_value,
                    "environment": "unknown",
                    "source": "third_party_key",
                })

        return findings

    @staticmethod
    def _infer_env(url):
        """从 URL 推断环境类型"""
        lower = url.lower()
        if any(kw in lower for kw in ["test", "staging", "uat", "sandbox", "dev"]):
            return "test"
        if any(kw in lower for kw in ["internal", "local", "10.", "172.", "192.168"]):
            return "internal"
        if "prod" in lower:
            return "prod"
        return "unknown"
