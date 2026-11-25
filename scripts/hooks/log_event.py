#!/usr/bin/env python3
"""Agent hook: append one structured JSON line per AI event to ai-logs/ai-interactions.jsonl.

Usage (from a hook config):  python scripts/hooks/log_event.py <eventName>
Reads the hook payload as JSON on stdin. Payload field names differ slightly between
Copilot (camelCase) and Claude-compatible (snake_case) hooks, so both are accepted.
Always prints {} to stdout (no decision) and never blocks the agent.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_FILE = REPO_ROOT / "ai-logs" / "ai-interactions.jsonl"
MAX_TEXT = 4000  # keep the log readable; long tool output is truncated

SECRET_MARKERS = ("password", "token", "secret", "apikey", "api_key", "authorization")


def first(payload: dict, *keys: str):
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return None


def clip(value) -> str | None:
    if value is None:
        return None
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT] + f"... [{len(text)} chars]"


def redact(value):
    if isinstance(value, dict):
        return {
            key: "***" if any(m in key.lower() for m in SECRET_MARKERS) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def main() -> None:
    event = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {"unparsed": raw}

    tool_args = first(payload, "toolArgs", "tool_input", "toolInput")
    if isinstance(tool_args, str):
        try:
            tool_args = json.loads(tool_args)
        except json.JSONDecodeError:
            pass

    entry = {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "event": event,
        "session": first(payload, "sessionId", "session_id"),
        "agent": first(payload, "agentName", "agent_name", "subagentName", "agent_type")
        or os.environ.get("AI_AGENT_NAME"),
        "prompt": clip(first(payload, "prompt", "initialPrompt", "initial_prompt", "userPrompt")),
        "tool": first(payload, "toolName", "tool_name"),
        "tool_args": redact(tool_args),
        "tool_result": clip(first(payload, "toolResult", "tool_response", "tool_output")),
        "reason": first(payload, "reason", "stopReason", "stop_reason"),
    }
    entry = {key: value for key, value in entry.items() if value not in (None, "", {})}

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    print("{}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # a logging failure must never break the agent
        print(f"log_event failed: {error}", file=sys.stderr)
        print("{}")
