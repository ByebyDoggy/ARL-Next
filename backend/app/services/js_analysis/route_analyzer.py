"""SPA 路由分析器（自定义）

从 Vue Router / React Router / Angular Router 配置中提取业务页面路径。
"""
import re
from . import patterns as p


class RouteAnalyzer:
    """SPA 前端路由分析器"""

    def analyze(self, content, js_url=None):
        """从 JS 内容中提取前端路由

        Returns:
            dict: {framework, routes: [{path, name, confidence}]}
        """
        if not content:
            return {"framework": "", "routes": []}

        framework = self._detect_framework(content)
        routes = self._extract_routes(content, framework)

        seen = set()
        unique_routes = []
        for route in routes:
            path = route["path"]
            if path in seen or len(path) < 2:
                continue
            seen.add(path)
            unique_routes.append(route)

        return {"framework": framework, "routes": unique_routes}

    @staticmethod
    def _detect_framework(content):
        """检测前端框架类型"""
        if re.search(r"createRouter|createWebHistory|vue-router", content):
            return "vue"
        if re.search(r"react-router|BrowserRouter|Routes\s+|Route\s+path=", content):
            return "react"
        if re.search(r"RouterModule|provideRouter|withComponentInputBinding", content):
            return "angular"
        if re.search(r"router\.push|navigate\s*\(", content):
            return "spa-generic"
        return "unknown"

    @staticmethod
    def _extract_routes(content, framework):
        """根据框架类型提取路由"""
        routes = []

        # Vue Router: path: 'xxx'
        if framework in ("vue", "unknown", "spa-generic"):
            for match in p.VUE_ROUTER_PATH_RE.finditer(content):
                path = match.group(1)
                if path and not path.startswith("http"):
                    routes.append({
                        "path": path, "name": "",
                        "confidence": "high" if framework == "vue" else "medium",
                    })

        # React Router: <Route path='xxx'>
        if framework in ("react", "unknown"):
            for match in p.REACT_ROUTER_PATH_RE.finditer(content):
                path = match.group(1)
                if path and not path.startswith("http"):
                    routes.append({
                        "path": path, "name": "",
                        "confidence": "high" if framework == "react" else "medium",
                    })

        # Angular Router: path: 'xxx', loadChildren:
        if framework in ("angular", "unknown"):
            for match in p.ANGULAR_ROUTER_PATH_RE.finditer(content):
                path = match.group(1)
                if path and not path.startswith("http"):
                    routes.append({
                        "path": path, "name": "",
                        "confidence": "high" if framework == "angular" else "medium",
                    })

        # 通用: router.push/navigate
        if framework == "spa-generic":
            for match in p.SPA_NAVIGATE_RE.finditer(content):
                path = match.group(1)
                if path and not path.startswith("http"):
                    routes.append({"path": path, "name": "", "confidence": "low"})

        return routes
