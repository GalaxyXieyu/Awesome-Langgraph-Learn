---
name: feishu-wiki-builder
description: |
  Build and maintain a Feishu/Lark Wiki knowledge base from course/case/concept content via the local lark-cli.
  Use when the user asks to turn tutorials, 讲义, case studies, or concepts into a 飞书知识库 / Feishu wiki / Lark wiki,
  to create richly-formatted Feishu docs (callout / 分栏 / 表格 / mermaid & SVG 画板 / 交叉链接), to organize pages
  into a single library with nested sub-documents (子文档), or to批量发布/整理 Feishu wiki spaces and nodes.
  Covers: DocxXML authoring, whiteboard diagrams, media-insert, wiki space/node操作, subagent orchestration, cross-linking.
---

# feishu-wiki-builder — 用 lark-cli 搭飞书知识库的 SOP

把课程 / 案例 / 概念内容做成一个**读起来能学到东西、好看、可持续维护**的飞书 Wiki 知识库。这套流程已经跑通并验证：11 章系统课 + 8 篇案例拆解 + 9 个概念词条，共 28 页、互相交叉链接、合并进一个库做子文档嵌套。

> 目标不是"把 markdown 倒进飞书"，而是**按心智模型重排成富 block + 画板 + 三向交叉链接**的成品。

---

## 0. 前置条件（必读，别跳）

- `lark-cli` 是**飞书官方开放平台 CLI**（`@larksuite/cli`），不是前端脚手架。文档操作默认 **`--as user`**（归属用户本人，不是 bot）。首次用先 `lark-cli auth login`，`lark-cli auth status` 确认 `docx:document:create`、`docs:document.media:upload`、`board:whiteboard:node:create`、`wiki:space:write_only`、`wiki:node:create` 等 scope 齐全。
- CLI 强制要求：动手前先读内嵌 skill（版本匹配，别 grep 本地 SKILL.md）：
  ```bash
  lark-cli skills read lark-doc                              # 文档 workflow
  lark-cli skills read lark-doc references/lark-doc-xml.md   # DocxXML 语法
  lark-cli skills read lark-wiki                             # 知识空间 / 节点
  lark-cli skills read lark-shared                           # 认证 / 全局参数
  ```
- 所有 `docs`/`wiki` 命令加 `--api-version v2 --as user`。

---

## 1. 心智模型：加工厂 ↔ 展示厅

```text
本地 markdown（加工厂，私有）        飞书 Wiki（展示厅，面向读者）
raw/  收原始素材                     ← 发布 → 精修、可导航、可分享的成品
wiki/ 编译成交叉链接的成品页
```

- 飞书擅长漂亮/可分享/富排版 → 当**展示厅**；不擅长批量 ingest 原始 md、lint 死链、git 版本 → **别让飞书当加工厂**。
- 内容按**加工程度**分层，不按主题：① 素材层(raw，私有) → ② 知识层(课程/案例/概念，成品) → ③ 导航层(首页/学习地图)。
- 结构默认**单库 + 子文档嵌套**（一个 Wiki 空间，三个分区父页面，各页做子文档）。用户可能一开始说"多空间"，看到实际效果后常改成单库——以最终确认为准。

---

## 2. 内容契约（质量的核心）

对齐项目 `CLAUDE.md`：这门课教**心智模型**不是 API 手册。每个概念按固定顺序重写：

```text
人类自然动作 → 图/Agent 为什么不会自然这么做 → 学生的反直觉点 → 机制需求 → 白话模型 → API 名 → 可运行证据
```

- 不要用 API 术语开场；不要逐句照搬讲义——重排成富、可扫读的 block。
- 每个 `<h1>` 章节尽量至少含一个非纯文本 block（callout / 表格 / 分栏 / 代码 / 画板）。
- **标题**：emoji + 简洁中文，**不带 LG-0X / 01-02 编号前缀**（顺序由页面树表达）。见记忆 `feishu-page-title-style`。

### 三种页面模板

- **课程章节**：人类场景 → 图的限制 → 机制图 → 最小证据 → 练习。
- **案例拆解（8 段）**：要解决什么 → 为什么用 LangGraph → 架构(mermaid) → 用到的机制(表格) → 关键决策与取舍 → 能偷师什么 → 局限与坑 → 原文链接(bookmark)。
- **概念词条（6 段）**：一句话是什么 → 为什么需要 → 在图/Agent 里怎么体现(小 mermaid) → 常见误区 → 在课程哪节讲透(链接) → 哪些案例用了它(链接)。

### 三向交叉链接（让库"活"起来的关键）

课程 ↔ 案例 ↔ 概念 互相 `<a href="https://<domain>/wiki/<node_token>">名称</a>`。案例的"用到的机制"表逐条链回课程章节和概念词条；概念页往上链课程、往下链案例。**联网找真实案例时用 subagent + WebFetch，只收验证过的真实 URL，指标标来源、推测处标注"（合理推测）"，不编造。**

---

## 3. 发布管线（单页）

```text
写 DocxXML → docs +create(stdin) → 嵌画板/图 → wiki +move 移入库 → 嵌套为子文档 → 排序 + 首页目录
```

1. **写正文**到 `.xml` 文件（见 §4 语法）。
2. **建文档**——大段中文 XML 走 **stdin**（`@file` 只认相对路径，会踩坑）：
   ```bash
   lark-cli docs +create --api-version v2 --as user --content - < body.xml
   ```
   返回 `document_id`。
3. **嵌图**（见 §5）：SVG/mermaid 直接内联在 create 的正文里；栅格 PNG 用 `docs +media-insert`。
4. **移入库**：
   ```bash
   lark-cli wiki +move --as user --obj-type docx --obj-token <doc_id> --target-space-id <space_id>
   ```
   返回 `node_token`。
5. **嵌套/排序/目录**：见 §6。

---

## 4. 飞书 DocxXML 速查

```text
块级：<title>(唯一置顶) <h1>..<h9> <p> <ul>/<ol>+<li>(有序用 seq="auto")
      <table>(<thead>/<tbody>/<tr>/<th>/<td>，th/td 可 background-color)
      <callout>(emoji, background-color, border-color) <grid>+<column>(width-ratio 各列和=1)
      <pre lang caption>+<code> <blockquote> <hr/> <checkbox done> <whiteboard type> <bookmark name href>
行内：<b> <em> <u> <del> <code> <span text-color background-color> <a href> <br/>
      行内嵌套顺序(外→内)：a → b → em → del → u → code → span → 文本
命名色：red orange yellow green blue purple gray
      callout background = gray | light-{色} | medium-{色}；border = 基础色；span/th 背景 = light-{色}|medium-gray
```

**转义（关键）**：标签本身**不转义**；只有**文本内容**里的 `&`→`&amp;`、`<`→`&lt;`、`>`→`&gt;`。`<code>` 内换行写成 `<br/>`。**mermaid 画板内部不适用转义规则**——`-->` 保持原样。箭头 `→ ├─ └─` 直接写。

---

## 5. 配图三条路

| 场景 | 做法 | 说明 |
|---|---|---|
| **现成 SVG** | 内联 `<whiteboard type="svg">完整自包含 SVG</whiteboard>` | 文档内**可编辑矢量图**，比贴图强。`docs +create` 直接接受内联画板。 |
| **新画流程/架构图** | 内联 `<whiteboard type="mermaid">flowchart TD ...</whiteboard>` | mermaid 内 `-->` 不转义；中文标签用引号 `A["标签"]`。 |
| **栅格 PNG（截图/精修图）** | `docs +media-insert` | 上传+绑定；用 `--selection-with-ellipsis "文本..." --before` 精准定位，否则追加到末尾。 |

**子 agent 不碰 SVG 字节**：让 agent 在正文放占位符 `<wb src="文件名.svg"/>`，主线程用 `scripts/assemble_whiteboards.py <body.xml> <images_dir> <out.xml>` 做字节精确替换后再 create。mermaid 让 agent 直接内联（无需占位符）。

---

## 6. Wiki 结构操作

**原则：一条命令只做一件事**——建空间、移动节点、删除各自单独跑，不要串进一条复合命令，更好调试、出错也好定位。

```bash
# 建空间（仅 --as user）
lark-cli wiki +space-create --as user --name "库名" --description "…"

# 移一篇云文档进库（docs-to-wiki）
lark-cli wiki +move --as user --obj-type docx --obj-token <doc_id> --target-space-id <space>

# 把页面收成某父页面的子文档（子文档嵌套）
lark-cli wiki +move --as user --node-token <child> --target-parent-token <parent> --target-space-id <space>

# 跨空间搬迁（合并进一个库）——移父节点会带整棵子树，node_token 不变
lark-cli wiki +move --as user --node-token <parent> --source-space-id <old> --target-space-id <new>

# 列子节点（校验）
lark-cli wiki +node-list --as user --space-id <space> --parent-node-token <parent> --format json

# 删空节点（如误建的未命名文档，注意 obj-type 是 wiki）
lark-cli wiki +node-delete --as user --node-token <node> --obj-type wiki --yes
```

**排序**：把节点依次 `wiki +move` 到目标父/根下（≈ 追加到末尾）。子文档层排序可靠；**顶层排序结果不稳定**，实在不齐让用户在 UI 拖。

**首页/目录页**：每个分区做一个父页面（callout 介绍 + 每页一个 `<a href=".../wiki/<node_token>">` 链接，可分组）。用 `docs +update --command overwrite --content - < home.xml` 整篇更新。

**推荐最终形态**：
```text
一个库（AI Agents 应用实战）
├── 🏠 从这里开始（首页/学习地图，含 mermaid）
├── 📚 系统课程（父）── N 章子文档
├── 🔬 实战案例拆解（父）── N 篇子文档
└── 🧠 概念词条（父）── N 个子文档
```

**只能用户在飞书 UI 做的事**（开放 API 不支持，都是界面操作）：空间改名、删除空间、拖动顶层节点顺序。做完记得提醒用户。

---

## 7. 子 agent 并行编排（规模化的关键）

**把慢的创作并行化，把有状态的 API 操作串行化。**

1. **主线程**：建空间、建首页、定黄金模板（先手写 1 页样板，如最丰富的一章）。
2. **并行 agent（只读源 + 只写一个 XML 文件，不碰 lark-cli/git）**：每个 agent 拿到——章节/概念 + 规范标题 + 课程/案例的 node_token 链接表 + DocxXML 语法 + 黄金模板路径 + 输出路径；产出一个 `.xml`。案例类 agent 额外先 WebFetch 来源。
3. **主线程发布**：逐个 `assemble_whiteboards.py`（如有 SVG 占位符）→ `docs +create`(stdin) → `wiki +move`，记录到 manifest（slug/doc_id/node_token/title）。
4. **收尾**：嵌套子文档 + 排序 + 首页目录 + 交叉链接回填。

给 agent 的提示词务必包含：**标题精确文案、node_token 链接映射表、"标签不转义/文本转义/mermaid 内不转义"、"不编造、推测标注"、输出路径**。

---

## 8. 踩坑清单（都是真摔过的）

- **stdin 而非 @file**：`--content @file` 只认当前目录相对路径；大段中文 XML 一律 `--content - < file.xml`。
- **whiteboard 可内联进 +create**：一次 create 即含 SVG/mermaid 画板，无需事后插入。
- **跨空间移动带整棵子树，node_token 不变** → 合并库后所有交叉链接不失效。先库内嵌套，再整棵子树跨空间移，最省事。
- **删节点要 `--obj-type wiki`**（不是 docx）。
- **并行启动 agent 偶发瞬时不可用/限流** → 重试；重试时务必核对是哪个没发出去（曾误把同一个发两遍、漏发另一个）。分批（4~6 个）更稳。
- **overwrite 原地替换正文、保留 doc/node_token**：改错别字、回填链接、纠偏用它，不影响 wiki 位置和入链。
- **fetch 输出会把引号转义成 `href=\"`**：grep 校验链接数时用 `feishu.cn/wiki/` 而不是带引号的完整串。
- **AI 写的内容会有错**：让 agent 明确"只写来源有据的、推测标注、不编数字"；发现纠偏（如删掉未证实的协议声明、改回真实机制名）就用 overwrite 覆盖已发布版。

---

## 9. 相关

- 记忆：`knowledge-base-architecture`（整体架构 + 当前库的 space/node token 全表）、`feishu-page-title-style`、`course-writing-agent-mental-model`。
- 方法论来源：Karpathy 的 LLM Wiki（`~/.claude/skills/llm-wiki-skill/`）——raw 素材编译成交叉链接的 wiki，知识随每次 ingest 增值。
- 内容改写原则统一遵循项目 `CLAUDE.md`。
