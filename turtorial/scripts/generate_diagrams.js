#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

let chromium;
try {
  ({ chromium } = require('playwright'));
} catch {
  ({ chromium } = require('/Users/galaxyxieyu/.claude/skills/html-ppt-skill/node_modules/playwright'));
}

const ROOT = path.resolve(__dirname, '..');
const OUT_DIR = path.join(ROOT, 'diagrams');
fs.mkdirSync(OUT_DIR, { recursive: true });

const C = {
  bg: '#0f172a',
  card: '#1e293b',
  card2: '#111827',
  border: '#334155',
  line: '#64748b',
  text: '#e2e8f0',
  sub: '#94a3b8',
  blue: '#38bdf8',
  green: '#9ece6a',
  orange: '#e0a068',
  pink: '#f7768e',
  purple: '#a78bfa',
};

const charts = [
  { id: 'LG-01-2-state-flow', title: 'State 流转示意', type: 'state',
    left: ['节点 A：parse_intent', 'user_input：北京天气', 'intent：空', 'response：空'],
    mid: 'Reducer 合并',
    right: ['节点 B：get_weather', 'user_input：北京天气', 'intent：weather', 'response：空'],
    note: '节点接收完整 State → 返回变更字段 → Reducer 自动合并 → 传递给下一节点' },
  { id: 'LG-01-3-build-steps', title: '五步构建 LangGraph 工作流', type: 'steps',
    items: ['定义 StateSchema', '创建 Node 函数', '添加 Edge 连接', 'compile 编译', 'invoke / stream 运行'] },
  { id: 'LG-02-1-tool-loop', title: 'Tool 调用循环', type: 'cycle',
    items: ['LLM 推理', 'ToolNode 路由', '工具执行', '返回 ToolMessage', 'LLM 再次推理'], center: '循环直到 LLM 不再调用工具' },
  { id: 'LG-02-2-tool-fallback', title: '生产级 Tool 五层兜底设计', type: 'layers',
    items: ['参数校验', '权限控制', '超时重试', '缓存降级', '审计追踪'] },
  { id: 'LG-02-3-mcp-architecture', title: 'MCP 协议架构对比', type: 'compare',
    leftTitle: '传统集成', left: ['每个应用单独接工具', '协议不统一', '迁移成本高'],
    rightTitle: 'MCP 标准化', right: ['统一协议层', '工具可复用', 'Client / Server 解耦'] },
  { id: 'LG-03-1-hitl-layers', title: 'HITL 三层架构', type: 'layers',
    items: ['业务审批层', 'interrupt 中断层', 'Checkpoint 恢复层'] },
  { id: 'LG-03-2-interrupt-flow', title: 'interrupt_before / after 对比', type: 'compare',
    leftTitle: 'interrupt_before', left: ['节点执行前暂停', '适合人工审批', '可阻止风险动作'],
    rightTitle: 'interrupt_after', right: ['节点执行后暂停', '适合结果确认', '可检查工具输出'] },
  { id: 'LG-03-3-resume-state', title: 'Resume 协议状态流转', type: 'steps',
    items: ['运行图', '触发 interrupt', '保存快照', '人工输入', 'Command(resume) 恢复'] },
  { id: 'LG-04-1-memory-layers', title: '四层记忆架构', type: 'layers',
    items: ['消息历史', 'Checkpoint 短期记忆', 'Store 长期记忆', 'Cache 加速层'] },
  { id: 'LG-04-2-checkpoint-flow', title: 'Checkpoint 数据流', type: 'steps',
    items: ['用户输入', '节点执行', '状态快照', '线程恢复', '继续运行'] },
  { id: 'LG-04-3-context-trim', title: '上下文裁剪策略对比', type: 'compare',
    leftTitle: '不裁剪', left: ['上下文持续膨胀', 'Token 成本升高', '关键信息被淹没'],
    rightTitle: '策略裁剪', right: ['保留摘要和关键事实', '控制窗口大小', '提升响应稳定性'] },
  { id: 'LG-05-1-fanout-fanin', title: 'Fan-out / Fan-in 流程', type: 'fan',
    source: '任务分发', branches: ['查财报', '查新闻', '查竞品', '查专家'], sink: '汇总报告' },
  { id: 'LG-05-2-map-reduce', title: 'Map-Reduce 动态分发', type: 'fan',
    source: 'dispatch 节点', branches: ['子任务 A', '子任务 B', '子任务 C', '子任务 D'], sink: 'Reducer 汇总' },
  { id: 'LG-05-3-subgraph-state', title: '父子图状态映射', type: 'state',
    left: ['父图 State', 'topic', 'user_id', 'reports[]'], mid: '输入/输出映射', right: ['子图 State', 'company', 'context', 'result'] },
  { id: 'LG-06-1-react-loop', title: 'ReAct 循环流程', type: 'cycle',
    items: ['观察问题', '思考下一步', '调用工具', '获得结果', '生成答案'], center: 'Thought → Action → Observation' },
  { id: 'LG-06-2-multi-agent', title: '三种多 Agent 模式', type: 'columns',
    items: ['Supervisor 统一调度', 'Handoff 主动交接', 'Network 网状协作'] },
  { id: 'LG-06-3-prebuilt-decision', title: '预构建 vs 自定义决策树', type: 'tree',
    root: '是否需要深度控制？', branches: ['否：create_react_agent', '部分：预构建 + Hooks', '是：自定义 StateGraph'] },
  { id: 'LG-07-1-stream-spectrum', title: '7 种 stream_mode 粒度光谱', type: 'spectrum',
    items: ['values', 'updates', 'messages', 'custom', 'events', 'debug', 'tasks'] },
  { id: 'LG-07-2-frontend-protocol', title: '前端三段式协议时序', type: 'timeline',
    items: ['Start：创建任务', 'Processing：持续推送', 'End：完成/错误'] },
  { id: 'LG-08-1-deepagents-arch', title: 'DeepAgents 整体架构', type: 'layers',
    items: ['用户任务', 'Planning', 'Sub-agents', 'Filesystem', 'Middleware', 'LangGraph Runtime'] },
  { id: 'LG-08-2-planning-flow', title: 'Planning 执行流程', type: 'steps',
    items: ['理解任务', '拆解计划', '分派子任务', '跟踪进度', '汇总结果'] },
  { id: 'LG-08-3-subagent-parallel', title: 'Sub-agent 并行协作', type: 'fan',
    source: '主 Agent', branches: ['研究 Agent', '代码 Agent', '验证 Agent', '写作 Agent'], sink: '最终报告' },
  { id: 'LG-08-4-middleware-onion', title: '10 层 Middleware 洋葱模型', type: 'onion',
    items: ['日志', '权限', '限流', '缓存', '重试', '审计', '记忆', '工具', '模型', '输出'] },
  { id: 'LG-09-1-langfuse-trace', title: 'Langfuse Trace 链路树', type: 'tree',
    root: 'Trace：一次请求', branches: ['Span：LLM 调用', 'Span：Tool 调用', 'Event：中间状态'] },
  { id: 'LG-09-2-prompt-lifecycle', title: 'Prompt 生命周期工作流', type: 'steps',
    items: ['设计 YAML', '提交 Hub', '版本评审', '灰度发布', '指标回看'] },
  { id: 'LG-09-3-hybrid-dataflow', title: 'Redis + PostgreSQL 混合架构', type: 'state',
    left: ['请求入口', 'thread_id', 'session'], mid: '缓存策略', right: ['Redis 热数据', 'PostgreSQL 持久化', 'Langfuse Trace'] },
  { id: 'LG-10-1-studio-zones', title: 'Studio 界面分区', type: 'columns',
    items: ['图结构区', '状态检查区', '执行日志区', '调试控制区'] },
  { id: 'LG-10-2-langfuse-tree', title: 'Trace / Span / Event 树形结构', type: 'tree',
    root: 'Trace', branches: ['Span：Graph Run', 'Span：Node', 'Event：State Update', 'Event：Token Usage'] },
];

function esc(s) {
  return String(s).replace(/[&<>]/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[m]));
}

function text(x, y, body, opts = {}) {
  const size = opts.size || 34;
  const fill = opts.fill || C.text;
  const weight = opts.weight || 500;
  const anchor = opts.anchor || 'middle';
  return `<text x="${x}" y="${y}" text-anchor="${anchor}" font-size="${size}" font-weight="${weight}" fill="${fill}" font-family="Inter, Noto Sans SC, PingFang SC, Microsoft YaHei, sans-serif">${esc(body)}</text>`;
}

function titleSvg(title) {
  return `${text(80, 86, title, { size: 46, weight: 800, anchor: 'start' })}
${text(80, 126, 'LangGraph 教程图解', { size: 20, fill: C.sub, anchor: 'start' })}`;
}

function card(x, y, w, h, label, color = C.blue, sub = []) {
  const lines = Array.isArray(sub) ? sub : [sub];
  let s = `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="12" fill="${C.card}" stroke="${color}" stroke-width="3"/>`;
  s += text(x + w / 2, y + 48, label, { size: 28, weight: 700, fill: C.text });
  lines.forEach((line, i) => {
    s += text(x + w / 2, y + 92 + i * 34, line, { size: 22, fill: C.sub });
  });
  return s;
}

function arrow(x1, y1, x2, y2, color = C.line) {
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="4" marker-end="url(#arrow)"/>`;
}

function base(inner) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
<defs>
  <marker id="arrow" markerWidth="14" markerHeight="14" refX="10" refY="5" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,5 L0,10 z" fill="${C.line}"/></marker>
</defs>
<rect width="1600" height="900" fill="${C.bg}"/>
${inner}
</svg>`;
}

function render(spec) {
  const title = titleSvg(spec.title);
  if (spec.type === 'state') {
    return base(`${title}
${card(110, 260, 420, 250, spec.left[0], C.blue, spec.left.slice(1))}
${arrow(540, 385, 705, 385)}
<circle cx="800" cy="385" r="90" fill="${C.card}" stroke="${C.orange}" stroke-width="4"/>
${text(800, 395, spec.mid || 'Reducer', { size: 28, weight: 800, fill: C.orange })}
${arrow(895, 385, 1060, 385)}
${card(1070, 260, 420, 250, spec.right[0], C.green, spec.right.slice(1))}
${text(800, 700, spec.note || '状态通过节点返回值增量更新，并在图中持续传递', { size: 28, fill: C.sub })}`);
  }
  if (spec.type === 'steps') {
    const gap = 34, w = 255, y = 300;
    let s = title;
    spec.items.forEach((it, i) => {
      const x = 80 + i * (w + gap);
      s += `<rect x="${x}" y="${y}" width="${w}" height="220" rx="12" fill="${C.card}" stroke="${i === spec.items.length - 1 ? C.green : C.blue}" stroke-width="3"/>`;
      s += `<circle cx="${x + 50}" cy="${y + 54}" r="30" fill="${i === spec.items.length - 1 ? C.green : C.blue}"/>`;
      s += text(x + 50, y + 65, i + 1, { size: 28, weight: 800, fill: '#0f172a' });
      s += text(x + w / 2, y + 132, it, { size: 25, weight: 700 });
      if (i < spec.items.length - 1) s += arrow(x + w + 8, y + 110, x + w + gap - 8, y + 110);
    });
    s += text(800, 690, '从定义数据结构到运行图，按顺序完成闭环', { size: 28, fill: C.sub });
    return base(s);
  }
  if (spec.type === 'cycle') {
    const pts = [[800,210],[1140,360],[1010,650],[590,650],[460,360]];
    let s = title;
    pts.forEach((p, i) => {
      const next = pts[(i + 1) % pts.length];
      s += arrow(p[0] + (next[0] > p[0] ? 120 : -120), p[1], next[0] + (next[0] > p[0] ? -120 : 120), next[1]);
      s += card(p[0] - 150, p[1] - 58, 300, 116, spec.items[i], i % 2 ? C.orange : C.blue, []);
    });
    s += `<circle cx="800" cy="450" r="125" fill="${C.card2}" stroke="${C.purple}" stroke-width="3"/>`;
    s += text(800, 444, spec.center || '循环执行', { size: 26, weight: 700, fill: C.purple });
    s += text(800, 482, '直到条件满足', { size: 22, fill: C.sub });
    return base(s);
  }
  if (spec.type === 'layers') {
    let s = title;
    const h = Math.min(88, 500 / spec.items.length);
    spec.items.forEach((it, i) => {
      const x = 230 + i * 32, y = 220 + i * (h + 12), w = 1140 - i * 64;
      const colors = [C.blue, C.green, C.orange, C.pink, C.purple, C.line];
      s += `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="12" fill="${C.card}" stroke="${colors[i % colors.length]}" stroke-width="3"/>`;
      s += text(800, y + h / 2 + 12, it, { size: 30, weight: 700 });
    });
    return base(s);
  }
  if (spec.type === 'compare') {
    let s = title;
    s += card(145, 230, 560, 430, spec.leftTitle, C.pink, spec.left);
    s += card(895, 230, 560, 430, spec.rightTitle, C.green, spec.right);
    s += text(800, 455, 'VS', { size: 54, weight: 900, fill: C.orange });
    return base(s);
  }
  if (spec.type === 'fan') {
    let s = title;
    s += card(650, 180, 300, 110, spec.source, C.blue, []);
    const xs = [230, 560, 890, 1220];
    spec.branches.forEach((b, i) => {
      s += arrow(800, 295, xs[i] + 110, 405);
      s += card(xs[i], 410, 220, 105, b, C.orange, []);
      s += arrow(xs[i] + 110, 520, 800, 625);
    });
    s += card(650, 635, 300, 110, spec.sink, C.green, []);
    return base(s);
  }
  if (spec.type === 'columns') {
    let s = title;
    const w = 310, gap = 42, total = spec.items.length * w + (spec.items.length - 1) * gap;
    const start = (1600 - total) / 2;
    spec.items.forEach((it, i) => {
      const color = [C.blue, C.green, C.orange, C.purple][i % 4];
      s += card(start + i * (w + gap), 300, w, 260, it, color, ['核心职责', '边界清晰', '可组合复用']);
    });
    return base(s);
  }
  if (spec.type === 'tree') {
    let s = title;
    s += card(610, 185, 380, 120, spec.root, C.blue, []);
    const w = 330, start = 140, y = 520;
    spec.branches.forEach((b, i) => {
      const x = start + i * 370;
      s += arrow(800, 310, x + w / 2, y - 15);
      s += card(x, y, w, 130, b, [C.green, C.orange, C.purple, C.pink][i % 4], []);
    });
    return base(s);
  }
  if (spec.type === 'spectrum') {
    let s = title;
    const x0 = 150, y = 410, w = 1300;
    s += `<line x1="${x0}" y1="${y}" x2="${x0 + w}" y2="${y}" stroke="${C.line}" stroke-width="8" marker-end="url(#arrow)"/>`;
    spec.items.forEach((it, i) => {
      const x = x0 + i * (w / (spec.items.length - 1));
      const color = [C.blue, C.green, C.orange, C.pink, C.purple, C.blue, C.green][i];
      s += `<circle cx="${x}" cy="${y}" r="42" fill="${C.card}" stroke="${color}" stroke-width="4"/>`;
      s += text(x, y + 95, it, { size: 24, weight: 700 });
    });
    s += text(150, 540, '粗粒度', { size: 26, fill: C.sub, anchor: 'start' });
    s += text(1450, 540, '细粒度', { size: 26, fill: C.sub, anchor: 'end' });
    return base(s);
  }
  if (spec.type === 'timeline') {
    let s = title;
    const xs = [300, 800, 1300];
    spec.items.forEach((it, i) => {
      if (i < xs.length - 1) s += arrow(xs[i] + 130, 420, xs[i + 1] - 130, 420);
      s += card(xs[i] - 180, 325, 360, 190, it, [C.green, C.orange, C.blue][i], []);
    });
    return base(s);
  }
  if (spec.type === 'onion') {
    let s = title;
    const colors = [C.blue, C.green, C.orange, C.pink, C.purple];
    spec.items.forEach((it, i) => {
      const r = 310 - i * 24;
      s += `<circle cx="800" cy="470" r="${r}" fill="none" stroke="${colors[i % colors.length]}" stroke-width="3" opacity="${0.95 - i * 0.05}"/>`;
      if (i < 5) s += text(800, 470 - r + 32, it, { size: 20, fill: colors[i % colors.length] });
    });
    s += text(800, 482, 'Agent Core', { size: 34, weight: 800 });
    s += text(800, 528, '由外到内逐层增强', { size: 24, fill: C.sub });
    return base(s);
  }
  return base(`${title}${text(800, 450, spec.title, { size: 42, weight: 800 })}`);
}

async function main() {
  const existingWeather = path.join(ROOT, 'LG-01-1-weatherbot-flow.png');
  const copiedWeather = path.join(OUT_DIR, 'LG-01-1-weatherbot-flow.png');
  if (fs.existsSync(existingWeather) && !fs.existsSync(copiedWeather)) {
    fs.copyFileSync(existingWeather, copiedWeather);
    console.log(`copied ${copiedWeather}`);
  }

  const browser = await chromium.launch({
    executablePath: fs.existsSync('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
      ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
      : undefined,
  });

  for (const spec of charts) {
    const svg = render(spec);
    const svgPath = path.join(OUT_DIR, `${spec.id}.svg`);
    const pngPath = path.join(OUT_DIR, `${spec.id}.png`);
    fs.writeFileSync(svgPath, svg);
    const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
    await page.goto(`file://${svgPath}`);
    await page.screenshot({ path: pngPath, type: 'png' });
    await page.close();
    console.log(`generated ${pngPath}`);
  }
  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
