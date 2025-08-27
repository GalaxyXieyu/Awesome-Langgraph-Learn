# Writer配置使用说明

## 🚀 快速开始

### 1. 基本用法
```python
from writer import create_workflow_processor
from writer_config import WriterConfig

# 使用默认配置（自动加载writer_config.yaml）
processor = create_workflow_processor("my_node", "my_agent")

# 或者指定配置文件
config = WriterConfig("custom_config.yaml")
processor = create_workflow_processor("my_node", "my_agent", config=config)
```

### 2. 配置文件修改
直接编辑 `writer_config.yaml` 文件，修改后会自动生效。

## 📋 配置选项详解

### 节点控制 (nodes)
```yaml
nodes:
  subgraph:
    include: ["research", "writing"]  # 只显示研究和写作节点
    exclude: ["debug"]               # 隐藏调试节点
  main:
    include: []                      # 空列表 = 显示所有
    exclude: ["internal"]            # 隐藏内部节点
```

### 消息类型控制 (messages)
```yaml
messages:
  include: []                        # 空 = 显示所有消息类型
  exclude: ["thinking", "reasoning"] # 隐藏思考过程
  # 可用类型: tool_call, tool_result, thinking, reasoning, 
  #          content_streaming, step_progress, step_complete
```

### Agent控制 (agents)
```yaml
agents:
  include: ["research", "writing"]   # 只显示特定Agent
  exclude: ["supervisor"]            # 隐藏监督Agent
```

### 流式控制 (streaming)
```yaml
streaming:
  enabled: true                     # true=流式, false=批量
  batch_size: 10                    # 批量模式时的批次大小
  max_buffer: 100                   # 最大缓冲区
```

### 详细程度 (verbosity)
```yaml
verbosity:
  level: "normal"                   # minimal, normal, detailed, full
  show_metadata: true               # 显示元数据
  show_timing: true                 # 显示时间信息
  show_agent_hierarchy: true        # 显示Agent层级
```

## 🛠️ 实用配置示例

### 示例1: 只看核心输出
```yaml
nodes:
  subgraph:
    include: ["research", "writing"]
messages:
  exclude: ["thinking", "reasoning", "step_progress"]
agents:
  exclude: ["supervisor"]
verbosity:
  level: "minimal"
  show_metadata: false
```

### 示例2: 调试模式（看所有输出）
```yaml
# 所有配置项都为空或true，显示所有信息
verbosity:
  level: "full"
  show_metadata: true
  show_timing: true
  show_agent_hierarchy: true
```

### 示例3: 只看工具调用和结果
```yaml
messages:
  include: ["tool_call", "tool_result", "content_streaming"]
verbosity:
  level: "normal"
  show_timing: false
```

### 示例4: 非流式批量模式
```yaml
streaming:
  enabled: false
  batch_size: 20
messages:
  exclude: ["thinking", "step_progress"]
```

## 🔄 动态重新加载配置

```python
# 在代码中重新加载配置
from writer_config import get_writer_config

config = get_writer_config()
config.reload()  # 重新加载配置文件
```

## 💡 使用技巧

1. **逐步调试**: 先设置 `verbosity.level: "full"` 看全部输出，然后逐步减少
2. **性能优化**: 如果输出太多，使用 `exclude` 排除不需要的消息类型
3. **专注特定Agent**: 使用 `agents.include` 只看特定Agent的输出
4. **批量处理**: 设置 `streaming.enabled: false` 可以减少网络开销

## ⚠️ 注意事项

- 配置文件不存在时会使用默认值（显示所有内容）
- `include` 为空表示包含所有，`exclude` 优先级更高
- 修改配置文件后可能需要重新运行程序才能生效
- YAML格式要求严格，注意缩进和语法