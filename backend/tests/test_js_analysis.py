"""
JS 深度静态分析 — 单元测试

用法: python -m pytest tests/test_js_analysis.py -v
      python tests/test_js_analysis.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.modules.jsAnalysis import (
    JsEndpoint, JsSourceMap, JsRoute, JsConfigItem, JsReport
)
from app.services.js_analysis.patterns import (
    is_false_positive, calculate_entropy, looks_like_js_identifier,
    FETCH_RE, AXIOS_RE, XHR_RE, WEBSOCKET_RE,
    SOURCEMAP_URL_RE, ADMIN_PATH_RE, PERMISSION_CHECK_RE,
    MULTI_ENV_URL_RE, INTERNAL_DOMAIN_RE, BASE_URL_RE,
)
from app.services.js_analysis.analyzer import JsAnalyzer
from app.services.js_analysis.route_analyzer import RouteAnalyzer
from app.services.js_analysis.config_extractor import ConfigExtractor
from app.services.js_analysis.admin_detector import AdminDetector
from app.services.convergence import ConvergenceController


# ============================================================
# 测试数据模型
# ============================================================
class TestJsModels(unittest.TestCase):

    def test_js_endpoint_basic(self):
        ep = JsEndpoint(
            task_id="abc123", site="https://example.com",
            js_url="https://example.com/app.js", method="GET",
            url="https://api.example.com/v1/user/list",
            path="/v1/user/list", source="fetch",
        )
        d = ep.dump_json()
        self.assertEqual(d["task_id"], "abc123")
        self.assertEqual(d["method"], "GET")
        self.assertEqual(d["path"], "/v1/user/list")
        self.assertEqual(d["confidence"], "medium")
        self.assertIn("fnv_hash", d)

    def test_js_endpoint_dedup(self):
        ep1 = JsEndpoint("t1", "s1", "js1.js", "GET",
                         "https://api.example.com/v1/user", "/v1/user")
        ep2 = JsEndpoint("t1", "s1", "js1.js", "GET",
                         "https://api.example.com/v1/user", "/v1/user")
        ep3 = JsEndpoint("t1", "s1", "js1.js", "POST",
                         "https://api.example.com/v1/user", "/v1/user")
        self.assertEqual(ep1, ep2)
        self.assertNotEqual(ep1, ep3)

    def test_js_sourcemap_no_source(self):
        sm = JsSourceMap(
            task_id="t1", site="https://example.com",
            js_url="https://example.com/app.js",
            map_url="https://example.com/app.js.map",
            accessible=True, detection_method="content_url",
        )
        d = sm.dump_json()
        self.assertEqual(d["map_url"], "https://example.com/app.js.map")
        self.assertTrue(d["map_accessible"])
        self.assertEqual(d["sensitive_findings"], [])
        self.assertNotIn("reconstructed_files", d)

    def test_js_route_basic(self):
        r = JsRoute("t1", "https://example.com", "app.js", "vue", [
            {"path": "/admin", "name": "admin"},
            {"path": "/user/list", "name": "userList"},
        ])
        d = r.dump_json()
        self.assertEqual(d["framework"], "vue")
        self.assertEqual(len(d["routes"]), 2)

    def test_js_config_item(self):
        ci = JsConfigItem("t1", "https://example.com", "config.js",
                          "internal_domain", "internal_host",
                          "10.0.1.5", environment="internal")
        d = ci.dump_json()
        self.assertEqual(d["config_type"], "internal_domain")
        self.assertEqual(d["value"], "10.0.1.5")
        self.assertEqual(d["environment"], "internal")

    def test_js_report(self):
        r = JsReport("t1", "https://example.com",
                     js_files_found=10, js_files_analyzed=8,
                     api_endpoints=15, assessment="发现 15 个 API 端点")
        d = r.dump_json()
        self.assertEqual(d["api_endpoints"], 15)
        self.assertEqual(d["js_files_found"], 10)


# ============================================================
# 测试匹配模式
# ============================================================
class TestPatterns(unittest.TestCase):

    def test_is_false_positive_placeholder(self):
        self.assertTrue(is_false_positive("YOUR_API_KEY"))
        self.assertTrue(is_false_positive("CHANGE_ME"))

    def test_is_false_positive_too_short(self):
        self.assertTrue(is_false_positive("abc"))

    def test_is_false_positive_css_color(self):
        self.assertTrue(is_false_positive("#aabbcc"))

    def test_is_false_positive_version(self):
        self.assertTrue(is_false_positive("1.2.3"))

    def test_is_false_positive_real_secret(self):
        self.assertFalse(is_false_positive("sk-live-1234567890abcdef123456"))
        self.assertFalse(is_false_positive("AKIAIOSFODNN7EXAMPLE"))

    def test_calculate_entropy(self):
        self.assertGreater(calculate_entropy("abc123xyz!@#"), 3.0)
        self.assertLess(calculate_entropy("aaaaaaaaaaaa"), 1.0)

    def test_fetch_regex(self):
        matches = FETCH_RE.findall("fetch('https://api.example.com/users')")
        self.assertEqual(len(matches), 1)
        self.assertIn("api.example.com", matches[0])

    def test_axios_regex(self):
        matches = AXIOS_RE.findall("axios.get('/api/v1/user/list')")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], "/api/v1/user/list")

    def test_xhr_regex(self):
        matches = XHR_RE.findall(
            "xhr.open('GET', 'https://admin.example.com/manage', true)")
        self.assertEqual(len(matches), 1)
        self.assertIn("admin.example.com", matches[0])

    def test_websocket_regex(self):
        matches = WEBSOCKET_RE.findall(
            "new WebSocket('wss://ws.example.com/socket')")
        self.assertEqual(len(matches), 1)

    def test_sourcemap_url_regex(self):
        matches = SOURCEMAP_URL_RE.findall(
            "//# sourceMappingURL=https://example.com/app.js.map")
        self.assertEqual(len(matches), 1)
        self.assertIn("app.js.map", matches[0])

    def test_admin_path_regex(self):
        matches = ADMIN_PATH_RE.findall("'/admin/user/list'")
        self.assertTrue(any("admin" in m for m in matches))

    def test_permission_check_regex(self):
        matches = PERMISSION_CHECK_RE.findall("if (user.role === 'admin')")
        self.assertTrue(len(matches) >= 1)

    def test_multi_env_url(self):
        matches = MULTI_ENV_URL_RE.findall(
            "prodURL: 'https://api.example.com'")
        self.assertEqual(len(matches), 1)
        self.assertIn("api.example.com", matches[0])

    def test_internal_domain_regex(self):
        matches = INTERNAL_DOMAIN_RE.findall(
            "backend: 'http://10.0.1.5:8080'")
        self.assertTrue(len(matches) >= 1)

    def test_base_url_regex(self):
        matches = BASE_URL_RE.findall(
            "baseURL: 'https://test-api.example.com'")
        self.assertEqual(len(matches), 1)


# ============================================================
# 测试核心分析引擎
# ============================================================
class TestJsAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = JsAnalyzer()

    def test_endpoint_fetch(self):
        code = "fetch('https://api.example.com/v1/users');"
        result = self.analyzer.analyze_content(code)
        self.assertTrue(len(result["endpoints"]) >= 1)

    def test_endpoint_axios(self):
        code = "axios.get('/api/v1/user/list');"
        result = self.analyzer.analyze_content(code)
        self.assertTrue(len(result["endpoints"]) >= 1)

    def test_endpoint_websocket(self):
        code = "const ws = new WebSocket('wss://ws.example.com/chat');"
        result = self.analyzer.analyze_content(code)
        self.assertTrue(
            any("ws.example.com" in ep["url"] for ep in result["endpoints"]))

    def test_sensitive_assignments(self):
        code = "const apiKey = 'sk-live-1234567890abcdef123456';"
        result = self.analyzer.analyze_content(code)
        self.assertTrue(len(result["assignments"]) >= 1)

    def test_config_objects(self):
        code = """
        const config = {
            secretKey: 'my-secret-key-12345',
            databaseUrl: 'postgresql://user:pass@localhost:5432/db'
        };
        """
        result = self.analyzer.analyze_content(code)
        self.assertTrue(len(result["config_objects"]) >= 1)

    def test_env_leaks(self):
        code = "const db = process.env.DB_URL || 'postgresql://u:p@localhost/db';"
        result = self.analyzer.analyze_content(code)
        self.assertTrue(len(result["env_leaks"]) >= 1)

    def test_dom_storage(self):
        code = "localStorage.setItem('auth_token', 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgN');"
        result = self.analyzer.analyze_content(code)
        self.assertTrue(len(result["dom_storage"]) >= 1)


# ============================================================
# 测试路由分析器
# ============================================================
class TestRouteAnalyzer(unittest.TestCase):

    def setUp(self):
        self.ra = RouteAnalyzer()

    def test_vue_routes(self):
        code = """
        const routes = [
            { path: '/', component: Home },
            { path: '/admin', component: Admin },
            { path: '/user/list', component: UserList },
        ];
        const router = createRouter({ history: createWebHistory(), routes });
        """
        result = self.ra.analyze(code)
        self.assertEqual(result["framework"], "vue")
        paths = [r["path"] for r in result["routes"]]
        self.assertIn("/admin", paths)
        self.assertIn("/user/list", paths)

    def test_react_routes(self):
        code = """
        <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/settings" element={<Settings />} />
        </Routes>
        """
        result = self.ra.analyze(code)
        self.assertIn("react", result["framework"])
        paths = [r["path"] for r in result["routes"]]
        self.assertIn("/dashboard", paths)


# ============================================================
# 测试配置提取器
# ============================================================
class TestConfigExtractor(unittest.TestCase):

    def setUp(self):
        self.ce = ConfigExtractor()

    def test_multi_env(self):
        code = """
        const prodAPI = 'https://api.example.com';
        const internalHost = 'http://10.0.1.5:8080';
        """
        results = self.ce.analyze(code)
        types = [r["config_type"] for r in results]
        self.assertIn("internal_domain", types)

    def test_base_url(self):
        code = "axios.create({baseURL: 'https://api.example.com/v2'});"
        results = self.ce.analyze(code)
        self.assertTrue(len(results) >= 1)


# ============================================================
# 测试后台发现器
# ============================================================
class TestAdminDetector(unittest.TestCase):

    def setUp(self):
        self.ad = AdminDetector()

    def test_admin_paths(self):
        code = "const adminRoutes = ['/admin', '/admin/user/manage', '/console'];"
        result = self.ad.analyze(code)
        self.assertTrue(len(result["admin_paths"]) >= 1)

    def test_permission_check(self):
        code = "if (user.role === 'admin') { showAdminPanel(); }"
        result = self.ad.analyze(code)
        self.assertTrue(len(result["permission_fields"]) >= 1)

    def test_admin_components(self):
        code = "import AdminPanel from './components/AdminPanel';"
        result = self.ad.analyze(code)
        self.assertTrue(len(result["admin_components"]) >= 1)


# ============================================================
# 测试收敛控制器
# ============================================================
class TestConvergence(unittest.TestCase):

    def test_disabled(self):
        cc = ConvergenceController("t1", {"convergence_enabled": False})
        converged, reason = cc.should_converge(1, {"seed1"})
        self.assertTrue(converged)
        self.assertIn("未启用", reason)

    def test_first_round_not_converged(self):
        cc = ConvergenceController("t1", {
            "convergence_enabled": True,
            "convergence_max_rounds": 3,
        })
        cc._all_known = {"a.com", "b.com"}
        converged, _ = cc.should_converge(1, {"c.com"})
        self.assertFalse(converged)

    def test_max_rounds_converges(self):
        cc = ConvergenceController("t1", {
            "convergence_enabled": True,
            "convergence_max_rounds": 2,
        })
        cc._all_known = {"a.com", "b.com", "c.com"}
        converged, reason = cc.should_converge(2, {"d.com"})
        self.assertTrue(converged)
        self.assertIn("最大轮次", reason)

    def test_min_new_converges(self):
        cc = ConvergenceController("t1", {
            "convergence_enabled": True,
            "convergence_max_rounds": 5,
            "convergence_min_new": 5,
        })
        cc._all_known = {"a.com", "b.com", "c.com"}
        converged, _ = cc.should_converge(3, {"d.com"})
        self.assertTrue(converged)


# ============================================================
# 集成测试
# ============================================================
class TestIntegration(unittest.TestCase):

    def test_full_pipeline(self):
        sample_js = """
        import axios from 'axios';
        import { createRouter } from 'vue-router';

        axios.defaults.baseURL = 'https://api.example.com/v2';
        axios.get('/user/list').then(r => {});
        axios.post('/order/create', {name: 'test'});
        fetch('https://admin.example.com/manage/user/delete/123');

        const routes = [
            { path: '/', component: Home },
            { path: '/admin', component: Admin },
        ];
        const router = createRouter({ routes });

        const config = {
            apiKey: 'sk-live-xxxxyyyyzzzz1234567890',
            databaseUrl: 'postgresql://u:p@db.internal:5432/db',
        };
        if (user.role === 'admin') { console.log('panel'); }
        """

        analyzer = JsAnalyzer()
        rr = RouteAnalyzer().analyze(sample_js)
        ce = ConfigExtractor().analyze(sample_js)
        ad = AdminDetector().analyze(sample_js)
        ar = analyzer.analyze_content(sample_js)

        self.assertGreater(len(ar["endpoints"]), 0, "应有 API 端点")
        self.assertGreater(len(rr["routes"]), 0, "应有前端路由")
        self.assertGreater(len(ce), 0, "应有敏感配置")
        self.assertGreater(len(ad["admin_paths"]), 0, "应有管理路径")
        self.assertGreater(len(ad["permission_fields"]), 0, "应有权限判断")


if __name__ == "__main__":
    unittest.main(verbosity=2)
