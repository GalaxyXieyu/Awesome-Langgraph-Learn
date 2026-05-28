# System storytelling suite

A focused subset of html-ppt for technical talks, architecture reviews, and
platform introductions.

Use this suite when the deck is primarily about:

- system architecture
- request lifecycle
- platform capability layers
- orchestration logic
- service collaboration
- technical strategy / migration / infra design

The suite is designed around one principle:

> show the whole system, then guide the audience through the right part at the right time

## Included patterns

### 1. Node-focus architecture

- **Template:** `templates/single-page/architecture-focus.html`
- **Best for:** platform/system intros, multi-part architecture
- **Narrative role:** “Here is the map. Now let me explain this node.”

### 2. Pipeline-focus flow

- **Template:** `templates/single-page/pipeline-focus.html`
- **Best for:** task pipeline, request chain, workflow explanation
- **Narrative role:** “Here is the path. Now let me zoom into this stage.”

### 3. Layer-stack focus

- **Template:** `templates/single-page/layer-stack-focus.html`
- **Best for:** layered systems, capability stacks, platform strata
- **Narrative role:** “This system is built in layers. This is the layer that matters now.”

### 4. Sequence flow

- **Template:** `templates/single-page/sequence-flow.html`
- **Best for:** message passing, service collaboration, frontend↔backend↔runtime interactions
- **Narrative role:** “This actor talks to that actor, then the result comes back.”

## When to choose which

- If the audience needs a **map of parts** → `architecture-focus`
- If the audience needs a **chain of stages** → `pipeline-focus`
- If the audience needs a **hierarchy of layers** → `layer-stack-focus`
- If the audience needs a **who-talks-to-whom timeline** → `sequence-flow`

## Recommended deck skeleton

For a 10-20 minute technical intro:

```text
cover
→ agenda
→ why this problem becomes a system problem
→ one suite page for the high-level structure
→ one suite page for the request / execution flow
→ one proof page from real code / repo structure
→ one delivery / readiness page
→ summary
```

## Motion defaults for this suite

- Use 1 current focus per beat
- Keep previous context visible but dimmer
- Avoid making every box animate independently
- Use direction semantically:
  - left→right for pipelines
  - top→down for hierarchy
  - row/actor columns for sequence

## Visual defaults for professional technical decks

- Prefer restrained dark or blueprint-like themes:
  - `tokyo-night`
  - `blueprint`
  - `engineering-whiteprint`
  - `corporate-clean`
- Keep labels short and structural
- Prefer 4 major nodes/layers max
- Use the detail panel for explanation, not the node itself

## What this suite avoids

- giant static architecture posters
- every bullet becoming one click
- random motion directions
- equal emphasis on all nodes
- decorative diagrams with no speaking rhythm

## Recommended companion references

- `references/motion-storytelling.md`
- `references/diagram-patterns.md`
- `references/layouts.md`
