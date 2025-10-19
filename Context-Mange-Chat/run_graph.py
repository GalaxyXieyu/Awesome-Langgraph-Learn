import asyncio
import argparse
import time
import re
import os
import math
from typing import List
try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.graph import StateGraph, START, END

from .graph import (
    ChatState,
    prep_node,
    react_agent,
    suggestion_node,
    _approx_tokens,
    agent_hook_node,
    prep_cache_policy,
)


def parse_args():
    p = argparse.ArgumentParser(description="Official-only ReAct chatbot with saver/store/cache + compression")
    p.add_argument("--limit", type=int, default=800, help="Hard token limit for node compression")
    # Compression behavior
    p.add_argument("--mode", type=str, choices=["token", "rounds"], default="token", help="Compression mode: token budget or rounds-based")
    p.add_argument("--rounds", type=int, default=6, help="Rounds to keep when mode=rounds (count human/user turns)")
    p.add_argument("--no-sum", action="store_true", help="Disable LLM summary in node compressor")
    p.add_argument(
        "--target",
        type=str,
        choices=["all", "human", "ai"],
        default="all",
        help="Compression target: all/human/ai",
    )
    p.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="Stable user id for long-term memory namespace; defaults to thread id if not set",
    )
    return p.parse_args()


async def main():
    args = parse_args()
    thread_id = f"react_{int(time.time())}"
    config = {"configurable": {"thread_id": thread_id}}

    # 以“组合而非包装”的方式在 runner 中装配参数
    # 压缩目标来自 CLI: --target (all/human/ai)
    prep = prep_node(
        hard_limit=args.limit,
        summarize=not args.no_sum,
        compress_target=args.target,
        mode=args.mode,
        rounds_limit=args.rounds,
    )
    # 使用 graph.react_agent 内置工具（web_search / inject_memory / search_memory）。
    # 为便于在无网络/无API Key环境下自测，提供可选的离线回显Agent。
    offline = (os.getenv("OFFLINE_AGENT", "false").lower() in {"1","true","yes"})
    agent = None if offline else react_agent()

    # 将 ReAct agent 包装成一个普通节点，避免子图兼容性差异带来的错误
    async def agent_node(state: dict) -> dict:  # type: ignore[override]
        # 优先使用 agent_hook_node 产生的 agent_view（模拟“agent 侧 hook”）
        prev_msgs = state.get("agent_view") or state.get("history_window") or state.get("messages", []) or []

        # 离线回显模式：从最近一条 human 消息生成即时回复，便于验证“同轮可见”
        if offline:
            last_human = None
            for m in reversed(prev_msgs):
                role = m.get("type") if isinstance(m, dict) else getattr(m, "type", None)
                if role in ("human", "user"):
                    last_human = m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
                    break
            reply = f"已收到：{(last_human or '').strip()}"
            delta = {"type": "ai", "content": reply}
            return {"messages": [delta], "history": [delta]}

        # 在线模式：真实调用 ReAct Agent（带容错）
        try:
            result = await agent.ainvoke({"messages": prev_msgs})
        except Exception as e:
            print(f"[agent][error] 调用失败: {e}")
            return {"messages": []}
        new_msgs = result.get("messages", []) or []

        updates = {"messages": []}
        if len(new_msgs) > len(prev_msgs):
            updates["messages"] = new_msgs[len(prev_msgs) :]
        elif new_msgs:
            updates["messages"] = new_msgs[-1:]

        # 将 agent 的“增量回复”也累计进 history，供跨轮压缩统计使用
        if updates["messages"]:
            updates["history"] = updates["messages"]

        # 解析工具意图：注入长期记忆 / 记忆检索
        for m in new_msgs:
            text = m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
            if not isinstance(text, str):
                continue
            if "已请求注入长期记忆" in text:
                updates["inject_memory_request"] = True
            if "MEMORY_SEARCH_REQUEST:" in text:
                q = text.split("MEMORY_SEARCH_REQUEST:", 1)[1].strip()
                if q:
                    updates["memory_search_query"] = q
        return updates

    suggest = suggestion_node()
    a_hook = agent_hook_node(agent_limit=max(400, args.limit - 200))

    graph = StateGraph(ChatState)
    graph.add_node("prep", prep)
    graph.add_node("agent_hook", a_hook)
    # 为 ReAct agent 启用节点级缓存：按“最近一条用户消息文本”作为 key
    graph.add_node("agent", agent_node, cache=prep_cache_policy(ttl_sec=300))
    graph.add_node("suggest", suggest)
    graph.add_edge(START, "prep")
    graph.add_edge("prep", "agent_hook")
    graph.add_edge("agent_hook", "agent")
    graph.add_edge("agent", "suggest")
    graph.add_edge("suggest", END)

    # Official saver/store and using saver as cache
    saver = InMemorySaver()
    store = InMemoryStore()
    app = graph.compile(checkpointer=saver, store=store, cache=saver)

    print(
        f"Limit={args.limit}, Mode={args.mode}, Rounds={args.rounds}, Target={args.target}, Summarize={'on' if not args.no_sum else 'off'}"
    )
    print("Type your message. 'exit' to quit.\n")
    print(
        "提示: 将 --limit 调小(如 100) 更容易触发压缩; --mode 选择 token/rounds; "
        "--rounds 控制 rounds 模式下保留的人类轮数; 用 --target 选择按 human/ai 定向摘要; 用 --user-id 跨线程复用记忆\n"
    )

    # 仅用于展示与统计的“本地抄本”，避免与图的累加历史重复
    transcript = [
        {"type": "system", "content": "你是一个 ReAct 代理，必要时会调用联网检索工具。"},
    ]
    first_turn = True
    # 跨轮控制标记：用于节点请求在下一轮注入长期记忆等
    control: dict = {}
    # 用于每轮展示“压缩后的当前窗口”（严格只打印窗口，不再回落到完整抄本）
    last_window: list = []

    # 基于 user_id（若未提供则回落到 thread_id）构造长期记忆命名空间，实现跨线程/会话复用
    user_id = args.user_id or thread_id
    mem_ns = ("memory", user_id)

    async def _aget(key: str):
        try:
            item = await store.aget(namespace=mem_ns, key=key)
            return getattr(item, "value", None) if item is not None else None
        except Exception:
            return None

    async def _aput(key: str, value):
        try:
            await store.aput(namespace=mem_ns, key=key, value=value)
        except Exception:
            pass

    async def _build_memory_message() -> dict | None:
        profile = await _aget("profile")
        facts = await _aget("facts") or []
        parts = []
        if isinstance(profile, dict) and profile.get("name"):
            parts.append(f"用户名: {profile['name']}")
        if isinstance(facts, list) and facts:
            recent = facts[-3:]
            parts.append("近期记忆:\n" + "\n".join(f"- {x}" for x in recent))
        if not parts:
            return None
        return {"type": "system", "content": "长期记忆：\n" + "\n".join(parts)}

    async def _extract_and_store_from_user(text: str):
        updates = []
        m = re.search(r"(?:我叫|我是)\s*([A-Za-z0-9_\u4e00-\u9fa5]+)", text)
        if m:
            name = m.group(1)
            prof = (await _aget("profile")) or {}
            if not isinstance(prof, dict):
                prof = {}
            prof["name"] = name
            await _aput("profile", prof)
            updates.append(f"name={name}")
        m2 = re.search(r"我喜欢[:：\s]*([^。！!？?\n]+)", text)
        if m2:
            like = m2.group(1).strip()
            facts = (await _aget("facts")) or []
            if not isinstance(facts, list):
                facts = []
            facts.append(f"偏好: {like}")
            await _aput("facts", facts)
            updates.append(f"like={like}")
        return updates

    while True:
        try:
            q = input(">> ").strip()
        except EOFError:
            break
        if not q:
            continue
        if q.lower() in {"exit", "quit", "q"}:
            break
        if first_turn:
            turn_state = {
                "messages": [
                    {"type": "system", "content": "你是一个 ReAct 代理，必要时会调用联网检索工具。"},
                    {"type": "human", "content": q},
                ]
            }
            first_turn = False
        else:
            turn_state = {"messages": [{"type": "human", "content": q}]}

        # 若上一节点（agent）请求注入长期记忆，则在进入图前注入记忆
        if control.get("inject_memory_request"):
            mem_msg = await _build_memory_message()
            if mem_msg is not None:
                turn_state["messages"] = [mem_msg, *turn_state["messages"]]
            # 单次消费后清除请求标记
            control.pop("inject_memory_request", None)

        # 默认窗口：先用当轮输入作为窗口初值，随后由 prep 节点更新为“压缩窗口”
        last_window = turn_state.get("messages", [])
        # 分隔线：回合开始
        print("\n──────── 回合开始 ────────")
        print(f"[user] {q}")

        new_deltas = []
        last_agent_text = None
        last_suggest_text = None
        last_lookup_meta = None

        async for chunk in app.astream(turn_state, config=config, stream_mode=["updates"]):
            # 兼容不同版本的 astream 输出：dict 或 tuple("updates", {...})
            updates = None
            if isinstance(chunk, dict) and "updates" in chunk:
                updates = chunk.get("updates") or {}
            elif isinstance(chunk, tuple) and len(chunk) == 2 and chunk[0] == "updates" and isinstance(chunk[1], dict):
                updates = chunk[1]
            else:
                # 忽略非 updates 的噪声，避免刷屏
                continue

            for node, upd in (updates or {}).items():
                if not upd:
                    continue
                if node == "prep":
                    stats = upd.get("stats") or {}
                    if stats:
                        before = stats.get("before", {})
                        window_stats = stats.get("window", {})
                        compressed = stats.get("compressed")
                        summary = stats.get("summary") or ""
                        print(
                            f"[prep] before: count={before.get('count')} ~tokens={before.get('approx_tokens')} | "
                            f"window: count={window_stats.get('count')} ~tokens={window_stats.get('approx_tokens')} | "
                            f"compressed={compressed}"
                        )
                        if summary:
                            print(f"[prep] 摘要: {summary}")
                        # 记录当前窗口（messages=压缩窗口）
                        last_window = upd.get("messages") or last_window
                elif node == "lookup":
                    # 兼容直接写在 update 或写在 stats.lookup 两种情况
                    meta = upd.get("lookup") or (upd.get("stats") or {}).get("lookup") or {}
                    if meta:
                        last_lookup_meta = meta
                        print(f"[lookup] query='{meta.get('query')}', counter={meta.get('counter')}, ts={meta.get('ts')}")
                elif node == "agent":
                    msgs = upd.get("messages") or []
                    if msgs:
                        new_deltas.extend(msgs)
                        last = msgs[-1]
                        content = last.get("content") if isinstance(last, dict) else getattr(last, "content", "")
                        last_agent_text = str(content) if content is not None else None
                    # 读取节点标记：是否请求注入长期记忆
                    if upd.get("inject_memory_request"):
                        control["inject_memory_request"] = True
                elif node == "suggest":
                    msgs = upd.get("messages") or []
                    if msgs:
                        new_deltas.extend(msgs)
                        last = msgs[-1]
                        content = last.get("content") if isinstance(last, dict) else getattr(last, "content", "")
                        last_suggest_text = str(content) if content is not None else None

        # 更新本地抄本用于展示（不回传到图中，避免重复累计）
        transcript.append({"type": "human", "content": q})
        if new_deltas:
            transcript.extend(new_deltas)

        # 先打印“当前上下文”（仅展示 prep 产生的压缩窗口，或本轮输入）
        msgs = last_window
        tok = _approx_tokens(msgs) if msgs else 0

        def _role(m):
            if isinstance(m, dict):
                return m.get("type") or m.get("role") or "unknown"
            return getattr(m, "type", "unknown") or "unknown"

        print("\n──────── 当前上下文 ────────")
        print("(共{}条，~tokens={})".format(len(msgs), tok))
        for i, m in enumerate(msgs, 1):
            if isinstance(m, dict):
                content = m.get("content", "")
            else:
                content = getattr(m, "content", "")
            content_str = str(content).replace("\n", " ")
            print(f"{i:02d}. [{_role(m)}] {content_str[:300]}")
        print("──────── 结束 ────────")

        # 回合结果摘要（在上下文之后展示更符合阅读节奏）
        print("\n──────── 本轮结果 ────────")
        if last_lookup_meta:
            print(
                f"[cache] lookup 计数={last_lookup_meta.get('counter')} (命中缓存则保持不变)"
            )
        if last_agent_text:
            print(f"[agent] {last_agent_text}")
        else:
            print("[agent] (无回复)")
        if last_suggest_text:
            print(f"[suggest]\n{last_suggest_text}")

        # 从用户输入抽取“可长期记忆”的信息并写入 InMemoryStore
        mem_updates = await _extract_and_store_from_user(q)
        if mem_updates:
            print(f"[memory] 已更新: {', '.join(mem_updates)}")
        print()

    # 退出后：从图状态取出完整 history 并打印
    try:
        state = await app.aget_state(config)  # type: ignore[attr-defined]
    except Exception:
        try:
            state = app.get_state(config)  # type: ignore[attr-defined]
        except Exception:
            state = None

    hist = None
    if state is not None:
        values = getattr(state, "values", None)
        if isinstance(values, dict):
            hist = values.get("history")
        elif isinstance(state, dict):
            hist = state.get("history")

    if isinstance(hist, list) and hist:
        print("\n──────── 完整历史（来自 state.history） ────────")
        tok = _approx_tokens(hist)
        print("(共{}条，~tokens={})".format(len(hist), tok))
        for i, m in enumerate(hist, 1):
            if isinstance(m, dict):
                role = m.get("type") or m.get("role") or "unknown"
                content = m.get("content", "")
            else:
                role = getattr(m, "type", "unknown") or "unknown"
                content = getattr(m, "content", "")
            content_str = str(content).replace("\n", " ")
            print(f"{i:02d}. [{role}] {content_str[:300]}")
        print("──────── 结束 ────────\n")


if __name__ == "__main__":
    asyncio.run(main())
