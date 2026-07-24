const http = require('http');
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const wappalyzerCode = fs.readFileSync(path.join(__dirname, 'wappalyzer.js'), 'utf8');
const vm = require('vm');
const wappalyzerScript = new vm.Script(wappalyzerCode);
const json = JSON.parse(fs.readFileSync(path.join(__dirname, 'apps.json'), 'utf8'));

let browser;

async function initBrowser() {
    browser = await puppeteer.launch({
        executablePath: '/usr/bin/chromium',
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox', 
            '--disable-dev-shm-usage', 
            '--ignore-certificate-errors', 
            '--disable-gpu'
        ],
        ignoreHTTPSErrors: true
    });
}

function analyzeUrl(url) {
    return new Promise(async (resolve, reject) => {
        let page;
        let context;
        let timeoutId;

        const cleanupAndResolve = async (apps) => {
            if (timeoutId) clearTimeout(timeoutId);
            if (page) await page.close().catch(() => true);
            if (context) await context.close().catch(() => true);
            resolve({ url: url, originalUrl: url, applications: apps || [] });
        };

        timeoutId = setTimeout(() => {
            console.log(`[Timeout] 32s limit reached for ${url}`);
            cleanupAndResolve([]);
        }, 32000);
        try {
            // Create a new incognito context for isolation
            context = await browser.createIncognitoBrowserContext();
            page = await context.newPage();
            await page.setViewport({ width: 1280, height: 1024 });

            // Resource blocking to save CPU and Bandwidth
            await page.setRequestInterception(true);
            page.on('request', (req) => {
                const resourceType = req.resourceType();
                if (['image', 'stylesheet', 'font', 'media'].includes(resourceType)) {
                    req.abort();
                } else {
                    req.continue();
                }
            });

            let headers = {};
            let html = '';

            page.on('response', response => {
                // We want the headers from the main document response
                if (response.url().replace(/\/$/, '') === url.replace(/\/$/, '') || response.url() === url) {
                    const contentType = response.headers()['content-type'];
                    if (response.status() === 200 && contentType && contentType.includes('text/html')) {
                        headers = response.headers();
                    }
                }
            });

            try {
                await page.goto(url, { waitUntil: 'networkidle2', timeout: 25000 });
            } catch (e) {
                // timeout is fine, we might still have DOM
            }

            html = await page.content();
            
            // Truncate huge HTML to avoid regex explosion in wappalyzer
            if (html.length > 50000) {
                html = html.substring(0, 25000) + html.substring(html.length - 25000, html.length);
            }

            const environmentVarsArray = await page.evaluate(() => {
                return Object.keys(window);
            });
            const environmentVars = environmentVarsArray.slice(0, 500).join(' ');

            // Close page and context
            await page.close();
            await context.close();

            // Evaluate Wappalyzer using a precompiled vm.Script to save massive CPU cycles while maintaining state isolation
            const contextObj = {};
            vm.createContext(contextObj);
            wappalyzerScript.runInContext(contextObj);
            const wappalyzer = contextObj.wappalyzer;

            wappalyzer.apps = json.apps;
            wappalyzer.categories = json.categories;

            wappalyzer.driver = {
                log: function(args) { },
                displayApps: function() {
                    let apps = [];
                    for (let app in wappalyzer.detected[url]) {
                        let cats = [];
                        wappalyzer.apps[app].cats.forEach(function(cat) {
                            cats.push(wappalyzer.categories[cat].name);
                        });
                        apps.push({
                            name: app,
                            confidence: wappalyzer.detected[url][app].confidenceTotal.toString(),
                            version: wappalyzer.detected[url][app].version,
                            icon: wappalyzer.apps[app].icon || 'default.svg',
                            website: wappalyzer.apps[app].website,
                            categories: cats
                        });
                    }
                    this.sendResponse(apps);
                },
                sendResponse: function(apps) {
                    cleanupAndResolve(apps);
                }
            };

            const parsedUrl = new URL(url);
            wappalyzer.analyze(parsedUrl.hostname, url, {
                html: html,
                headers: headers,
                env: environmentVars
            });

        } catch (e) {
            cleanupAndResolve([]);
        }
    });
}

let requestsCount = 0;
let activeRequests = 0;
let isShuttingDown = false;
const MAX_REQUESTS = 300; // Self-heal to prevent memory leaks

function checkShutdown() {
    if (requestsCount >= MAX_REQUESTS && !isShuttingDown) {
        isShuttingDown = true;
        console.log('Max requests reached, stopping new requests and waiting for active tasks to finish...');
    }
    
    if (isShuttingDown && activeRequests === 0) {
        console.log('All active tasks finished, exiting for self-healing...');
        if (browser) browser.close().catch(() => true).finally(() => process.exit(0));
        else process.exit(0);
    }
}

const server = http.createServer(async (req, res) => {
    if (isShuttingDown) {
        res.writeHead(503, { 'Connection': 'close' });
        res.end('Server is restarting');
        return;
    }

    activeRequests++;

    if (req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk.toString());
        req.on('end', async () => {
            try {
                const data = JSON.parse(body);
                const url = data.url;
                if (!url) {
                    res.writeHead(400);
                    res.end('Missing url');
                    return;
                }
                
                const result = await analyzeUrl(url);
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify(result));
                
                requestsCount++;
            } catch (e) {
                res.writeHead(500);
                res.end(e.message);
            } finally {
                activeRequests--;
                checkShutdown();
            }
        });
    } else {
        res.writeHead(200);
        res.end('Puppeteer Wappalyzer Server OK');
        activeRequests--;
        checkShutdown();
    }
});

initBrowser().then(() => {
    server.listen(5005, '0.0.0.0', () => {
        console.log('Puppeteer server running on port 5005');
    });
}).catch(console.error);
