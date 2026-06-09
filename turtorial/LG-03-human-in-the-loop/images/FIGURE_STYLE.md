# LangGraph course figure style

Use this style for conceptual teaching diagrams in LangGraph lessons.

## Visual direction

- Academic teaching figure, close to NeurIPS / Nature / Science Translational Medicine figure aesthetics.
- White or warm off-white background.
- Soft literature-science palette: muted teal, dusty blue, warm sand, sage green, soft coral accents, slate gray text.
- Thin vector-like arrows, precise alignment, generous whitespace, subtle shadows only.
- No neon, no dark background, no glossy UI, no fake logos, no watermark, no cartoonish characters.
- Labels must be short, readable, and preferably Chinese for student-facing figures.

## Content rules

- Use figures to reduce prose, not decorate prose.
- One figure should carry one cognitive job.
- For concept introduction, show the mismatch: human-world intuition vs Agent/Graph execution model.
- For mechanism explanation, show the minimal flow and only then place API names under the plain-language actions.
- Keep technical names secondary: smaller text under the Chinese concept label.

## SVG vs GPT image

Use editable SVG/Mermaid when:

- Labels must be exact.
- The diagram will be reused in HTML/PPT.
- We expect to revise wording often.
- It explains API or state transitions.

Use GPT image when:

- The figure is a visual hook or Figure 1 style overview.
- The goal is emotional clarity, memorability, or visual polish.
- Text is sparse and can tolerate small imperfections.

Best pattern: SVG first as a precise wireframe, then generate a GPT-polished version from the SVG/prompt if needed.

## Prompt template

```text
Landscape 16:9 academic teaching figure, NeurIPS / Nature-style educational concept diagram, publication-ready, white background, soft literature-science palette, muted teal, dusty blue, warm sand, soft coral accents, thin vector-like arrows, generous whitespace, crisp readable labels, no watermark, no fake logos.

Figure title: "<title>".

Layout: <2-4 panel layout with exact labels>.

Panel A: <human-world intuition>.
Panel B: <Agent/Graph limitation>.
Panel C: <mechanism that bridges the gap>.

Style requirements: refined academic figure, not cartoonish, no 3D, no glossy UI, subtle shadows only, precise layout, all text must be crisp and legible. Keep technical API names smaller than plain-language labels.
```
