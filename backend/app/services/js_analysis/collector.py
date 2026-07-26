"""JS 文件收集器

复用 siteUrlSpider 爬虫结果 + getfrontend chunk 发现算法。不需要 Puppeteer。
"""
import os
import requests

from app import utils
from app.config import Config

logger = utils.get_logger()


class JsCollector:
    """JS 文件收集器"""

    def __init__(self, tmp_path=None):
        self.tmp_path = tmp_path or Config.TMP_PATH
        self.downloaded = []

    def collect_from_spider(self, task_id):
        """从 siteUrlSpider 爬虫结果中提取 JS 文件 URL

        Returns:
            list[dict]: [{url}]
        """
        js_files = []
        try:
            results = utils.conn_db("url").find(
                {"task_id": task_id, "type": "js"},
                {"crawl_url": 1, "url": 1}
            )
            for r in results:
                url = r.get("crawl_url") or r.get("url", "")
                if url and (url.endswith(".js") or ".js?" in url):
                    js_files.append({"url": url})
        except Exception as e:
            logger.warning("collect_from_spider error: {}".format(e))

        logger.info("collected {} JS URLs from spider for task {}".format(
            len(js_files), task_id))
        return js_files

    def download_js_files(self, js_files):
        """批量下载 JS 文件到本地

        Returns:
            list[dict]: [{url, path, size, hash}]
        """
        self.downloaded = []
        for entry in js_files:
            url = entry.get("url")
            if not url:
                continue
            try:
                local_path = self._download_single(url)
                if local_path:
                    file_size = os.path.getsize(local_path)
                    with open(local_path, "rb") as f:
                        content_hash = utils.gen_md5(f.read())
                    self.downloaded.append({
                        "url": url, "path": local_path,
                        "size": file_size, "hash": content_hash,
                    })
            except Exception as e:
                logger.debug("failed to download {}: {}".format(url, e))

        return self.downloaded

    def _download_single(self, url):
        """下载单个 JS 文件到临时目录"""
        rand_str = utils.random_choices()
        local_path = os.path.join(self.tmp_path, "js_{}_{}".format(
            utils.gen_md5(url)[:8], rand_str))

        try:
            resp = requests.get(
                url, timeout=15,
                headers={"User-Agent": utils.get_ua()},
                verify=False,
            )
            if resp.status_code == 200 and len(resp.content) > 50:
                max_size = getattr(Config, "JS_ANALYSIS_MAX_SIZE", 5 * 1024 * 1024)
                if len(resp.content) > max_size:
                    logger.debug("skipped {} (size > {}MB)".format(
                        url, max_size // 1024 // 1024))
                    return None
                with open(local_path, "wb") as f:
                    f.write(resp.content)
                return local_path
        except requests.RequestException as e:
            logger.debug("download failed {}: {}".format(url, e))

        return None

    def cleanup(self):
        """清理下载的临时文件"""
        for entry in self.downloaded:
            path = entry.get("path")
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception:
                    pass
        self.downloaded = []
