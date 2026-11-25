#!/usr/bin/env python3
"""postToolUse hook: after the agent edits a .py file, run ruff format + ruff check --fix
on that file, so every AI edit lands in the same house style. Lint problems that ruff
cannot fix are fed back to the agent as additionalContext."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EDIT_TOOLS = {"edit", "write", "create", "editfiles", "createfile", "multiedit", "str_replace"}


def edited_paths(payload: dict) -> list[Path]:
    tool = str(payload.get("toolName") or payload.get("tool_name") or "").lower()
    if not any(name in tool.replace("_", "") for name in EDIT_TOOLS):
        return []
    args = payload.get("toolArgs") or payload.get("tool_input") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return []
    candidates = [args.get(k) for k in ("file_path", "filePath", "path")] + list(
        args.get("files", []) or []
    )
    paths = [Path(c) for c in candidates if isinstance(c, str) and c.endswith(".py")]
    return [p if p.is_absolute() else REPO_ROOT / p for p in paths if (REPO_ROOT / p).exists()]


def main() -> None:
    payload = json.loads(sys.stdin.read() or "{}")
    files = edited_paths(payload)
    ruff = shutil.which("ruff")
    if not files or ruff is None:
        print("{}")
        return

    config = ["--config", str(REPO_ROOT / "backend" / "pyproject.toml")]
    names = [str(f) for f in files]
    subprocess.run([ruff, "format", *config, *names], capture_output=True, text=True)
    check = subprocess.run(
        [ruff, "check", "--fix", *config, *names], capture_output=True, text=True
    )
    if check.returncode != 0:
        print(json.dumps({"additionalContext": "ruff found issues to fix:\n" + check.stdout}))
    else:
        print("{}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"format_python failed: {error}", file=sys.stderr)
        print("{}")
