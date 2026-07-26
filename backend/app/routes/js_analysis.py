"""JS 深度分析 - API 路由

按项目现有 ARLResource 模式实现。
"""
from flask_restx import Namespace, fields
from . import ARLResource, base_query_fields, get_arl_parser

ns = Namespace('js_analysis', description="JS 深度分析结果")

# ============================================================
# JS 端点查询
# ============================================================
js_endpoint_fields = {
    'task_id': fields.String(description="任务 ID"),
    'site': fields.String(description="站点 URL"),
    'method': fields.String(description="HTTP 方法"),
    'url': fields.String(description="URL"),
    'path': fields.String(description="路径"),
    'source': fields.String(description="来源"),
    'confidence': fields.String(description="可信度"),
}
js_endpoint_fields.update(base_query_fields)

@ns.route('/js_endpoint/')
class JsEndpointAPI(ARLResource):
    parser = get_arl_parser(js_endpoint_fields, location='args')

    @ns.expect(parser)
    def get(self):
        args = self.parse_args(js_endpoint_fields)
        return self.build_data(args=args, collection='js_endpoint')


# ============================================================
# Source Map 查询
# ============================================================
js_sourcemap_fields = {
    'task_id': fields.String(description="任务 ID"),
    'site': fields.String(description="站点 URL"),
    'map_accessible': fields.String(description="是否可访问"),
    'detection_method': fields.String(description="发现方式"),
}
js_sourcemap_fields.update(base_query_fields)

@ns.route('/js_sourcemap/')
class JsSourceMapAPI(ARLResource):
    parser = get_arl_parser(js_sourcemap_fields, location='args')

    @ns.expect(parser)
    def get(self):
        args = self.parse_args(js_sourcemap_fields)
        return self.build_data(args=args, collection='js_sourcemap')


# ============================================================
# 前端路由查询
# ============================================================
js_route_fields = {
    'task_id': fields.String(description="任务 ID"),
    'site': fields.String(description="站点 URL"),
    'framework': fields.String(description="前端框架"),
}
js_route_fields.update(base_query_fields)

@ns.route('/js_route/')
class JsRouteAPI(ARLResource):
    parser = get_arl_parser(js_route_fields, location='args')

    @ns.expect(parser)
    def get(self):
        args = self.parse_args(js_route_fields)
        return self.build_data(args=args, collection='js_route')


# ============================================================
# JS 配置查询
# ============================================================
js_config_fields = {
    'task_id': fields.String(description="任务 ID"),
    'site': fields.String(description="站点 URL"),
    'config_type': fields.String(description="配置类型"),
    'environment': fields.String(description="环境"),
}
js_config_fields.update(base_query_fields)

@ns.route('/js_config/')
class JsConfigAPI(ARLResource):
    parser = get_arl_parser(js_config_fields, location='args')

    @ns.expect(parser)
    def get(self):
        args = self.parse_args(js_config_fields)
        return self.build_data(args=args, collection='js_config')


# ============================================================
# JS 报告查询
# ============================================================
js_report_fields = {
    'task_id': fields.String(description="任务 ID"),
    'site': fields.String(description="站点 URL"),
}
js_report_fields.update(base_query_fields)

@ns.route('/js_report/')
class JsReportAPI(ARLResource):
    parser = get_arl_parser(js_report_fields, location='args')

    @ns.expect(parser)
    def get(self):
        args = self.parse_args(js_report_fields)
        return self.build_data(args=args, collection='js_report')
