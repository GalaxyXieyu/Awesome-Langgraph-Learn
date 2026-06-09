from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

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


def print_json(title: str, value: Any) -> None:
    print(title)
    print(json.dumps(value, ensure_ascii=False, indent=2))


def display_bool(value: bool) -> str:
    return "是" if value else "否"
