#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

const plan = {
  'LG-01-basics': [
    ['LG-01-2-state-flow', 'State 流转示意', 4],
    ['LG-01-3-build-steps', '五步构建流程', 7],
    ['LG-01-1-weatherbot-flow', 'WeatherBot 图结构可视化', 8],
  ],
  'LG-02-tools': [
    ['LG-02-1-tool-loop', 'Tool 调用循环流程图', 3],
    ['LG-02-2-tool-fallback', '五层兜底设计架构图', 5],
    ['LG-02-3-mcp-architecture', 'MCP 协议架构对比图', 9],
  ],
  'LG-03-human-in-the-loop': [
    ['LG-03-1-hitl-layers', 'HITL 三层架构对比图', 3],
    ['LG-03-2-interrupt-flow', 'interrupt_before / after 执行流程对比', 4],
    ['LG-03-3-resume-state', 'Resume 协议状态流转图', 7],
  ],
  'LG-04-memory': [
    ['LG-04-1-memory-layers', '四层记忆架构图', 3],
    ['LG-04-2-checkpoint-flow', 'Checkpoint 数据流图', 5],
    ['LG-04-3-context-trim', '上下文裁剪策略对比图', 8],
  ],
  'LG-05-subgraphs': [
    ['LG-05-1-fanout-fanin', 'Fan-out / Fan-in 流程图', 3],
    ['LG-05-2-map-reduce', 'Map-Reduce 动态分发图', 5],
    ['LG-05-3-subgraph-state', '父子图状态映射示意图', 7],
  ],
  'LG-06-prebuilt-agents': [
    ['LG-06-1-react-loop', 'ReAct 循环流程图', 4],
    ['LG-06-2-multi-agent', '三种多 Agent 模式架构对比图', 6],
    ['LG-06-3-prebuilt-decision', '预构建 vs 自定义决策树', 7],
  ],
  'LG-07-streaming': [
    ['LG-07-1-stream-spectrum', '7 种 stream_mode 粒度光谱图', 3],
    ['LG-07-2-frontend-protocol', '前端三段式协议时序图', 8],
  ],
  'LG-08-deepagent': [
    ['LG-08-1-deepagents-arch', 'DeepAgents 整体架构图', 3],
    ['LG-08-2-planning-flow', 'Planning 执行流程图', 5],
    ['LG-08-3-subagent-parallel', 'Sub-agent 并行协作图', 7],
    ['LG-08-4-middleware-onion', '10 层 Middleware 洋葱模型', 9],
  ],
  'LG-09-production-langfuse': [
    ['LG-09-3-hybrid-dataflow', '混合架构数据流图', 3],
    ['LG-09-1-langfuse-trace', 'Langfuse Trace 链路树形图', 4],
    ['LG-09-2-prompt-lifecycle', 'Prompt 生命周期工作流图', 7],
  ],
  'LG-10-langgraph-studio-langfuse': [
    ['LG-10-1-studio-zones', 'Studio 界面分区标注图', 3],
    ['LG-10-2-langfuse-tree', 'Langfuse Trace 树形结构图', 6],
  ],
};

function diagramSlide(id, title, relPrefix) {
  const img = `${relPrefix}diagrams/${id}.png`;
  return `

<!-- Diagram: ${id} -->
<section class="slide diagram-slide" data-title="图解：${title}">
  <div class="kicker">Diagram</div>
  <div class="h2" style="margin-bottom:14px;">${title}</div>
  <div style="flex:1;display:flex;align-items:center;justify-content:center;min-height:0;">
    <img src="${img}" alt="${title}" style="width:100%;height:auto;max-height:292pt;object-fit:contain;border-radius:8px;border:1px solid rgba(148,163,184,0.2);background:#0f172a;">
  </div>
  <div class="deck-footer">
    <span>LangGraph 教程</span>
    <span>图解</span>
  </div>
  <div class="notes">
    这页是配套图解，用来在讲解 ${title} 时先建立整体结构感，再回到代码或细节页展开。
  </div>
</section>`;
}

function sectionRegex() {
  return /<section\b[\s\S]*?<\/section>/g;
}

function normalizeActive(html) {
  let seen = false;
  return html.replace(/<section\b([^>]*)class="([^"]*\bslide\b[^"]*)"([^>]*)>/g, (m, pre, cls, post) => {
    let classes = cls.split(/\s+/).filter(Boolean).filter((c) => c !== 'is-active');
    if (!seen) {
      classes.push('is-active');
      seen = true;
    }
    return `<section${pre}class="${classes.join(' ')}"${post}>`;
  });
}

function removeOldDiagramSlides(html) {
  return html.replace(/\n*<!-- Diagram: [\s\S]*?<\/section>/g, '');
}

function insertForFile(file, diagrams, relPrefix) {
  if (!fs.existsSync(file)) return false;
  let html = fs.readFileSync(file, 'utf8');
  html = removeOldDiagramSlides(normalizeActive(html));

  const sections = [...html.matchAll(sectionRegex())];
  if (!sections.length) {
    console.warn(`skip: no <section> slides in ${file}`);
    return false;
  }

  let offset = 0;
  const ordered = [...diagrams].sort((a, b) => a[2] - b[2]);
  for (const [id, title, afterSlide] of ordered) {
    const pngPath = path.join(ROOT, 'diagrams', `${id}.png`);
    if (!fs.existsSync(pngPath)) {
      console.warn(`missing diagram: ${pngPath}`);
      continue;
    }
    const idx = Math.min(afterSlide - 1, sections.length - 1);
    const insertAt = sections[idx].index + sections[idx][0].length + offset;
    const slide = diagramSlide(id, title, relPrefix);
    html = html.slice(0, insertAt) + slide + html.slice(insertAt);
    offset += slide.length;
  }

  fs.writeFileSync(file, html);
  return true;
}

function main() {
  let changed = 0;
  for (const [deck, diagrams] of Object.entries(plan)) {
    const source = path.join(ROOT, deck, `${deck}.html`);
    const output = path.join(ROOT, 'ppt-output', `${deck}.html`);
    if (insertForFile(source, diagrams, '../')) {
      console.log(`patched source ${source}`);
      changed++;
    }
    if (insertForFile(output, diagrams, '../')) {
      console.log(`patched output ${output}`);
      changed++;
    }
  }
  console.log(`done: patched ${changed} html files`);
}

main();
