# Diagram patterns

How to choose the right logic / architecture / process diagram for a deck.

The goal is not “draw a chart”. The goal is:

- show structure clearly
- guide attention in the order you speak
- keep detail attached to the currently discussed node

## 1. Node-focus architecture

**Use when:** you are explaining a platform, system stack, layered product, or
multi-part architecture.

**Pattern:**

- top row or map shows all major nodes
- one node is highlighted at a time
- a detail panel below or beside explains that node
- previous nodes stay visible but quieter

**Why it works:**

- the audience always knows where they are in the map
- detail stays attached to the right node
- it feels like walking through a system instead of reading a poster

**Use templates:**

- `templates/single-page/architecture-focus.html`
- `templates/single-page/arch-diagram.html` for a simpler static version
- `templates/single-page/layer-stack-focus.html` if the system is best explained as vertical layers

**Best for:**

- platform intros
- enterprise system architecture
- backend/frontend/runtime/data layer talks

## 2. Pipeline-focus flow

**Use when:** you are explaining request lifecycle, workflow orchestration,
ETL/data flow, or task execution.

**Pattern:**

- a horizontal chain of 4-6 stages
- one stage highlighted
- detail panel shows input / action / output / risk

**Why it works:**

- the audience understands sequence immediately
- each stage can be unpacked without redrawing the flow
- ideal for “how one request moves through the system”

**Use templates:**

- `templates/single-page/pipeline-focus.html`
- `templates/single-page/flow-diagram.html` for a lighter static version
- `templates/single-page/sequence-flow.html` if the key story is actor-to-actor interaction

**Best for:**

- request lifecycle
- task pipeline
- AI agent execution chain
- user journey through a backend

## 3. Layer build-up

**Use when:** the key story is “the system is built from these layers”.

**Pattern:**

- layers appear one by one
- each new layer lands above / beside earlier layers
- previous layers remain visible as the foundation

**Why it works:**

- communicates hierarchy and dependency
- good for infra/platform/developer tool talks

**Use templates:**

- `arch-diagram.html`
- `layer-stack-focus.html`
- custom composition from `section-divider.html` + `architecture-focus.html`

## 4. Before/after contrast

**Use when:** the story is change, improvement, migration, or tradeoff.

**Pattern:**

- left side enters from left, right side enters from right
- one strong contrast headline
- 2-4 differences max

**Use templates:**

- `comparison.html`
- `pros-cons.html`
- `diff.html`

## 5. Timeline spotlight

**Use when:** the audience needs temporal understanding rather than structure.

**Pattern:**

- show the whole timeline
- highlight current milestone
- explain why it matters now

**Use templates:**

- `timeline.html`
- `roadmap.html`
- `gantt.html`

## 6. Mindmap / concept graph

**Use when:** the story is category spread, relationship web, or concept map.

**Pattern:**

- central concept first
- nearby clusters next
- outer edges last

**Use templates:**

- `mindmap.html`
- combine with `data-fx="knowledge-graph"` very sparingly

## 7. Which pattern should I pick?

Use this quick rule:

- **System with parts** → node-focus architecture
- **Process with stages** → pipeline-focus flow
- **Stack with dependencies** → layer build-up
- **Interaction between actors/services** → sequence flow
- **Change or tradeoff** → before/after contrast
- **Time-based plan** → timeline spotlight
- **Relationship web** → mindmap / concept graph

## 8. Professional-looking defaults

For architecture and logic diagrams:

- 4 major nodes is usually better than 7
- 1 highlighted node per beat
- 2-4 detail bullets/cards below
- directional flow should mean something
- keep labels short and structural

Avoid:

- huge walls of detail inside every node
- equal emphasis everywhere
- too many arrows crossing each other
- making every box animate independently

## 9. Motion guidance for diagrams

- show the full map first if the audience needs orientation
- then highlight the active node/stage
- reveal detail panel after focus is established
- dim previous nodes slightly, don't remove them entirely
- use one ambient FX at most, and usually only on cover/intros

The audience should feel:

> I know where we are in the system, and I know why this node matters now.
