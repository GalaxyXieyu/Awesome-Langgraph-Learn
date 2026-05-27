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

def prep_node(
    *,
    hard_limit: int,
    summarize: bool,
    compress_target: str = "all",
    mode: str = "token",  # "token" | "rounds"
    rounds_limit: int = 6,
):
    """创建“普通节点压缩”的节点函数（返回 async 可调用）。

    压缩触发：当“窗口基线”的近似 tokens 超过 ``hard_limit`` 才执行压缩。

    压缩模式（单选）：
    - ``mode="token"``：基于 token 预算的尾窗回填（推荐）。
    - ``mode="rounds"``：保留最近 ``rounds_limit`` 个“用户轮”（human 消息计数）的尾窗。
      若轮数尚未达到 ``rounds_limit`` 但 token 已超限，则回退到 token 预算压缩，保障上限。

    其他：
    - ``summarize=False`` 时改用静态提示，避免 LLM 调用。
    - ``compress_target`` 控制摘要聚焦目标："all"（默认）/ "human" / "ai"。
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

        def _is_tool(x) -> bool:
            if isinstance(x, dict):
                t = (x.get("type") or x.get("role") or "").lower()
                return t == "tool"
            name = getattr(x, "type", "") or getattr(x, "role", "")
            return str(name).lower() == "tool"

        def _match_role(m: BaseMessage) -> bool:
            if compress_target == "human":
                return isinstance(m, HumanMessage)
            if compress_target == "ai":
                return isinstance(m, AIMessage)
            return True

        async def _summarize(early_for_summary: List[BaseMessage], early_count: int) -> tuple[str, SystemMessage]:
            nonlocal summarize
            if summarize:
                llm = get_llm(0.2)
                try:
                    prompt: List[BaseMessage] = [
                        SystemMessage(content="你是一个对话摘要助手，用最短语言保留事实、实体、数字、结论。"),
                        *early_for_summary,
                        HumanMessage(content="请将以上早期对话压缩为<=120字摘要，避免重复，保留关键信息。若有冲突，以最近消息为准。"),
                    ]
                    resp = await llm.ainvoke(prompt)
                    stext = getattr(resp, "content", "") or ""
                    label = {
                        "human": "(仅用户)",
                        "ai": "(仅助手)",
                        "all": "",
                    }.get(compress_target, "")
                    return stext, SystemMessage(content=f"摘要{label}: {stext}")
                except Exception:
                    pass
            stext = f"早期内容已压缩（约{early_count}条被概括）。"
            return stext, SystemMessage(content=f"摘要: {stext}")

        def _pack_tail_by_token_budget(history_msgs: List[Any], base_msgs: List[Any], turn_msgs: List[Any]) -> List[Any]:
            # 预留10%的预算给摘要/工具，先用 90% 预算回填尾部
            BUDGET = max(1, int(hard_limit * 0.9))
            tail_rev: List[Any] = []
            for m in reversed(history_msgs):
                tentative = [*base_msgs, *reversed(tail_rev), *turn_msgs, m]
                if _approx_tokens(tentative) > BUDGET:
                    break
                tail_rev.append(m)
            return list(reversed(tail_rev))

        if before["approx_tokens"] > hard_limit:
            compressed = True

            # 根据模式选择尾窗
            if mode == "rounds":
                # 计算最后 rounds_limit 个 human 的起始下标
                human_idx = [i for i, m in enumerate(history) if (
                    (m.get("type") if isinstance(m, dict) else getattr(m, "type", "")) in ("human", "user")
                )]
                start_idx = human_idx[-rounds_limit] if len(human_idx) >= rounds_limit else 0
                tail = history[start_idx:]
                early_orig = history[:start_idx]

                # 早期摘要（按 compress_target 过滤）
                norm_msgs = _normalize_messages(early_orig)
                selected_early = [m for m in norm_msgs if _match_role(m)]
                focus_early = selected_early[-40:] if len(selected_early) > 40 else selected_early
                summary_text, summary_msg = await _summarize(focus_early, len(early_orig))

                window = [summary_msg, *tail]

                # 如果仍然超过 token 上限，退回 token 预算压缩
                if _approx_tokens([*window, *turn_msgs]) > hard_limit:
                    base = [summary_msg]
                    tail = _pack_tail_by_token_budget(history, base, turn_msgs)
                    window = [summary_msg, *tail]
            else:  # mode == "token"
                # 先生成“占位”摘要对象，tail 选出后再用真实摘要替换（并校正预算）
                placeholder_summary = SystemMessage(content="摘要: ……")
                base = [placeholder_summary]
                # 先按预算回填尾部
                tail = _pack_tail_by_token_budget(history, base, turn_msgs)
                # 早期区域：除去尾部的剩余消息
                early_cut = len(history) - len(tail)
                early_orig = history[:early_cut]
                # 早期摘要
                norm_msgs = _normalize_messages(early_orig)
                selected_early = [m for m in norm_msgs if _match_role(m)]
                focus_early = selected_early[-40:] if len(selected_early) > 40 else selected_early
                summary_text, summary_msg = await _summarize(focus_early, len(early_orig))
                window = [summary_msg, *tail]

                # 若加入真实摘要后超限，则从 tail 前端剔除直至达标
                while window and _approx_tokens([*window, *turn_msgs]) > hard_limit:
                    # 移除最早的非摘要/非工具条目（即 tail 的头部）
                    # 保留摘要与工具早期信息的优先级更高
                    if len(window) > 0 and not _is_tool(window[0]) and not isinstance(window[0], SystemMessage):
                        window.pop(0)
                    elif len(window) > 1:
                        window.pop(1)
                    else:
                        break
        else:
            window = history

        # 关键修复：将“当轮新消息（turn_msgs）”附加到窗口尾部，确保下游 Agent
        # 在同一轮即可看到当前用户输入，避免出现“滞后一轮”现象。
        window_with_turn = [*window, *turn_msgs] if turn_msgs else window

        result: Dict[str, Any] = {
            # 面向下游 LLM/Agent 的上下文：使用“窗口 + 当轮增量”
            "messages": window_with_turn,
            # 将“窗口 + 当轮增量”作为下一轮的基准窗口，确保连续性
            "history_window": window_with_turn,
            "stats": {
                "before": before,
                # 统计以“实际提供给下游的窗口”为准
                "window": {"count": len(window_with_turn), "approx_tokens": _approx_tokens(window_with_turn)},
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

