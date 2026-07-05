from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from json_repair import repair_json
from langchain.chat_models import init_chat_model


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip('"').strip("'")


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


def parse_json_message(message: Any) -> dict[str, Any]:
    content = message.content
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    text = str(content).strip()

    # Remove markdown code fences if present.
    if text.startswith("```"):
        text = text[3:]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3].strip()

    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        pass

    # Extract the first balanced JSON object.
    start = text.find("{")
    if start >= 0:
        depth = 0
        in_string = False
        escape = False
        for i, ch in enumerate(text[start:], start=start):
            if escape:
                escape = False
                continue
            if ch == "\\" and in_string:
                escape = True
                continue
            if ch == '"' and not in_string:
                in_string = True
            elif ch == '"' and in_string:
                in_string = False
            elif not in_string:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start : i + 1], strict=False)
                        except json.JSONDecodeError:
                            break
                        break

    # Last resort: use json_repair to fix common LLM JSON mistakes.
    try:
        repaired = repair_json(text)
        if isinstance(repaired, str):
            repaired = json.loads(repaired, strict=False)
        if isinstance(repaired, dict):
            return repaired
    except Exception:
        pass

    raise ValueError(f"模型没有返回可解析的 JSON：{text}")


def print_json(title: str, value: Any) -> None:
    print(title)
    print(json.dumps(value, ensure_ascii=False, indent=2))


def display_bool(value: bool) -> str:
    return "是" if value else "否"
