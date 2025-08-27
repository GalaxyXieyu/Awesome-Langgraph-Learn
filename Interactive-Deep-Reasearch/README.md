# 🧠 智能报告生成器 (Interactive Deep Research)

一个基于 LangGraph 的智能深度研究报告生成系统，支持实时流式输出和交互式确认。

## ✨ 特性

### 🎯 核心功能
- **智能报告生成**: 基于 AI 的深度研究报告自动生成
- **实时流式展示**: 实时显示 AI 工作过程和生成进度
- **交互式确认**: 支持工具调用的用户确认和参数编辑
- **层级化大纲**: 清晰的报告章节结构和进度展示
- **多种工作模式**: 交互模式、副驾驶模式、引导模式

### 🎨 设计特色
- **苹果风格 UI**: 现代化的 macOS 风格界面设计
- **毛玻璃效果**: 优雅的视觉层次和透明度
- **流畅动画**: 基于 Framer Motion 的微交互
- **响应式设计**: 适配不同屏幕尺寸

### 🔧 技术栈
- **后端**: Python + FastAPI + LangGraph + Celery + Redis
- **前端**: React + TypeScript + Tailwind CSS + Framer Motion
- **AI模型**: 支持多种 LLM 集成
- **实时通信**: Server-Sent Events (SSE)

## 🏗️ 项目结构

```
Interactive-Deep-Research/
├── backend/                 # 后端服务
│   ├── main.py             # FastAPI 主服务
│   ├── graph.py            # LangGraph 工作流定义
│   ├── state.py            # 状态管理和数据模型
│   ├── tools/              # 工具集合
│   ├── subgraphs/          # 子图定义
│   └── writer/             # 流式输出核心
├── frontend/               # 前端界面
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── hooks/          # 自定义 Hooks
│   │   ├── types/          # TypeScript 类型定义
│   │   ├── utils/          # 工具函数
│   │   └── App.tsx         # 主应用组件
│   ├── tailwind.config.js  # Tailwind 配置
│   └── package.json        # 前端依赖
└── README.md               # 项目文档
```

## 🚀 快速开始

### 1. 后端启动

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动 Redis (必需)
redis-server

# 启动 Celery Worker
celery -A main.celery_app worker --loglevel=info

# 启动 FastAPI 服务
python main.py
# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

### 3. 访问应用

- 前端界面: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 🎮 使用指南

### 创建研究任务

1. **选择工作模式**:
   - 🤝 **交互模式**: 每个工具调用都需要用户确认
   - ⚡ **副驾驶模式**: 自动执行所有操作
   - 🧭 **引导模式**: AI 提供建议但需要确认

2. **输入研究主题**: 例如 "人工智能发展趋势"

3. **配置参数** (可选):
   - 报告类型、目标读者、章节数量、字数等

4. **开始生成**: 点击"生成报告"按钮

### 交互式确认

当 AI 需要调用工具时，系统会显示确认界面：

- ✅ **允许 (yes)**: 批准工具调用
- ❌ **拒绝 (no)**: 拒绝工具调用
- ✏️ **编辑 (edit)**: 修改工具参数后调用
- ⏭️ **跳过 (response)**: 不调用工具，直接提供反馈

### 实时监控

- 📊 **进度展示**: 实时显示生成进度
- 💭 **思考过程**: AI 的推理和思考过程
- 🔧 **工具调用**: 工具使用情况和结果
- 📖 **大纲更新**: 报告结构的实时构建

## 🔗 API 接口

### 核心接口

```typescript
// 创建任务
POST /research/tasks
{
  "topic": "研究主题",
  "mode": "interactive",
  "max_sections": 3,
  "target_length": 2000
}

// 获取任务状态
GET /research/tasks/{task_id}

// 流式数据 (SSE)
GET /research/tasks/{task_id}/stream

// 取消任务
POST /research/tasks/{task_id}/cancel
```

### 流式消息格式

```typescript
interface StreamMessage {
  message_type: 'step_start' | 'step_progress' | 'tool_call' | 'interrupt_request' | ...;
  content: string;
  node: string;
  timestamp: number;
  // 其他字段根据消息类型变化
}
```

## 🛠️ 开发指南

### 自定义工具

在 `backend/tools/` 目录下添加新工具：

```python
from langchain_core.tools import tool

@tool
def my_custom_tool(query: str) -> str:
    """自定义工具描述"""
    # 工具实现
    return result
```

### 添加新的消息类型

1. 在 `frontend/src/types/index.ts` 中添加类型定义
2. 在 `StreamMessage.tsx` 中添加渲染逻辑
3. 在 `useReportGenerator.ts` 中添加处理逻辑

### 自定义样式

使用 Tailwind CSS 自定义主题：

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        'apple': {
          // 自定义颜色
        }
      }
    }
  }
}
```

## 🔧 环境配置

### 环境变量

**后端** (`.env`):
```bash
REDIS_URL=redis://localhost:6379/0
PG_URL=postgresql://user:pass@localhost/db  # 可选
OPENAI_API_KEY=your_api_key
```

**前端** (`.env`):
```bash
REACT_APP_API_URL=http://localhost:8000
```

### Docker 部署

```bash
# 使用 docker-compose
docker-compose up -d
```

## 📝 更新日志

### v1.0.0 (2024-01-XX)
- ✨ 初始版本发布
- 🎨 苹果风格 UI 设计
- ⚡ 实时流式数据展示
- 🤝 交互式工具确认
- 📊 报告大纲层级展示

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 强大的 AI 工作流框架
- [React](https://reactjs.org/) - 用户界面库
- [Tailwind CSS](https://tailwindcss.com/) - CSS 框架
- [Framer Motion](https://www.framer.com/motion/) - 动画库

---

🌟 **如果这个项目对你有帮助，请给它一个 Star！**