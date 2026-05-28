---
name: html-ppt
description: |
  HTML PPT Studio + 数据分析与办公提效全能助手。覆盖数据处理、分析洞察、报告撰写、数据可视化、PPT制作的端到端工作流。
  支持：Excel数据分析、投放数据复盘、ROI测算、数据可视化、报告生成、PPT制作（静态HTML演示 + HTML→PPTX）、公式生成。
  Use when the user asks for a presentation, PPT, slides, keynote, deck, slideshow, "幻灯片", "演讲稿", "做一份 PPT", "做一份 slides",
  a reveal-style HTML deck, a 小红书 图文, 数据分析, 报告, Excel, 投放分析, ROI, 复盘, 周报, 月报, 数据处理, 图表, 可视化, 汇报, 表格, 公式,
  or any kind of multi-slide pitch/report/sharing document. Triggers include keywords like "presentation", "ppt", "slides", "deck", "keynote",
  "reveal", "slideshow", "幻灯片", "演讲稿", "分享稿", "小红书图文", "talk slides", "pitch deck", "tech sharing", "technical presentation",
  "分析数据", "做报告", "Excel", "投放分析", "ROI", "复盘", "周报", "月报", "数据处理", "图表", "可视化", "汇报", "表格", "公式".
---

# html-ppt — Content Intelligence Engine

Author professional HTML presentations, data-driven reports, and visualizations.
One skill covers the full pipeline:
**raw data / user input → insight extraction → narrative orchestration → rendered output.**

One theme file = one look. One layout file = one page type. One animation class
= one entry effect. All pages share a token-based design system in `assets/base.css`.

## Install

```bash
npx skills add https://github.com/lewislulu/html-ppt-skill
```

One command, no build. Pure static HTML/CSS/JS with only CDN webfonts.

## What the skill gives you

- **36 themes** (`assets/themes/*.css`) — minimal-white, editorial-serif, soft-pastel, sharp-mono, arctic-cool, sunset-warm, catppuccin-latte/mocha, dracula, tokyo-night, nord, solarized-light, gruvbox-dark, rose-pine, neo-brutalism, glassmorphism, bauhaus, swiss-grid, terminal-green, xiaohongshu-white, rainbow-gradient, aurora, blueprint, memphis-pop, cyberpunk-neon, y2k-chrome, retro-tv, japanese-minimal, vaporwave, midcentury, corporate-clean, academic-paper, news-broadcast, pitch-deck-vc, magazine-bold, engineering-whiteprint
- **15 full-deck templates** (`templates/full-decks/<name>/`) — complete multi-slide decks with scoped `.tpl-<name>` CSS. 8 extracted from real-world decks (xhs-white-editorial, graphify-dark-graph, knowledge-arch-blueprint, hermes-cyber-terminal, obsidian-claude-gradient, testing-safety-alert, xhs-pastel-card, dir-key-nav-minimal), 7 scenario scaffolds (pitch-deck, product-launch, tech-sharing, weekly-report, xhs-post 3:4, course-module, **presenter-mode-reveal** — 演讲者模式专用)
- **31 layouts** (`templates/single-page/*.html`) with realistic demo data
- **27 CSS animations** (`assets/animations/animations.css`) via `data-anim`
- **20 canvas FX animations** (`assets/animations/fx/*.js`) via `data-fx` — particle-burst, confetti-cannon, firework, starfield, matrix-rain, knowledge-graph (force-directed), neural-net (pulses), constellation, orbit-ring, galaxy-swirl, word-cascade, letter-explode, chain-react, magnetic-field, data-stream, gradient-blob, sparkle-trail, shockwave, typewriter-multi, counter-explosion
- **Keyboard runtime** (`assets/runtime.js`) — arrows, T (theme), A (anim), F/O, **S (presenter mode: magnetic-card popup with CURRENT / NEXT / SCRIPT / TIMER cards)**, N (notes drawer), R (reset timer in presenter)
- **FX runtime** (`assets/animations/fx-runtime.js`) — auto-inits `[data-fx]` on slide enter, cleans up on leave
- **Showcase decks** for themes / layouts / animations / full-decks gallery
- **Headless Chrome render script** for PNG export

---

## Core workflow: four layers

This skill is not a "PPT tool" — it is a **content intelligence engine**.
Every request flows through four layers:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Demand Parser (需求解析)                           │
│  — Understand what the user truly needs                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Data Engine (数据层) 【auto-triggered】            │
│  — Detect any data input → analyze → generate insight cards  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Narrative Orchestrator (叙事编排层)                 │
│  — Assemble raw material + insights into a story arc         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Output Adapter (输出层)                            │
│  — Render the same outline into the right container format   │
└─────────────────────────────────────────────────────────────┘
```

**Key principle**: Data analysis is a **bottom-layer capability**, not an optional
output format. If the user provides any analyzable data, insights are automatically
extracted and injected into the content. The user does not need to ask for
"analysis" separately.

---

## Layer 1: Demand parser

**Do not start writing anything until you understand four things.**
Either ask the user directly, or — if they already handed you rich content —
propose a tasteful default and confirm.

### Step 1: Data detection

Detect whether the user has provided any analyzable data:

| Source | Detection | Action |
|--------|-----------|--------|
| Excel / CSV attachment | File extension / content | `read_excel.py` → structured data |
| Markdown table in message | `\|` characters | Parse → structured array |
| Numbers in text | "3.1% → 3.8%", "Q3 GMV ¥12M" | NLP extract → key-value pairs |
| JSON data | `{...}` structure | `json.parse` → structured |
| Vague claim ("转化很差") | No numbers detected | **Probe**: "具体数字是多少？环比变化多少？" |
| No data at all | None of above | Skip data layer, pure narrative |

**Rule**: Any structured or semi-structured data automatically triggers Layer 2.
The user does not need to say "analyze this."

### Step 2: Intent recognition

What is the user trying to achieve?

| Signal | Intent | Default container |
|--------|--------|-------------------|
| "给团队讲" / "技术分享" / "演讲" / "逐字稿" | Talk / presentation | Static HTML PPT |
| "分析报告" / "复盘" / "看看数据" / "周报" | Analysis / report | Interactive HTML report |
| "发给客户" / "需要编辑" / "pptx" | Editable deliverable | HTML → PPTX |
| "快速看一下" / "数字多少" | Exploratory scan | Terminal + Markdown |
| Mixed ("分析一下然后做个PPT") | Hybrid | **Dual-track** (see below) |

### Step 3: Audience mapping

| Audience | Theme direction | Layout bias | Information density |
|----------|----------------|-------------|---------------------|
| Engineers | Dark, monospace, technical | Code, architecture, diagrams | Medium |
| Executives / Board | Clean, conservative, light | KPI grids, minimal bullets | Low |
| Customers | Warm, approachable | Before/after, benefit-focused | Low |
| Investors | High-contrast, metric-heavy | Charts, growth curves, comparisons | Medium-High |
| Students | Educational or playful | Step-by-step, visual-heavy | Medium |

### Step 4: Delivery mode

| Mode | Theme recommendation | Special considerations |
|------|---------------------|------------------------|
| Projector / live talk | High-contrast darks (dracula, tokyo-night) | Large fonts, high contrast |
| Screen share (Zoom) | Clean lights (minimal-white, corporate-clean) | Avoid fine details |
| Self-read / document | Eye-comfort lights (solarized-light) | Higher info density OK |
| Mobile / social | Vertical-friendly (xiaohongshu-white) | Fewer columns, larger tap targets |
| Print / PDF | Pure whites (minimal-white) | No animations, pure static |

---

## Layer 2: Data engine

**Triggered automatically when any data is detected.**

### 2.1 Data ingestion (多源读取)

All data sources normalize to a standard structure:

```python
# Unified data object
{
  "fields": ["日期", "渠道", "花费", "转化", "ROI"],
  "records": [
    {"日期": "2024-01", "渠道": "搜索", "花费": 120000, "转化": 3400, "ROI": 2.83},
    ...
  ],
  "source": "excel",  # or "markdown_table", "text_extraction", "json"
  "derived_metrics": []  # populated by insight engine
}
```

**Read tools**:
- `read_excel.py` — Excel/CSV → markdown / csv / json
- Built-in parsers — Markdown tables, JSON, text numbers

### 2.2 Insight engine (洞察生成)

Automatically compute and generate **insight cards**:

| Calculation | Trigger | Example output |
|-------------|---------|----------------|
| 同比/环比 | Time-series detected | "Q3 环比增长 23%" |
| 占比/构成 | Categorical data | "搜索广告占预算 62%" |
| 均值/中位数/分布 | Numeric column | "客单价中位数 ¥328，均值 ¥415（右偏）" |
| ROI / 效率 | Cost + outcome fields | "ROI 1:3.2，高于行业均值 1:2.1" |
| 异常检测 | Variance > threshold | "11月 CTR 异常下跌 40%，需排查" |
| 相关性 | Multi-dimensional | "预算与转化相关性 r=0.87" |
| 排名/TopN | Grouped data | "Top3 渠道贡献 78% 转化" |

### 2.3 Insight card format (标准中间格式)

Every insight is packaged as a card — the bridge between data layer and narrative layer:

```yaml
- headline: "Q3转化率提升23%"        # 断言式标题，≤10字
  number: "23%"                      # 核心数字，带单位
  trend: up                          # up / down / neutral → 决定颜色
  context: "落地页优化+定向收紧"      # 一句话解释，≤30字
  evidence: "Q2: 3.1% → Q3: 3.8%"   # 支撑数据
  action: "Q4预算向高转化渠道倾斜"    # 可执行建议（如有）
  chart_type: line                   # 推荐图表: bar/line/pie/kpi/table
  priority: high                     # high / medium / low
```

**Insight card → layout mapping** (used by Layer 3):

| Card characteristic | Recommended layout |
|--------------------|--------------------|
| 1 card, big number | `stat-highlight.html` |
| 2-4 cards, comparison | `kpi-grid.html` |
| Time trend | `chart-line.html` |
| Category comparison | `chart-bar.html` |
| Composition / share | `chart-pie.html` |
| Multi-dimension radar | `chart-radar.html` |
| Dense tabular data | `table.html` |
| Before vs after | `comparison.html` |

---

## Layer 3: Narrative orchestrator

**Assemble user material + insight cards into a story arc.**

### 3.1 Standard narrative arc

```
Slide 1:  Hook        → Cover / one-sentence core conclusion
Slide 2:  Context     → Background / problem / data overview
Slide 3-5: Build       → Arguments supported by insights
Slide 6-7: Proof       → KPI grid / charts / evidence
Slide 8:   Plan        → Recommendations / timeline
Slide 9:   Close       → Summary / CTA / thanks
```

### 3.2 Rules for integrating insights

- **Lead with the headline, not the data.** The insight card's `headline`
  becomes the slide title (assertion format).
- **One insight per slide.** If you have 8 insight cards, you do not need
  8 data slides. Select the top 3-5 by `priority`, and group related ones.
- **Data slides alternate with argument slides.** Never stack 5 chart slides
  in a row.
- **Context matters.** The `evidence` field fills the body text; `action`
  goes into the recommendation slide.

### 3.3 Hybrid delivery (mixed demands)

When the user says something like "analyze this and make a deck for the boss":

**Dual-track strategy**:

```
├─ Track A: Detailed analysis (interactive HTML report)
│   └── All insights, full tables, every chart
│   └── Purpose: pre-read, archive, deep dive
│
└─ Track B: Talk version (static HTML PPT, 5-10 slides)
    └── Top 3 insights only, large fonts, minimal text
    └── Purpose: live presentation, 1 minute per slide
```

Deliver Track A first, then ask: "Shall I also make a condensed talk version?"

---

## Layer 4: Output adapter

**Render the same outline into the right container format.**

| Container | Technology | Best for |
|-----------|-----------|----------|
| **Static HTML PPT** | HTML/CSS/JS + 36 themes + 31 layouts | Talks, tech sharing, speaker scripts |
| **Interactive HTML report** | HTML + ECharts + 5 report styles | Deep analysis, weekly reports, data review |
| **PPTX file** | `html2pptx.js` / `build_pptx.js` | Client delivery, Office editing |
| **PNG image** | `render.sh` (headless Chrome) | Social media, quick sharing |
| **Markdown / text** | Plain text | Exploratory scan, raw numbers |

**Key principle**: The **content** (story arc + insight cards) is stable.
The **container** is flexible. The same outline can render into multiple formats.

---

## Design philosophy

### What we pursue

- **Warm professionalism** — Not cold tech-blue, not flashy cyber-neon. Warm tones
  (cream, coral, dark gold) convey expertise with humanity, like a well-designed
  magazine.
- **Information first** — Design serves data. Every visual element must help
  understand the data, not decorate. Titles are conclusions, not descriptions.
  Colors have semantics (red = problem, green = healthy, gray = reference).
  Only label key data points.
- **10-meter readable** — Designed for projection / training. Headlines occupy
  15–30% of the area, body text ≥ 10 pt, tables have zebra-striping to prevent
  line-skipping, rankings run largest to smallest.
- **Data honesty** — Bar charts start Y-axis at 0 (unless explicitly noted),
  bar charts use absolute proportions, tiny values have minimum-width protection,
  stacked charts merge < 3% slices into "Other".

### What we avoid

- Cyber-neon / deep-blue (#0D1117) / purple backgrounds / pure black or white
- CDN dependencies (Playwright offline screenshots go blank) — charts must be pure
  SVG or inline JS
- CSS absolute-positioned data points (precision loss causes overlap) — use SVG
  exact coordinates
- Visual inconsistency across a report series (mixed padding / fonts / bg colors)
- `flex: 1` filling a container when content only covers 40% (large blank areas)
- Gold (#FFD700) on white text (insufficient contrast; use dark gold #D4A017)

### Style selection

*Data-report style* (for HTML visualization reports):

When the user does not specify a style, **randomly choose from these 5** to keep
each output fresh. Briefly tell the user which one you picked.

| Style | Signature elements | Best for |
|---|---|---|
| Financial Times | Salmon-pink background + 4 px blue top bar + serif headlines | Financial analysis, narrative reports |
| McKinsey Consulting | Deep-blue header + Exhibit numbering + conclusion-style titles | Strategic analysis, framework evaluation |
| The Economist | Red thin bar + editorial headline + magazine density | Industry insight, opinion reports |
| Goldman Sachs | Rating badge + gold accent + dense tables | Financial modeling, valuation reports |
| Swiss / NZZ | Black-white-gray-red + 72 px giant type + extreme size contrast | Data display, design-forward reports |

Full specs → `references/report-style-gallery.md`

*Traditional PPT style* (for HTML → PPTX):

| Scenario | Recommended style | Keywords |
|---|---|---|
| Data report / training demo | Neo-Brutalism | Thick borders, color blocks, oversized type, offset shadows |
| Client proposal / external report | Warm Narrative | Rounded cards, warm tones, generous whitespace |
| Quick internal share | Minimal professional | Light gray background, thin lines, restrained information |

PPT style parameters → `references/visual-design-system.md`

*Static HTML PPT style* (for talks / tech sharing): see **Theme selector** below.

### Post-generation self-check

After generating any HTML report / chart / deck:
1. Charts are pure SVG / inline JS? (CDN = screenshot blank screen)
2. SVG annotations stay inside viewBox? (Overflow = cropped)
3. Body text ≥ 10 pt? (Smaller = unreadable when projected)
4. Visual consistency across the series? (padding / fonts / background)
5. Data honesty? (baseline / proportions / tiny-value protection)

---

## Theme system

### Theme selector (3 questions → smart recommendation)

Instead of dumping 36 themes on the user, ask **3 filter questions** and recommend
**1 best + 1 alternative**, explaining why.

**Q1: Who is the audience?**
- Engineers → developer themes (dark, monospace-friendly)
- Executives / Board → professional light themes (clean, conservative)
- Customers / Consumers → warm, approachable themes
- Students → educational or playful themes
- Investors → pitch-optimized themes (big metrics, high contrast)
- Designers → editorial or grid-based themes

**Q2: What is the tone?**
- Serious / Formal → minimal-white, corporate-clean, swiss-grid, academic-paper
- Playful / Creative → soft-pastel, memphis-pop, rainbow-gradient, neo-brutalism
- Technical / Engineering → tokyo-night, dracula, blueprint, terminal-green
- Edgy / Futuristic → cyberpunk-neon, vaporwave, y2k-chrome
- Warm / Human → sunset-warm, editorial-serif, xiaohongshu-white
- Minimal / Zen → japanese-minimal, minimal-white, nord

**Q3: How will it be delivered?**
- Projector / live talk → high-contrast darks (dracula, tokyo-night, catppuccin-mocha)
- Screen share (Zoom) → clean lights (minimal-white, corporate-clean, arctic-cool)
- Self-read / document → eye-comfort lights (solarized-light, catppuccin-latte)
- Mobile / social → vertical-friendly (xiaohongshu-white, soft-pastel)
- Print / PDF → pure whites (minimal-white, corporate-clean, academic-paper)

**Example recommendation:**
> Based on your needs (engineer audience + live talk + technical content),
> I recommend **`tokyo-night`** — deep blue night sky + neon highlights,
> excellent contrast for code and architecture diagrams. It's the default safe
> choice for tech talks.
>
> Alternative: **`catppuccin-mocha`** — warmer dark tones + pastel accents,
> easier on the eyes for long sessions.

Full design-system DNA (philosophy, typography, composition, audience mapping)
→ `references/theme-design-systems.md`

---

## Presenter mode (演讲者模式 + 逐字稿)

If the user mentions any of: **演讲 / 分享 / 讲稿 / 逐字稿 / speaker notes / presenter view / 演讲者视图 / 提词器**, or says things like "我要去给团队讲 xxx", "要做一场技术分享", "怕讲不流畅", "想要一份带逐字稿的 PPT" — **use the `presenter-mode-reveal` full-deck template** and write 150–300 words of 逐字稿 in each slide's `<aside class="notes">`.

See [references/presenter-mode.md](references/presenter-mode.md) for the full authoring guide including the 3 rules of speaker script writing:
1. **不是讲稿，是提示信号** — 加粗核心词 + 过渡句独立成段
2. **每页 150–300 字** — 2–3 分钟/页的节奏
3. **用口语，不用书面语** — "因此"→"所以"，"该方案"→"这个方案"

All full-deck templates support the S key presenter mode (it's built into `runtime.js`). **S opens a new popup window with 4 magnetic cards**:
- 🔵 **CURRENT** — pixel-perfect iframe preview of the current slide
- 🟣 **NEXT** — pixel-perfect iframe preview of the next slide
- 🟠 **SPEAKER SCRIPT** — large-font 逐字稿 (scrollable)
- 🟢 **TIMER** — elapsed time + slide counter + prev/next/reset buttons

Each card is **draggable by its header** and **resizable by the bottom-right corner handle**. Card positions/sizes persist to `localStorage` per deck. A "Reset layout" button restores the default arrangement.

**Why the previews are pixel-perfect**: each preview is an `<iframe>` that loads the actual deck HTML with a `?preview=N` query param; `runtime.js` detects this and renders only slide N with no chrome. So the preview uses the **same CSS, theme, fonts, and viewport as the audience view** — colors and layout are guaranteed identical.

**Smooth navigation**: on slide change, the presenter window sends `postMessage({type:'preview-goto', idx:N})` to each iframe. The iframe just toggles `.is-active` between slides — **no reload, no flicker**. The two windows also stay in sync via `BroadcastChannel`.

Only `presenter-mode-reveal` is designed from the ground up around the feature with proper example 逐字稿 on every slide.

Keyboard in presenter window: `← →` navigate (syncs audience) · `R` reset timer · `Esc` close popup.
Keyboard in audience window: `S` open presenter · `T` cycle theme · `← →` navigate (syncs presenter) · `F` fullscreen · `O` overview.

---

## Content & cognitive load rules

Apply these rules to every deck:

- **Assertion titles.** Every slide title must be a complete sentence stating a
  claim, not a noun phrase. Good: "Caching cut latency by 40%." Bad: "Performance."
- **5/5/5 rule.** ≤5 words per headline line, ≤5 bullets per slide, ≤5 text-heavy
  slides in a row. Alternate text slides with visuals, data, or diagrams.
- **One idea per slide.** If a slide needs 5+ beats to explain, split it into two.
- **Slides complement speech.** Never put full sentences on a slide that you plan
  to read verbatim. The slide shows the claim; your voice adds the evidence.

---

## Lightweight checkpoints

Use 2 checkpoints to catch problems early without slowing down the workflow.

**Checkpoint 1: Outline confirmation**
Present a table before writing any HTML:

| # | Slide title (assertion) | Narrative role | Layout | Notes |
|---|------------------------|----------------|--------|-------|
| 1 | "Our API latency dropped 40% after caching" | Hook | cover | With particle-burst FX |
| 2 | ... | Context | bullets | 3 pain points |

Ask the user to confirm or adjust:
- Slide count (target: 1 minute per slide for live talks)
- Each title is an assertion, not a topic
- Narrative arc flows logically (Hook → Context → Build → Proof → Close)

**Checkpoint 2: Sample confirmation**
Generate 1-2 sample slides with real content before building the full deck.
Show the rendered HTML (or describe it if rendering isn't possible).
Ask: "Does this look/feel right? Adjust theme, layout, or tone before I continue."

Only after both checkpoints are clear, scaffold the full deck and start writing.

---

## Motion & storytelling defaults

**Every deck should have a motion plan, not just animation classes.** When the
user asks for a PPT / slides / talk deck, default to these rules unless they
explicitly want a static, document-like deck.

1. **Think in beats, not slides.** For every slide, decide the 1 core thesis
   and the 2-4 reveal beats that support it. If a slide needs 5+ beats, split
   it into two slides instead of cramming.
2. **Prefer focus shift over endless add-ons.** The current beat should become
   visually primary; previous beats should stay visible but quieter. Don't just
   keep stacking more cards on screen at equal emphasis.
3. **Map motion to narrative role.**
   - Hook / cover → `rise-in`, `blur-in`, one ambient FX at most
   - Build / explain → `fade-up`, `fade-left`, `fade-right`, `stagger-list`
   - Numbers / proof → `counter-up`, `zoom-pop`
   - Compare / contrast → directional entries from opposite sides
   - Land / close → calmer, simpler motion; don't end with chaos
   - Logic / architecture → one node highlighted at a time, with matching
     detail content below or beside it
4. **Use direction semantically.** Left→right should imply process, before→after,
   or layer build-up. Top→down should imply hierarchy. Don't choose directions
   randomly.
5. **One hero motion per slide.** Most slides should have 1 main motion idea
   plus 0-1 support motion. If a slide has 4 unrelated motions, it will feel
   template-driven instead of authored.
6. **For live talks, design reveal rhythm intentionally.** Agenda pages usually
   stagger once; proof/architecture pages may reveal in steps; dense checklists
   often should not require one click per bullet.
7. **If optimizing an existing deck, restructure before animating.** First fix
   the story arc and beat count. Only then add motion.
8. **Account for mobile when relevant.** If the deck is likely to be shown on
   a phone/tablet, reduce simultaneous columns, enlarge tap targets, and add
   swipe/tap navigation if step-based reveals matter.

Load [references/motion-storytelling.md](references/motion-storytelling.md)
whenever the user wants a more talk-like, cinematic, progressive, or
speaker-friendly deck.

For platform, logic, or system-heavy decks, also load
[references/diagram-patterns.md](references/diagram-patterns.md) so the deck
uses the right diagram pattern instead of a generic card grid.
For technical platform decks, also load
[references/system-storytelling-suite.md](references/system-storytelling-suite.md)
to choose from the focused set of architecture / pipeline / layer / sequence
layouts designed for professional system talks.

---

## Image generation capability

This skill is **code-driven first, image-enhanced second**.

| Image role | Generation method | When to use |
|-----------|-------------------|-------------|
| **Cover / hero image** | AI generation (nano-banana / image-this MCP) | When user wants visual impact on opening slide |
| **Concept illustration** | AI generation | Abstract concepts that are hard to draw with code |
| **Data visualization** | ECharts / SVG (code) | Always preferred — offline-safe, editable, precise |
| **Architecture / flow diagrams** | SVG / CSS (code) | Always preferred — scalable, theme-aware |
| **Product screenshots** | User-provided | Factual evidence, not generated |

**Principle**: Generate images only when they add genuine narrative value.
Never use AI images as decoration. Data charts and diagrams should always be
code-rendered (SVG/ECharts) to ensure offline availability, editability, and
consistency with the theme system.

---

## Analysis philosophy

When working with data, reports, or analytics:

### Report writing

- **Conclusion first** — Say whether it's good or bad first, then explain why.
- **Data speaks** — Every claim has data backing it.
- **Actionable specifics** — Recommendations must be directly executable;
  avoid "needs further research."
- **No fluff** — Delete phrases like "in summary" or "it should be noted that."
- Use Chinese full-width quotation marks 「」.

### Analysis output structure

```
Core conclusion (1–3 sentences; management only needs to read this)
→ Data support (specific numbers, comparisons, trends)
→ Anomalies / risks
→ Actionable recommendations (3–5 items, prioritized)
→ Next steps (one step further: what else can be dug into)
```

### Ask when uncertain

- Data field meaning unclear → Misunderstanding a field can skew the entire analysis.
- Analysis dimension choice → Different dimensions yield different conclusions.
- Report audience unclear → A CEO and an execution layer need completely different levels of detail.
- Involves business judgment → AI lacks business context.

---

## Quick start

1. **Scaffold a new deck.** From the repo root:
   ```bash
   ./scripts/new-deck.sh my-talk
   open examples/my-talk/index.html
   ```
2. **Pick a theme.** Open the deck and press `T` to cycle. Or hard-code it:
   ```html
   <link rel="stylesheet" id="theme-link" href="../assets/themes/aurora.css">
   ```
   Catalog in [references/themes.md](references/themes.md).
3. **Pick layouts.** Copy `<section class="slide">...</section>` blocks out of
   files in `templates/single-page/` into your deck. Replace the demo data.
   Catalog in [references/layouts.md](references/layouts.md).
4. **Add animations.** Put `data-anim="fade-up"` (or `class="anim-fade-up"`) on
   any element. On `<ul>`/grids, use `anim-stagger-list` for sequenced reveals.
   For canvas FX, use `<div data-fx="knowledge-graph">...</div>` and include
   `<script src="../assets/animations/fx-runtime.js"></script>`.
   Catalog in [references/animations.md](references/animations.md).
5. **Use a full-deck template.** Copy `templates/full-decks/<name>/` into
   `examples/my-talk/` as a starting point. Each folder is self-contained with
   scoped CSS. Catalog in [references/full-decks.md](references/full-decks.md)
   and gallery at `templates/full-decks-index.html`.
6. **Render to PNG.**
   ```bash
   ./scripts/render.sh templates/theme-showcase.html       # one shot
   ./scripts/render.sh examples/my-talk/index.html 12      # 12 slides
   ```

---

## Authoring rules (important)

- **Always start from a template.** Don't author slides from scratch — copy the
  closest layout from `templates/single-page/` first, then replace content.
- **Plan reveal beats before you animate.** Decide the slide's thesis and
  2-4 beats first. Motion should serve the explanation order.
- **Use tokens, not literal colors.** Every color, radius, shadow should come
  from CSS variables defined in `assets/base.css` and overridden by a theme.
  Good: `color: var(--text-1)`. Bad: `color: #111`.
- **Don't invent new layout files.** Prefer composing existing ones. Only add
  a new `templates/single-page/*.html` if none of the 30 fit.
- **Respect chrome slots.** `.deck-header`, `.deck-footer`, `.slide-number`
  and the progress bar are provided by `assets/base.css` + `runtime.js`.
- **Keyboard-first.** Always include `<script src="../assets/runtime.js"></script>`
  so the deck supports ← → / T / A / F / S / O / hash deep-links.
- **One `.slide` per logical page.** `runtime.js` makes `.slide.is-active`
  visible; all others are hidden.
- **Supply notes.** Wrap speaker notes in `<div class="notes">…</div>` inside
  each slide. Press S to open the overlay.
- **Prefer focus choreography for live talks.** If a slide reveals multiple
  beats, the newest beat should be visually strongest and earlier beats should
  recede. Avoid equal-weight piles of content.
- **Design motion by slide role.** Covers can have one ambient FX; architecture
  and workflow slides benefit from step-by-step build-up; summary slides should
  usually calm down instead of adding more spectacle.
- **For platform/system diagrams, prefer node-focus layouts.** Show the whole
  map, then highlight one node and expand its detail area. This is usually more
  understandable than dumping all node details at once.
- **NEVER put presenter-only text on the slide itself.** Descriptive text like
  "这一页展示了……" or "Speaker: 这里可以补充……" or small explanatory captions
  aimed at the presenter MUST go inside `<div class="notes">`, NOT as visible
  `<p>` / `<span>` elements on the slide. The `.notes` class is `display:none`
  by default — it only appears in the S overlay. Slides should contain ONLY
  audience-facing content (titles, bullet points, data, charts, images).

---

## Writing guide

See [references/authoring-guide.md](references/authoring-guide.md) for a
step-by-step walkthrough: file structure, naming, how to transform an outline
into a deck, how to choose layouts and themes per audience, how to do a
Chinese + English deck, and how to export. For motion-first decks, also load
[references/motion-storytelling.md](references/motion-storytelling.md).

---

## Catalogs (load when needed)

**Design & presentation**

- [references/theme-design-systems.md](references/theme-design-systems.md) — **36 themes with full design-system DNA**: philosophy, emotional intent, typography, composition, visual language, audience mapping, and delivery-mode constraints. Use this to pick themes by worldview, not just color.
- [references/themes.md](references/themes.md) — quick-reference catalog of all 36 themes.
- [references/layouts.md](references/layouts.md) — **31 layouts with narrative roles and content capacity limits**. Use this to match layouts to story beats and avoid cognitive overload.
- [references/animations.md](references/animations.md) — 27 CSS + 20 canvas FX animations.
- [references/full-decks.md](references/full-decks.md) — all 15 full-deck templates.
- [references/narrative-blueprints.md](references/narrative-blueprints.md) — **narrative blueprints for every scenario deck**: per-slide role, layout, animation, timing, and speaker-script length. Use this to structure a deck before writing content.
- [references/presenter-mode.md](references/presenter-mode.md) — **演讲者模式 + 逐字稿编写指南（技术分享/演讲必看）**.
- [references/authoring-guide.md](references/authoring-guide.md) — full workflow.
- [references/motion-storytelling.md](references/motion-storytelling.md) — how to design reveal beats, focus choreography, and talk-like motion.
- [references/diagram-patterns.md](references/diagram-patterns.md) — which diagram/storytelling pattern to use for architecture, flow, timeline, and logic slides.
- [references/system-storytelling-suite.md](references/system-storytelling-suite.md) — curated subset for technical/system/platform presentations.

**Data & analysis**

- [references/report-style-gallery.md](references/report-style-gallery.md) — data-report style library (FT / McKinsey / Economist / GS / Swiss). Colors, fonts, layout rules, and ECharts configs.
- [references/visual-design-system.md](references/visual-design-system.md) — traditional PPT style parameters (Neo-Brutalism, Warm Narrative, Minimal Professional).
- [references/html-templates.md](references/html-templates.md) — HTML visualization templates: KPI dashboard, tables, charts, diagnostic cards, flow diagrams.
- [references/workflows.md](references/workflows.md) — detailed workflows for data analysis, Excel processing, report writing, HTML report generation, and PPT production.
- [references/ad-analytics.md](references/ad-analytics.md) — ad / performance marketing domain knowledge: ROI formulas, dimensions, and heuristics.

---

## File structure

```
html-ppt/
├── SKILL.md                 (this file)
├── references/              (detailed catalogs, load as needed)
├── assets/
│   ├── base.css             (tokens + primitives — do not edit per deck)
│   ├── fonts.css            (webfont imports)
│   ├── runtime.js           (keyboard + presenter + overview + theme cycle)
│   ├── themes/*.css         (36 token overrides, one per theme)
│   └── animations/
│       ├── animations.css   (27 named CSS entry animations)
│       ├── fx-runtime.js    (auto-init [data-fx] on slide enter)
│       └── fx/*.js          (20 canvas FX modules: particles/graph/fireworks…)
├── templates/
│   ├── deck.html                  (minimal 6-slide starter)
│   ├── theme-showcase.html        (36 slides, iframe-isolated per theme)
│   ├── layout-showcase.html       (iframe tour of all 31 layouts)
│   ├── animation-showcase.html    (20 FX + 27 CSS animation slides)
│   ├── full-decks-index.html      (gallery of all 14 full-deck templates)
│   ├── full-decks/<name>/         (14 scoped multi-slide deck templates)
│   └── single-page/*.html         (31 layout files with demo data)
├── scripts/
│   ├── new-deck.sh                (scaffold a deck from deck.html)
│   ├── render.sh                  (headless Chrome → PNG)
│   ├── html2pptx.js               (HTML slide → PPTX conversion engine)
│   ├── build_pptx.js              (multi-page HTML → single PPTX)
│   ├── read_excel.py              (Excel reader: markdown / csv / json output)
│   └── read_pptx.py               (PPTX structure reader)
└── examples/demo-deck/            (complete working deck)
```

---

## Tools & scripts

| Script | Purpose |
|--------|---------|
| `scripts/html2pptx.js` | HTML slide → PPTX conversion engine |
| `scripts/build_pptx.js` | Multi-page HTML → single PPTX |
| `scripts/read_excel.py` | Excel reader (markdown / csv / json output) |
| `scripts/read_pptx.py` | PPTX structure reader |
| `scripts/new-deck.sh` | Scaffold a static HTML deck from deck.html |
| `scripts/render.sh` | Headless Chrome → PNG screenshots |

**Dependencies**

PPT production needs: `pptxgenjs`, `playwright`, `sharp` (Node.js)
Excel analysis needs: `pandas`, `openpyxl` (Python)
Static HTML PPT: Pure static, no build needed, only a browser
Install automatically when missing; never ask the user to do it manually.

**Screenshot one-liner**

```bash
npx playwright screenshot "file:///path/to/file.html" output.png \
  --viewport-size=1200,675 --wait-for-timeout=2000
```

---

## Rendering to PNG

`scripts/render.sh` wraps headless Chrome at
`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`. For multi-slide
capture, runtime.js exposes `#/N` deep-links, and render.sh iterates 1..N.

```bash
./scripts/render.sh templates/single-page/kpi-grid.html        # single page
./scripts/render.sh examples/demo-deck/index.html 8 out-dir    # 8 slides, custom dir
```

---

## Keyboard cheat sheet

```
←  →  Space  PgUp  PgDn  Home  End    navigate
F                                       fullscreen
S                                       open presenter window (magnetic cards: current/next/script/timer)
N                                       quick notes drawer (bottom overlay)
R                                       reset timer (in presenter window)
?preview=N                              URL param — force preview-only mode (single slide, no chrome)
O                                       slide overview grid
T                                       cycle themes (reads data-themes attr)
A                                       cycle demo animation on current slide
#/N in URL                              deep-link to slide N
Esc                                     close all overlays
```

---

## License & author

MIT. Copyright (c) 2026 lewis &lt;sudolewis@gmail.com&gt;.
