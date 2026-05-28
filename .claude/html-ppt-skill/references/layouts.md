# Layouts catalog

Every layout lives in `templates/single-page/<name>.html` as a fully
functional standalone page with realistic demo data. Open any file directly
in Chrome to see it working.

To compose a new deck: open the file, copy the `<section class="slide">…</section>`
block (or multiple blocks) into your deck HTML, and replace the demo data.
Shared CSS (base, theme, animations) is already wired by `deck.html`.

---

## Narrative roles & content capacity

Every layout has a **narrative role** — its function in the story arc — and a
**content capacity** — how much information it can hold before cognitive overload.

**Assertion title rule:** Every slide title should be a complete assertion sentence,
not a noun phrase. Good: "Q3 latency dropped 40% after caching." Bad: "Q3 Performance."

### Content capacity legend

| Constraint | Meaning |
|---|---|
| **Low** | 1 headline + 1 lede sentence. Use for impact, not information. |
| **Medium** | 3–4 bullet points, or 1 headline + 2 supporting points. |
| **High** | Dense data: tables, charts, multi-column comparisons. Still obey 5/5/5. |
| **Visual** | Image/diagram-heavy; text plays supporting role. |

### Narrative role legend

| Role | Function | Typical position |
|---|---|---|
| **Hook** | Grab attention, set emotional tone | Opening |
| **Context** | Establish background, problem, or stakes | Early |
| **Build** | Present argument, solution, or explanation | Middle |
| **Proof** | Data, evidence, validation | Middle-late |
| **Contrast** | Compare before/after, pros/cons, options | Middle |
| **Plan** | Roadmap, timeline, sequence | Late-middle |
| **Close** | Summarize, call to action, gratitude | End |
| **Transition** | Bridge between sections | Any section boundary |

---

## Openers & transitions

| file | purpose | narrative role | capacity |
|---|---|---|---|
| `cover.html` | Deck cover. Kicker + huge title + lede + pill row. | **Hook** | Low |
| `toc.html` | Table of contents. 2×3 grid of numbered cards. | **Context** | Medium |
| `section-divider.html` | Big numbered section break (02 · Theme). | **Transition** | Low |

## Text-centric

| file | purpose | narrative role | capacity |
|---|---|---|---|
| `bullets.html` | Classic bullet list with card-wrapped items. | **Build** | Medium |
| `two-column.html` | Concept + example side by side. | **Build** | Medium |
| `three-column.html` | Three equal pillars with icons. | **Build** | Medium |
| `big-quote.html` | Full-bleed pull quote in editorial-serif style. | **Hook / Close** | Low |

## Numbers & data

| file | purpose | narrative role | capacity |
|---|---|---|---|
| `stat-highlight.html` | One giant number + subtitle (uses `.counter` animation). | **Proof** | Low |
| `kpi-grid.html` | 4 KPIs in a row with up/down deltas. | **Proof** | Medium |
| `table.html` | Data table with hover rows, right-aligned numerics. | **Proof** | High |
| `chart-bar.html` | Chart.js bar chart, theme-aware colors. | **Proof** | Medium |
| `chart-line.html` | Chart.js dual-line chart with filled area. | **Proof** | Medium |
| `chart-pie.html` | Chart.js doughnut + takeaways card. | **Proof** | Medium |
| `chart-radar.html` | Chart.js radar comparing 2 products on 6 axes. | **Contrast** | Medium |

## Code & terminal

| file | purpose | narrative role | capacity |
|---|---|---|---|
| `code.html` | Syntax-highlighted code via highlight.js (JS example). | **Build** | High |
| `diff.html` | Hand-rolled +/- diff view. | **Contrast** | Medium |
| `terminal.html` | Terminal window mock with traffic-light header. | **Build** | Medium |

## Diagrams & flows

| file | purpose | narrative role | capacity |
|---|---|---|---|
| `flow-diagram.html` | 5-node pipeline with arrows and one highlighted node. | **Build** | Medium |
| `arch-diagram.html` | 3-tier architecture grid. | **Build** | High |
| `architecture-focus.html` | Top-row node rail + focused detail panel below; good for逐个讲解架构节点. | **Build** | Medium |
| `pipeline-focus.html` | Stage-by-stage pipeline with focused detail panel; good for请求链路/工作流讲解. | **Build** | Medium |
| `layer-stack-focus.html` | Layered stack with one active layer and a detail panel; good for平台分层/能力栈讲解. | **Build** | Medium |
| `sequence-flow.html` | Multi-actor message sequence with focused interaction panel; good for前后端/服务协同时序说明. | **Build** | Medium |
| `process-steps.html` | 4 numbered steps in cards. | **Plan / Build** | Medium |
| `mindmap.html` | Radial mindmap with SVG path-draw animation. | **Context** | Medium |

## Plans & comparisons

| file | purpose | narrative role | capacity |
|---|---|---|---|
| `timeline.html` | 5-point horizontal timeline with dots. | **Plan** | Medium |
| `roadmap.html` | 4-column NOW / NEXT / LATER / VISION. | **Plan** | Medium |
| `gantt.html` | 12-week gantt chart with 5 parallel tracks. | **Plan** | High |
| `comparison.html` | Before vs After two-panel card. | **Contrast** | Medium |
| `pros-cons.html` | Pros and cons two-card layout. | **Contrast** | Medium |
| `todo-checklist.html` | Checklist with checked/unchecked states. | **Plan / Build** | Medium |

## Visuals

| file | purpose | narrative role | capacity |
|---|---|---|---|
| `image-hero.html` | Full-bleed hero with Ken Burns gradient background. | **Hook** | Visual |
| `image-grid.html` | 7-cell bento grid with gradient placeholders. | **Build / Proof** | Visual |

## Closers

| file | purpose | narrative role | capacity |
|---|---|---|---|
| `cta.html` | Call-to-action with big gradient headline + buttons. | **Close** | Low |
| `thanks.html` | Final "Thanks" page with confetti burst. | **Close** | Low |

## Picking a layout

- **Opener**: `cover.html`, often followed by `toc.html`.
- **Section break**: `section-divider.html` before every major section.
- **Core content**: `bullets.html`, `two-column.html`, `three-column.html`.
- **Show numbers**: `stat-highlight.html` (single) or `kpi-grid.html` (4-up).
- **Show plot**: `chart-bar.html` / `chart-line.html` / `chart-pie.html` / `chart-radar.html`.
- **Show a diff or change**: `comparison.html`, `diff.html`, `pros-cons.html`.
- **Show a plan**: `timeline.html`, `roadmap.html`, `gantt.html`, `process-steps.html`.
- **Show architecture**: `arch-diagram.html`, `architecture-focus.html`, `flow-diagram.html`, `pipeline-focus.html`, `layer-stack-focus.html`, `sequence-flow.html`, `mindmap.html`.
- **Code / demo**: `code.html`, `terminal.html`.
- **Closer**: `cta.html` → `thanks.html`.

## Content capacity rules (cognitive load management)

The **5/5/5 rule** governs all layouts:

1. **≤5 words per line** for headlines — force brevity.
2. **≤5 bullet points per slide** — if you need more, split into two slides.
3. **≤5 text-heavy slides in a row** — alternate with visuals, data, or diagrams.

**Per-layout capacity limits:**

| Layout | Max bullets | Max words/title | Notes |
|---|---|---|---|
| `cover.html` | 0 (use lede only) | 8 words | One headline + one sentence max |
| `bullets.html` | 4 | 12 words | Each bullet ≤2 lines |
| `two-column.html` | 3 per column | 10 words | Balance both columns |
| `three-column.html` | 2 per column | 8 words | Icons help, text must be minimal |
| `stat-highlight.html` | 0 | 10 words | One number + one sentence |
| `kpi-grid.html` | 0 | N/A | 4 KPIs max; each label ≤4 words |
| `table.html` | N/A | N/A | Max 6 rows × 4 columns; right-align numbers |
| `chart-*.html` | 2 takeaways | 10 words | Chart does the talking |
| `timeline.html` | 5 nodes | 8 words/node | Each node: time + event + result |
| `roadmap.html` | 4 columns | 8 words/column | NOW/NEXT/LATER/VISION |
| `comparison.html` | 3 per side | 10 words | Before vs After, equal weight |
| `process-steps.html` | 4 steps | 8 words/step | Numbered, sequential |
| `image-hero.html` | 0 | 6 words | Image dominates; text is caption |
| `big-quote.html` | 0 | 30 words total | One quote + attribution |

**One idea per slide.** If a slide needs 5+ beats to explain, split it into two slides.
Slides complement speech; they never duplicate it.

## Story arc: composing a deck

A well-structured deck follows a narrative arc. Map layouts to roles:

```
HOOK      → cover.html (impact) + optional image-hero.html
CONTEXT   → toc.html + section-divider.html
BUILD     → bullets.html, two-column.html, three-column.html,
            process-steps.html, flow-diagram.html
PROOF     → stat-highlight.html, kpi-grid.html, chart-*.html,
            comparison.html, diff.html
PLAN      → timeline.html, roadmap.html, gantt.html, todo-checklist.html
CONTRAST  → comparison.html, pros-cons.html, chart-radar.html
CLOSE     → cta.html + thanks.html
```

**Typical arc for a 10-slide deck:**
| # | Role | Layout | Notes |
|---|---|---|---|
| 1 | Hook | cover.html | One big idea |
| 2 | Context | bullets.html | 3 problems or 3 contexts |
| 3 | Build | two-column.html | Problem → Solution |
| 4 | Build | architecture-focus.html | How it works |
| 5 | Proof | stat-highlight.html | One killer metric |
| 6 | Proof | chart-bar.html | Trend over time |
| 7 | Contrast | comparison.html | Before vs After |
| 8 | Plan | timeline.html | Rollout plan |
| 9 | Close | cta.html | What to do next |
| 10 | Close | thanks.html | Contact / Q&A |

## Naming / structure conventions

- Each slide is `<section class="slide" data-title="...">`.
- Header pills: `<p class="kicker">…</p>`, eyebrow: `<p class="eyebrow">…</p>`.
- Titles: `<h1 class="h1">…</h1>` / `<h2 class="h2">…</h2>`.
- Lede: `<p class="lede">…</p>`.
- Cards: `<div class="card">…</div>` (variants: `card-soft`, `card-outline`, `card-accent`).
- Grids: `.grid.g2`, `.grid.g3`, `.grid.g4`.
- Notes: `<div class="notes">…</div>` per slide.
