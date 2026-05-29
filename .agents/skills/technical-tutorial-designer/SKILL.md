---
name: technical-tutorial-designer
description: Design, refine, and validate technical tutorials as runnable learning experiments. Use when creating or improving course notebooks, technical lessons, demo code, exercises, teaching cases, or student-facing documentation across any technology stack.
---

# Technical Tutorial Designer

Use this skill to turn a technical topic into a student-facing, runnable tutorial. The tutorial must build a concept, carry it with a realistic case, and prove it with executable evidence.

## Core Principle

A technical tutorial is not a knowledge-point article. It is a runnable learning experiment:

1. Build the concept.
2. Create the need through a case.
3. Implement the concept in code.
4. Prove the result with observable output.

## Required Tutorial Structure

Every tutorial should follow this order unless the user explicitly asks for a different format:

1. **Core Concept**: One-sentence definition, problem type it solves, and where it sits in the technical system.
2. **Concept Boundary**: What it is not, common confusions, and when not to use it.
3. **Case Background**: Realistic business or engineering scenario, user questions, and expected workflow.
4. **Design Thinking**: Ask the learner to predict modules, data flow, state, tools, routes, errors, or tradeoffs before implementation.
5. **Data / Environment Setup**: Local reproducible data, dependencies, desensitized samples, and scale.
6. **Naive / Bad Example**: A natural but flawed implementation that exposes the pain point.
7. **Problem Observation**: Use output, numbers, errors, performance, state changes, or complexity to show the issue.
8. **Core Implementation**: Implement the target concept step by step. Code must stay tied to the case.
9. **Runnable Chain**: Execute the full path, not just define functions or classes.
10. **Comparative Output**: Show before/after differences with concrete evidence.
11. **Final Demo + Exercises**: One final cell/block summarizes all key capabilities. Exercises only extend the main concept.

## Writing Rules

- Write for students, not for the author or instructor.
- Do not include author-facing notes in the tutorial body. See `references/checklist.md` for the blocked wording list.
- Do not use toy data when the concept depends on scale, privacy, state, latency, errors, or integration.
- Do not define APIs/tools/classes without running them in a visible chain.
- Prefer one strong concept per lesson. Supporting techniques must serve the main concept.
- The final demo should read like an acceptance report: it must show what worked and the evidence.

## Validation Workflow

Before final handoff:

1. Run the tutorial from a clean state when feasible.
2. Validate structured files: notebooks, JSON, YAML, scripts.
3. Confirm the final demo prints the lesson’s core evidence.
4. Scan for author-facing or instructor-facing wording.
5. Report what was run, key outputs, unresolved risks, and next steps.

For detailed quality gates, read `references/checklist.md`.

For automated checks, run:

```bash
python .agents/skills/technical-tutorial-designer/scripts/validate_tutorial.py <tutorial-path>
```
