"""管理后台发现器（自定义）

从 JS 中搜索 admin/manage/console 路径、权限字段、管理组件引用。
"""
from . import patterns as p


class AdminDetector:
    """管理后台发现器"""

    def analyze(self, content, js_url=None):
        """从 JS 内容中检测管理后台相关痕迹

        Returns:
            dict: {admin_paths, permission_fields, admin_components, summary}
        """
        if not content:
            return {"admin_paths": [], "permission_fields": [],
                    "admin_components": [], "summary": ""}

        admin_paths = self._find_admin_paths(content)
        permission_fields = self._find_permission_fields(content)
        admin_components = self._find_admin_components(content)

        summary_parts = []
        if admin_paths:
            summary_parts.append("发现 {} 个管理路径".format(len(admin_paths)))
        if permission_fields:
            summary_parts.append("发现 {} 处权限判断".format(len(permission_fields)))
        if admin_components:
            summary_parts.append("发现 {} 个管理组件".format(len(admin_components)))

        return {
            "admin_paths": admin_paths,
            "permission_fields": permission_fields,
            "admin_components": admin_components,
            "summary": "; ".join(summary_parts) or "未发现管理后台痕迹",
        }

    @staticmethod
    def _find_admin_paths(content):
        """搜索 JS 中的管理后台路径"""
        found = set()
        results = []
        for match in p.ADMIN_PATH_RE.finditer(content):
            path = match.group(1).strip().lower()
            if path in found:
                continue
            found.add(path)
            results.append({
                "path": path,
                "context": content[max(0, match.start() - 30):match.end() + 30].strip()[:100],
            })
        return results

    @staticmethod
    def _find_permission_fields(content):
        """检测权限判断逻辑"""
        found = set()
        results = []
        for match in p.PERMISSION_CHECK_RE.finditer(content):
            snippet = match.group(0).strip()[:80]
            if snippet in found:
                continue
            found.add(snippet)
            results.append({
                "snippet": snippet,
                "context": content[max(0, match.start() - 30):match.end() + 30].strip()[:100],
            })
        return results

    @staticmethod
    def _find_admin_components(content):
        """检测管理员相关组件引用"""
        found = set()
        results = []
        for match in p.ADMIN_COMPONENT_RE.finditer(content):
            component = match.group(0)
            if component in found:
                continue
            found.add(component)
            results.append({
                "component": component,
                "context": content[max(0, match.start() - 30):match.end() + 30].strip()[:100],
            })
        return results
