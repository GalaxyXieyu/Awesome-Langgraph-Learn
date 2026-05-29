#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

const style = `
<style id="responsive-deck-style">
html, body { width: 100%; height: 100%; }
body.responsive-deck-enabled {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
body.responsive-deck-enabled .deck {
  position: relative;
  width: 720pt;
  height: 405pt;
  transform-origin: center center;
}
.deck-nav {
  position: fixed;
  left: 50%;
  bottom: 18px;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.22);
  backdrop-filter: blur(10px);
}
.deck-nav .deck-export {
  width: auto;
  min-width: 54px;
  padding: 0 11px;
  font-size: 12px;
}
.deck-nav button {
  width: 38px;
  height: 34px;
  border: 0;
  border-radius: 8px;
  background: rgba(56, 189, 248, 0.16);
  color: #e2e8f0;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}
.deck-nav button:hover { background: rgba(56, 189, 248, 0.28); }
.deck-nav .deck-nav-count {
  min-width: 64px;
  text-align: center;
  color: #94a3b8;
  font: 12px/1.2 Inter, "Noto Sans SC", sans-serif;
}
@media print {
  @page { size: 16in 9in; margin: 0; }
  html, body { width: auto; height: auto; background: #0f172a !important; }
  body.responsive-deck-enabled { display: block; overflow: visible; min-height: 0; }
  body.responsive-deck-enabled .deck { transform: none !important; width: auto; height: auto; }
  body.responsive-deck-enabled .slide {
    display: flex !important;
    width: 16in !important;
    height: 9in !important;
    page-break-after: always;
    break-after: page;
  }
  body.responsive-deck-enabled .slide:last-child {
    page-break-after: auto;
    break-after: auto;
  }
  .deck-nav { display: none !important; }
}
</style>`;

const script = `
<script id="responsive-deck-script">
(function () {
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }
  ready(function () {
    var deck = document.querySelector('.deck');
    if (!deck) return;
    var slides = Array.prototype.slice.call(deck.querySelectorAll('.slide'));
    if (!slides.length) return;
    document.body.classList.add('responsive-deck-enabled');

    var idx = Math.max(0, slides.findIndex(function (s) { return s.classList.contains('is-active'); }));
    if (idx < 0) idx = 0;

    function fit() {
      var baseW = 960;
      var baseH = 540;
      var scale = Math.min(window.innerWidth / baseW, window.innerHeight / baseH);
      deck.style.transform = 'scale(' + scale + ')';
    }

    function go(n) {
      idx = Math.max(0, Math.min(slides.length - 1, n));
      slides.forEach(function (s, i) {
        s.classList.toggle('is-active', i === idx);
        s.style.display = i === idx ? 'flex' : 'none';
        s.style.opacity = '1';
        s.style.visibility = 'visible';
      });
      var count = document.querySelector('.deck-nav-count');
      if (count) count.textContent = (idx + 1) + ' / ' + slides.length;
      if (location.hash !== '#/' + (idx + 1)) history.replaceState(null, '', '#/' + (idx + 1));
    }

    var m = /#\\/(\\d+)/.exec(location.hash || '');
    if (m) idx = Math.max(0, Math.min(slides.length - 1, parseInt(m[1], 10) - 1));

    var nav = document.createElement('div');
    nav.className = 'deck-nav';
    nav.innerHTML = '<button type="button" aria-label="上一页">‹</button><span class="deck-nav-count"></span><button type="button" aria-label="下一页">›</button><button class="deck-export" type="button" aria-label="导出 PDF">导出</button>';
    nav.children[0].addEventListener('click', function (e) { e.stopPropagation(); go(idx - 1); });
    nav.children[2].addEventListener('click', function (e) { e.stopPropagation(); go(idx + 1); });
    nav.children[3].addEventListener('click', function (e) {
      e.stopPropagation();
      document.body.classList.add('deck-printing');
      slides.forEach(function (s) {
        s.style.display = 'flex';
        s.style.opacity = '1';
        s.style.visibility = 'visible';
      });
      setTimeout(function () {
        window.print();
        setTimeout(function () {
          document.body.classList.remove('deck-printing');
          go(idx);
          fit();
        }, 500);
      }, 50);
    });
    document.body.appendChild(nav);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') go(idx + 1);
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') go(idx - 1);
      if (e.key === 'Home') go(0);
      if (e.key === 'End') go(slides.length - 1);
    });
    document.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('.deck-nav')) return;
      go(e.clientX > window.innerWidth / 2 ? idx + 1 : idx - 1);
    });
    window.addEventListener('resize', fit);
    fit();
    go(idx);
  });
})();
</script>`;

function patch(file) {
  let html = fs.readFileSync(file, 'utf8');
  html = html.replace(/\n?<style id="responsive-deck-style">[\s\S]*?<\/style>/, '');
  html = html.replace(/\n?<script id="responsive-deck-script">[\s\S]*?<\/script>/, '');
  html = html.replace(/\n?<script\s+src="[^"]*html-ppt-skill\/assets\/runtime\.js"><\/script>/g, '');
  html = html.replace(/src="\.\.\/diagrams\//g, 'src="../diagrams/');
  if (file.includes(`${path.sep}ppt-output${path.sep}`)) {
    html = html.replace(/src="\.\.\/diagrams\//g, 'src="../diagrams/');
  }
  html = html.replace('</head>', `${style}\n</head>`);
  html = html.replace('</body>', `${script}\n</body>`);
  fs.writeFileSync(file, html);
}

function main() {
  const files = [];
  for (const dirent of fs.readdirSync(ROOT, { withFileTypes: true })) {
    if (dirent.isDirectory() && dirent.name.startsWith('LG-')) {
      const f = path.join(ROOT, dirent.name, `${dirent.name}.html`);
      if (fs.existsSync(f)) files.push(f);
    }
  }
  const outputDir = path.join(ROOT, 'ppt-output');
  if (fs.existsSync(outputDir)) {
    for (const f of fs.readdirSync(outputDir)) {
      if (f.endsWith('.html')) files.push(path.join(outputDir, f));
    }
  }
  for (const f of files) {
    patch(f);
    console.log(`enhanced ${f}`);
  }
}

main();
