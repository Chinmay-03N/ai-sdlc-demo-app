---
name: ai-log
description: Render and summarise the AI interaction log captured by the hooks (ai-logs/ai-interactions.jsonl). Use when asked about the AI log, AI usage evidence, or before submitting.
---
# AI interaction log

The hooks in `.github/hooks/ai-logging.json` append one JSON object per event to `ai-logs/ai-interactions.jsonl`
with the fixed keys `ts, event, session, agent, prompt, tool, tool_args, tool_result, reason`
(keys with no value are omitted; secrets are redacted to `***`).

To publish it:

1. `python scripts/render_ai_log.py` → writes `docs/AI_LOG.md`.
2. Summarise in this format:

```
AI log summary
Sessions: <n>  Prompts: <n>  Tool calls: <n>  Sub-agent runs: <n>
Date range: <first ts> – <last ts>
Notable: <1–3 bullets, e.g. "guard hook denied a force-push">
```

Never edit `ai-logs/ai-interactions.jsonl` by hand except to append clearly marked `"event": "manual"` entries
for AI use outside VS Code.
