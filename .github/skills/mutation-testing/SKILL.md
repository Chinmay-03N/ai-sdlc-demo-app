---
name: mutation-testing
description: Run mutmut on the domain package and report the mutation score and surviving mutants in a fixed format. Use when asked for mutation scores, test strength, or before/after test hardening.
---
# Mutation testing with mutmut

Runs on Linux/macOS/WSL only.

1. `cd backend && rm -rf mutants && mutmut run`
2. Counts: `mutmut results --all true | awk '{print $NF}' | sort | uniq -c`
3. Survivors: `mutmut results`, then `mutmut show <name>` for each.

Report exactly in this format:

```
Mutation run — <date> — <git short sha>
Scope: backend/src/invoice_app/domain
Total: <n>  Killed: <k>  Survived: <s>  Timeout: <t>  Score: <k/(k+s)*100, 1 decimal>%

Survivors:
| Mutant | Change | Real gap or equivalent? | Test that would kill it |
|---|---|---|---|
```

A mutant is **equivalent** only if no input can make its behaviour differ (e.g. `False` → `None` where only truthiness is used).
Say why. Everything else is a real gap and needs a test. Never change production code to kill a mutant.
