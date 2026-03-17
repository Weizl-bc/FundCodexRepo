import json
import os
from pathlib import Path
from typing import Any
from urllib import error, request


DEFAULT_MODEL = "qwen-max-latest"
QWEN_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


def call_qwen(prompt: str, model: str = DEFAULT_MODEL) -> str:
    if not prompt or not prompt.strip():
        raise ValueError("prompt is required")

    api_key = os.getenv("DASHSCOPE_API_KEY") or _read_api_key_from_env_file()
    if not api_key:
        raise EnvironmentError("DASHSCOPE_API_KEY is not set")

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt.strip()},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        QWEN_API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=60) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Qwen API request failed: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Qwen API connection failed: {exc.reason}") from exc

    result = json.loads(body)
    return _extract_content(result)


def _extract_content(result: dict[str, Any]) -> str:
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Qwen API response: {result}") from exc

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        merged = "".join(text_parts).strip()
        if merged:
            return merged

    raise RuntimeError(f"Qwen API returned empty content: {result}")


def _read_api_key_from_env_file() -> str:
    if not ENV_FILE.exists():
        return ""

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        if key.strip() == "DASHSCOPE_API_KEY":
            return value.strip().strip('"').strip("'")

    return ""


if __name__ == "__main__":
    demo_prompt = "我现在要"
    print(call_qwen(demo_prompt))
