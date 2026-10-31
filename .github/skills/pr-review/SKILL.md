---
name: pr-review
description: Review prompt and output format for reviewing a pull request diff in this repo. Use when asked to review a PR, a branch or a diff.
---
# Pull request review

> If your workshop supplied its own review prompt, paste it below "Review prompt" and keep the output format.

## Review prompt

You are reviewing a pull request to an invoice approval service. Read `AGENTS.md` first. Review the diff for:

1. **Correctness against the rules** R1–R7 in AGENTS.md. Check boundaries (`<` vs `<=`), the two-approver
   flow, the same-user comparison, and that refusals happen before any state change.
2. **Tests**: does every rule have positive, negative and boundary tests? Would the negative tests fail if the
   rule were removed? Are refused attempts asserted to leave the invoice unchanged?
3. **Layering**: no business rules in routes, auth or UI.
4. **Security and data**: authorization on endpoints, no secrets, no PII in logs.
5. **Error handling**: clear reasons, correct HTTP codes, no swallowed exceptions.
6. **Maintainability**: naming, duplication, dead code, magic numbers.

Only report real issues you can point to in the diff. Cite file and line.

## Output format (exactly)

```
## Review findings
| # | File:line | Severity | Category | Finding | Suggested fix |
|---|---|---|---|---|---|
| 1 | backend/src/...:42 | High/Medium/Low | Correctness/Tests/Layering/Security/Errors/Maintainability | ... | ... |

## Summary
- High: <n>  Medium: <n>  Low: <n>
- Merge recommendation: <approve | approve with changes | request changes> — <one sentence>
```

The human then adds a **Verdict** column: Fixed (commit), Dismissed (reason) or Deferred (reason).
