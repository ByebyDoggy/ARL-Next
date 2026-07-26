"""汇总报告生成器（自定义）

聚合一个站点的所有 JS 分析结果，生成 js_report 文档。
"""
from urllib.parse import urlparse

from app import utils
from app.modules.jsAnalysis import JsReport

logger = utils.get_logger()


class ReportGenerator:
    """JS 分析汇总报告生成器"""

    def generate(self, task_id, site, js_files_found, js_files_analyzed,
                 analyzer_results, sourcemap_results, route_results,
                 config_items, admin_results):
        """生成站点级 JS 分析报告

        Returns:
            JsReport 对象的 dump_json() dict
        """
        api_endpoints = 0
        internal_domains = set()
        admin_panels = set()
        frameworks = set()

        for ar in analyzer_results:
            api_endpoints += len(ar.get("endpoints", []))
            for ep in ar.get("endpoints", []):
                url = ep.get("url", "")
                if url.startswith("http"):
                    try:
                        domain = urlparse(url).netloc
                        if domain and not domain.startswith(
                                ("example", "localhost", "127.")):
                            internal_domains.add(domain)
                    except Exception:
                        pass

        for rr in route_results:
            framework = rr.get("framework", "")
            if framework and framework != "unknown":
                frameworks.add(framework)

        for ci in config_items:
            if ci.get("config_type") == "internal_domain":
                internal_domains.add(ci.get("value", ""))

        for ap in admin_results.get("admin_paths", []):
            admin_panels.add(ap.get("path", ""))

        assessment_parts = []
        if api_endpoints > 0:
            assessment_parts.append("发现 {} 个 API 端点".format(api_endpoints))
        accessible = sum(1 for s in sourcemap_results if s.get("map_accessible"))
        if sourcemap_results:
            assessment_parts.append("检测到 {} 个 Source Map（{} 个可访问）".format(
                len(sourcemap_results), accessible))
        if frameworks:
            assessment_parts.append("前端框架: {}".format(", ".join(frameworks)))
        if admin_panels:
            assessment_parts.append("发现 {} 个疑似管理路径".format(len(admin_panels)))
        if internal_domains:
            assessment_parts.append("发现 {} 个内部域名/IP".format(len(internal_domains)))

        assessment = "; ".join(assessment_parts) if assessment_parts else "JS 分析完成"

        report = JsReport(
            task_id=task_id, site=site,
            js_files_found=js_files_found,
            js_files_analyzed=js_files_analyzed,
            sourcemap_found=len(sourcemap_results) > 0,
            sourcemap_count=len(sourcemap_results),
            api_endpoints=api_endpoints,
            routes_found=sum(len(rr.get("routes", [])) for rr in route_results),
            config_items=len(config_items),
            internal_domains=sorted(internal_domains),
            admin_panels=sorted(admin_panels),
            framework=", ".join(sorted(frameworks)),
            assessment=assessment,
        )

        return report.dump_json()
