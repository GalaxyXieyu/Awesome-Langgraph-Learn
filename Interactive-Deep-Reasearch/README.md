# Interactive Deep Research 🚀

一个基于LangGraph的高级交互式深度研究报告生成系统，集成了Multi-Agent协作、Human-in-loop交互和实时流式输出。专为前端交互式报告生成设计，支持多种运行模式和智能化工作流。

## ✨ 核心特性

### 🤖 Multi-Agent协作系统
- **智能监督器**: 全局任务协调和智能路由
- **研究专家**: 深度信息收集和多源数据整合  
- **分析专家**: 趋势识别和洞察生成
- **写作专家**: 专业内容创作和报告生成
- **验证专家**: 质量控制和标准验证

### 🔄 Human-in-loop交互
- **交互模式 (Interactive)**: 每个关键步骤需要用户确认
- **副驾驶模式 (Copilot)**: 自动通过所有确认，完全自动化
- **引导模式 (Guided)**: 提供建议但需要用户最终决策
- **智能中断**: 支持工作流中断和恢复

### 📡 实时流式输出
- **多模式流式**: 支持custom、updates、messages等模式
- **进度追踪**: 实时显示执行进度和状态
- **内容展示**: 实时输出大纲结构和完整报告内容
- **打字机效果**: Token级别的实时内容展示
- **前端友好**: 专为Web界面优化的数据格式
- **完整内容流**: 大纲生成时即可看到完整结构，报告完成时即可看到全文

### 🧠 智能化工作流
- **自适应规划**: 根据主题和需求智能制定执行计划
- **动态路由**: 基于执行状态智能选择下一步行动
- **错误恢复**: 完善的异常处理和自动重试机制
- **状态持久化**: 支持工作流中断和恢复

## 🏗️ 系统架构

```
Interactive-Deep-Research/
├── state.py          # 状态管理模块
├── tools.py          # 工具集合模块  
├── graph.py          # 核心工作流图
├── test.py           # 测试和演示脚本
└── README.md         # 项目文档
```

### 📊 状态管理 (state.py)
```python
class DeepResearchState(TypedDict):
    # 基础配置
    topic: str                    # 研究主题
    mode: ReportMode             # 运行模式
    user_id: str                 # 用户ID
    
    # 报告配置  
    report_type: str             # 报告类型
    target_audience: str         # 目标读者
    depth_level: str             # 深度级别
    
    # 核心内容
    outline: Optional[Dict]      # 报告大纲
    research_results: List[Dict] # 研究结果
    analysis_insights: List[Dict] # 分析洞察
    final_report: Optional[str]  # 最终报告
    
    # 交互状态
    user_feedback: Dict[str, Any]     # 用户反馈
    approval_status: Dict[str, bool]  # 审批状态
    
    # 系统状态
    performance_metrics: Dict[str, Any] # 性能指标
    messages: List[BaseMessage]         # 消息历史
```

### 🛠️ 工具系统 (tools.py)
- **搜索工具**: `advanced_web_search`, `multi_source_research`
- **分析工具**: `content_analyzer`, `trend_analyzer`  
- **写作工具**: `section_content_generator`, `report_formatter`
- **验证工具**: `quality_validator`

### 🌊 工作流图 (graph.py)
```python
# 核心节点
intelligent_supervisor_node    # 智能监督协调
outline_generation_node       # 大纲生成
multi_agent_research_node     # Multi-Agent研究
analysis_generation_node      # 分析洞察生成
interaction_nodes            # 交互确认节点

# 工作流程
START → 智能监督 → 大纲生成 → 用户确认 → 深度研究 → 分析生成 → 内容创建 → END
```

## 🚀 快速开始 

### 环境要求
- Python 3.8+
- LangGraph >= 0.1.0
- LangChain >= 0.1.0  
- OpenAI API或兼容API
- Tavily API Key (可选)

### 安装依赖
```bash
pip install langgraph langchain langchain-openai langchain-community
```

### ⚡ 立即体验流式输出

最快的体验方式是运行测试脚本：

```bash
python test.py
```

然后选择 `3` (交互演示模拟) 或 `4` (完整内容展示)，你将立即看到：
- 🔄 实时的生成进度
- 📋 完整的大纲结构流式输出
- 📄 完整的报告内容流式输出
- ⏱️ 详细的性能统计

### 🎯 一分钟快速测试

```bash
python test.py
# 选择 5 (快速功能验证)
# 将在1-2分钟内看到完整的流式输出演示
```

### 基本使用

#### 1. 简单报告生成
```python
import asyncio
from graph import run_deep_research_report
from state import ReportMode

async def generate_report():
    result = await run_deep_research_report(
        topic="人工智能在医疗领域的应用前景",
        user_id="user_001",
        mode=ReportMode.COPILOT,  # 自动模式
        report_type="research",
        target_audience="医疗专业人士",
        depth_level="deep",
        target_length=3000
    )
    
    if result["success"]:
        print(f"✅ 报告生成成功: {result['session_id']}")
        print(f"📊 研究数据: {result['quality_summary']['research_data_count']}条")
        print(f"💡 分析洞察: {result['quality_summary']['analysis_insights_count']}个")
    else:
        print(f"❌ 生成失败: {result['error']}")

# 运行
asyncio.run(generate_report())
```

#### 2. 流式输出使用 - 实时查看大纲和报告
```python
import asyncio
from graph import stream_deep_research_report
from state import ReportMode

async def stream_example():
    outline_received = False
    report_received = False
    
    async for chunk in stream_deep_research_report(
        topic="区块链技术发展趋势",
        user_id="user_002", 
        mode=ReportMode.COPILOT  # 自动模式，完整展示内容
    ):
        chunk_type = chunk.get("type")
        
        if chunk_type == "stream_chunk":
            # 处理流式数据块
            data = chunk.get("data", {})
            if isinstance(data, tuple) and len(data) == 2:
                mode, content = data
                if mode == "custom":
                    step = content.get("step", "")
                    status = content.get("status", "")
                    progress = content.get("progress", 0)
                    print(f"[{progress:3d}%] {step}: {status}")
                    
                    # ========== 实时内容展示 ==========
                    content_data = content.get("content")
                    if content_data and progress == 100:
                        content_type = content_data.get("type")
                        
                        # 显示完整大纲
                        if content_type == "outline" and not outline_received:
                            outline_received = True
                            print("\\n" + "="*50)
                            print("📋 实时大纲展示:")
                            print("="*50)
                            
                            display_text = content_data.get("display_text", "")
                            if display_text:
                                print(display_text)
                            
                            print("="*50)
                        
                        # 显示完整报告
                        elif content_type == "final_report" and not report_received:
                            report_received = True
                            print("\\n" + "="*50)
                            print("📄 完整报告内容:")
                            print("="*50)
                            
                            full_report = content_data.get("full_report", "")
                            if full_report:
                                print(full_report)
                            
                            print("="*50)
                    
        elif chunk_type == "stream_complete":
            print("\\n✅ 流式生成完成")
            print(f"📋 大纲展示: {'✅' if outline_received else '❌'}")
            print(f"📄 报告展示: {'✅' if report_received else '❌'}")
            break
            
        elif chunk_type == "stream_error":
            print(f"❌ 生成错误: {chunk.get('error')}")
            break

# 运行流式示例
asyncio.run(stream_example())
```

#### 3. 交互模式处理
```python
from langgraph.types import interrupt

# 在交互模式中，系统会在关键点暂停等待用户输入
# 用户需要处理interrupt消息并提供响应

def handle_user_interaction(interrupt_data):
    """处理用户交互"""
    interaction_type = interrupt_data.get("type")
    message = interrupt_data.get("message")
    options = interrupt_data.get("options", [])
    
    print(f"🤝 {message}")
    print(f"选项: {', '.join(options)}")
    
    # 返回用户选择
    return {"approved": True, "choice": options[0]}
```

## 📋 运行模式

### 🤖 Copilot模式 (自动模式)
```python
mode=ReportMode.COPILOT
```
- ✅ 完全自动化执行
- ✅ 无需用户干预  
- ✅ 最快的执行速度
- ✅ 适合批量处理

### 🤝 Interactive模式 (交互模式)
```python
mode=ReportMode.INTERACTIVE
```
- 🛑 关键步骤需要用户确认
- 🎯 用户可以调整方向
- 📝 支持实时反馈
- 🎨 最高的定制化程度

### 🧭 Guided模式 (引导模式)
```python
mode=ReportMode.GUIDED
```
- 💡 系统提供建议
- 🤔 用户做最终决策
- ⚖️ 平衡自动化和控制
- 🎓 适合学习和探索

## 🛠️ 高级配置

### 报告类型配置
```python
# 研究报告 - 重点是信息收集和综合分析
report_type="research"

# 分析报告 - 重点是趋势分析和洞察
report_type="analysis"  

# 市场报告 - 重点是市场数据和预测
report_type="market"

# 技术报告 - 重点是技术深度和实现
report_type="technical"
```

### 深度级别配置
```python
# 浅层研究 - 快速概览
depth_level="shallow"

# 中等深度 - 平衡深度和速度  
depth_level="medium"

# 深度研究 - 全面深入分析
depth_level="deep"
```

### 自定义工具配置
```python
from tools import get_all_tools, advanced_web_search

# 获取所有可用工具
tools = get_all_tools()

# 自定义搜索参数
search_result = advanced_web_search.invoke({
    "query": "深度学习最新进展",
    "max_results": 10,
    "search_depth": "advanced"
})
```

## 📊 性能优化

### 并发处理
```python
# 系统自动进行并发研究
# 多个章节的研究会并行执行
# 分析和洞察生成会复用数据
```

### 缓存机制
```python
# 研究结果自动缓存
# 相似查询会复用结果
# 减少重复的API调用
```

### 流式优化
```python
# Token级别的实时输出
# 渐进式结果展示
# 最小化延迟感知
```

## 🧪 测试和演示

### 运行综合测试 - 全流式输出展示
```bash
python test.py
```

选择测试模式:
1. **📋 综合测试套件** - 完整功能验证，包含流式内容展示
2. **⚡ 性能基准测试** - 实时性能监控和阶段计时
3. **🎭 交互演示模拟** - 完整大纲和报告内容的流式展示
4. **📄 完整内容展示** - 详细的大纲结构和完整报告文本
5. **⚡ 快速功能验证** - 流式输出的快速测试
6. **🔧 仅环境检查** - 工具和API状态验证

### 🌊 流式输出特性展示

所有测试模式都已升级为**流式输出**，你将能够：

#### 📋 实时查看大纲生成
```
============================================================
📋 生成的报告大纲 (实时流式输出)
============================================================
🎯 报告标题：Python机器学习入门
📝 执行摘要：本报告旨在为编程初学者提供一个全面的Python机器学习入门指南...
📚 研究章节：
  1. 引言
     介绍报告的目的、背景和重要性。
  2. Python基础
     介绍Python编程语言的基本概念和语法...
============================================================
```

#### 📄 实时查看完整报告
```
============================================================
📄 最终报告内容 (实时流式输出)
============================================================
# Python机器学习入门

## 引言
机器学习作为人工智能的核心分支，正在各个领域产生深远影响...

## Python基础
Python作为一门简洁而强大的编程语言，已成为机器学习领域的首选工具...
============================================================
```

#### ⚡ 实时性能监控
```
📊 基准测试 1: 快速AI应用测试
  🔄 大纲生成完成: 45.2s
  🔍 研究完成: 120.5s  
  📝 内容生成完成: 150.8s
  ✅ 总执行时间: 150.8s (预期: 120s)
  📈 性能比率: 1.26
  📊 数据块处理: 186个
```

### 测试用例
```python
# 系统包含优化的流式测试用例
STREAMING_TEST_CASES = [
    {
        "name": "AI技术应用",
        "topic": "人工智能在智慧医疗中的应用前景",
        "mode": ReportMode.COPILOT,
        "target_length": 1200,
        "depth_level": "medium",
        "expected_duration": 180
    },
    {
        "name": "教育技术发展", 
        "topic": "在线教育平台的用户体验设计",
        "mode": ReportMode.INTERACTIVE,
        "target_length": 1000,
        "depth_level": "medium", 
        "expected_duration": 150
    }
]
```

## 🎯 应用场景

### 📊 商业分析
- 市场研究报告
- 竞争对手分析  
- 行业趋势分析
- 投资决策支持

### 🔬 学术研究
- 文献综述生成
- 研究现状分析
- 技术发展报告
- 学科前沿调研

### 💼 企业应用
- 产品调研报告
- 技术选型分析
- 业务发展规划
- 风险评估报告

### 🎓 教育培训
- 教学材料准备
- 课程内容设计
- 知识点总结
- 案例研究分析

## 🔧 扩展开发

### 添加新的Agent
```python
from langgraph.prebuilt import create_react_agent
from tools import get_custom_tools

# 创建专业化Agent
custom_agent = create_react_agent(
    llm=create_llm(),
    tools=get_custom_tools(),
    prompt="你是一个专业的...专家"
)

# 添加到Agent注册表
agents[AgentType.CUSTOM] = custom_agent
```

### 自定义工具开发
```python
from langchain_core.tools import tool
from typing import Dict, Any

@tool
def custom_analysis_tool(data: str, analysis_type: str) -> Dict[str, Any]:
    """自定义分析工具"""
    # 实现分析逻辑
    return {"result": "分析结果"}

# 将工具添加到工具集
custom_tools = [custom_analysis_tool]
```

### 新交互类型
```python
from state import InteractionType

# 定义新的交互类型
class CustomInteractionType(str, Enum):
    CUSTOM_APPROVAL = "custom_approval"

# 创建对应的交互节点
custom_interaction_node = create_interaction_node(
    CustomInteractionType.CUSTOM_APPROVAL
)
```

## 🔍 监控和调试

### 日志配置
```python
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 跟踪执行过程
logger.info("开始报告生成...")
```

### 性能监控
```python
# 系统自动收集性能指标
performance_metrics = {
    "start_time": 1234567890,
    "agent_execution_times": {
        "researcher": 45.2,
        "analyst": 23.1,
        "writer": 67.8
    },
    "interaction_count": 3,
    "research_queries_count": 15,
    "total_words_generated": 3247
}
```

### 错误处理
```python
# 完善的错误恢复机制
try:
    result = await run_deep_research_report(...)
except Exception as e:
    logger.error(f"生成失败: {e}")
    # 系统会自动重试或提供替代方案
```

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 贡献类型
- 🐛 Bug修复
- ✨ 新功能开发
- 📚 文档改进
- 🧪 测试用例增加
- 🎨 UI/UX改进

### 开发流程
1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目的支持：
- [LangChain](https://github.com/langchain-ai/langchain) - 强大的LLM应用框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - 状态图工作流引擎
- [Tavily](https://tavily.com/) - 高质量搜索API
- [OpenAI](https://openai.com/) - 先进的语言模型

## 📞 联系我们

- 🐛 问题反馈: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 讨论交流: [GitHub Discussions](https://github.com/your-repo/discussions)
- 📧 邮件联系: your-email@example.com

---

<div align="center">

**🚀 Interactive Deep Research - 让AI研究更智能、更交互、更高效！**

⭐ 如果这个项目对您有帮助，请给我们一个Star！

</div>

# 交互打断功能系统分析

## 📋 功能概述

Interactive Deep Research 系统实现了完整的 Human-in-loop 交互打断机制，支持用户在报告生成过程中的关键节点进行干预和控制。

## 🏗️ 系统架构

### 1. 核心组件

```
交互系统架构:
├── InteractionType 枚举     # 定义5种交互类型
├── ReportMode 枚举          # 定义3种运行模式  
├── create_interaction_node  # 交互节点工厂函数
├── get_interaction_config   # 交互配置管理
└── format_interaction_message # 消息格式化器
```

### 2. 交互类型定义

| 交互类型 | 触发时机 | 用途 | 配置选项 |
|---------|---------|------|----------|
| `OUTLINE_CONFIRMATION` | 大纲生成后 | 确认研究大纲是否符合需求 | 确认继续/修改大纲/重新生成 |
| `RESEARCH_PERMISSION` | 开始研究前 | 授权进行网络搜索和数据收集 | 允许研究/跳过研究/限制范围 |
| `ANALYSIS_APPROVAL` | 分析完成后 | 审批分析结果和洞察质量 | 确认分析/重新分析/调整方向 |
| `CONTENT_REVIEW` | 内容生成后 | 审查报告内容质量和准确性 | 通过审查/修改内容/重写章节 |
| `FINAL_APPROVAL` | 报告完成前 | 最终确认和发布批准 | 最终确认/再次修改/生成新版本 |

### 3. 运行模式对比

| 模式 | 说明 | 交互方式 | 适用场景 |
|------|------|----------|----------|
| **COPILOT** | 自动化模式 | 所有交互点自动通过 | 批量处理、快速生成 |
| **INTERACTIVE** | 完全交互模式 | 每个交互点都需要用户确认 | 高质量定制、精确控制 |
| **GUIDED** | 引导模式 | 系统提供建议，用户决策 | 平衡自动化和控制性 |

## 🔧 技术实现

### 1. 交互节点工厂

```python
def create_interaction_node(interaction_type: InteractionType):
    def interaction_node(state: DeepResearchState) -> DeepResearchState:
        # 1. 检查运行模式
        # 2. COPILOT模式自动通过
        # 3. 其他模式使用interrupt()等待用户输入
        # 4. 处理用户响应并更新状态
        # 5. 记录交互历史
    return interaction_node
```

### 2. 中断机制

```python
# 使用LangGraph的interrupt功能暂停工作流
user_response = interrupt({
    "type": interaction_type.value,
    "title": "交互标题",
    "message": "详细提示信息", 
    "options": ["选项1", "选项2", "选项3"],
    "default": "默认选项"
})
```

### 3. 状态管理

```python
# 记录用户反馈
state["user_feedback"][interaction_type.value] = user_response

# 记录审批状态  
state["approval_status"][interaction_type.value] = approved

# 添加交互历史
add_user_interaction(state, interaction_type.value, user_response)
```

## 📊 流式输出集成

交互功能与流式输出完全集成：

```python
writer({
    "step": f"interaction_{interaction_type.value}",
    "status": "等待用户确认", 
    "progress": 50,
    "awaiting_user_input": True,
    "interaction_type": interaction_type.value,
    "message": formatted_message,
    "options": available_options
})
```

## 🎯 使用示例

### 1. 自动化模式（COPILOT）

```python
result = await run_deep_research_report(
    topic="AI应用研究",
    mode=ReportMode.COPILOT,  # 自动通过所有交互点
    user_id="auto_user"
)
```

### 2. 交互模式（INTERACTIVE）

```python
# 需要配合checkpointer和interrupt handler
result = await run_deep_research_report(
    topic="AI应用研究", 
    mode=ReportMode.INTERACTIVE,  # 每个交互点都需要确认
    user_id="interactive_user"
)

# 在工作流执行中会触发interrupt，需要外部处理：
def handle_interrupt(interrupt_data):
    print(f"用户确认: {interrupt_data['message']}")
    return {"approved": True, "choice": "确认继续"}
```

### 3. 流式交互模式

```python
async for chunk in stream_deep_research_report(
    topic="AI应用研究",
    mode=ReportMode.INTERACTIVE
):
    if chunk.get("type") == "stream_chunk":
        data = chunk.get("data", {})
        if isinstance(data, tuple):
            mode, content = data
            if content.get("awaiting_user_input"):
                # 处理用户交互请求
                interaction_type = content.get("interaction_type")
                message = content.get("message")  
                options = content.get("options")
                # 显示给用户并获取响应
```

## 🛠️ 配置管理

每种交互类型都有专门的配置：

```python
INTERACTION_CONFIGS = {
    InteractionType.OUTLINE_CONFIRMATION: {
        "title": "大纲确认",
        "copilot_message": "自动确认报告大纲，继续执行研究",
        "options": ["确认继续", "修改大纲", "重新生成"],
        "default": "确认继续"
    },
    # ... 其他配置
}
```

## 📝 消息格式化

为不同交互类型提供定制化的用户提示：

```python
def format_interaction_message(state, interaction_type, config):
    if interaction_type == InteractionType.OUTLINE_CONFIRMATION:
        # 展示详细的大纲信息供用户确认
        return formatted_outline_message
    elif interaction_type == InteractionType.RESEARCH_PERMISSION:
        # 说明研究范围和时间预估
        return formatted_research_message  
    # ... 其他格式化逻辑
```

## 🔄 工作流集成

交互节点完全集成到LangGraph工作流中：

```python
# 工作流定义
graph.add_node("outline_generation", outline_generation_node)
graph.add_node("outline_confirmation", outline_confirmation_node)  # 交互节点
graph.add_node("research_execution", multi_agent_research_node)
graph.add_node("research_permission", research_permission_node)    # 交互节点

# 路由逻辑
graph.add_edge("outline_generation", "outline_confirmation") 
graph.add_edge("outline_confirmation", "research_execution")
```

## 🎮 前端集成建议

### 1. Web界面交互

```javascript
// 监听流式数据中的交互请求
if (chunk.awaiting_user_input) {
    showInteractionDialog({
        title: chunk.interaction_type,
        message: chunk.message,
        options: chunk.options,
        onConfirm: (response) => {
            // 恢复工作流执行
            continueWorkflow(response);
        }
    });
}
```

### 2. 状态持久化

```python
# 使用checkpointer支持工作流中断和恢复
checkpointer = InMemorySaver()
config = {"configurable": {"thread_id": "user_session_001"}}

# 中断后可以从断点恢复
result = await graph.ainvoke(initial_state, config=config)
```

## 🚀 扩展功能

### 1. 自定义交互类型

```python
class CustomInteractionType(str, Enum):
    CUSTOM_REVIEW = "custom_review"

# 添加自定义配置
INTERACTION_CONFIGS[CustomInteractionType.CUSTOM_REVIEW] = {
    "title": "自定义审查",
    "options": ["通过", "修改", "拒绝"],
    "default": "通过"
}
```

### 2. 条件交互

```python
def conditional_interaction_node(state):
    """根据条件决定是否需要交互"""
    if should_require_interaction(state):
        return interaction_node(state)
    else:
        return auto_approve_node(state)
```

## 📈 监控和分析

系统自动记录交互统计：

```python
# 性能指标中包含交互数据
performance_metrics = {
    "interaction_count": 5,           # 交互次数
    "avg_response_time": 15.2,        # 平均响应时间  
    "approval_rate": 0.8,             # 批准率
    "interaction_types": [            # 交互类型分布
        "outline_confirmation", 
        "research_permission",
        "analysis_approval"
    ]
}
```

## ✨ 核心优势

1. **🔄 灵活性**: 支持完全自动化到完全手动的各种模式
2. **📊 可视化**: 完整的流式输出和进度跟踪  
3. **💾 持久化**: 支持工作流中断和恢复
4. **🎯 精确控制**: 在关键决策点提供用户控制
5. **📈 可扩展**: 易于添加新的交互类型和配置
6. **🔧 集成性**: 与整个报告生成系统无缝集成

这套交互打断功能系统为用户提供了在自动化和人工控制之间的完美平衡，确保既能享受AI的效率，又能保持对结果质量的精确控制。