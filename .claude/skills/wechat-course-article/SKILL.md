---
name: wechat-course-article
description: |
  Convert LangGraph course notebooks/handouts into polished WeChat Official Account article drafts.
  Use when the user asks to turn tutorial notebooks, 讲义, or course chapters into 公众号文章/草稿箱内容, including Markdown conversion, article rewriting, image generation, SVG/PNG handling, image-this artifacts, and Wenyan MCP publishing.
---

# wechat-course-article — LangGraph 课程公众号转化 SOP

把本项目的课程 notebook / 讲义转成公众号文章时，按这套流程执行。目标不是“把 notebook 原样搬过去”，而是把课程机制改写成适合公众号阅读的图文文章，并能通过 Wenyan MCP 进入微信公众号草稿箱。

## 1. 输入与输出目录

常见输入：

- `turtorial/LG-xx-*/tutorial.ipynb`
- `turtorial/LG-xx-*/讲义.md`
- 已转换出的 `tutorial.md`

公众号草稿输出目录：

```text
turtorial/wechat-articles/
```

该目录必须保持 gitignored，不要提交公众号草稿、封面、发布副本或临时图片。

## 2. Notebook 先转 Markdown

使用项目脚本：

```bash
python turtorial/scripts/ipynb_to_md.py turtorial/LG-02-tools
```

批量转换：

```bash
python turtorial/scripts/ipynb_to_md.py turtorial/LG-*
```

注意：

- `tutorial.md` 是素材，不是公众号终稿。
- 如果目录里没有 `tutorial.ipynb`，检查是否有 `讲义.md`。
- Notebook 输出、长代码、安装命令都要在公众号稿里筛选，不要原样堆进去。

## 3. 公众号文章重写原则

必须遵守项目最高原则：先讲人的直觉，再讲 Graph/Agent 的限制，最后再引入 API 名。

推荐结构：

```text
标题 / 副标题
封面图
开场冲突：Demo 能跑，但生产不可控
人类自然动作
Graph/Agent 为什么不会自然这样做
机制需求：状态、分支、恢复、审批、工具边界
核心图 1：问题差异图
核心图 2：机制模型图
最小代码片段
可迁移场景
适用边界
一句话总结
下一篇预告
```

文章不是 API 文档。每篇只抓一个核心问题，例如：

- `Demo 能跑，不等于生产可控`
- `工具调用不是消息，而是副作用`
- `待办不是聊天，是恢复事件`
- `记忆不是 checkpoint，而是跨会话偏好`

## 4. 代码与文字取舍

公众号里只保留能证明机制的最小代码：

- State 定义可以保留。
- Node / Edge 示例只保留最小函数和最小路由。
- 安装命令、setup 输出、长运行输出一般删除。
- 代码块前后必须解释“它证明了什么”。

不要把 `tutorial.md` 直接发到公众号。它只是素材池。

## 5. 配图策略

每篇公众号至少准备三类图：

1. 封面图：用 `image-this-remote` + `gpt-image-2` 生成。
2. 正文机制图：需要文字准确时，优先手写 SVG。
3. 发布图片：SVG 要导出成 PNG，再用于公众号。

### 5.1 SVG 到 PNG

本机没有 `rsvg-convert` / `magick` 时，用 macOS 自带 Quick Look：

```bash
qlmanage -t -s 1600 -o turtorial/wechat-articles/images \
  turtorial/wechat-articles/images/demo-vs-production.svg
```

`qlmanage` 会生成：

```text
demo-vs-production.svg.png
```

记得重命名：

```bash
mv demo-vs-production.svg.png demo-vs-production.png
```

### 5.2 GPT 图片生成

优先使用 `image-this-remote` MCP，不要自己写 OpenAI 图片脚本。

推荐参数：

```text
tool: mcp__image-this-remote__generate_image
provider: openai
model: gpt-image-2
aspect_ratio: 16:9
resolution: high
output_dir: turtorial/wechat-articles/images
```

注意：

- 当前 `openai` provider 默认模型就是 `gpt-image-2`。
- 不要随便传 `negative_prompt`，该模型列表显示不支持 negative prompt，裸参数更稳。
- MCP 返回的 `full_path` 可能不是本机真实路径，以 `artifact_url` 为准。
- 需要落地本地文件时，用 `curl -L --fail <artifact_url> -o <local.png>`。

### 5.3 公众号封面比例

微信公众号首图展示常见裁切接近 `2.35:1`，但当前 `gpt-image-2` 在 MCP 里稳定输出的是 `16:9`。

实操策略：

- 生成 `16:9`。
- 按 `2.35:1` 安全区设计。
- 所有重要文字放在画面中间横向安全带内。
- 文字距离上下边缘至少 22%，距离左右边缘至少 8%。
- 最稳布局：左侧 60% 文字安全区，右侧 40% 装饰机制图。
- 合集文章要明确标注：`LangGraph 企业级 Agent 课`、`第 N 集`、主标题、副标题。

封面 prompt 必须强调：

```text
标题不能被任何图形遮挡。
右侧图形不能进入左侧文字区。
所有重要文字必须位于公众号 2.35:1 裁切安全区。
这是合集课程第 N 集。
```

## 6. Wenyan MCP 发布

可用工具：

- `mcp__wenyan-mcp__gzh_article_publish`
- `mcp__wenyan-mcp__gzh_image_upload`

实际注意事项：

- Wenyan MCP 可能读不到本机 `/Volumes/...` 或 `/tmp/...` 文件。
- 不要依赖 `markdownPath` 或本地图片路径发布。
- 发布副本中的图片尽量全部换成远端 URL。
- `image-this-remote` 生成图后，直接使用 `artifact_url` 作为 Markdown 图片 URL。
- 本地编辑稿可以用 `images/*.png`，发布副本使用远端 URL。

推荐保存两份：

```text
LG-xx-article.md          # 本地编辑稿，引用 images/*.png
LG-xx-article.publish.md  # 发布副本，引用 artifact URL
```

发布调用：

```text
gzh_article_publish(
  dryRun=false,
  themeId="default",
  hlThemeId="solarized-light",
  title="文章标题",
  markdown="带远端图片 URL 的完整 Markdown"
)
```

成功后记录返回的 `mediaId`。如果重新发布新封面，Wenyan 会创建新草稿，不会原地覆盖旧草稿。最终以最新 `mediaId` 为准。

## 7. Git 规则

不要提交：

- `turtorial/wechat-articles/`
- 公众号封面图
- 公众号发布副本
- 临时 artifact 下载图

可以提交：

- 转换脚本本身，例如 `turtorial/scripts/ipynb_to_md.py`
- 课程源 notebook / 讲义的真实内容变更

批量生成的 `turtorial/LG-*/tutorial.md` 是否提交，需要用户单独确认。

## 8. 每篇交付清单

完成一篇公众号文章后，向用户汇报：

- 本地编辑稿路径
- 发布副本路径
- 封面图路径
- 正文图片路径
- 使用的 artifact URL
- Wenyan 草稿 `mediaId`
- 是否有旧草稿需要忽略或删除

## 9. 常见坑

- `21:9` 可能被 `gpt-image-2` 回退成方图，不要直接信任；看返回的 `width` / `height`。
- 生成图中文字可能挡住标题，必须要求“左文右图”和“文字安全区”。
- `artifact_url` 文件名不要手抄错，尤其日期段。
- Wenyan 读不到本地图片时，不要反复传本地路径，改用远端 URL。
- 旧草稿不会自动覆盖，新 `mediaId` 才是最终版本。
- SVG 精确但公众号兼容性弱，正式发布前转 PNG。
