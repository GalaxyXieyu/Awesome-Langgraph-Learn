# Narrative Blueprints for Full-Deck Templates

Every full-deck template is more than a visual skin — it is a **narrative scaffold**.
This document provides a blueprint for each scenario deck: the role of every slide,
recommended layout, animation, timing, and speaker-script length.

Use these blueprints as starting points. Adapt them to your content, but preserve
the narrative arc (Hook → Context → Build → Proof → Close) unless you have a
deliberate reason to deviate.

---

## Archetype: Tech Sharing (`tech-sharing`)

**Default audience:** Engineers, technical peers
**Default theme:** `tokyo-night`, `dracula`, `obsidian-claude-gradient`
**Duration:** 15–20 minutes (8 slides × ~2 min each)
**Narrative goal:** Explain a technical concept, demonstrate a solution, prove it works.

| # | Slide | Role | Layout suggestion | Animation | Duration | Script words |
|---|-------|------|-------------------|-----------|----------|--------------|
| 1 | **Cover** | Hook | `cover.html` | `rise-in` + `particle-burst` | 1 min | 150 |
| 2 | **Agenda** | Context | `toc.html` | `stagger-list` | 1 min | 150 |
| 3 | **Problem** | Context | `bullets.html` (3 pain points) | `fade-up` | 2 min | 250 |
| 4 | **Architecture** | Build | `architecture-focus.html` | `fade-up` + step reveals | 3 min | 300 |
| 5 | **Code walkthrough** | Build | `code.html` or `terminal.html` | `fade-up` | 3 min | 300 |
| 6 | **Results** | Proof | `stat-highlight.html` + `kpi-grid.html` | `counter-up` + `zoom-pop` | 2 min | 250 |
| 7 | **Q&A / Next steps** | Plan | `cta.html` | `blur-in` | 1 min | 150 |
| 8 | **Thanks** | Close | `thanks.html` | `rise-in` | 30 sec | — |

**Motion plan:**
- Slides 1–2: One ambient FX (`particle-burst`) on cover only.
- Slides 3–5: Step-by-step build. Each new beat appears with `fade-up`;
  previous beats stay visible but recede (reduce opacity or shrink slightly).
- Slides 6–8: Calm down. No new FX. Let the numbers speak.

**Speaker script rules:**
- Slide 1: State the one-sentence thesis. "Today I'll show you how we cut API latency by 40%."
- Slide 3: Make the pain visceral. "Before caching, p99 was 2.3 seconds. Users were bouncing."
- Slide 5: Walk through code line by line. Don't read the code — explain the *decision* behind each line.
- Slide 6: Pause after the big number. Let it land. "40%. That's the difference between a user staying and leaving."

---

## Archetype: Presenter Mode Reveal (`presenter-mode-reveal`)

**Default audience:** Conference attendees, workshop participants
**Default theme:** `tokyo-night` (T-cycles through 5 themes)
**Duration:** 12–18 minutes (6 slides × ~2–3 min each)
**Narrative goal:** A complete talk with full speaker scripts, designed around the `S` key presenter mode.

| # | Slide | Role | Layout suggestion | Animation | Duration | Script words |
|---|-------|------|-------------------|-----------|----------|--------------|
| 1 | **Hook** | Hook | `cover.html` | `rise-in` + `particle-burst` | 2 min | 200 |
| 2 | **Problem** | Context | `two-column.html` (pain + impact) | `fade-up` | 2 min | 200 |
| 3 | **Solution** | Build | `architecture-focus.html` | `stagger-list` | 3 min | 280 |
| 4 | **Demo / Evidence** | Proof | `code.html` or `terminal.html` | `fade-up` | 3 min | 280 |
| 5 | **Results** | Proof | `stat-highlight.html` | `counter-up` | 2 min | 200 |
| 6 | **Takeaway** | Close | `big-quote.html` | `blur-in` | 2 min | 200 |

**Presenter mode notes:**
- Every slide must have `<aside class="notes">` with 150–300 words of script.
- Script is not a transcript — it's **prompt signals**: bold keywords + transition sentences.
- Practice at 120–150 words/minute. 200 words ≈ 90 seconds of speaking.
- The timer card helps you stay on pace. If you're 30 seconds behind, trim the next slide's script.

**Motion plan:**
- Covers can have one ambient FX.
- Architecture and workflow slides benefit from step-by-step build-up.
- Summary slides should calm down — no new spectacle.

---

## Archetype: Pitch Deck (`pitch-deck`)

**Default audience:** Investors, VCs, accelerators
**Default theme:** `pitch-deck-vc`, `corporate-clean`, `minimal-white`
**Duration:** 10–15 minutes (10 slides × ~1 min each)
**Narrative goal:** Prove investability. Problem → Solution → Traction → Ask.

| # | Slide | Role | Layout suggestion | Animation | Duration | Script words |
|---|-------|------|-------------------|-----------|----------|--------------|
| 1 | **Cover** | Hook | `cover.html` | `rise-in` | 30 sec | — |
| 2 | **Problem** | Context | `bullets.html` (3 pains) | `fade-up` | 1 min | 150 |
| 3 | **Solution** | Build | `two-column.html` (problem → solution) | `fade-left` + `fade-right` | 1 min | 150 |
| 4 | **Market** | Build | `stat-highlight.html` (TAM) | `counter-up` | 1 min | 150 |
| 5 | **Product** | Build | `three-column.html` (3 features) | `stagger-list` | 1.5 min | 200 |
| 6 | **Traction** | Proof | `kpi-grid.html` (4 metrics) | `counter-up` | 1 min | 150 |
| 7 | **Business model** | Build | `chart-pie.html` (revenue mix) | `zoom-pop` | 1 min | 150 |
| 8 | **Team** | Proof | `image-grid.html` (team photos) | `stagger-list` | 1 min | 100 |
| 9 | **Ask** | Plan | `cta.html` | `blur-in` | 1 min | 150 |
| 10 | **Thanks** | Close | `thanks.html` | `rise-in` | 30 sec | — |

**Motion plan:**
- Fast pace. Most slides get one clean animation (`fade-up` or `stagger-list`).
- Numbers slides (4, 6, 7) use `counter-up` to make metrics feel dynamic.
- The "Ask" slide should feel calm and confident — `blur-in` or `fade-up`, nothing chaotic.

**Speaker script rules:**
- Slide 2: Make the problem expensive. "This costs the industry $X billion per year."
- Slide 3: Your solution is the *only* logical next sentence after the problem.
- Slide 6: Traction beats vision. Lead with the most impressive number.
- Slide 9: Be specific. "We're raising $X at $Y valuation for Z purpose."

---

## Archetype: Product Launch (`product-launch`)

**Default audience:** Customers, press, community
**Default theme:** `glassmorphism`, `soft-pastel`, `aurora`
**Duration:** 15–20 minutes (8 slides × ~2 min each)
**Narrative goal:** Build desire, reveal the product, prove it works, drive action.

| # | Slide | Role | Layout suggestion | Animation | Duration | Script words |
|---|-------|------|-------------------|-----------|----------|--------------|
| 1 | **Teaser** | Hook | `image-hero.html` | `rise-in` + `aurora` FX | 1 min | 150 |
| 2 | **Problem** | Context | `bullets.html` | `fade-up` | 2 min | 250 |
| 3 | **Product reveal** | Build | `image-hero.html` or `cover.html` | `zoom-pop` | 2 min | 250 |
| 4 | **Features** | Build | `three-column.html` | `stagger-list` | 2 min | 250 |
| 5 | **Demo** | Build | `terminal.html` or `code.html` | `fade-up` | 3 min | 300 |
| 6 | **Social proof** | Proof | `big-quote.html` | `fade-up` | 1.5 min | 200 |
| 7 | **Pricing** | Plan | `comparison.html` (3 tiers) | `stagger-list` | 1.5 min | 200 |
| 8 | **CTA** | Close | `cta.html` | `blur-in` | 1 min | 150 |

**Motion plan:**
- Slide 1: One ambient FX (`aurora` or `gradient-blob`) sets the mood.
- Slide 3: The reveal is the hero moment. Use `zoom-pop` or `blur-in` for impact.
- Slides 4–5: Step-by-step feature build. Each feature appears sequentially.
- Slides 6–8: Calm down. Let social proof and pricing breathe.

---

## Archetype: Weekly Report (`weekly-report`)

**Default audience:** Manager, team, stakeholders
**Default theme:** `corporate-clean`, `arctic-cool`, `minimal-white`
**Duration:** 5–8 minutes (7 slides × ~1 min each)
**Narrative goal:** Summarize what happened, show metrics, flag risks, preview next week.

| # | Slide | Role | Layout suggestion | Animation | Duration | Script words |
|---|-------|------|-------------------|-----------|----------|--------------|
| 1 | **Title** | Hook | `cover.html` | `rise-in` | 30 sec | — |
| 2 | **KPIs** | Proof | `kpi-grid.html` (4 metrics) | `counter-up` | 1 min | 100 |
| 3 | **Shipped** | Build | `todo-checklist.html` | `stagger-list` | 1 min | 100 |
| 4 | **Trends** | Proof | `chart-line.html` or `chart-bar.html` | `fade-up` | 1 min | 100 |
| 5 | **Risks / blockers** | Context | `pros-cons.html` | `fade-up` | 1 min | 100 |
| 6 | **Next week** | Plan | `roadmap.html` or `timeline.html` | `stagger-list` | 1 min | 100 |
| 7 | **Thanks** | Close | `thanks.html` | `rise-in` | 30 sec | — |

**Motion plan:**
- Minimal animation. This is a utility deck, not a performance.
- Use `counter-up` for KPIs and `stagger-list` for shipped items.
- No FX. Keep it clean and fast.

**Speaker script rules:**
- Slide 2: Lead with the most important metric. Don't read all four — highlight one.
- Slide 5: Be honest about blockers. "Blocked on X, need decision by Y."
- Slide 6: End with ownership. "I'll own A, B owns B, we ship by Friday."

---

## Archetype: Course Module (`course-module`)

**Default audience:** Students, learners, workshop attendees
**Default theme:** `solarized-light`, `catppuccin-latte`, `soft-pastel`
**Duration:** 20–30 minutes (7 slides × ~3 min each)
**Narrative goal:** Teach a concept, check understanding, provide takeaways.

| # | Slide | Role | Layout suggestion | Animation | Duration | Script words |
|---|-------|------|-------------------|-----------|----------|--------------|
| 1 | **Module title** | Hook | `cover.html` | `rise-in` | 1 min | 150 |
| 2 | **Learning objectives** | Context | `bullets.html` (3 objectives) | `stagger-list` | 2 min | 200 |
| 3 | **Concept** | Build | `two-column.html` (concept + example) | `fade-up` | 4 min | 400 |
| 4 | **Deep dive** | Build | `code.html` or `arch-diagram.html` | `fade-up` | 5 min | 500 |
| 5 | **Exercise / Demo** | Build | `terminal.html` or `process-steps.html` | `stagger-list` | 5 min | 400 |
| 6 | **Self-check** | Proof | `pros-cons.html` or custom MCQ | `fade-up` | 2 min | 200 |
| 7 | **Summary** | Close | `three-column.html` (3 takeaways) | `stagger-list` | 1 min | 150 |

**Motion plan:**
- Slides 3–5: Slow, deliberate reveals. Learners need time to process.
- Use `stagger-list` for multi-step explanations — reveal one step at a time.
- Slide 6: Self-check should feel interactive, even in static HTML. Use color-coded feedback.

**Speaker script rules:**
- Slide 2: "By the end of this module, you'll be able to X, Y, and Z."
- Slide 3: Use analogies. "Think of caching like keeping your favorite book on your desk instead of the library."
- Slide 5: Pause after each step. "Try this yourself. I'll wait."
- Slide 7: End with a transferable takeaway. "You can use this pattern in any API, not just ours."

---

## Archetype: Xiaohongshu Post (`xhs-post`)

**Default audience:** Social media readers
**Default theme:** `xiaohongshu-white`, `xhs-pastel-card`, `xhs-white-editorial`
**Duration:** Self-read (9 slides, swipe through)
**Narrative goal:** Share tips, reviews, or lifestyle content in a visually engaging 3:4 format.

| # | Slide | Role | Layout suggestion | Notes |
|---|-------|------|-------------------|-------|
| 1 | **Cover** | Hook | `cover.html` | Big headline, lifestyle image |
| 2 | **Intro** | Context | `big-quote.html` | Personal voice, relatable hook |
| 3 | **Tip 1** | Build | `bullets.html` or `two-column.html` | Numbered, visual |
| 4 | **Tip 2** | Build | `bullets.html` or `two-column.html` | Consistent format |
| 5 | **Tip 3** | Build | `bullets.html` or `two-column.html` | Consistent format |
| 6 | **Before/After** | Proof | `comparison.html` | Visual proof |
| 7 | **Product grid** | Proof | `image-grid.html` | 7-cell bento |
| 8 | **CTA** | Plan | `cta.html` | "Follow for more" |
| 9 | **Profile** | Close | `thanks.html` | Avatar + bio |

**Design notes:**
- 3:4 portrait (810×1080). Text must be readable on mobile.
- Short text. Max 2 sentences per slide.
- Emoji and icons replace bullets.
- No complex animations — users swipe quickly.

---

## Narrative arc cheat sheet

Use this to diagnose any deck's structure:

```
HOOK     → Does the first slide make me care? (emotion, curiosity, stakes)
CONTEXT  → Do I understand the problem/background? (3 points max)
BUILD    → Is the solution/explanation clear? (step-by-step, one idea per slide)
PROOF    → Is there evidence? (numbers, demos, testimonials, before/after)
PLAN     → Do I know what happens next? (roadmap, next steps, CTA)
CLOSE    → Does it end cleanly? (summary, thanks, contact)
```

**Common structural problems:**
- **No Hook →** Audience tunes out before slide 3. Fix: Start with stakes or curiosity.
- **No Proof →** Claims feel empty. Fix: Add one data slide or demo.
- **Build too long →** Audience forgets the problem. Fix: Insert a "recap" slide mid-deck.
- **No Close →** Audience leaves without action. Fix: Always end with a CTA or takeaway.

---

## Per-slide timing formula

For live talks, use this rule of thumb:

| Slide type | Duration | Script words |
|---|---|---|
| Cover / title | 30–60 sec | — |
| Hook / problem | 1–2 min | 150–200 |
| Build / explanation | 2–3 min | 200–300 |
| Proof / data | 1–2 min | 150–200 |
| Plan / CTA | 1 min | 100–150 |
| Thanks | 15–30 sec | — |

**Total deck time = slide count × 1.5 min (average).**
A 10-slide deck ≈ 15 minutes. A 20-slide deck ≈ 30 minutes.

If your allocated time is shorter, cut slides rather than rush each one.
