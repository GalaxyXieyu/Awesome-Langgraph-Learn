#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

function filesToPatch() {
  const files = [];
  for (const d of fs.readdirSync(ROOT, { withFileTypes: true })) {
    if (d.isDirectory() && d.name.startsWith('LG-')) {
      const f = path.join(ROOT, d.name, `${d.name}.html`);
      if (fs.existsSync(f)) files.push(f);
    }
  }
  const out = path.join(ROOT, 'ppt-output');
  if (fs.existsSync(out)) {
    for (const f of fs.readdirSync(out)) {
      if (f.endsWith('.html')) files.push(path.join(out, f));
    }
  }
  return files;
}

function mimeFor(file) {
  const ext = path.extname(file).toLowerCase();
  if (ext === '.jpg' || ext === '.jpeg') return 'image/jpeg';
  if (ext === '.webp') return 'image/webp';
  if (ext === '.svg') return 'image/svg+xml';
  return 'image/png';
}

function resolveImage(file, src) {
  if (/^(data:|https?:|file:)/i.test(src)) return null;
  const local = path.resolve(path.dirname(file), src);
  if (fs.existsSync(local)) return local;
  const byName = path.join(ROOT, 'diagrams', path.basename(src));
  if (fs.existsSync(byName)) return byName;
  return null;
}

function patch(file) {
  let html = fs.readFileSync(file, 'utf8');
  let changed = 0;
  html = html.replace(/<img\b([^>]*?)\bsrc="([^"]+)"([^>]*)>/g, (match, before, src, after) => {
    const imagePath = resolveImage(file, src);
    if (!imagePath) return match;
    const b64 = fs.readFileSync(imagePath).toString('base64');
    changed++;
    return `<img${before}src="data:${mimeFor(imagePath)};base64,${b64}"${after}>`;
  });
  if (changed) {
    fs.writeFileSync(file, html);
  }
  return changed;
}

let total = 0;
for (const f of filesToPatch()) {
  const n = patch(f);
  total += n;
  console.log(`${n ? 'embedded' : 'unchanged'} ${n} ${f}`);
}
console.log(`done: embedded ${total} image references`);
