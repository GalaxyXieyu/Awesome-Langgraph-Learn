# Motion storytelling guide

How to make a deck feel like a talk, not a template.

## 1. Start from narrative, not animation

For each slide, define:

1. **Thesis** — the one sentence the audience should remember.
2. **Beats** — the 2-4 steps that lead them there.
3. **Focus** — which beat should feel strongest.
4. **Exit state** — what stays on screen before the next slide.

If a slide has no clear thesis, motion will feel random.

If a slide needs more than 4 beats, split it into two slides.

## 2. Slide roles and their motion language

### Hook / cover

- Goal: make the audience lean in.
- Good motion: `rise-in`, `blur-in`, one subtle ambient FX.
- Avoid: too many badges, counters, or multiple simultaneous effects.

### Build / explain

- Goal: guide understanding step by step.
- Good motion: `fade-up`, `fade-left`, `fade-right`, `stagger-list`.
- Use reveal to control *sequence*, not to show off.

### Compare / contrast

- Goal: make two sides legible.
- Good motion: left and right enter from opposite directions.
- Use color/weight to make the contrast obvious.

### Architecture / workflow

- Goal: show how a system is assembled.
- Good motion: reveal layers or stages in order.
- Best pattern: current layer bright, previous layers quieter but still visible.
- Stronger pattern for platform/system talks: **node focus rail + detail panel**.
  Put the main nodes in one row (or one chain), highlight exactly one node per
  beat, and show the detailed explanation / submodules / metrics in a panel
  below or beside it.

### Proof / metrics

- Goal: make evidence feel earned.
- Good motion: `counter-up`, `zoom-pop`, one focused highlight.
- Avoid turning every number into a scoreboard.

### Close / summary

- Goal: land one memorable line.
- Good motion: simpler, calmer, more spacious.
- The ending should feel resolved, not busier than the middle.

## 3. Focus choreography

The most important rule for演讲感:

**New content should not just appear. It should become the center of attention.**

Preferred pattern:

- Current beat = full opacity / stronger border / brighter accent
- Previous beats = still visible, but dimmer and less dominant
- Future beats = hidden

This feels authored.

Weak pattern:

- Beat 1 appears
- Beat 2 appears
- Beat 3 appears
- All three stay at equal weight

That feels like “I added fragments” rather than “I designed a talk”.

## 4. Direction should mean something

Use entry direction to encode meaning:

- **Left → right**: sequence, pipeline, before→after, layer build-up
- **Top → down**: hierarchy, unpacking, zooming into detail
- **Opposite directions**: conflict, comparison, tradeoff
- **Center pop / zoom**: one strong fact, KPI, CTA

Do not assign directions randomly just for variety.

For logic and architecture diagrams, a very effective pattern is:

1. Show the **whole map** first.
2. Highlight **node A**.
3. Expand **node A's detail panel** below.
4. Dim A slightly.
5. Highlight **node B**.
6. Expand **node B's detail panel**.

This makes the audience feel they are walking through the system, not staring
at a flat chart.

## 5. How many clicks should a slide have?

Use this rule of thumb:

- Agenda / TOC: usually 1 stagger, not 5 separate clicks
- Architecture / process: often 3-5 beats
- Code proof / evidence: 2-3 beats
- Dense bullet lists: often should be rewritten, not fragmented

Each click should answer one question:

- What changed in the audience's understanding?

If the answer is “almost nothing”, remove the click.

## 6. When to use ambient FX

Ambient FX can add atmosphere, but only if they support the slide's role.

Good uses:

- Cover / intro: `constellation`, `knowledge-graph`, `gradient-blob`
- System / pipeline / infra: `data-stream`, `chain-react`, `orbit-ring`
- Celebration / landing: `particle-burst`, `confetti-cannon`

Bad uses:

- Adding a running FX to every slide
- Using loud FX behind dense text
- Mixing multiple ambient FX on one slide

Rule:

- Most decks need **0-2** ambient FX slides total.

## 7. Mobile and touch

If the deck may be shown on phone/tablet:

- Reduce columns
- Increase spacing and type size
- Make step reveals reachable by swipe/tap, not keyboard only
- Avoid tiny diagrams that only work on desktop

For mobile live use:

- Swipe left = next beat / next slide
- Swipe right = previous beat / previous slide
- Keep the interaction model consistent

## 8. Optimization checklist for existing decks

When improving an existing deck, do this in order:

1. Rewrite the slide arc.
2. Reduce the number of equal-weight ideas per slide.
3. Decide the beat order.
4. Add focus choreography.
5. Add animation classes.
6. Add ambient FX only if needed.

Never start with step 5.

## 9. A good motion plan template

Before authoring, fill this in:

```md
Slide 1
- Thesis:
- Beat 1:
- Beat 2:
- Beat 3:
- Motion role:
- What should remain visible at the end:

Slide 2
- Thesis:
- Beat 1:
- Beat 2:
- Motion role:
- What should remain visible at the end:
```

## 10. Recommended default behavior for the skill

Unless the user asks for a static report deck:

- Give each slide a thesis.
- Give important slides 2-4 beats.
- Prefer focus shift over endless accumulation.
- Use motion to support explanation order.
- Keep the deck coherent across all slides.

The audience should feel:

> “I was guided through an idea.”

Not:

> “I saw a lot of animated boxes.”

For structure-heavy decks, pair this guide with
[diagram-patterns.md](./diagram-patterns.md).
