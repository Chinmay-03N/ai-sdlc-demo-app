#!/usr/bin/env python3
"""Render ai-logs/ai-interactions.jsonl into a readable docs/AI_LOG.md (same format every time)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "ai-logs" / "ai-interactions.jsonl"
TARGET = REPO_ROOT / "docs" / "AI_LOG.md"


def one_line(text: str, limit: int = 160) -> str:
    text = " ".join(str(text).split()).replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def main() -> None:
    entries = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line]
    counts = Counter(entry["event"] for entry in entries)

    lines = [
        "# AI interaction log",
        "",
        f"Generated from `ai-logs/ai-interactions.jsonl` ({len(entries)} events).",
        "",
        "| Event | Count |",
        "|---|---|",
        *[f"| {event} | {count} |" for event, count in sorted(counts.items())],
        "",
        "## Timeline",
        "",
        "| Time (UTC) | Event | Agent | Prompt / tool | Detail |",
        "|---|---|---|---|---|",
    ]
    for entry in entries:
        what = entry.get("prompt") or entry.get("tool") or ""
        detail = entry.get("tool_args") or entry.get("reason") or ""
        lines.append(
            f"| {entry['ts']} | {entry['event']} | {entry.get('agent', '')} "
            f"| {one_line(what)} | {one_line(json.dumps(detail) if detail else '')} |"
        )

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(REPO_ROOT)} ({len(entries)} events)")


if __name__ == "__main__":
    main()
