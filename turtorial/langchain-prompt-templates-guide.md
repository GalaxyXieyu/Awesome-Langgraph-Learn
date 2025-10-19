# LangChain Prompt Templates 完全指南

## 📋 目录

- [1. 概述](#1-概述)
- [2. 基础模板类型](#2-基础模板类型)
- [3. 聊天模板类型](#3-聊天模板类型)
- [4. 高级模板类型](#4-高级模板类型)
- [5. 辅助组件](#5-辅助组件)
- [6. 工具函数](#6-工具函数)
- [7. 类型对比与选择指南](#7-类型对比与选择指南)
- [8. 最佳实践](#8-最佳实践)

---

## 1. 概述

### 1.1 什么是 Prompt Template?

Prompt Template 是 LangChain 中用于**构建可复用、动态化提示词**的工具。它们帮助:

- **翻译用户输入**: 将用户输入和参数转换为 LLM 指令
- **保持一致性**: 确保提示词格式统一
- **提高可维护性**: 模板化管理,减少重复代码
- **动态定制**: 通过变量插值生成个性化提示

### 1.2 核心概念

**PromptValue:**
- 所有模板的输出都是 `PromptValue` 对象
- 可以传递给 LLM 或 ChatModel
- 可以转换为字符串或消息列表
- 便于在字符串和消息之间切换

**输入字典:**
- 模板接收字典作为输入
- 每个键对应模板中的一个变量
- 运行时填充变量生成最终提示

---

## 2. 基础模板类型

### 2.1 PromptTemplate (字符串模板)

**定义:** 用于格式化单个字符串的基础模板,适用于简单输入场景。

**特点:**
- 最简单的模板类型
- 用于 Completion 模式的 LLM
- 支持 Python f-string 风格的变量插值

**使用场景:**
- Completion 风格的模型 (如 text-davinci-003)
- 简单的单轮问答
- 不需要角色区分的场景

**代码示例:**

```python
from langchain_core.prompts import PromptTemplate

# 创建模板
prompt_template = PromptTemplate.from_template(
    "Tell me a joke about {topic}"
)

# 填充变量
filled_prompt = prompt_template.invoke({"topic": "cats"})
print(filled_prompt)
# 输出: Tell me a joke about cats
```

**多变量示例:**

```python
template = """You are a helpful assistant.
Human: Tell me a {adjective} story about a {animal}.
Assistant:"""

prompt = PromptTemplate.from_template(template)
result = prompt.invoke({
    "adjective": "funny", 
    "animal": "panda"
})
```

### 2.2 StringPromptTemplate

**定义:** `PromptTemplate` 的基类,用于自定义字符串模板。

**使用场景:**
- 需要自定义模板格式化逻辑
- 扩展标准模板功能

**示例:**

```python
from langchain_core.prompts import StringPromptTemplate

class CustomPromptTemplate(StringPromptTemplate):
    def format(self, **kwargs) -> str:
        # 自定义格式化逻辑
        return f"Custom: {kwargs.get('text', '')}"
```

---

## 3. 聊天模板类型

### 3.1 ChatPromptTemplate (聊天模板)

**定义:** 用于格式化消息列表的模板,支持角色区分 (system/user/assistant)。

**特点:**
- 支持多消息结构
- 每条消息有明确的角色标识
- 适用于现代聊天模型 (GPT-4, Claude, Gemini)

**使用场景:**
- Chat 风格的 LLM
- 需要系统提示词的场景
- 多轮对话应用

**基础示例:**

```python
from langchain_core.prompts import ChatPromptTemplate

# 方式1: 使用元组
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    ("user", "Tell me a joke about {topic}")
])

# 填充变量
messages = chat_prompt.invoke({"topic": "cats"})
```

**输出结构:**

```python
[
    SystemMessage(content="You are a helpful assistant"),
    HumanMessage(content="Tell me a joke about cats")
]
```

**多变量示例:**

```python
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a comedian who tells jokes about {topic}."),
    ("human", "Tell me {joke_count} jokes.")
])

messages = chat_prompt.invoke({
    "topic": "lawyers", 
    "joke_count": 3
})
```

### 3.2 BaseChatPromptTemplate

**定义:** 所有聊天模板的抽象基类。

**使用场景:**
- 创建自定义聊天模板
- 扩展聊天模板功能

### 3.3 AIMessagePromptTemplate

**定义:** 用于创建 AI/Assistant 消息的模板。

**使用场景:**
- Few-shot 示例中的 AI 回复
- 预设 AI 响应

**示例:**

```python
from langchain_core.prompts import AIMessagePromptTemplate

ai_template = AIMessagePromptTemplate.from_template(
    "The capital of {country} is {capital}."
)
```

### 3.4 HumanMessagePromptTemplate

**定义:** 用于创建 Human/User 消息的模板。

**使用场景:**
- 用户消息模板
- Few-shot 示例中的用户输入

**示例:**

```python
from langchain_core.prompts import HumanMessagePromptTemplate

human_template = HumanMessagePromptTemplate.from_template(
    "What is the capital of {country}?"
)
```

### 3.5 SystemMessagePromptTemplate

**定义:** 用于创建系统消息的模板。

**使用场景:**
- 设定 AI 角色和行为
- 提供全局指令

**示例:**

```python
from langchain_core.prompts import SystemMessagePromptTemplate

system_template = SystemMessagePromptTemplate.from_template(
    "You are a {role} who {behavior}."
)

message = system_template.format(
    role="teacher",
    behavior="explains concepts clearly"
)
```

### 3.6 ChatMessagePromptTemplate

**定义:** 用于创建任意角色消息的模板。

**使用场景:**
- 自定义角色名称
- 特殊角色消息 (如 "function", "tool")

**示例:**

```python
from langchain_core.prompts import ChatMessagePromptTemplate

custom_template = ChatMessagePromptTemplate.from_template(
    role="moderator",
    template="Moderating the discussion about {topic}"
)
```

### 3.7 BaseStringMessagePromptTemplate

**定义:** 字符串消息模板的基类。

---

## 4. 高级模板类型

### 4.1 FewShotPromptTemplate (少样本提示模板)

**定义:** 用于包含示例的提示模板,实现 Few-shot Learning。

**特点:**
- 包含多个示例 (examples)
- 可以固定示例或动态选择
- 提高模型理解任务的能力

**使用场景:**
- 需要提供示例指导模型
- 格式化任务 (如翻译、分类)
- 提高模型准确性

**示例:**

```python
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

# 定义示例
examples = [
    {"input": "happy", "output": "sad"},
    {"input": "tall", "output": "short"},
    {"input": "hot", "output": "cold"}
]

# 定义示例模板
example_template = PromptTemplate(
    input_variables=["input", "output"],
    template="Input: {input}\nOutput: {output}"
)

# 创建 Few-shot 模板
few_shot_prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_template,
    prefix="Find the antonym:",
    suffix="Input: {word}\nOutput:",
    input_variables=["word"]
)

# 使用
result = few_shot_prompt.format(word="big")
```

**输出:**

```
Find the antonym:

Input: happy
Output: sad

Input: tall
Output: short

Input: hot
Output: cold

Input: big
Output:
```

### 4.2 FewShotChatMessagePromptTemplate (聊天少样本模板)

**定义:** 用于聊天模型的 Few-shot 模板。

**特点:**
- 支持聊天格式的示例
- 每个示例包含多条消息
- 可动态选择示例

**使用场景:**
- 聊天模型的 Few-shot Learning
- 对话格式示例
- 复杂任务指导

**示例:**

```python
from langchain_core.prompts import (
    FewShotChatMessagePromptTemplate,
    ChatPromptTemplate
)

# 定义示例
examples = [
    {
        "input": "What's 2+2?",
        "output": "2+2 equals 4."
    },
    {
        "input": "What's 5*5?",
        "output": "5*5 equals 25."
    }
]

# 定义示例模板
example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai", "{output}")
])

# 创建 Few-shot 聊天模板
few_shot_prompt = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=example_prompt
)

# 组合到最终模板
final_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a math tutor"),
    few_shot_prompt,
    ("human", "{input}")
])
```

### 4.3 FewShotPromptWithTemplates

**定义:** 支持多个示例模板的 Few-shot 模板。

**使用场景:**
- 不同类型的示例需要不同格式
- 复杂的示例结构

### 4.4 ImagePromptTemplate (图像模板)

**定义:** 用于多模态模型的图像提示模板。

**特点:**
- 支持图像 URL
- 支持 base64 编码图像
- 用于 Vision 模型

**使用场景:**
- GPT-4 Vision, Claude 3 等多模态模型
- 图像分析任务
- 图文混合提示

**示例:**

```python
from langchain_core.prompts import ImagePromptTemplate

# 方式1: 使用 URL
image_prompt = ImagePromptTemplate(
    template={"url": "https://example.com/image.jpg"}
)

# 方式2: 使用变量
image_prompt = ImagePromptTemplate(
    input_variables=["image_url"],
    template={"url": "{image_url}"}
)

# 使用
result = image_prompt.invoke({
    "image_url": "https://example.com/cat.jpg"
})
```

**与文本结合:**

```python
from langchain_core.prompts import ChatPromptTemplate

multimodal_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful image analyzer"),
    ("human", [
        {"type": "text", "text": "What's in this image?"},
        {"type": "image_url", "image_url": "{image_url}"}
    ])
])
```

### 4.5 StructuredPrompt

**定义:** 用于结构化输出的提示模板。

**使用场景:**
- 需要 JSON 格式输出
- 函数调用 (Function Calling)
- 结构化数据提取

**示例:**

```python
from langchain_core.prompts import StructuredPrompt
from pydantic import BaseModel, Field

class PersonInfo(BaseModel):
    name: str = Field(description="Person's name")
    age: int = Field(description="Person's age")
    occupation: str = Field(description="Person's occupation")

structured_prompt = StructuredPrompt.from_messages(
    [("human", "Extract information: {text}")],
    schema=PersonInfo
)
```

---

## 5. 辅助组件

### 5.1 MessagesPlaceholder (消息占位符)

**定义:** 用于在模板中插入动态消息列表的占位符。

**特点:**
- 可以插入任意数量的消息
- 常用于聊天历史
- 保持消息顺序

**使用场景:**
- 插入对话历史
- 动态消息列表
- 多轮对话管理

**基础示例:**

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# 创建模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}")
])

# 使用
chat_history = [
    HumanMessage(content="What's the capital of France?"),
    AIMessage(content="Paris is the capital of France.")
]

messages = prompt.invoke({
    "chat_history": chat_history,
    "input": "What about Germany?"
})
```

**输出:**

```python
[
    SystemMessage(content="You are a helpful assistant"),
    HumanMessage(content="What's the capital of France?"),
    AIMessage(content="Paris is the capital of France."),
    HumanMessage(content="What about Germany?")
]
```

**简化写法:**

```python
# 使用 ("placeholder", "{variable_name}") 元组
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    ("placeholder", "{chat_history}"),
    ("human", "{input}")
])
```

### 5.2 BaseMessagePromptTemplate

**定义:** 所有消息模板的抽象基类。

### 5.3 DictPromptTemplate

**定义:** 用于字典格式提示的模板。

**使用场景:**
- 结构化输入
- 复杂数据格式

---

## 6. 工具函数

### 6.1 aformat_document / format_document

**定义:** 用于格式化文档对象的工具函数。

**使用场景:**
- RAG (检索增强生成) 系统
- 文档处理
- 格式化检索结果

**示例:**

```python
from langchain_core.prompts import format_document
from langchain_core.documents import Document

doc = Document(
    page_content="LangChain is a framework...",
    metadata={"source": "docs.langchain.com"}
)

template = "Source: {source}\nContent: {page_content}"
formatted = format_document(doc, template)
```

### 6.2 load_prompt / load_prompt_from_config

**定义:** 从文件或配置加载提示模板。

**使用场景:**
- 提示词版本管理
- 配置文件管理
- 团队协作

**示例:**

```yaml
# prompt.yaml
_type: "prompt"
template: "Tell me a joke about {topic}"
input_variables: ["topic"]
```

```python
from langchain_core.prompts import load_prompt

prompt = load_prompt("prompt.yaml")
```

### 6.3 check_valid_template

**定义:** 验证模板字符串是否有效。

**使用场景:**
- 模板验证
- 错误预防

### 6.4 get_template_variables

**定义:** 提取模板中的所有变量。

**示例:**

```python
from langchain_core.prompts import get_template_variables

template = "Tell me about {topic} and {subtopic}"
variables = get_template_variables(template)
# 返回: ["topic", "subtopic"]
```

### 6.5 jinja2_formatter / mustache_formatter

**定义:** 支持 Jinja2 和 Mustache 模板语法的格式化器。

**使用场景:**
- 复杂模板逻辑 (循环、条件)
- 团队习惯的模板语法

**Jinja2 示例:**

```python
from langchain_core.prompts import PromptTemplate

template = """
{% for item in items %}
- {{ item }}
{% endfor %}
"""

prompt = PromptTemplate(
    template=template,
    input_variables=["items"],
    template_format="jinja2"
)

result = prompt.format(items=["apple", "banana", "orange"])
```

---

## 7. 类型对比与选择指南

### 7.1 基础模板对比

| 模板类型 | 输出格式 | 适用模型 | 复杂度 | 使用场景 |
|---------|---------|---------|--------|---------|
| **PromptTemplate** | 字符串 | Completion 模型 | ⭐ | 简单单轮问答 |
| **ChatPromptTemplate** | 消息列表 | Chat 模型 | ⭐⭐ | 多轮对话、角色区分 |
| **FewShotPromptTemplate** | 字符串 + 示例 | Completion 模型 | ⭐⭐⭐ | 需要示例指导 |
| **FewShotChatMessagePromptTemplate** | 消息列表 + 示例 | Chat 模型 | ⭐⭐⭐ | 聊天模型 Few-shot |
| **ImagePromptTemplate** | 多模态 | Vision 模型 | ⭐⭐ | 图像分析 |
| **StructuredPrompt** | 结构化 | 支持函数调用的模型 | ⭐⭐⭐ | 结构化输出 |

### 7.2 消息模板对比

| 模板类型 | 角色 | 使用频率 | 典型用途 |
|---------|------|---------|---------|
| **SystemMessagePromptTemplate** | system | 高 | 设定 AI 角色 |
| **HumanMessagePromptTemplate** | user | 高 | 用户输入 |
| **AIMessagePromptTemplate** | assistant | 中 | Few-shot 示例 |
| **ChatMessagePromptTemplate** | 自定义 | 低 | 特殊角色 |

### 7.3 选择流程图

```
是否需要角色区分?
├─ 否 → PromptTemplate
└─ 是 → 是否需要示例?
    ├─ 否 → ChatPromptTemplate
    └─ 是 → 是否需要图像?
        ├─ 否 → FewShotChatMessagePromptTemplate
        └─ 是 → ImagePromptTemplate + ChatPromptTemplate
```

### 7.4 实际场景映射

| 场景 | 推荐模板 | 理由 |
|------|---------|------|
| **简单文本生成** | PromptTemplate | 最简单直接 |
| **聊天机器人** | ChatPromptTemplate + MessagesPlaceholder | 支持多轮对话历史 |
| **翻译任务** | FewShotPromptTemplate | 提供翻译示例 |
| **数据提取** | StructuredPrompt | 确保输出格式 |
| **图像描述** | ImagePromptTemplate | 多模态输入 |
| **客服机器人** | ChatPromptTemplate + SystemMessage | 角色设定 + 对话 |
| **Few-shot 分类** | FewShotChatMessagePromptTemplate | 示例 + 聊天格式 |

---

## 8. 最佳实践

### 8.1 模板设计原则

#### 1. 明确性

```python
# ❌ 不清晰
template = "Do something with {input}"

# ✅ 清晰
template = "Translate the following English text to French: {text}"
```

#### 2. 一致性

```python
# ✅ 保持角色一致
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}"),
    ("human", "{input}"),
    # 始终保持 system → human → ai 的顺序
])
```

#### 3. 可复用性

```python
# ✅ 创建可复用组件
SYSTEM_TEMPLATE = SystemMessagePromptTemplate.from_template(
    "You are a helpful {role}"
)

# 在多个场景复用
customer_service_prompt = ChatPromptTemplate.from_messages([
    SYSTEM_TEMPLATE,
    ("human", "{query}")
])
```

### 8.2 变量命名规范

```python
# ✅ 使用描述性变量名
good_template = "Summarize this {document_type}: {content}"

# ❌ 避免模糊变量名
bad_template = "Do this: {x} and {y}"
```

### 8.3 错误处理

```python
from langchain_core.prompts import PromptTemplate

template = "Tell me about {topic}"
prompt = PromptTemplate.from_template(template)

# ✅ 验证输入
try:
    result = prompt.invoke({"topic": "Python"})
except KeyError as e:
    print(f"Missing variable: {e}")
```

### 8.4 动态消息注意事项

```python
from langchain_core.messages import HumanMessage

# ❌ 不支持: HumanMessage 中使用变量
messages = [
    ("system", "You are a comedian about {topic}."),
    HumanMessage(content="Tell me {count} jokes.")  # 无法填充 {count}
]

# ✅ 正确: 使用元组
messages = [
    ("system", "You are a comedian about {topic}."),
    ("human", "Tell me {count} jokes.")  # 可以填充变量
]
```

### 8.5 性能优化

```python
# ✅ 缓存常用模板
from functools import lru_cache

@lru_cache(maxsize=128)
def get_translation_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", "You are a translator"),
        ("human", "Translate to {language}: {text}")
    ])
```

### 8.6 版本管理

```python
# ✅ 使用配置文件管理提示词
# prompts/v1/translation.yaml
_type: "chat_prompt"
messages:
  - role: "system"
    content: "You are a translator"
  - role: "human"
    content: "Translate to {language}: {text}"

# 代码中加载
from langchain_core.prompts import load_prompt

translation_prompt = load_prompt("prompts/v1/translation.yaml")
```

### 8.7 测试策略

```python
import pytest
from langchain_core.prompts import ChatPromptTemplate

def test_prompt_template():
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a {role}"),
        ("human", "{input}")
    ])
    
    # 测试变量填充
    result = prompt.invoke({
        "role": "teacher",
        "input": "Explain gravity"
    })
    
    assert len(result.messages) == 2
    assert result.messages[0].content == "You are a teacher"
    assert result.messages[1].content == "Explain gravity"
```

---

## 9. 常见问题与解决方案

### 9.1 变量未填充错误

**问题:**
```python
KeyError: 'topic'
```

**原因:** 模板中的变量未在 `invoke()` 中提供。

**解决:**
```python
# 确保所有变量都提供
prompt.invoke({"topic": "cats"})  # ✅

# 或设置默认值
template = PromptTemplate(
    template="Tell me about {topic}",
    input_variables=["topic"],
    partial_variables={"topic": "general topics"}
)
```

### 9.2 MessagesPlaceholder 不生效

**问题:** 传入的消息没有插入到模板中。

**原因:** 传入的不是消息对象列表。

**解决:**
```python
from langchain_core.messages import HumanMessage, AIMessage

# ✅ 正确: 使用消息对象
chat_history = [
    HumanMessage(content="Hi"),
    AIMessage(content="Hello!")
]

# ❌ 错误: 使用字符串
chat_history = ["Hi", "Hello!"]
```

### 9.3 Jinja2 模板语法冲突

**问题:** 使用 `{variable}` 时与 Jinja2 语法冲突。

**解决:**
```python
# 指定模板格式
prompt = PromptTemplate(
    template="Tell me about {{ topic }}",  # Jinja2 语法
    input_variables=["topic"],
    template_format="jinja2"
)
```

---

## 10. 快速参考

### 常用模板创建模式

```python
# 1. 简单字符串模板
from langchain_core.prompts import PromptTemplate
simple = PromptTemplate.from_template("Tell me about {topic}")

# 2. 聊天模板
from langchain_core.prompts import ChatPromptTemplate
chat = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}"),
    ("human", "{input}")
])

# 3. 带历史的聊天模板
from langchain_core.prompts import MessagesPlaceholder
with_history = ChatPromptTemplate.from_messages([
    ("system", "You are helpful"),
    MessagesPlaceholder("history"),
    ("human", "{input}")
])

# 4. Few-shot 模板
from langchain_core.prompts import FewShotChatMessagePromptTemplate
few_shot = FewShotChatMessagePromptTemplate(
    examples=[{"input": "hi", "output": "hello"}],
    example_prompt=ChatPromptTemplate.from_messages([
        ("human", "{input}"),
        ("ai", "{output}")
    ])
)

# 5. 多模态模板
multimodal = ChatPromptTemplate.from_messages([
    ("human", [
        {"type": "text", "text": "{text}"},
        {"type": "image_url", "image_url": "{image_url}"}
    ])
])
```

---

## 11. 参考资源

- [LangChain Prompt Templates 官方文档](https://python.langchain.com/docs/concepts/prompt_templates/)
- [LangChain API 参考](https://python.langchain.com/api_reference/core/prompts/langchain_core.prompts)
- [Few-shot Learning 指南](https://python.langchain.com/docs/how_to/few_shot_examples/)
- [多模态提示指南](https://python.langchain.com/docs/how_to/multimodal_prompts/)

---

**总结:** LangChain 提供了丰富的 Prompt Template 类型,从简单的字符串模板到复杂的多模态、Few-shot 模板,满足各种应用场景。选择合适的模板类型,遵循最佳实践,可以大幅提升 LLM 应用的质量和可维护性。
