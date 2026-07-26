"""
JS 深度静态分析 — 独立测试
直接测试关键函数逻辑（复制核心函数到本文件，避免项目 import 依赖）
"""
import re
import math
import hashlib
import unittest
from collections import Counter

# ============================================================
# 内联测试代码（复制自被测试模块）
# ============================================================

def _fnv_hash(content):
    raw = hashlib.md5(content.encode("utf-8")).hexdigest()
    return int(raw[:12], 16)

# --- 数据模型 ---
class JsEndpoint:
    def __init__(self, task_id, site, js_url, method, url, path,
                 params=None, source=None, framework=None, confidence="medium"):
        self.task_id = task_id; self.site = site; self.js_url = js_url
        self.method = method.upper(); self.url = url; self.path = path
        self.params = params or []; self.source = source or "unknown"
        self.framework = framework or ""; self.confidence = confidence
        self.fnv_hash = _fnv_hash("{}{}{}{}".format(task_id, url, method, js_url))
    def __eq__(self, o):
        return isinstance(o, JsEndpoint) and self.fnv_hash == o.fnv_hash
    def __hash__(self): return self.fnv_hash
    def dump_json(self):
        return {"task_id": self.task_id, "site": self.site, "js_url": self.js_url,
                "method": self.method, "url": self.url, "path": self.path,
                "params": self.params, "source": self.source,
                "framework": self.framework, "confidence": self.confidence,
                "fnv_hash": str(self.fnv_hash)}

class JsSourceMap:
    def __init__(self, task_id, site, js_url, map_url, accessible=False,
                 detection_method=None, sensitive_findings=None):
        self.task_id = task_id; self.site = site; self.js_url = js_url
        self.map_url = map_url; self.accessible = accessible
        self.detection_method = detection_method or "unknown"
        self.sensitive_findings = sensitive_findings or []
        self.fnv_hash = _fnv_hash("{}{}{}".format(task_id, map_url, js_url))
    def __eq__(self, o):
        return isinstance(o, JsSourceMap) and self.fnv_hash == o.fnv_hash
    def dump_json(self):
        return {"task_id": self.task_id, "site": self.site, "js_url": self.js_url,
                "map_url": self.map_url, "map_accessible": self.accessible,
                "detection_method": self.detection_method,
                "sensitive_findings": self.sensitive_findings,
                "fnv_hash": str(self.fnv_hash)}

class JsRoute:
    def __init__(self, task_id, site, js_url, framework, routes=None):
        self.task_id = task_id; self.site = site; self.js_url = js_url
        self.framework = framework or ""; self.routes = routes or []
        self.fnv_hash = _fnv_hash("{}{}{}".format(task_id, js_url, framework))
    def dump_json(self):
        return {"task_id": self.task_id, "site": self.site, "js_url": self.js_url,
                "framework": self.framework, "routes": self.routes,
                "fnv_hash": str(self.fnv_hash)}

class JsConfigItem:
    def __init__(self, task_id, site, js_url, config_type, key, value,
                 environment="unknown", source="pattern"):
        self.task_id = task_id; self.site = site; self.js_url = js_url
        self.config_type = config_type; self.key = key; self.value = value
        self.environment = environment; self.source = source
        self.fnv_hash = _fnv_hash("{}{}{}{}".format(task_id, config_type, key, value))
    def dump_json(self):
        return {"task_id": self.task_id, "site": self.site, "js_url": self.js_url,
                "config_type": self.config_type, "key": self.key, "value": self.value,
                "environment": self.environment, "source": self.source,
                "fnv_hash": str(self.fnv_hash)}

class JsReport:
    def __init__(self, task_id, site, **kw):
        self.task_id = task_id; self.site = site
        self.js_files_found = kw.get("js_files_found", 0)
        self.api_endpoints = kw.get("api_endpoints", 0)
        self.assessment = kw.get("assessment", "")
    def dump_json(self):
        return {"task_id": self.task_id, "site": self.site,
                "js_files_found": self.js_files_found,
                "api_endpoints": self.api_endpoints,
                "assessment": self.assessment}

# --- 匹配模式 ---
PLACEHOLDER_PATTERN = re.compile(
    r"^(YOUR_?API_?KEY.*|CHANGE_?ME.*|TODO.*|FIXME.*|REPLACE_?ME.*|"
    r"xxx+|XXX+|test_?key.*|example_?key.*|demo_?key.*|dummy.*|"
    r"<[A-Z_]+>|\{\{.*\}\}|\$\{.*\}|process\.env\..*|"
    r"undefined|null|true|false)$", re.IGNORECASE)
CSS_HEX_RE = re.compile(r"^#?[0-9a-fA-F]{3,8}$")
VERSION_RE = re.compile(r"^v?\d+\.\d+\.\d+([\-.]\w+)?$")
MINIFIED_VAR_RE = re.compile(r"^[a-zA-Z_$][a-zA-Z0-9_$]{0,3}$")
CAMELCASE_IDENT_RE = re.compile(r"^[a-zA-Z_$][a-zA-Z0-9_$]*$")

def looks_like_js_identifier(value):
    if not CAMELCASE_IDENT_RE.match(value): return False
    has_upper = bool(re.search(r"[a-z][A-Z]", value))
    if has_upper and value.isalpha(): return True
    if value[0].isupper() and has_upper and value.isalpha(): return True
    if value.isalpha() and value.islower() and len(value) >= 8: return True
    return False

def is_false_positive(value, context=""):
    stripped = value.strip().strip("\"'")
    if len(stripped) < 8 or len(stripped) > 512: return True
    if PLACEHOLDER_PATTERN.match(stripped): return True
    if stripped.lower() in {"content-type","authorization","accept","user-agent",
                            "GET","POST","PUT","DELETE","localhost",
                            "undefined","null","true","false"}: return True
    if CSS_HEX_RE.match(stripped): return True
    if VERSION_RE.match(stripped): return True
    if MINIFIED_VAR_RE.match(stripped): return True
    if looks_like_js_identifier(stripped): return True
    if stripped.isdigit(): return True
    if len(set(stripped)) <= 2 and len(stripped) >= 8: return True
    return False

def calculate_entropy(value):
    if not value: return 0.0
    counts = Counter(value); length = len(value)
    return round(-sum((c/length)*math.log2(c/length) for c in counts.values() if c > 0), 2)

# 正则模式
FETCH_RE = re.compile(r"fetch\s*\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
AXIOS_RE = re.compile(r"axios\.(?:get|post|put|delete)\s*\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
XHR_RE = re.compile(r"xhr\.open\s*\(\s*['\"](?:GET|POST)['\"],\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
WEBSOCKET_RE = re.compile(r"new\s+WebSocket\s*\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
SOURCEMAP_RE = re.compile(r"sourceMappingURL=(?!data:)([^\s?#*]+)")
ADMIN_PATH_RE = re.compile(r"['\"]/?("
    r"admin|manage|console|backend|dashboard|ops|administrator|"
    r"management|controlpanel|system|setting|config|maintenance)[/'\"]", re.IGNORECASE)
PERMISSION_CHECK_RE = re.compile(
    r"(?:user\.(?:role|isAdmin|userType)|hasRole|isAdmin)\s*[=!]==?\s*"
    r"['\"]?(admin|administrator|superadmin|manager|root)['\"]?", re.IGNORECASE)
MULTI_ENV_RE = re.compile(
    r"(?:prod|test|dev|staging|internal|uat|pre)(?:URL|API|HOST|ENDPOINT|BASE)"
    r"\s*:\s*['\"](https?://[^'\"]+)['\"]", re.IGNORECASE)
INTERNAL_DOMAIN_RE = re.compile(
    r"['\"](https?://)?([a-zA-Z0-9.\-]+(?:\.internal|\.local|\.dev|"
    r"10\.\d+\.\d+\.\d+|172\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+))(:\d+)?['\"]", re.IGNORECASE)
BASE_URL_RE = re.compile(
    r"(?:baseURL|baseUrl|base_url)\s*[:=]\s*['\"](https?://[^'\"]+)['\"]", re.IGNORECASE)
VUE_ROUTER_RE = re.compile(r"path\s*:\s*['\"]([^'\"]+)['\"]")
REACT_ROUTER_RE = re.compile(r"<Route\s+[^>]*path=['\"]([^'\"]+)['\"]")

# --- JsAnalyzer ---
class JsAnalyzer:
    BASE64_IMAGE_RE = re.compile(r"data:image\/[^,]+;base64,[A-Za-z0-9+/=\s]{100,}", re.IGNORECASE)
    LARGE_BASE64_RE = re.compile(r"[A-Za-z0-9+/]{400,}={0,2}")
    VAR_ASSIGNMENT_RE = re.compile(
        r"(?:const|let|var|this\.)\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*['\"]([^'\"]{8,256})['\"]")
    OBJ_PROPERTY_RE = re.compile(
        r"([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:\s*['\"]([^'\"]{8,256})['\"]")
    ENV_LEAK_RE = re.compile(r"process\.env\.([A-Z_][A-Z0-9_]*)")
    DOM_STORAGE_RE = re.compile(
        r"(?:localStorage|sessionStorage)\.(?:setItem|getItem)\s*\(\s*['\"]([^'\"]+)['\"]"
        r"(?:,\s*['\"]([^'\"]{8,256})['\"])?")
    SENSITIVE_VAR_NAMES = re.compile(
        r"(?:api[_-]?key|api[_-]?secret|auth[_-]?token|access[_-]?token|"
        r"secret[_-]?key|private[_-]?key|client[_-]?secret|"
        r"password|passwd|pwd|token|credentials?|"
        r"database[_-]?(?:url|password|uri)|"
        r"encryption[_-]?key|signing[_-]?(?:key|secret)|"
        r"webhook[_-]?(?:secret|url)|jwt[_-]?secret)", re.IGNORECASE)
    ALL_HTTP_PATTERNS = [
        ("fetch", FETCH_RE), ("axios", AXIOS_RE), ("xhr", XHR_RE), ("ws", WEBSOCKET_RE),
    ]

    def analyze_content(self, content):
        if not content: return {"endpoints": [],"assignments": [],"config_objects": [],
                                "env_leaks": [], "dom_storage": []}
        content = self.BASE64_IMAGE_RE.sub("", content)
        content = self.LARGE_BASE64_RE.sub("", content)
        return {"endpoints": self._find_endpoints(content),
                "assignments": self._find_assignments(content),
                "config_objects": self._find_config(content),
                "env_leaks": self._find_env(content),
                "dom_storage": self._find_dom(content)}

    def _find_endpoints(self, content):
        found = set(); results = []
        for src, regex in self.ALL_HTTP_PATTERNS:
            for m in regex.finditer(content):
                url = m.group(1).strip().strip("'\"")
                if not self._valid(url): continue
                k = (src, url)
                if k in found: continue
                found.add(k)
                results.append({"method": "GET", "url": url, "path": "/",
                                "source": src, "confidence": "high"})
        return results

    @staticmethod
    def _valid(url):
        if len(url) < 8 or len(url) > 500: return False
        low = url.lower()
        if any(t in low for t in ["license","github.com/","stackoverflow.com",
                                   "w3.org","npmjs.com","unpkg.com"]): return False
        if any(low.startswith(x) for x in ["http://example","https://example",
                                            "http://localhost","/path/"]): return False
        if any(low.endswith(x) for x in [".css",".png",".jpg",".svg",".ico",
                                          ".woff",".ttf",".mp4",".pdf",".zip"]): return False
        return True

    def _find_assignments(self, content):
        f = []
        for m in self.VAR_ASSIGNMENT_RE.finditer(content):
            n, v = m.group(1), m.group(2)
            if not self.SENSITIVE_VAR_NAMES.search(n): continue
            ctx = content[max(0,m.start()-50):m.end()+50]
            if is_false_positive(v, ctx): continue
            if calculate_entropy(v) < 2.0: continue
            f.append({"type":"sensitive:"+n,"value":v,"var_name":n,"confidence":"medium"})
        return f

    def _find_config(self, content):
        f = []
        for m in self.OBJ_PROPERTY_RE.finditer(content):
            n, v = m.group(1), m.group(2)
            if not self.SENSITIVE_VAR_NAMES.search(n): continue
            ctx = content[max(0,m.start()-50):m.end()+50]
            if is_false_positive(v, ctx): continue
            if calculate_entropy(v) < 2.5: continue
            f.append({"type":"config:"+n,"key":n,"value":v,"confidence":"medium"})
        return f

    def _find_env(self, content):
        f = []
        for m in self.ENV_LEAK_RE.finditer(content):
            ev = m.group(1)
            if not any(p in ev.upper() for p in ["KEY","SECRET","TOKEN","PASSWORD",
                                                    "AUTH","API","DATABASE","DB_"]): continue
            fm = re.search(r"process\.env\."+re.escape(ev)+r"\s*\|\|\s*['\"]([^'\"]{8,256})['\"]",
                           content[max(0,m.start()-20):m.end()+300])
            if fm:
                fv = fm.group(1)
                if not is_false_positive(fv):
                    f.append({"type":"env_fallback:"+ev,"value":fv,"confidence":"high"})
        return f

    def _find_dom(self, content):
        f = []
        for m in self.DOM_STORAGE_RE.finditer(content):
            k = m.group(1)
            v = m.group(2) if m.lastindex and m.group(2) else None
            if not any(s in k.lower() for s in ["token","key","secret","auth","jwt","password"]): continue
            if v:
                f.append({"type":"dom:"+k,"key":k,"value":v,"confidence":"medium"})
            else:
                f.append({"type":"dom_key:"+k,"key":k,"value":k,"confidence":"info"})
        return f

# --- RouteAnalyzer ---
class RouteAnalyzer:
    def analyze(self, content):
        if not content: return {"framework":"","routes":[]}
        fw = "unknown"
        if re.search(r"createRouter|createWebHistory|vue-router", content): fw = "vue"
        elif re.search(r"react-router|BrowserRouter|Routes\s+|Route\s+path=", content): fw = "react"
        elif re.search(r"RouterModule|provideRouter", content): fw = "angular"
        routes = []
        for m in VUE_ROUTER_RE.finditer(content):
            p = m.group(1)
            if p and not p.startswith("http"): routes.append({"path":p,"confidence":"high" if fw=="vue" else "medium"})
        for m in REACT_ROUTER_RE.finditer(content):
            p = m.group(1)
            if p and not p.startswith("http"): routes.append({"path":p,"confidence":"high" if fw=="react" else "medium"})
        seen = set(); dedup = []
        for r in routes:
            if r["path"] not in seen: seen.add(r["path"]); dedup.append(r)
        return {"framework": fw, "routes": dedup}

# --- ConfigExtractor ---
class ConfigExtractor:
    def analyze(self, content):
        if not content: return []
        f = []
        for m in MULTI_ENV_RE.finditer(content):
            f.append({"config_type":"endpoint","value":m.group(1),"environment":"unknown","source":"multi_env"})
        for m in INTERNAL_DOMAIN_RE.finditer(content):
            f.append({"config_type":"internal_domain","value":m.group(2),"environment":"internal","source":"internal"})
        for m in BASE_URL_RE.finditer(content):
            f.append({"config_type":"endpoint","value":m.group(1),"environment":"unknown","source":"base_url"})
        return f

# --- AdminDetector ---
class AdminDetector:
    def analyze(self, content):
        if not content: return {"admin_paths":[],"permission_fields":[],"admin_components":[],"summary":""}
        ap = [{"path":m.group(1).strip().lower()} for m in ADMIN_PATH_RE.finditer(content)]
        pf = [{"snippet":m.group(0)[:60]} for m in PERMISSION_CHECK_RE.finditer(content)]
        return {"admin_paths":ap,"permission_fields":pf,"admin_components":[],"summary":""}


# ============================================================
# 测试案例
# ============================================================

class TestDataModels(unittest.TestCase):
    def test_endpoint_basic(self):
        ep = JsEndpoint("t1","https://ex.com","app.js","GET",
                        "https://api.ex.com/v1/user","/v1/user")
        d = ep.dump_json()
        self.assertEqual(d["method"],"GET")
        self.assertIn("fnv_hash",d)

    def test_endpoint_dedup(self):
        ep1 = JsEndpoint("t1","s1","j1.js","GET","https://api.ex/u","/u")
        ep2 = JsEndpoint("t1","s1","j1.js","GET","https://api.ex/u","/u")
        self.assertEqual(ep1,ep2)

    def test_sourcemap_no_reconstructed(self):
        sm = JsSourceMap("t1","https://ex.com","app.js","app.js.map",True,"url")
        d = sm.dump_json()
        self.assertNotIn("reconstructed_files",d)
        self.assertIn("map_url",d)

    def test_route(self):
        r = JsRoute("t1","https://ex.com","app.js","vue",[{"path":"/admin"}])
        self.assertEqual(r.dump_json()["framework"],"vue")

    def test_config_item(self):
        ci = JsConfigItem("t1","https://ex.com","c.js","internal_domain","k","10.0.1.5")
        self.assertEqual(ci.dump_json()["config_type"],"internal_domain")

    def test_report(self):
        r = JsReport("t1","https://ex.com",api_endpoints=15)
        self.assertEqual(r.dump_json()["api_endpoints"],15)

class TestPatterns(unittest.TestCase):
    def test_placeholder(self): self.assertTrue(is_false_positive("YOUR_API_KEY"))
    def test_short(self): self.assertTrue(is_false_positive("abc"))
    def test_css(self): self.assertTrue(is_false_positive("#aabbcc"))
    def test_version(self): self.assertTrue(is_false_positive("1.2.3"))
    def test_valid_secret(self):
        self.assertFalse(is_false_positive("sk-live-xxxxxxxxxxxxx"))
        self.assertFalse(is_false_positive("AKIAIOSFODNN7EXAMPLE"))
    def test_entropy(self):
        self.assertGreater(calculate_entropy("abc123!@#"),3.0)
        self.assertLess(calculate_entropy("aaaaaaa"),1.0)
    def test_identifier(self):
        self.assertTrue(looks_like_js_identifier("componentWillUnmount"))
        self.assertFalse(looks_like_js_identifier("sk_live_xxx"))
    def test_fetch(self): self.assertEqual(len(FETCH_RE.findall("fetch('https://api.ex/u')")),1)
    def test_axios(self): self.assertEqual(len(AXIOS_RE.findall("axios.get('/api/v1/list')")),1)
    def test_ws(self): self.assertEqual(len(WEBSOCKET_RE.findall("new WebSocket('wss://ws.ex/s')")),1)
    def test_sourcemap(self): self.assertEqual(len(SOURCEMAP_RE.findall("//# sourceMappingURL=app.js.map")),1)
    def test_admin(self): self.assertTrue(len(ADMIN_PATH_RE.findall("'/admin/user'"))>0)
    def test_perm(self): self.assertTrue(len(PERMISSION_CHECK_RE.findall("if(user.role==='admin'){}"))>=1)
    def test_env(self): self.assertEqual(len(MULTI_ENV_RE.findall("prodURL:'https://api.ex.com'")),1)
    def test_internal(self): self.assertTrue(len(INTERNAL_DOMAIN_RE.findall("backend:'http://db.internal:5432'"))>=1)
    def test_baseurl(self): self.assertEqual(len(BASE_URL_RE.findall("baseURL:'https://test-api.ex.com'")),1)

class TestAnalyzer(unittest.TestCase):
    def setUp(self): self.a = JsAnalyzer()
    def test_fetch(self): r = self.a.analyze_content("fetch('https://api.ex/v1')"); self.assertTrue(len(r["endpoints"])>=1)
    def test_axios(self): r = self.a.analyze_content("axios.get('/api/v1/list')"); self.assertTrue(len(r["endpoints"])>=1)
    def test_ws(self): r = self.a.analyze_content("new WebSocket('wss://ws.ex/chat')"); self.assertTrue(len(r["endpoints"])>=1)
    def test_sensitive(self): r = self.a.analyze_content("const apiKey = 'sk-live-xxxxxxxxxxxxx';"); self.assertTrue(len(r["assignments"])>=1)
    def test_config(self): r = self.a.analyze_content("const c = {secretKey:'abc-12345'}"); self.assertTrue(len(r["config_objects"])>=1)
    def test_env(self): r = self.a.analyze_content("process.env.DATABASE_URL||'postgresql://u:p@localhost/db'"); self.assertTrue(len(r["env_leaks"])>=1)
    def test_dom(self): r = self.a.analyze_content("localStorage.setItem('auth_token','eyJhbGciOiJIUzI1NiJ9.test')"); self.assertTrue(len(r["dom_storage"])>=1)
    def test_empty(self): r = self.a.analyze_content(""); self.assertEqual(r["endpoints"],[])
    def test_github_filtered(self): r = self.a.analyze_content("fetch('https://github.com/user/repo')"); self.assertEqual(len(r["endpoints"]),0)
    def test_multiple_calls(self):
        code = "fetch('https://api.ex/v1/users'); axios.get('/api/v2/orders'); new WebSocket('wss://ws.ex/chat');"
        r = self.a.analyze_content(code)
        self.assertGreaterEqual(len(r["endpoints"]), 3, "should extract all 3 endpoints")
    def test_noise_removed(self):
        code = "fetch('https://cdn.example.com/style.css')"
        r = self.a.analyze_content(code)
        self.assertEqual(len(r["endpoints"]), 0, "CSS extension should be filtered")

class TestRoute(unittest.TestCase):
    def test_vue(self):
        c = "const routes=[{path:'/admin',component:Admin}];createRouter({routes})"
        r = RouteAnalyzer().analyze(c)
        self.assertEqual(r["framework"],"vue")
        self.assertTrue(any(x["path"]=="/admin" for x in r["routes"]))
    def test_react(self):
        r = RouteAnalyzer().analyze('<Route path="/dashboard" element={<D/>}/>')
        self.assertIn("react",r["framework"])
        self.assertTrue(any(x["path"]=="/dashboard" for x in r["routes"]))

class TestConfig(unittest.TestCase):
    def test_multi_env(self):
        r = ConfigExtractor().analyze("prodURL:'https://api.ex.com'")
        self.assertTrue(len(r)>=1)
    def test_empty(self): self.assertEqual(ConfigExtractor().analyze(""),[])
    def test_internal(self):
        r = ConfigExtractor().analyze("const h='http://db.internal:5432'")
        types=[x["config_type"] for x in r]
        self.assertIn("internal_domain",types)

class TestAdmin(unittest.TestCase):
    def test_paths(self): r=AdminDetector().analyze("const r=['/admin','/console'];"); self.assertTrue(len(r["admin_paths"])>=1)
    def test_perm(self): r=AdminDetector().analyze("if(user.role==='admin'){}"); self.assertTrue(len(r["permission_fields"])>=1)

class TestIntegration(unittest.TestCase):
    def test_full(self):
        src="""
        axios.get('/api/v1/list');
        fetch('https://admin.ex.com/manage');
        const routes=[{path:'/admin'}]; const router=createRouter({routes});
        const c={apiKey:'sk-live-xxxxxxxxx'};
        const h='http://db.internal:5432';
        if(user.role==='admin'){}
        """
        a=JsAnalyzer(); ar=a.analyze_content(src)
        self.assertGreater(len(ar["endpoints"]),0)
        rr=RouteAnalyzer().analyze(src)
        self.assertGreater(len(rr["routes"]),0)
        ce=ConfigExtractor().analyze(src)
        self.assertGreater(len(ce),0)
        ad=AdminDetector().analyze(src)
        self.assertGreater(len(ad["admin_paths"]),0)

if __name__=="__main__":
    unittest.main(verbosity=2)
