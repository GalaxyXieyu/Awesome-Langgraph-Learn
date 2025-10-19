from __future__ import annotations

import os
from typing import Any, Dict, List, TypedDict, Annotated
import operator

from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, HumanMessage
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import CachePolicy


def _replace_messages(_old: List[BaseMessage], new: List[BaseMessage]) -> List[BaseMessage]:
    """Reducer: 总是用新值覆盖旧值，用于在发生压缩或节点写回时直接覆盖消息列表。"""
    return new


class ChatState(TypedDict, total=False):
    # 覆盖式聚合：当节点返回 messages 时，直接替换全量列表
    messages: Annotated[List[BaseMessage], _replace_messages]
    # 追加式聚合：跨轮累积完整对话历史（人类+助手+系统）
    history: Annotated[List[BaseMessage], operator.add]
    stats: Dict[str, Any]
    agent_stats: Dict[str, Any]


def _approx_tokens(msgs: List[BaseMessage]) -> int:
    """返回对消息列表的“近似 token 数”。

    为什么需要先规范化：
    - 上游可能传入 dict 形式（包含 ``type/role`` 与 ``content``）或 BaseMessage 对象。
    - ``count_tokens_approximately`` 期望统一的 ``BaseMessage`` 列表，便于在不同角色上应用一致的估算规则。

    处理流程：
    1) 将每条消息按角色映射为具体的 BaseMessage 子类：
       - {"human","user"} -> HumanMessage
       - {"ai","assistant"} -> AIMessage
       - 其他 -> SystemMessage
    2) 对规范化后的列表调用 ``count_tokens_approximately``。
    3) 若出现异常（结构不符等），退化为按 ``content`` 的空白分词计数，保证教学/演示场景的健壮性。
    """
    try:
        normalized: List[BaseMessage] = []
        for m in msgs:
            if isinstance(m, dict):
                role = m.get("type") or m.get("role") or "human"
                content = m.get("content", "")
                if role in ("human", "user"):
                    normalized.append(HumanMessage(content=content))
                elif role in ("ai", "assistant"):
                    normalized.append(AIMessage(content=content))
                else:
                    normalized.append(SystemMessage(content=content))
            else:
                # already a BaseMessage; keep as-is
                normalized.append(m)
        return count_tokens_approximately(normalized)
    except Exception:
        # Fallback: approximate by word count of text content
        total = 0
        for m in msgs:
            c = m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "")
            if isinstance(c, str):
                total += len(c.split())
        return total

def _normalize_messages(msgs: List[BaseMessage]) -> List[BaseMessage]:
    """将混合类型的消息规范化为 BaseMessage 列表。

    作用：
    - 确保下游 LLM/Agent 始终接收统一的消息格式。
    - 同时兼容 dict 风格与已有的 BaseMessage 实例。

    映射规则：
    - ``type/role`` in {"human","user"} -> HumanMessage
    - {"ai","assistant"} -> AIMessage
    - 其他 -> SystemMessage

    保留原始顺序，仅统一表示形式。
    """
    norm: List[BaseMessage] = []
    for m in msgs:
        if isinstance(m, dict):
            role = m.get("type") or m.get("role") or "human"
            content = m.get("content", "")
            if role in ("human", "user"):
                norm.append(HumanMessage(content=content))
            elif role in ("ai", "assistant"):
                norm.append(AIMessage(content=content))
            else:
                norm.append(SystemMessage(content=content))
        else:
            norm.append(m)
    return norm

def get_llm(temp: float = 0.2) -> ChatOpenAI:
    """构造 ChatOpenAI（官方客户端）。

    从环境变量读取：``GPT_4O_MODEL / GPT_4O_BASE_URL / GPT_4O_API_KEY``。
    """
    return ChatOpenAI(
        model=os.getenv("GPT_4O_MODEL", "gpt-4o"),
        base_url=os.getenv("GPT_4O_BASE_URL"),
        api_key=os.getenv("GPT_4O_API_KEY"),
        temperature=temp,
    )

def prep_node(*, hard_limit: int, keep_last: int, summarize: bool, compress_target: str = "all"):
    """创建“普通节点压缩”的节点函数（返回 async 可调用）。

    - 当历史近似 tokens 超过 ``hard_limit`` 时：插入一条摘要并仅保留最近 ``keep_last`` 条原文。
    - ``summarize=False`` 时改用静态提示，避免 LLM 调用。
    - ``compress_target`` 控制压缩目标："all"（默认）/ "human" / "ai"。
      仅当选择 "human" 或 "ai" 时，早期历史会先按角色过滤后再做摘要；
      其他未选中的角色仅保留到最近 ``keep_last`` 的窗口中。
    """

    async def _prep(state: ChatState) -> ChatState:  # type: ignore[override]
        # 全量历史：由各节点把当轮新增内容写入 history（追加聚合）
        history = state.get("history", []) or []
        # 当轮新消息（通常是用户输入，或上游注入的系统记忆）
        turn_msgs = state.get("messages", []) or []
        # 使用上一轮提交的“history_window”（已经是压缩后的窗口）作为阈值基准
        base = state.get("history_window") or history
        before = {"count": len(base), "approx_tokens": _approx_tokens(base)}
        summary_text = ""
        compressed = False

        if before["approx_tokens"] > hard_limit:
            compressed = True
            early = max(0, len(history) - keep_last)
            norm_msgs = _normalize_messages(history)
            early_msgs = norm_msgs[:-keep_last] if keep_last > 0 else norm_msgs
            # 仅对选定角色进行摘要
            def _match_role(m: BaseMessage) -> bool:
                if compress_target == "human":
                    return isinstance(m, HumanMessage)
                if compress_target == "ai":
                    return isinstance(m, AIMessage)
                return True

            selected_early = [m for m in early_msgs if _match_role(m)]
            focus_early = selected_early[-40:] if len(selected_early) > 40 else selected_early

            # 识别早期的 tool 类型消息（不参与摘要，不被裁剪，直接保留原文）
            def _is_tool(x) -> bool:
                if isinstance(x, dict):
                    t = (x.get("type") or x.get("role") or "").lower()
                    return t == "tool"
                # 对于 BaseMessage 的 tool 类型，这里保守处理：LangChain 中 ToolMessage 也可视为“工具输出”
                name = getattr(x, "type", "") or getattr(x, "role", "")
                return str(name).lower() == "tool"

            early_orig = history[:-keep_last] if keep_last > 0 else history
            tool_early = [m for m in early_orig if _is_tool(m)]
            # 为避免窗口爆炸，仅保留最近若干条早期工具消息
            TOOL_PRESERVE_MAX = 8
            tool_early = tool_early[-TOOL_PRESERVE_MAX:]

            if summarize:
                llm = get_llm(0.2)
                try:
                    prompt: List[BaseMessage] = [
                        SystemMessage(content="你是一个对话摘要助手，用最短语言保留事实、实体、数字、结论。"),
                        *focus_early,
                        HumanMessage(content="请将以上早期对话压缩为<=120字摘要，避免重复，保留关键信息。若有冲突，以最近消息为准。"),
                    ]
                    resp = await llm.ainvoke(prompt)
                    summary_text = getattr(resp, "content", "") or ""
                    label = {
                        "human": "(仅用户)",
                        "ai": "(仅助手)",
                        "all": "",
                    }.get(compress_target, "")
                    summary_msg = SystemMessage(content=f"摘要{label}: {summary_text}")
                except Exception:
                    summary_text = f"早期内容已压缩，仅保留最近 {keep_last} 条（共{early}条被省略）。"
                    summary_msg = SystemMessage(content=f"摘要: {summary_text}")
            else:
                summary_text = f"早期内容已压缩，仅保留最近 {keep_last} 条（共{early}条被省略）。"
                summary_msg = SystemMessage(content=f"摘要: {summary_text}")

            # 压缩后的窗口：摘要 + 早期保留的工具消息 + 最近 keep_last 条原文
            # 注意：tool_early 取自原始 history（可能是 dict/BaseMessage 混合），可被下游正常处理
            window = [summary_msg, *tool_early, *history[-keep_last:]]
        else:
            window = history

        result: Dict[str, Any] = {
            # 面向下游 LLM/Agent 的上下文：用压缩后的窗口作为 messages
            "messages": window,
            # 将本轮的压缩窗口“提交”为下一轮的基准窗口
            "history_window": window,
            "stats": {
                "before": before,
                "window": {"count": len(window), "approx_tokens": _approx_tokens(window)},
                "compressed": compressed,
                "summary": summary_text,
                "compress_target": compress_target,
                "early_selected": len(selected_early) if before["approx_tokens"] > hard_limit else 0,
            },
        }
        # 把当轮输入追加到 history，供跨轮压缩与统计使用
        if turn_msgs:
            # 返回一个浅拷贝，避免传出对只读/被复用列表的引用
            result["history"] = [
                (m if isinstance(m, dict) else {"type": getattr(m, "type", "unknown"), "content": getattr(m, "content", "")})
                for m in turn_msgs
            ]
        # 不再清空 messages：messages 承载压缩后的窗口，供后续节点直接使用

        # 不再覆盖 messages：messages 仅承载“当轮新增”的人类/助手消息，由上游节点写入 history 做跨轮累积。

        return result

    return _prep

def react_agent():
    """创建官方 ReAct Agent（内置联网检索与“注入长期记忆”工具）。

    尽可能兼容不同版本的 Tavily 集成：
    - 优先: langchain_tavily.TavilySearch（推荐，避免弃用警告）
    - 其次: langchain_tavily.TavilySearchResults（较旧但可用）
    - 再次: langchain_community.tools.tavily_search.TavilySearchResults（更旧）
    - 最后: 占位 @tool 函数
    """

    web_tool = None
    try:
        # 新版推荐：避免 LangChainDeprecationWarning
        from langchain_tavily import TavilySearch  # type: ignore

        web_tool = TavilySearch(max_results=5)
    except Exception:
        try:
            # 兼容较旧 langchain_tavily 版本
            from langchain_tavily import TavilySearchResults  # type: ignore

            web_tool = TavilySearchResults(max_results=5)
        except Exception:
            try:
                # 最旧的社区版本
                from langchain_community.tools.tavily_search import TavilySearchResults  # type: ignore

                web_tool = TavilySearchResults(max_results=5)
            except Exception:
                @tool
                def web_search(query: str) -> str:  # type: ignore
                    return "(web_search 在当前环境不可用，已使用占位工具)"

                web_tool = web_search

    @tool
    def inject_memory() -> str:
        """请求在下一轮对话前注入长期记忆（用户名/偏好等）。"""
        return "已请求注入长期记忆（若存在）。"

    @tool
    def search_memory(query: str) -> str:
        """搜索长期记忆（按关键词）。返回: MEMORY_SEARCH_REQUEST:<query>，由外部节点执行检索并回填结果。"""
        q = (query or "").strip()
        if not q:
            return "MEMORY_SEARCH_REQUEST:"
        return f"MEMORY_SEARCH_REQUEST:{q}"

    tools_list = [web_tool, inject_memory, search_memory]

    agent = create_react_agent(
        model=get_llm(0.2),
        tools=tools_list,
        prompt=(
            "你是一个能够调用工具的助手。\n"
            "当需要外部信息时，先使用 web_search 检索，再进行回答。\n"
            "当你需要用户的历史信息（如姓名/偏好）来更好地回答时，请调用 inject_memory。\n"
            "当你需要从长期记忆中按关键词检索事实时，请调用 search_memory(query)。"
        ),
        name="react_agent",
    )
    return agent

def suggestion_node():
    """创建“建议/下一步”节点：基于当前对话生成 2-4 条后续建议。

    设计目的：在 ReAct agent 完成工具调用与回答后，附加可选的下一步操作建议，
    而不是再做一次兜底对话回复。建议将作为一条 AIMessage 写回 messages，
    便于在终端或前端一起渲染。
    """

    async def _suggest(state: ChatState) -> ChatState:  # type: ignore[override]
        # 从 history_window/history/messages 中获取最近上下文
        base = (
            state.get("history_window")
            or state.get("history")
            or state.get("messages", [])
            or []
        )
        if not base:
            return {}

        # 取最后若干条消息作为生成建议的依据
        window = _normalize_messages(base[-10:])
        llm = get_llm(0.2)
        prompt: List[BaseMessage] = [
            SystemMessage(
                content=(
                    "请基于当前对话，给出2-4条‘下一步’建议。"
                    "建议应具体、可执行，中文输出，使用项目符号，不要冗长解释。"
                )
            ),
            *window,
            HumanMessage(content="只输出建议清单，不要重复上文。"),
        ]
        try:
            resp = await llm.ainvoke(prompt)
            text = (getattr(resp, "content", "") or "").strip()
            if not text:
                raise ValueError("empty suggestions")
        except Exception:
            text = (
                "- 需要我继续联网检索更具体的信息吗？\n"
                "- 要将当前要点整理为结构化摘要吗？\n"
                "- 是否需要产出一个行动清单或时间表？"
            )

        # 仅返回“增量”消息，同时把增量追加到 history（使用 dict 以避免只读对象问题）
        delta = {"type": "ai", "content": text}
        return {"messages": [AIMessage(content=text)], "history": [delta]}

    return _suggest

def prep_cache_policy(ttl_sec: int = 300):
    """为 prep 节点创建一个简单的缓存策略：按“最近一条用户消息文本”作为 key。"""

    def _last_human_key(args: tuple, *_a, **_k) -> str:
        try:
            state = args[0] if args else {}
            msgs = state.get("messages", []) or []
            for m in reversed(msgs):
                role = m.get("type") if isinstance(m, dict) else getattr(m, "type", None)
                if role in ("human", "user"):
                    content = m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
                    return (content or "").strip().lower()
            return ""
        except Exception:
            return ""

    return CachePolicy(ttl=ttl_sec, key_func=_last_human_key)

def agent_hook_node(*, agent_limit: int = 600):
    """模拟“Agent 侧 hook”：在不修改 messages 的前提下，为 agent 构造 agent_view。

    行为：若窗口（messages 或 history_window）近似 tokens 超过 agent_limit，则在最前面插入一条“Agent摘要”。
    该节点仅返回 {"agent_view": ...}，供下游 agent 消费，强调 hook 的“非破坏性”。
    """

    async def _hook(state: ChatState) -> Dict[str, Any]:  # type: ignore[override]
        base = (
            state.get("history_window")
            or state.get("history")
            or state.get("messages", [])
            or []
        )
        approx = _approx_tokens(base)
        if approx <= agent_limit:
            return {"agent_view": base}

        # 简要摘要（为演示稳定性，这里使用静态提示；如需可改为 LLM 摘要）
        summary = "Agent摘要：为节省上下文，早期历史已被压缩，以下为关键内容与最近消息。"
        return {"agent_view": [SystemMessage(content=summary), *base]}

    return _hook

