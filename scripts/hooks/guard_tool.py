#!/usr/bin/env python3
"""preToolUse hook: deny a few dangerous agent actions before they run."""

from __future__ import annotations

import json
import re
import sys

BLOCKED_COMMANDS = [
    (r"git\s+push\s+.*--force", "Force-push is not allowed; push normally."),
    (r"\brm\s+-rf\s+(/|~|\.)(\s|$)", "Recursive delete of the repo or home is not allowed."),
    (r"git\s+commit\s+.*--no-verify", "Do not skip git hooks; fix the failure instead."),
]
PROTECTED_FILES = (".env", "ai-logs/ai-interactions.jsonl")


def main() -> None:
    payload = json.loads(sys.stdin.read() or "{}")
    args = payload.get("toolArgs") or payload.get("tool_input") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {"command": args}

    command = str(args.get("command", ""))
    for pattern, reason in BLOCKED_COMMANDS:
        if re.search(pattern, command):
            print(json.dumps({"permissionDecision": "deny", "permissionDecisionReason": reason}))
            return

    target = str(args.get("file_path") or args.get("filePath") or args.get("path") or "")
    if target.replace("\\", "/").endswith(PROTECTED_FILES):
        reason = f"{target} is protected; agents may not edit it."
        print(json.dumps({"permissionDecision": "deny", "permissionDecisionReason": reason}))
        return

    print("{}")


if __name__ == "__main__":
    main()
