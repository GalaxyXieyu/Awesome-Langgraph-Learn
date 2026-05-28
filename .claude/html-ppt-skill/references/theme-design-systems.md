# Theme Design Systems

Each theme in `assets/themes/*.css` is more than a color palette — it is a complete
visual language. This document maps every theme to its design-system DNA:
philosophy, emotional intent, typography, composition, visual language, audience,
and constraints.

Use this guide to pick themes by **worldview** rather than by color.

---

## Quick selector

Answer 3 questions, then see the recommended themes in the **Audience** column.

| Question | Options |
|---|---|
| **Q1: Audience** | Engineers / Executives / Customers / Students / Investors / General public |
| **Q2: Tone** | Serious / Playful / Edgy / Minimal / Warm / Technical |
| **Q3: Delivery** | Live talk (projector) / Screen share / Self-read / Mobile share |

**Decision logic:**
- Live talk + projector → prefer **high contrast** themes (dark bg + bright accent)
- Self-read / mobile → prefer **light bg** themes for eye comfort
- Screen share + code → prefer **developer themes** (catppuccin, dracula, tokyo-night)

---

## Light & calm

### `minimal-white`
- **Philosophy**: Maximum content, minimum chrome. The design disappears so the message dominates.
- **Emotional intent**: Trustworthy, institutional, invisible.
- **Typography**: Inter, strong weight contrast (800 vs 400), tight line-height for headers.
- **Composition**: Centered or left-aligned, generous whitespace, single-column hierarchy.
- **Visual language**: No decoration, no gradients, shadows only for depth on cards.
- **Audience**: Executives, engineers (peer review), academics.
- **Best for**: Internal review, data-heavy reports, architecture docs.
- **Don't use if**: You need emotional engagement or brand personality; this theme is deliberately faceless.

### `editorial-serif`
- **Philosophy**: The magazine page as a presentation. Typography is the image.
- **Emotional intent**: Cultured, authoritative, literary.
- **Typography**: Playfair Display (serif) for headlines, Inter for body. Large size contrast.
- **Composition**: Asymmetric text blocks, pull quotes, generous margins.
- **Visual language**: Cream backgrounds, ink-black text, serif as graphic surface.
- **Audience**: Brand storytellers, publishers, marketers.
- **Best for**: Brand narratives, long-form essays, literary talks.
- **Don't use if**: Heavy data or code; serifs reduce readability for dense technical content.

### `soft-pastel`
- **Philosophy**: Optimism through color. Softness signals approachability.
- **Emotional intent**: Friendly, inviting, light.
- **Typography**: Rounded sans-serif feel, medium weight, slightly larger body text.
- **Composition**: Cards with soft backgrounds, gentle gradients, rounded corners.
- **Visual language**: Macaron color trio (pink, mint, lavender), blurred accent blobs.
- **Audience**: Consumers, students, creative teams.
- **Best for**: Product launches, lifestyle content, onboarding decks.
- **Don't use if**: Serious financial or legal topics; pastels undermine gravitas.

### `xiaohongshu-white`
- **Philosophy**: Social-first aesthetic. White canvas + warm accent = aspirational lifestyle.
- **Emotional intent**: Aspirational, curated, personal.
- **Typography**: Noto Serif SC for headlines (elegant Chinese), warm sans body.
- **Composition**: Vertical-friendly 3:4 ratio, large imagery, short text blocks.
- **Visual language**: Warm red (#E85A4F) accent, cream undertone, lifestyle photography.
- **Audience**: Social media readers, lifestyle consumers, brand KOLs.
- **Best for**: Xiaohongshu/TikTok-style image-text posts, beauty/lifestyle reviews.
- **Don't use if**: B2B technical content or corporate boardrooms.

### `solarized-light`
- **Philosophy**: Reduced eye strain through scientifically tuned contrast.
- **Emotional intent**: Comfortable, enduring, focused.
- **Typography**: Monospace-friendly, medium weight, generous line-height.
- **Composition**: Structured, predictable, left-aligned blocks.
- **Visual language**: Muted teal/blue accent on beige, low saturation palette.
- **Audience**: Developers, long-workshop attendees, educators.
- **Best for**: 2+ hour workshops, code tutorials, teaching materials.
- **Don't use if**: You need visual punch or brand differentiation; this is intentionally neutral.

### `catppuccin-latte`
- **Philosophy**: Developer culture, but make it warm and welcoming.
- **Emotional intent**: Friendly-nerdy, approachable, community.
- **Typography**: Rounded sans, pink/mauve accents on cream.
- **Composition**: Card-based, soft shadows, gentle color coding.
- **Visual language**: Pastel pinks, mauves, sky blues; GitHub-README aesthetic.
- **Audience**: Open-source contributors, indie devs, community talks.
- **Best for**: Developer relations, OSS project intros, community updates.
- **Don't use if**: Executive-facing content; the "cute" palette reads as unserious to non-devs.

---

## Bold & statement

### `sharp-mono`
- **Philosophy**: Black and white are not absence — they are absolute clarity.
- **Emotional intent**: Radical, uncompromising, declarative.
- **Typography**: Archivo Black, extreme weight, uppercase headlines, zero serif.
- **Composition**: Brutal contrast, full-bleed images, hard edges, no gradients.
- **Visual language**: Pure black/white, hard drop shadows, text as architecture.
- **Audience**: Activists, manifesto writers, avant-garde designers.
- **Best for**: Manifestos, bold claims, launch announcements that demand attention.
- **Don't use if**: Nuanced or diplomatic content; this theme shouts.

### `neo-brutalism`
- **Philosophy**: The web should be fun again. Thick borders and hard shadows = playful rebellion.
- **Emotional intent**: Energetic, rebellious, startup-y.
- **Typography**: Bold, slightly irregular, chunky headlines.
- **Composition**: Offset cards, overlapping elements, bright yellow pops.
- **Visual language**: Thick black outlines (#000), hard shadows (4px 4px 0), bright yellow accent.
- **Audience**: Startups, Gen-Z brands, creative agencies.
- **Best for**: Pitch decks for young audiences, product launches, creative portfolios.
- **Don't use if**: Conservative industries (banking, healthcare, government).

### `bauhaus`
- **Philosophy**: Form follows function, but function can be beautiful. Primary colors as logic.
- **Emotional intent**: Intellectual, geometric, historically grounded.
- **Typography**: Geometric sans (circular forms), strong grid alignment.
- **Composition**: Strict grid, circles/triangles/squares as structural elements, red-yellow-blue accents.
- **Visual language**: Primary colors on white, geometric shapes, black rules/lines.
- **Audience**: Designers, art historians, architects, design-system teams.
- **Best for**: Design talks, art history, product-design methodology.
- **Don't use if**: General business audiences may find it too academic or abstract.

### `swiss-grid`
- **Philosophy**: The grid is not a constraint — it is the only honest way to organize information.
- **Emotional intent**: Rational, timeless, authoritative.
- **Typography**: Helvetica/Akzidenz-Grotesk feel, strict baseline grid, 8pt increments.
- **Composition**: 12-column grid visible, everything aligns, zero decorative elements.
- **Visual language**: Black lines on white, flush-left ragged-right, functionalist purity.
- **Audience**: Designers, typographers, serious professionals.
- **Best for**: Design portfolio reviews, typography talks, Swiss-style enthusiasts.
- **Don't use if**: You need warmth or personality; this is ice-cold rationalism.

### `memphis-pop`
- **Philosophy**: More is more. Pattern, color, and playfulness defeat minimalism.
- **Emotional intent**: Fun, chaotic, youthful, confident.
- **Typography**: Bold, large, slightly tilted or irregular.
- **Composition**: Scattered geometric shapes, dots, squiggles as background texture.
- **Visual language**: Memphis Group aesthetic — circles, squiggles, dots, bright primaries on light bg.
- **Audience**: Youth brands, fashion, entertainment.
- **Best for**: Creative pitches, brand collaborations, festival announcements.
- **Don't use if**: Any context requiring restraint or credibility (finance, healthcare, legal).

---

## Cool & dark

### `catppuccin-mocha`
- **Philosophy**: Dark mode for people who don't want to feel like hackers.
- **Emotional intent**: Cozy, inviting, community-belonging.
- **Typography**: Rounded sans, pink/flamingo accents on dark mocha bg.
- **Composition**: Soft cards, gentle hover states, pastel syntax highlighting.
- **Visual language**: Warm dark (#1e1e2e), pastel accents, no harsh neon.
- **Audience**: Developers, Discord communities, cozy-tech enthusiasts.
- **Best for**: Late-night streams, cozy coding talks, community updates.
- **Don't use if**: Bright-room projector use; dark themes wash out on weak projectors.

### `dracula`
- **Philosophy**: The classic dev dark theme, battle-tested for readability.
- **Emotional intent**: Professional, focused, nostalgic.
- **Typography**: Monospace for code, sans for body, strong magenta/green/cyan accents.
- **Composition**: Terminal-like panels, syntax-highlighted blocks, structured hierarchy.
- **Visual language**: Deep purple bg (#282a36), neon accents (pink #ff79c6, green #50fa7b).
- **Audience**: Software engineers, DevOps, SRE, terminal users.
- **Best for**: Code walkthroughs, CLI tool demos, infrastructure talks.
- **Don't use if**: Non-technical audiences find purple terminals alienating.

### `tokyo-night`
- **Philosophy**: Tokyo after midnight — calm, neon, precise.
- **Emotional intent**: Cool, precise, understated power.
- **Typography**: Clean sans, blue/teal accents, restrained.
- **Composition**: Dark blue bg, subtle panel divisions, minimal decoration.
- **Visual language**: Deep navy (#1a1b26), soft blue (#7aa2f7), red accent (#f7768e).
- **Audience**: Backend engineers, infrastructure teams, DevOps.
- **Best for**: API design talks, cloud architecture, backend deep-dives.
- **Don't use if**: Warm/emotional topics; this theme is emotionally cool.

### `nord`
- **Philosophy**: Arctic minimalism. Clarity through restraint and cold colors.
- **Emotional intent**: Calm, trustworthy, Scandinavian.
- **Typography**: Clean sans, moderate weight, excellent readability.
- **Composition**: Structured panels, frosted-glass effects, organized hierarchy.
- **Visual language**: Polar-night darks (#2e3440), frost blues (#88c0d0), snow whites (#d8dee9).
- **Audience**: Nordic developers, cloud-native teams, enterprise engineers.
- **Best for**: Cloud product demos, infrastructure talks, enterprise tooling.
- **Don't use if**: Warm/personal topics; the arctic palette feels clinical.

### `gruvbox-dark`
- **Philosophy**: Retro computing warmth. The terminal as a cozy living room.
- **Emotional intent**: Nostalgic, warm, accessible.
- **Typography**: Monospace for code, warm yellow/blue/green accents.
- **Composition**: Blocky panels, retro cursor effects, earthy backgrounds.
- **Visual language**: Warm dark bg (#282828), muted yellow (#fabd2f), teal (#83a598).
- **Audience**: Vim users, *nix enthusiasts, retro-computing fans.
- **Best for**: Terminal workflows, vintage computing talks, unix philosophy.
- **Don't use if**: Modern/forward-looking brand positioning; this reads as nostalgic.

### `rose-pine`
- **Philosophy**: Nature meets code. Soft dark with floral warmth.
- **Emotional intent**: Artistic, gentle, design-conscious.
- **Typography**: Rounded, soft weight transitions, rose/foam accents.
- **Composition**: Soft panels, gentle rounded corners, warm dark surfaces.
- **Visual language**: Dark rose bg (#191724), foam (#e0def4), pine (#31748f), rose (#ebbcba).
- **Audience**: Designer-developers, creative coders, aesthetic-focused teams.
- **Best for**: Design+code intersection talks, creative coding, aesthetic tooling.
- **Don't use if**: Hardcore technical audiences may find it too "soft".

### `arctic-cool`
- **Philosophy**: Business intelligence as ice. Cold precision for data truth.
- **Emotional intent**: Analytical, rational, trustworthy.
- **Typography**: Clean sans, tight numbers, blue/gray hierarchy.
- **Composition**: Grid-aligned data, card-based metrics, minimal embellishment.
- **Visual language**: White/light gray bg, slate blue (#475569), cyan accent (#06b6d4).
- **Audience**: Analysts, finance, consultants, data scientists.
- **Best for**: Financial reports, data dashboards, business analysis.
- **Don't use if**: Creative or emotional storytelling; this theme suppresses emotion.

---

## Warm & vibrant

### `sunset-warm`
- **Philosophy**: The day ends, but the feeling lingers. Warmth as optimism.
- **Emotional intent**: Optimistic, celebratory, human.
- **Typography**: Friendly sans, warm weight, generous sizing.
- **Composition**: Gradient warmth, soft cards, upward energy.
- **Visual language**: Orange-coral-amber gradient, warm shadows, golden highlights.
- **Audience**: General public, event attendees, team celebrations.
- **Best for**: Award ceremonies, team milestones, year-end reviews, celebratory talks.
- **Don't use if**: Serious warnings or negative news; warmth conflicts with urgency.

---

## Effect-heavy

### `glassmorphism`
- **Philosophy**: Transparency implies honesty — nothing to hide.
- **Emotional intent**: Premium, modern, Apple-esque.
- **Typography**: Light weights, large sizes, generous spacing.
- **Composition**: Floating cards with blur backdrops, depth through transparency.
- **Visual language**: Frosted glass (backdrop-filter: blur), subtle gradients, thin borders.
- **Audience**: Product managers, Apple ecosystem users, premium brands.
- **Best for**: Product feature reveals, iOS/Android app showcases, premium services.
- **Don't use if**: Older browsers, weak GPUs (blur is expensive), print (transparency breaks).

### `aurora`
- **Philosophy**: Nature's light show as digital background. Atmosphere over information.
- **Emotional intent**: Dreamy, expansive, awe-inspiring.
- **Typography**: Light, large, spaced-out — text must compete with the background.
- **Composition**: Full-bleed gradients, minimal content, maximum impact.
- **Visual language**: Flowing green-purple-blue gradients, heavy blur, high saturation.
- **Audience**: Creative directors, brand launches, visionary keynotes.
- **Best for**: Cover slides, closing slides, visionary statements, one-word headlines.
- **Don't use if**: Content-heavy pages; the background fights with text readability.

### `rainbow-gradient`
- **Philosophy**: Joy is a spectrum. Maximum positivity through maximum color.
- **Emotional intent**: Joyful, inclusive, celebratory.
- **Typography**: Bold, playful, slightly irregular.
- **Composition**: White bg with rainbow accent flows, cheerful cards.
- **Visual language**: Flowing rainbow gradient strip, bright accents on clean white.
- **Audience**: Children, educators, Pride events, inclusive brands.
- **Best for**: Celebrations, diversity initiatives, education, joyful announcements.
- **Don't use if**: Serious or somber topics; rainbows signal levity.

### `blueprint`
- **Philosophy**: The engineer's truth is in the drawing. Precision as beauty.
- **Emotional intent**: Technical, authoritative, constructed.
- **Typography**: Monospace or engineering sans, precise sizing.
- **Composition**: Grid lines visible, measurements implied, structured blocks.
- **Visual language**: Blue background (#1e3a5f), white lines (grid + borders), technical drawings.
- **Audience**: Engineers, architects, system designers.
- **Best for**: System architecture, API documentation, engineering proposals.
- **Don't use if**: Non-technical audiences; blueprints feel exclusive to engineering.

### `terminal-green`
- **Philosophy**: The command line is the only honest interface.
- **Emotional intent**: Underground, retro, hacker-cool.
- **Typography**: Strict monospace, glowing text, CRT scanlines.
- **Composition**: Terminal window frames, prompt lines, command outputs.
- **Visual language**: Black bg (#0c0c0c), phosphor green (#33ff00), glow effects, scanlines.
- **Audience**: Hackers, security researchers, retro-computing enthusiasts.
- **Best for**: Security talks, CLI demos, retro-gaming, CTF writeups.
- **Don't use if**: Corporate stakeholders; green-on-black reads as unprofessional to non-technical execs.

---

## v2 additions

### Light & professional

### `corporate-clean`
- **Philosophy**: Trust through restraint. The absence of risk signals professionalism.
- **Emotional intent**: Reliable, institutional, conservative.
- **Typography**: Inter, conservative sizes, navy + black hierarchy.
- **Composition**: Bordered cards, conservative spacing, predictable structure.
- **Visual language**: Pure white, navy blue (#1e3a8a), thin borders, minimal decoration.
- **Audience**: Board members, B2B buyers, financial institutions, enterprise.
- **Best for**: Board presentations, B2B sales, quarterly earnings, compliance reviews.
- **Don't use if**: You need to stand out or be memorable; this theme is intentionally forgettable (which is the point).

### `pitch-deck-vc`
- **Philosophy**: Y Combinator distilled — clarity + ambition in equal measure.
- **Emotional intent**: Ambitious, credible, investable.
- **Typography**: Large metrics (60pt+), tight subheadings, generous whitespace.
- **Composition**: Hero metric slides, problem/solution framing, traction proof.
- **Visual language**: White bg, blue-purple gradient accent, massive numbers, clean lines.
- **Audience**: Venture capitalists, angel investors, startup accelerators.
- **Best for**: Seed/Series A pitches, Demo Day, investor updates.
- **Don't use if**: Post-revenue corporate sales; VCs expect different signals than procurement teams.

### `academic-paper`
- **Philosophy**: Knowledge speaks for itself. The design is the absence of design.
- **Emotional intent**: Scholarly, rigorous, timeless.
- **Typography**: Serif for body (readable at length), sans for headers, blue for links.
- **Composition**: Single-column text, figures with captions, footnotes.
- **Visual language**: White paper, black ink, blue citations, minimal headers.
- **Audience**: Academics, researchers, scientists, peer reviewers.
- **Best for**: Conference presentations, thesis defenses, journal clubs, research seminars.
- **Don't use if**: Business audiences; the academic aesthetic signals "not actionable."

### `japanese-minimal`
- **Philosophy**: Ma — the power of the space between things. Silence as statement.
- **Emotional intent**: Contemplative, refined, zen.
- **Typography**: Noto Serif SC, extremely large whitespace, text as island.
- **Composition**: Vast emptiness, centered or isolated text blocks, single accent.
- **Visual language**: Ivory white, vermillion red (#c43e3a), ink black, gold accents.
- **Audience**: Luxury brands, artisans, meditation/wellness, Japanese culture enthusiasts.
- **Best for**: Brand philosophy, craftsmanship stories, cultural narratives.
- **Don't use if**: Content-heavy or fast-paced talks; this theme demands slow contemplation.

### `engineering-whiteprint`
- **Philosophy**: The whiteprint is the blueprint's honest twin — no darkness to hide flaws.
- **Emotional intent**: Precise, transparent, architectural.
- **Typography**: Monospace for specs, engineering sans for headers.
- **Composition**: Coordinate grid visible, measurement labels, structured blocks.
- **Visual language**: White bg, navy grid lines, technical annotations, dimension marks.
- **Audience**: Engineers, architects, technical PMs.
- **Best for**: System design docs, architecture reviews, API specifications.
- **Don't use if**: Non-technical audiences; the grid and annotations feel like noise to them.

---

### Bold & editorial

### `magazine-bold`
- **Philosophy**: The page is a poster. Typography is the image, the image is typography.
- **Emotional intent**: Confident, editorial, fashion-forward.
- **Typography**: Playfair Display at massive sizes, orange spot color, tight leading.
- **Composition**: Asymmetric, text overlapping images, bold hierarchy.
- **Visual language**: Cream bg, oversized serif headlines, orange spot (#e85d04), editorial photography.
- **Audience**: Magazine editors, fashion brands, creative directors.
- **Best for**: Cover stories, brand editorials, creative portfolios.
- **Don't use if**: Data or code-heavy content; the editorial aesthetic fights with technical density.

### `news-broadcast`
- **Philosophy**: Urgency through visual language. Red means "pay attention now."
- **Emotional intent**: Urgent, authoritative, breaking.
- **Typography**: Oswald uppercase, condensed, bold. All-caps headlines.
- **Composition**: Red vertical bars, hard shadows, ticker-like elements.
- **Visual language**: White bg, red (#cc0000) vertical rules, black uppercase text, hard shadows.
- **Audience**: Journalists, PR teams, crisis communicators, newsrooms.
- **Best for**: Breaking news, press releases, crisis communications, urgent announcements.
- **Don't use if**: Calm or positive topics; the urgency aesthetic creates false alarm.

### `midcentury`
- **Philosophy**: The 1950s knew how to balance optimism with geometry.
- **Emotional intent**: Retro-optimistic, design-literate, warm.
- **Typography**: Geometric sans, medium weight, slightly rounded.
- **Composition**: Sharp geometric shapes, three-color palette, sunburst motifs.
- **Visual language**: Cream bg, mustard (#e9c46a), teal (#2a9d8f), burnt orange (#e76f51).
- **Audience**: Designers, home enthusiasts, vintage brands.
- **Best for**: Design history, mid-century modern topics, retro brand campaigns.
- **Don't use if**: Ultra-modern tech positioning; the retro aesthetic creates temporal confusion.

### `retro-tv`
- **Philosophy**: Nostalgia is a design material. The CRT screen as emotional trigger.
- **Emotional intent**: Nostalgic, warm, playful.
- **Typography**: Pixel or monospace hints, slight blur, amber/orange glow.
- **Composition**: Rounded corners (TV screen), scanline overlay, warm vignette.
- **Visual language**: Warm cream, CRT scanlines, amber (#ff9f1c) accent, rounded frame.
- **Audience**: Millennials/Gen-Z nostalgia, gaming, retro computing.
- **Best for**: Retro gaming talks, 80s/90s culture, vintage tech retrospectives.
- **Don't use if**: Forward-looking or futuristic content; the retro frame contradicts the message.

---

### Effect-heavy / dramatic

### `cyberpunk-neon`
- **Philosophy**: The future is already here — it's just unevenly distributed. Neon as rebellion.
- **Emotional intent**: Rebellious, futuristic, underground.
- **Typography**: JetBrains Mono, glowing text, glitch effects.
- **Composition**: Dark void with neon highlights, asymmetric, chaotic energy.
- **Visual language**: Pure black, neon pink (#ff00ff), cyan (#00ffff), yellow (#ffff00), glow + bloom.
- **Audience**: Hackers, cyberpunk fans, futurists, underground culture.
- **Best for**: Security cons, hackathon pitches, futuristic product reveals, cyberpunk talks.
- **Don't use if**: Corporate stakeholders; neon reads as unprofessional to traditional business.

### `vaporwave`
- **Philosophy**: The past's future never arrived. A E S T H E T I C as coping mechanism.
- **Emotional intent**: Ironic, dreamy, nostalgic-futuristic.
- **Typography**: Italic, spaced-out, retro-futuristic fonts.
- **Composition**: Deep perspective grids, statues, palm trees, sunsets.
- **Visual language**: Deep purple (#2d1b4e), pink (#ff6ac1), cyan (#00f0ff), gradient blobs, Greek statues.
- **Audience**: Music culture, internet art, Gen-Z irony, creative communities.
- **Best for**: Music talks, art culture, internet history, ironic/surreal presentations.
- **Don't use if**: Any context requiring sincerity; vaporwave signals irony and detachment.

### `y2k-chrome`
- **Philosophy**: The millennium's optimism about technology, materialized in chrome and rainbow.
- **Emotional intent**: Playful, tech-optimistic, Gen-Z retro.
- **Typography**: Space Grotesk, rounded, slightly futuristic.
- **Composition**: Rounded cards, chrome gradients, rainbow accents, bubbly shapes.
- **Visual language**: Silver chrome gradients, rainbow accents, rounded corners (16px+), bubble motifs.
- **Audience**: Gen-Z, fashion brands, tech optimists.
- **Best for**: Fashion tech, Gen-Z marketing, millennium nostalgia, playful product launches.
- **Don't use if**: Serious B2B contexts; chrome and rainbows signal consumer/playful.

---

## Theme selection matrix

Use this table for quick decision-making based on audience + tone.

| Audience | Serious tone | Playful tone | Technical tone | Minimal tone |
|---|---|---|---|---|
| **Engineers** | tokyo-night, nord | catppuccin-mocha, gruvbox-dark | dracula, blueprint | minimal-white, solarized-light |
| **Executives** | corporate-clean, pitch-deck-vc | sunset-warm | arctic-cool | swiss-grid, minimal-white |
| **Customers** | soft-pastel, xiaohongshu-white | memphis-pop, rainbow-gradient | — | minimal-white, soft-pastel |
| **Students** | academic-paper | neo-brutalism, memphis-pop | terminal-green, blueprint | solarized-light |
| **Investors** | pitch-deck-vc, corporate-clean | — | arctic-cool | minimal-white, pitch-deck-vc |
| **Designers** | swiss-grid, bauhaus | memphis-pop, vaporwave | blueprint | japanese-minimal, minimal-white |
| **General public** | editorial-serif | rainbow-gradient, sunset-warm | — | minimal-white, soft-pastel |

---

## Delivery-mode constraints

| Delivery | Recommended themes | Avoid |
|---|---|---|
| **Projector / live talk** | High contrast darks: dracula, tokyo-night, cyberpunk-neon, catppuccin-mocha | Light themes with subtle contrast: solarized-light, soft-pastel |
| **Screen share (Zoom/Teams)** | All themes work; prefer clean: minimal-white, corporate-clean, arctic-cool | Heavy effects: glassmorphism, aurora (blur lags on video) |
| **Self-read / document** | Light themes for eye comfort: minimal-white, editorial-serif, solarized-light, catppuccin-latte | Dark themes for long reading strain |
| **Mobile / social share** | xiaohongshu-white, soft-pastel, rainbow-gradient | Complex grids: swiss-grid, bauhaus (don't scale down well) |
| **Print / PDF export** | Minimal-white, corporate-clean, academic-paper | Dark themes (ink-heavy), glassmorphism (transparency breaks) |
