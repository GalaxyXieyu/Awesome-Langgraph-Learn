from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 课程里直接读取项目根目录的 .env，避免在 notebook 里手动 export。
# 这里不做复杂兜底：缺少模型配置就让 os.environ[...] 明确报错。
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip('"').strip("'")

DATA_PATH = Path("content_review_data.json")
if not DATA_PATH.exists():
    DATA_PATH = PROJECT_ROOT / "turtorial/LG-03-human-in-the-loop/content_review_data.json"

CONTENT_DATA = json.loads(DATA_PATH.read_text(encoding="utf-8"))

# 模型配置必须显式提供。教学代码优先清晰，不做多层 fallback。
OPENAI_MODEL = os.environ["OPENAI_MODEL"]
OPENAI_BASE_URL = os.environ["OPENAI_BASE_URL"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_TEMPERATURE = float(os.environ.get("OPENAI_TEMPERATURE", "0"))
MODEL_NAME = f"openai:{OPENAI_MODEL}"

chat_model = init_chat_model(
    MODEL_NAME,
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY,
    temperature=OPENAI_TEMPERATURE,
)


def print_json(title: str, value: Any) -> None:
    print(title)
    print(json.dumps(value, ensure_ascii=False, indent=2))


def parse_json_message(message: Any) -> dict[str, Any]:
    content = message.content
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    text = str(content).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise ValueError(f"模型没有返回可解析的 JSON：{text}")


def find_publish_request(request_id: str) -> dict[str, Any]:
    return next(item for item in CONTENT_DATA["requests"] if item["request_id"] == request_id)


def policy_text() -> str:
    return json.dumps(CONTENT_DATA["policy_rules"], ensure_ascii=False, indent=2)


def display(value: Any) -> Any:
    labels = {
        "high": "高",
        "medium": "中",
        "low": "低",
        "none": "无",
        "approve": "通过",
        "edit_and_approve": "修改后通过",
        "reject": "拒绝",
        "published": "已发布",
        "published_after_edit": "修改后发布",
        "rejected": "已拒绝",
    }
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, tuple):
        return [display(item) for item in value]
    if isinstance(value, list):
        return [display(item) for item in value]
    return labels.get(value, value)
