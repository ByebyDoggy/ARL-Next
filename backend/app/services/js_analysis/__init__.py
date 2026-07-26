"""JS 深度静态分析服务"""
from . import patterns
from .analyzer import JsAnalyzer
from .soucemap import SourceMapDetector
from .route_analyzer import RouteAnalyzer
from .config_extractor import ConfigExtractor
from .admin_detector import AdminDetector
from .report_generator import ReportGenerator
from .collector import JsCollector

__all__ = [
    "JsAnalyzer", "SourceMapDetector", "RouteAnalyzer",
    "ConfigExtractor", "AdminDetector", "ReportGenerator", "JsCollector",
]
