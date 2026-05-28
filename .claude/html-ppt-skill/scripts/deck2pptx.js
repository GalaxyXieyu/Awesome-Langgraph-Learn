#!/usr/bin/env node
/**
 * deck2pptx.js — Convert an HTML slide deck to .pptx via screenshot
 *
 * Usage:
 *   node deck2pptx.js examples/demo-intro/index.html
 *   node deck2pptx.js examples/demo-intro/index.html --output intro.pptx
 *   node deck2pptx.js examples/demo-intro/index.html --viewport 1920x1080
 *
 * How it works:
 *   1. Renders each <section class="slide"> to a PNG via Playwright
 *   2. Assembles PNGs into a PPTX (16:9) with each image as full-bleed slide background
 *   3. Result is pixel-perfect compared to the HTML deck
 *
 * Requires: playwright, pptxgenjs
 */

const { chromium } = require('playwright');
const pptxgen = require('pptxgenjs');
const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');

// ─── Auto-discover Chromium ────────────────────────────────────────
async function findChrome() {
  if (process.env.CHROME) return process.env.CHROME;

  const macPaths = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
  ];
  for (const p of macPaths) {
    try { if (fs.statSync(p).isFile()) return p; } catch {}
  }

  try {
    const { execSync } = require('child_process');
    const found = execSync(
      'mdfind "kMDItemCFBundleIdentifier == \\"com.google.Chrome\\"" 2>/dev/null | head -1',
      { encoding: 'utf-8' }
    ).trim();
    if (found) {
      const bin = path.join(found, 'Contents/MacOS/Google Chrome');
      try { if (fs.statSync(bin).isFile()) return bin; } catch {}
    }
  } catch {}

  const home = os.homedir();
  const pwRoot = path.join(home, 'Library/Caches/ms-playwright');
  try {
    const entries = fs.readdirSync(pwRoot);
    for (const entry of entries.sort().reverse()) {
      const candidate = path.join(pwRoot, entry, 'chrome-mac/Chromium.app/Contents/MacOS/Chromium');
      try { if (fs.statSync(candidate).isFile()) return candidate; } catch {}
      const candidate2 = path.join(pwRoot, entry, 'chrome-linux/chrome');
      try { if (fs.statSync(candidate2).isFile()) return candidate2; } catch {}
    }
  } catch {}

  const linuxPaths = [
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    '/usr/local/bin/google-chrome', '/snap/bin/chromium', '/usr/lib/chromium/chromium',
  ];
  for (const p of linuxPaths) {
    try { if (fs.statSync(p).isFile()) return p; } catch {}
  }

  return undefined;
}

// ─── Local static server ───────────────────────────────────────────
function startServer(root, port = 0) {
  const mime = {
    '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
    '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
    '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf',
  };

  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const reqPath = path.normalize(decodeURIComponent(req.url.split('?')[0]));
      const safePath = path.join(root, reqPath.replace(/^\/+/, ''));
      if (!safePath.startsWith(root)) {
        res.writeHead(403); res.end('Forbidden'); return;
      }

      fs.readFile(safePath, (err, data) => {
        if (err) {
          res.writeHead(404); res.end('Not found');
        } else {
          const ext = path.extname(safePath);
          res.writeHead(200, { 'Content-Type': mime[ext] || 'application/octet-stream' });
          res.end(data);
        }
      });
    });

    server.listen(port, '127.0.0.1', () => {
      const addr = server.address();
      resolve({ server, url: `http://127.0.0.1:${addr.port}` });
    });
  });
}

// ─── Find project root ─────────────────────────────────────────────
function findProjectRoot(htmlFile) {
  let dir = path.dirname(htmlFile);
  for (let i = 0; i < 5; i++) {
    if (fs.existsSync(path.join(dir, 'assets'))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return path.dirname(htmlFile);
}

// ─── CLI args ──────────────────────────────────────────────────────
function parseArgs() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('usage: node deck2pptx.js <html-file> [--output out.pptx] [--viewport WxH]');
    process.exit(1);
  }

  const file = args[0];
  if (!fs.existsSync(file)) {
    console.error(`error: file not found: ${file}`);
    process.exit(1);
  }

  let output = '';
  let viewport = '1920x1080';

  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--output' && i + 1 < args.length) output = args[++i];
    if (args[i] === '--viewport' && i + 1 < args.length) viewport = args[++i];
  }

  const absFile = path.resolve(file);
  const stem = path.basename(file, path.extname(file));
  if (!output) output = path.join(path.dirname(absFile), `${stem}.pptx`);

  const vp = viewport.split('x').map(Number);
  return { file: absFile, output: path.resolve(output), viewport: { width: vp[0], height: vp[1] } };
}

// ─── Render slides to PNGs ─────────────────────────────────────────
async function renderSlides(config) {
  const chromePath = await findChrome();
  if (chromePath) console.log(`Chrome: ${chromePath}`);
  else console.log('Chrome: using Playwright bundled Chromium');

  const serveRoot = findProjectRoot(config.file);
  const { server, url } = await startServer(serveRoot);

  const relPath = path.relative(serveRoot, config.file);
  const pageUrl = `${url}/${relPath.replace(/\\/g, '/')}`;

  const launchOpts = chromePath ? { executablePath: chromePath } : {};
  const browser = await chromium.launch(launchOpts);
  const page = await browser.newPage({ viewport: config.viewport });

  await page.goto(pageUrl, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  const totalSlides = await page.locator('section.slide').count();
  console.log(`Found ${totalSlides} slide(s)`);

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'deck2pptx-'));
  const pngPaths = [];

  for (let i = 0; i < totalSlides; i++) {
    await page.evaluate((idx) => {
      document.querySelectorAll('section.slide').forEach((s, j) => {
        s.style.display = j === idx ? 'flex' : 'none';
        s.style.opacity = '1';
        s.style.visibility = 'visible';
      });
    }, i);
    await page.waitForTimeout(800);

    const num = String(i + 1).padStart(2, '0');
    const pngPath = path.join(tmpDir, `slide_${num}.png`);
    await page.screenshot({ path: pngPath, type: 'png' });
    pngPaths.push(pngPath);
    console.log(`  ✔ Rendered slide ${num}`);
  }

  await browser.close();
  server.close();

  return { pngPaths, tmpDir, totalSlides };
}

// ─── Build PPTX from PNGs ──────────────────────────────────────────
async function buildPPTX(config, rendered) {
  const { pngPaths, output } = rendered;

  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';

  for (const pngPath of pngPaths) {
    const slide = pptx.addSlide();
    slide.addImage({ path: pngPath, x: 0, y: 0, w: '100%', h: '100%' });
  }

  await pptx.writeFile({ fileName: config.output });
  console.log(`\n✅ PPTX saved: ${config.output}`);
}

// ─── Cleanup ───────────────────────────────────────────────────────
function cleanup(tmpDir) {
  try {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  } catch {}
}

// ─── Main ──────────────────────────────────────────────────────────
async function main() {
  const config = parseArgs();
  console.log(`HTML deck: ${config.file}`);
  console.log(`Output:    ${config.output}`);
  console.log(`Viewport:  ${config.viewport.width}x${config.viewport.height}`);
  console.log('');

  let rendered;
  try {
    rendered = await renderSlides(config);
    await buildPPTX(config, rendered);
  } finally {
    if (rendered?.tmpDir) cleanup(rendered.tmpDir);
  }
}

main().catch((err) => {
  console.error('error:', err.message);
  process.exit(1);
});
