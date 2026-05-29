# Technical Tutorial Quality Checklist

Use this checklist when creating or refining a technical tutorial.

## Structure Gates

- The tutorial starts by building the core concept before overloading the learner with case details.
- The case is realistic enough to make the concept necessary.
- The learner sees a design question before seeing the finished implementation.
- The bad example is runnable or safely observable, and it does not block the rest of the tutorial.
- The correct implementation directly resolves the observed problem.
- The runnable chain executes the capability end to end.
- The final demo summarizes the key concept in one place.
- Exercises stay within the lesson’s concept boundary.

## Evidence Gates

Each lesson needs observable proof. Choose evidence that matches the concept:

- Data/state concepts: print state keys, state size, accumulated records, or before/after state.
- Routing/edge concepts: print selected route, condition values, and final path.
- Tool/API concepts: print tool calls, returned summaries, full raw-data location, and error handling.
- Context-management concepts: print raw character/token pressure, clipped result size, and pass-through storage.
- Cache concepts: print hits/misses before and after repeated calls.
- Performance concepts: print timing, request count, batch size, or concurrency behavior.
- Security/privacy concepts: print redacted samples and confirm sensitive fields are not emitted.

## Data Gates

- Use local data where possible so the tutorial can run without external services.
- Use desensitized data for people, IDs, phones, addresses, tokens, or internal records.
- Data volume must be large enough to trigger the problem being taught.
- Record scale in output: counts, bytes/chars, rows, files, or graph nodes.
- If external APIs or model keys are optional, gate them behind environment checks.

## Student-Facing Writing Gates

Avoid author-facing language:

- 学员
- 课堂
- 讲师
- 老师
- 同学
- 读者
- 适合教学
- 更适合教学
- 这里要
- 先让
- 你可以直接告诉
- 为什么这样设计

Preferred style:

- “本节先建立……”
- “观察下面的输出……”
- “这个实现会产生……”
- “运行后可以看到……”
- “最终输出证明……”

## Notebook Gates

- All code cells run from a clean kernel, or skipped external cells clearly state why.
- The final demo cell does not depend on hidden manual state outside earlier cells.
- The notebook does not print huge raw payloads in full; it prints size plus small samples.
- Bad examples print truncated previews and numeric pressure.
- Long-running or paid API calls are optional.

## Final Handoff Gates

Report:

- Files changed.
- Validation commands run.
- Key final-demo outputs.
- Known risks, if any.
- Follow-up tasks, if any.

