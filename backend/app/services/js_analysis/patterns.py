"""JS 深度分析 — 匹配模式库

移植自 jsrip 的 HTTP 客户端正则、误报过滤函数和 Shannon 熵计算。
WIH 已有的密钥规则不动，新增 jsrip 前缀模式。
"""
import re
import math
from collections import Counter

# ============================================================
# HTTP 客户端调用模式（移植自 jsrip FETCH_URL_RE 系列）
# ============================================================

# fetch() 调用
FETCH_RE = re.compile(
    r"fetch\s*\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE
)

# axios 方法调用
AXIOS_RE = re.compile(
    r"axios\.(?:get|post|put|delete|patch|head|options)\s*\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE
)

# XMLHttpRequest
XHR_RE = re.compile(
    r"xhr\.open\s*\(\s*['\"](?:GET|POST|PUT|DELETE|PATCH)['\"],\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE
)

# jQuery ajax
JQUERY_AJAX_RE = re.compile(
    r"\$\.(?:ajax|get|post)\s*\(\s*\{[^}]*url\s*:\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE
)

# WebSocket
WEBSOCKET_RE = re.compile(
    r"new\s+WebSocket\s*\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE
)

# GraphQL 操作
GRAPHQL_RE = re.compile(
    r"(?:query|mutation)\s+(?:[a-zA-Z_]\w*\s*)?(?:\([^)]*\)\s*)?\{",
    re.IGNORECASE
)

# 通用 URL 端点
GENERIC_ENDPOINT_RE = re.compile(
    r"""['"](/api/|/v\d+/|/rest/|/graphql|/endpoint)[a-zA-Z0-9/\-_\.]+['"]""",
    re.IGNORECASE
)

ALL_HTTP_PATTERNS = [
    ("fetch", FETCH_RE),
    ("axios", AXIOS_RE),
    ("xhr", XHR_RE),
    ("jquery", JQUERY_AJAX_RE),
    ("websocket", WEBSOCKET_RE),
    ("generic", GENERIC_ENDPOINT_RE),
]


# ============================================================
# 误报过滤（移植自 jsrip is_false_positive）
# ============================================================

PLACEHOLDER_PATTERN = re.compile(
    r"^("
    r"YOUR_?API_?KEY.*|CHANGE_?ME.*|TODO.*|FIXME.*|REPLACE_?ME.*|"
    r"INSERT_?.*_?HERE|PUT_?YOUR_?.*|ENTER_?YOUR_?.*|"
    r"xxx+|XXX+|yyy+|zzz+|aaa+|bbb+|000+|111+|123+|"
    r"test_?key.*|example_?key.*|sample_?key.*|demo_?key.*|fake_?key.*|"
    r"dummy.*|placeholder.*|"
    r"<[A-Z_]+>|"    # <API_KEY> style
    r"\{\{.*\}\}|"   # {{TEMPLATE}} style
    r"\$\{.*\}|"     # ${VARIABLE} style
    r"process\.env\..*|"
    r"undefined|null|true|false"
    r")$",
    re.IGNORECASE,
)

FALSE_POSITIVE_VALUES = {
    "application/json", "application/xml", "text/html", "text/plain",
    "text/javascript", "multipart/form-data", "charset=utf-8",
    "content-type", "authorization", "accept", "user-agent",
    "no-cache", "no-store", "must-revalidate",
    "utf-8", "ascii", "latin1",
    "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD",
    "localhost", "undefined", "null", "true", "false",
    "none", "auto", "inherit", "initial", "unset",
}

CSS_HEX_RE = re.compile(r"^#?[0-9a-fA-F]{3,8}$")
VERSION_RE = re.compile(r"^v?\d+\.\d+\.\d+([\-.]\w+)?$")
MINIFIED_VAR_RE = re.compile(r"^[a-zA-Z_$][a-zA-Z0-9_$]{0,3}$")
CAMELCASE_IDENT_RE = re.compile(r"^[a-zA-Z_$][a-zA-Z0-9_$]*$")
URL_PATH_RE = re.compile(r"^/[a-zA-Z0-9/_.\-]+$")


def looks_like_js_identifier(value):
    """判断是否看起来像 JS 函数/变量名（不是密钥）"""
    if not CAMELCASE_IDENT_RE.match(value):
        return False
    has_upper = bool(re.search(r"[a-z][A-Z]", value))
    if has_upper and value.isalpha():
        return True
    if value[0].isupper() and has_upper and value.isalpha():
        return True
    if value.isalpha() and value.islower() and len(value) >= 8:
        return True
    return False


def is_false_positive(value, context=""):
    """12 层误报过滤。返回 True 表示该值应丢弃。"""
    stripped = value.strip().strip("\"'")
    if len(stripped) < 8 or len(stripped) > 512:
        return True
    if PLACEHOLDER_PATTERN.match(stripped):
        return True
    if stripped.lower() in FALSE_POSITIVE_VALUES:
        return True
    if CSS_HEX_RE.match(stripped):
        return True
    if VERSION_RE.match(stripped):
        return True
    if MINIFIED_VAR_RE.match(stripped):
        return True
    if looks_like_js_identifier(stripped):
        return True
    if URL_PATH_RE.match(stripped):
        return True
    if stripped.isdigit():
        return True
    if len(set(stripped)) <= 2 and len(stripped) >= 8:
        return True
    if stripped.startswith(("/usr/", "/var/", "/etc/", "/home/", "/tmp/",
                            "C:\\", "./node_modules/", "../")):
        return True
    if any(kw in stripped.lower() for kw in
           ["function(", "return ", "module.", "require(", "import ",
            ".prototype", ".constructor", "Object.", "Array."]):
        return True
    ctx_lower = context.lower()
    if any(marker in ctx_lower for marker in
           ["// example", "// test", "// sample", "// demo",
            "* @param", "* @returns", "todo:", "fixme:"]):
        return True
    return False


# ============================================================
# Shannon 熵计算（移植自 jsrip）
# ============================================================

def calculate_entropy(value):
    """计算字符串的 Shannon 熵"""
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    entropy = -sum(
        (count / length) * math.log2(count / length)
        for count in counts.values()
        if count > 0
    )
    return round(entropy, 2)


# ============================================================
# 敏感变量名检测（移植自 jsrip SENSITIVE_VAR_NAMES）
# ============================================================

SENSITIVE_VAR_NAMES = re.compile(
    r"(?:api[_-]?key|api[_-]?secret|auth[_-]?token|access[_-]?token|"
    r"secret[_-]?key|private[_-]?key|client[_-]?secret|"
    r"password|passwd|pwd|token|credentials?|"
    r"aws[_-]?(?:key|secret|token)|stripe[_-]?(?:key|secret)|"
    r"database[_-]?(?:url|password|uri)|"
    r"encryption[_-]?key|signing[_-]?(?:key|secret)|"
    r"webhook[_-]?(?:secret|url)|"
    r"smtp[_-]?(?:password|pass)|"
    r"app[_-]?secret|session[_-]?secret|jwt[_-]?secret)",
    re.IGNORECASE,
)

# 智能分析正则（移植自 jsrip）
VAR_ASSIGNMENT_RE = re.compile(
    r"(?:const|let|var|this\.)\s*"
    r"([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*"
    r"['\"]([^'\"]{8,256})['\"]",
)
OBJ_PROPERTY_RE = re.compile(
    r"([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:\s*"
    r"['\"]([^'\"]{8,256})['\"]",
)
ENV_LEAK_RE = re.compile(
    r"process\.env\.([A-Z_][A-Z0-9_]*)",
)
DOM_STORAGE_RE = re.compile(
    r"(?:localStorage|sessionStorage)\."
    r"(?:setItem|getItem)\s*\(\s*"
    r"['\"]([^'\"]+)['\"]\s*"
    r"(?:,\s*['\"]([^'\"]{8,256})['\"])?",
)

# 配置提取正则（自定义）
MULTI_ENV_URL_RE = re.compile(
    r"(?:prod|test|dev|staging|internal|uat|pre|gray)"
    r"(?:URL|API|HOST|ENDPOINT|BASE)\s*:\s*['\"]"
    r"(https?://[^'\"]+)['\"]",
    re.IGNORECASE,
)

BASE_URL_RE = re.compile(
    r"(?:baseURL|baseUrl|base_url|BASE_URL)\s*[:=]\s*['\"]"
    r"(https?://[^'\"]+)['\"]",
    re.IGNORECASE,
)

AUTH_WHITELIST_RE = re.compile(
    r"(?:whiteList|whitelist|noAuth|publicPath|publicRoutes)\s*[:=]",
    re.IGNORECASE,
)

INTERNAL_DOMAIN_RE = re.compile(
    r"['\"](https?://)?([a-zA-Z0-9.\-]+(?:\.internal|\.local|\.dev|"
    r"10\.\d+\.\d+\.\d+|172\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+))"
    r"(:\d+)?['\"]",
    re.IGNORECASE,
)

THIRD_PARTY_KEY_RE = re.compile(
    r"(?:appId|app_key|appKey|clientId|client_secret|clientSecret|"
    r"wxAppId|wx_app_id|alipay_|wechat_)\s*:\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)

# 管理后台关键词
ADMIN_PATH_RE = re.compile(
    r"['\"](/?(?:admin|manage|console|backend|dashboard|ops|"
    r"administrator|management|controlpanel|"
    r"system|setting|config|maintenance))[/'\"\s]",
    re.IGNORECASE,
)

PERMISSION_CHECK_RE = re.compile(
    r"(?:user\.(?:role|isAdmin|userType|permission)|"
    r"roles?\.(?:includes|indexOf)|hasRole|isAdmin)\s*[=!]==?\s*"
    r"['\"]?(admin|administrator|superadmin|manager|root)['\"]?",
    re.IGNORECASE,
)

ADMIN_COMPONENT_RE = re.compile(
    r"(?:AdminPanel|AdminLayout|AdminDashboard|AdminPage|"
    r"ManageLayout|DashboardLayout|BackendLayout)",
    re.IGNORECASE,
)

# SPA 路由模式
VUE_ROUTER_PATH_RE = re.compile(
    r"path\s*:\s*['\"]([^'\"]+)['\"]",
)
REACT_ROUTER_PATH_RE = re.compile(
    r"<Route\s+[^>]*path=['\"]([^'\"]+)['\"]",
)
ANGULAR_ROUTER_PATH_RE = re.compile(
    r"path\s*:\s*['\"]([^'\"]+)['\"]\s*,\s*(?:component|loadChildren)",
)
SPA_NAVIGATE_RE = re.compile(
    r"(?:router\.push|router\.navigate|navigate\s*\(\s*['\"])"
    r"\s*\(\s*['\"]([^'\"]+)['\"]",
)

# Source Map 检测
SOURCEMAP_URL_RE = re.compile(
    r"sourceMappingURL=(?!data:application/json)([^\s?#*]+)",
)
SOURCEMAP_HEADER_NAMES = ("SourceMap", "X-SourceMap")
