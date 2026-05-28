#!/usr/bin/env node
/**
 * render.js — Cross-platform HTML slide screenshotter (Playwright)
 *
 * Usage:
 *   node render.js <html-file>                     # one PNG, slide 1
 *   node render.js <html-file> <N>                 # N PNGs, slides 1..N
 *   node render.js <html-file> all                 # autodetect .slide count
 *   node render.js <html-file> <N> <out-dir>       # custom output dir
 *   node render.js <html-file> all <out-dir>       # all slides to custom dir
 *
 * Environment:
 *   CHROME     — path to Chrome/Chromium binary (optional)
 *   VIEWPORT   — viewport size, default 1920x1080
 *
 * Why a local server?
 *   Relative asset paths (<img src="../foo.png">) resolve correctly
 *   when served over HTTP, unlike file:// URLs.
 */

const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const PT_PER_PX = 0.75;
const PX_PER_IN = 96;

// ─── Auto-discover Chromium ────────────────────────────────────────
async function findChrome() {
  // 1. Env override
  if (process.env.CHROME) return process.env.CHROME;

  // 2. macOS standard paths
  const macPaths = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
  ];
  for (const p of macPaths) {
    try { if (fs.statSync(p).isFile()) return p; } catch {}
  }

  // 3. mdfind (Spotlight) on macOS
  try {
    const { execSync } = require('child_process');
    const found = execSync(
      'mdfind "kMDItemCFBundleIdentifier == \"com.google.Chrome\"" 2>/dev/null | head -1',
      { encoding: 'utf-8' }
    ).trim();
    if (found) {
      const bin = path.join(found, 'Contents/MacOS/Google Chrome');
      try { if (fs.statSync(bin).isFile()) return bin; } catch {}
    }
  } catch {}

  // 4. Playwright cache
  const home = require('os').homedir();
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

  // 5. Linux common paths
  const linuxPaths = [
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    '/usr/local/bin/google-chrome', '/snap/bin/chromium',
    '/usr/lib/chromium/chromium',
  ];
  for (const p of linuxPaths) {
    try { if (fs.statSync(p).isFile()) return p; } catch {}
  }

  // 6. Let Playwright find its bundled browser
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
      // Security: prevent directory traversal
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

// ─── CLI args ──────────────────────────────────────────────────────
function parseArgs() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('usage: node render.js <html-file> [N|all] [out-dir]');
    process.exit(1);
  }

  const file = args[0];
  if (!fs.existsSync(file)) {
    console.error(`error: file not found: ${file}`);
    process.exit(1);
  }

  let count = args[1] || '1';
  let outDir = args[2] || '';

  const absFile = path.resolve(file);
  const stem = path.basename(file, path.extname(file));

  // If count is "all", auto-detect
  if (count === 'all') {
    const html = fs.readFileSync(absFile, 'utf-8');
    const matches = html.match(/class="[^"]*slide[^"]*"/g);
    count = matches ? String(matches.length) : '1';
  }

  const countNum = parseInt(count, 10);
  if (isNaN(countNum) || countNum < 1) {
    console.error(`error: invalid slide count: ${count}`);
    process.exit(1);
  }

  if (!outDir && countNum > 1) {
    outDir = path.join(path.dirname(absFile), `${stem}-png`);
  }
  if (outDir) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  return { file: absFile, stem, count: countNum, outDir };
}

// ─── Main ──────────────────────────────────────────────────────────
async function main() {
  const config = parseArgs();
  const chromePath = await findChrome();

  if (chromePath) {
    console.log(`Chrome: ${chromePath}`);
  } else {
    console.log('Chrome: using Playwright bundled Chromium');
  }

  // Find project root (directory containing assets/) so relative paths resolve
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

  const serveRoot = findProjectRoot(config.file);
  const { server, url } = await startServer(serveRoot);

  const relPath = path.relative(serveRoot, config.file);
  const pageUrl = `${url}/${relPath.replace(/\\/g, '/')}`;
  console.log(`Serving from: ${serveRoot}`);
  console.log(`Page URL: ${pageUrl}`);

  // Parse viewport
  const viewportSize = (process.env.VIEWPORT || '1920x1080').split('x').map(Number);
  const viewport = { width: viewportSize[0], height: viewportSize[1] };

  const launchOpts = chromePath ? { executablePath: chromePath } : {};
  const browser = await chromium.launch(launchOpts);
  const page = await browser.newPage({ viewport });

  // Load page and wait for fonts/animations
  await page.goto(pageUrl, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  // Determine total slides
  const totalSlides = await page.locator('section.slide').count();
  const count = Math.min(config.count, totalSlides || 1);

  console.log(`Rendering ${count} slide(s) from ${config.file}`);

  for (let i = 0; i < count; i++) {
    // Show only current slide
    await page.evaluate((idx) => {
      document.querySelectorAll('section.slide').forEach((s, j) => {
        s.style.display = j === idx ? 'flex' : 'none';
        s.style.opacity = '1';
        s.style.visibility = 'visible';
      });
    }, i);

    // Wait for any CSS transitions / canvas FX
    await page.waitForTimeout(800);

    const num = String(i + 1).padStart(2, '0');
    const outPath = count === 1
      ? path.join(config.outDir || path.dirname(config.file), `${config.stem}.png`)
      : path.join(config.outDir, `${config.stem}_${num}.png`);

    await page.screenshot({ path: outPath, type: 'png' });
    console.log(`  ✔ ${outPath}`);
  }

  await browser.close();
  server.close();
  console.log(`done: rendered ${count} slide(s)`);
}

main().catch((err) => {
  console.error('error:', err.message);
  process.exit(1);
});
