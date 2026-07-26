"""循环收敛控制器

负责种子提取、去重比对、收敛判定。
整轮批处理模式：每轮完整跑完 → 整体去重 → 判定收敛 → 再入下一轮。
默认关闭（1 轮=线性扫描），与现有行为完全兼容。
"""
import time
from urllib.parse import urlparse

from app import utils
from app.config import Config

logger = utils.get_logger()


class ConvergenceController:
    """循环收敛控制器"""

    def __init__(self, task_id, options=None):
        self.task_id = task_id
        self.options = options or {}
        self.max_rounds = int(self.options.get("convergence_max_rounds", 3))
        self.min_new = int(self.options.get("convergence_min_new", 5))
        self.ratio_threshold = float(self.options.get("convergence_ratio", 0.05))
        self.enabled = bool(self.options.get("convergence_enabled", False))
        self.rounds_log = []
        self._all_known = set()

    def should_converge(self, round_num, new_seeds):
        """判断是否应当收敛

        Returns:
            (bool, str): (是否收敛, 原因)
        """
        if not self.enabled or self.max_rounds <= 1:
            return True, "收敛未启用或最大轮次为 1"

        if round_num < 2:
            return False, "至少跑两轮才判断收敛"

        if round_num >= self.max_rounds:
            return True, "达到最大轮次 {}".format(self.max_rounds)

        total_known = max(len(self._all_known), 1)
        new_count = len(new_seeds)
        new_ratio = new_count / total_known

        if new_count < self.min_new:
            return True, "新增资产 {} < {}".format(new_count, self.min_new)

        if new_ratio < self.ratio_threshold:
            return True, "新增占比 {:.2%} < {:.2%}".format(
                new_ratio, self.ratio_threshold)

        return False, "继续第 {} 轮（新增 {} 个，占比 {:.2%}）".format(
            round_num + 1, new_count, new_ratio)

    def extract_seeds(self, task_id):
        """从任务结果中提取新种子

        种子源: JS 端点 / 内部域名 / 证书 SAN / 跳转 / Spider / DNS
        """
        new_seeds = set()

        # 1. JS 端点中的域名
        for ep in utils.conn_db("js_endpoint").find(
                {"task_id": task_id}, {"url": 1}):
            url = ep.get("url", "")
            if url.startswith("http"):
                try:
                    domain = urlparse(url).netloc.split(":")[0]
                    if domain and not self._is_noise(domain):
                        new_seeds.add(domain)
                except Exception:
                    pass
            elif "." in url and not url.endswith(".js"):
                new_seeds.add(url)

        # 2. 内部域名
        for c in utils.conn_db("js_config").find(
                {"task_id": task_id, "config_type": "internal_domain"},
                {"value": 1}):
            domain = c.get("value", "")
            if domain and not self._is_noise(domain):
                new_seeds.add(domain)

        # 3. 证书 CN
        for cert in utils.conn_db("cert").find(
                {"task_id": task_id}, {"subject_cn": 1}):
            cn = cert.get("subject_cn", "")
            if cn and "." in cn and not self._is_noise(cn):
                new_seeds.add(cn)

        # 4. 跳转链
        for s in utils.conn_db("site").find(
                {"task_id": task_id, "status": {"$gte": 300, "$lt": 400}},
                {"location": 1}):
            location = s.get("location", "")
            if location and location.startswith("http"):
                try:
                    domain = urlparse(location).netloc.split(":")[0]
                    if domain and not self._is_noise(domain):
                        new_seeds.add(domain)
                except Exception:
                    pass

        # 5. Spider 结果
        for u in utils.conn_db("url").find(
                {"task_id": task_id}, {"crawl_url": 1}):
            crawl_url = u.get("crawl_url", "")
            if crawl_url.startswith("http"):
                try:
                    domain = urlparse(crawl_url).netloc.split(":")[0]
                    if domain and not self._is_noise(domain):
                        new_seeds.add(domain)
                except Exception:
                    pass

        # 6. DNS 新记录
        for d in utils.conn_db("domain").find(
                {"task_id": task_id}, {"ips": 1}):
            for ip in d.get("ips", []):
                if ip and not ip.startswith(("127.", "10.", "172.16", "192.168")):
                    new_seeds.add(ip)

        return new_seeds

    def filter_new(self, seeds):
        """过滤出不在全局资产池中的新种子"""
        new_set = set()
        for seed in seeds:
            if seed not in self._all_known:
                new_set.add(seed)
                self._all_known.add(seed)
        return new_set

    def log_round(self, round_num, new_seeds, converged=False, reason=""):
        """记录轮次日志"""
        entry = {
            "round": round_num,
            "new_seeds": len(new_seeds),
            "total_known": len(self._all_known),
            "converged": converged,
            "reason": reason,
            "timestamp": time.time(),
        }
        self.rounds_log.append(entry)
        return entry

    @staticmethod
    def _is_noise(domain):
        lower = domain.lower()
        if lower in ("example.com", "example.org", "localhost",
                     "test.com", "google.com", "github.com"):
            return True
        if lower.startswith(("127.", "0.")):
            return True
        if len(domain.split(".")) < 2:
            return True
        return False
