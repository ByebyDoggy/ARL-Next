import time
import os
import json
import requests
from app import utils
from app.config import Config
from .baseThread import BaseThread
logger = utils.get_logger()

# PUPPETEER_URL needs to point to the new docker service 'arl-puppeteer' on port 5005
PUPPETEER_URL = os.environ.get("PUPPETEER_URL", "http://arl-puppeteer:5005")

class WebAnalyze(BaseThread):
    def __init__(self, sites, concurrency=3):
        super().__init__(sites, concurrency = concurrency)
        self.analyze_map = {}

    def work(self, site):
        logger.debug("WebAnalyze HTTP => {}".format(site))
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Send HTTP POST request to the Puppeteer service
                res = requests.post(PUPPETEER_URL, json={"url": site}, timeout=35)
                if res.status_code == 200:
                    data = res.json()
                    self.analyze_map[site] = data.get("applications", [])
                    return
                elif res.status_code == 503:
                    logger.warning("WebAnalyze HTTP 503 for {}, server is restarting. Retrying in 10s...".format(site))
                    time.sleep(10)
                    continue
                else:
                    logger.warning("WebAnalyze HTTP Error {} for {}: {}".format(res.status_code, site, res.text))
                    self.analyze_map[site] = []
                    return
            except requests.exceptions.ConnectionError:
                logger.warning("WebAnalyze ConnectionError for {}. Retrying in 5s...".format(site))
                time.sleep(5)
                continue
            except Exception as e:
                logger.warning("Failed to parse webAnalyze output for {}: {}".format(site, e))
                self.analyze_map[site] = []
                return
        
        logger.error("WebAnalyze failed for {} after {} retries.".format(site, max_retries))
        self.analyze_map[site] = []

    def run(self):
        t1 = time.time()
        logger.info("start WebAnalyze {}".format(len(self.targets)))
        self._run()
        elapse = time.time() - t1
        logger.info("end WebAnalyze elapse {}".format(elapse))
        return self.analyze_map


def web_analyze(sites, concurrency=3):
    s = WebAnalyze(sites, concurrency=concurrency)
    return s.run()

