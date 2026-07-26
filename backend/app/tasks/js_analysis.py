"""JS 深度分析 Celery 任务

调用链: collector -> analyzer -> soucemap -> 各 analyzer -> report_generator -> 入库
"""
from app import utils
from app.config import Config
from app.services.js_analysis import (
    JsCollector, JsAnalyzer, SourceMapDetector,
    RouteAnalyzer, ConfigExtractor, AdminDetector, ReportGenerator,
)
from app.modules.jsAnalysis import (
    JsEndpoint, JsSourceMap, JsRoute, JsConfigItem,
)

logger = utils.get_logger()


def run_js_analysis(sites, task_id):
    """对站点列表执行完整的 JS 深度分析

    Args:
        sites: 站点 URL 列表
        task_id: 任务 ID

    Returns:
        dict: 分析统计
    """
    collector = JsCollector()
    analyzer = JsAnalyzer()
    proxy = {"http": Config.PROXY_URL} if Config.PROXY_URL else {}
    sm_detector = SourceMapDetector(proxies=proxy)
    route_analyzer = RouteAnalyzer()
    config_extractor = ConfigExtractor()
    admin_detector = AdminDetector()
    report_gen = ReportGenerator()

    total_stats = {"total_js": 0, "analyzed_js": 0, "endpoints": 0,
                   "sourcemaps": 0, "routes": 0, "configs": 0}

    try:
        for site in sites:
            logger.info("JS analysis for: {}".format(site))
            js_files = collector.collect_from_spider(task_id)
            total_stats["total_js"] += len(js_files)
            if not js_files:
                continue

            downloaded = collector.download_js_files(js_files)
            if not downloaded:
                continue
            total_stats["analyzed_js"] += len(downloaded)

            all_endpoints = []
            all_sourcemaps = []
            all_routes = []
            all_configs = []
            all_admin = {"admin_paths": [], "permission_fields": [],
                         "admin_components": [], "summary": ""}
            all_ar = []

            for js_file in downloaded:
                js_url = js_file["url"]
                filepath = js_file["path"]
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue
                if not content:
                    continue

                ar = analyzer.analyze_content(content, js_url=js_url, filepath=filepath)
                all_ar.append(ar)

                sm = sm_detector.detect_from_content(content, js_url)
                if sm:
                    sm["task_id"] = task_id
                    sm["site"] = site
                    all_sourcemaps.append(sm)

                rr = route_analyzer.analyze(content, js_url=js_url)
                if rr.get("routes"):
                    all_routes.append(rr)

                cfgs = config_extractor.analyze(content, js_url=js_url)
                all_configs.extend(cfgs)

                adm = admin_detector.analyze(content, js_url=js_url)
                if adm.get("admin_paths") or adm.get("permission_fields"):
                    all_admin = adm

                for ep in ar.get("endpoints", []):
                    obj = JsEndpoint(
                        task_id=task_id, site=site, js_url=js_url,
                        method=ep["method"], url=ep["url"], path=ep["path"],
                        params=ep.get("params", []), source=ep.get("source", ""),
                        confidence=ep.get("confidence", "medium"),
                    )
                    utils.conn_db("js_endpoint").insert_one(obj.dump_json())
                    total_stats["endpoints"] += 1

                if rr.get("routes"):
                    ro = JsRoute(
                        task_id=task_id, site=site, js_url=js_url,
                        framework=rr.get("framework", ""), routes=rr["routes"],
                    )
                    utils.conn_db("js_route").insert_one(ro.dump_json())
                    total_stats["routes"] += len(rr["routes"])

            for sm in all_sourcemaps:
                utils.conn_db("js_sourcemap").insert_one(sm)
                total_stats["sourcemaps"] += 1

            for cfg in all_configs:
                obj = JsConfigItem(
                    task_id=task_id, site=site, js_url=cfg.get("js_url", site),
                    config_type=cfg["config_type"], key=cfg["key"],
                    value=cfg["value"], environment=cfg.get("environment", "unknown"),
                    source=cfg.get("source", "pattern"),
                )
                utils.conn_db("js_config").insert_one(obj.dump_json())
                total_stats["configs"] += 1

            report = report_gen.generate(
                task_id=task_id, site=site,
                js_files_found=len(js_files),
                js_files_analyzed=len(downloaded),
                analyzer_results=all_ar,
                sourcemap_results=all_sourcemaps,
                route_results=all_routes,
                config_items=all_configs,
                admin_results=all_admin,
            )
            utils.conn_db("js_report").insert_one(report)

    finally:
        collector.cleanup()

    logger.info("JS analysis done: {}".format(total_stats))
    return total_stats
