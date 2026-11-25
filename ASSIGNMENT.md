# AI in SDLC — Approval limits by role

**Author:** <your name> · **Pull request:** https://github.com/Chinmay-03N/ai-sdlc-demo-app/pull/1 · **Demo video:** <link to MP4 (unlisted YouTube / Drive)>

Fork of `NITIN1670/ai-sdlc-demo-app`, ported to **Python 3 + FastAPI**, with role-based approval limits added by an AI agent
(GitHub Copilot, agent mode in VS Code) while I held the checks: specification, review, tests, mutation testing and verdicts.

---

## 1. The feature

| Rule | Behaviour |
|---|---|
| Manager limit | Manager may approve up to **50,000.00** (inclusive) |
| Director limit | Director may approve up to **500,000.00** (inclusive) |
| Two approvers | Above 500,000.00: first approval (Manager or Director) → `AwaitingSecondApproval`; a **different Director** completes it |
| Distinct users | The same user never counts as both approvers — usernames compared **case-insensitively after trimming** |
| Refusal | Clear reason, HTTP **403**, and **nothing about the invoice changes** (no repository write) |

## 2. Tools and setup

| Area | What I used |
|---|---|
| Language / stack | Python 3, FastAPI, pytest, ruff, mutmut 3 (in WSL Ubuntu), Playwright for Python |
| AI tool | GitHub Copilot, agent mode in VS Code ("Local" session) |
| Spec-driven tool | GitHub Spec Kit (`specify init --integration copilot`): constitution, specify, clarify, plan, tasks, analyze |
| Context | `AGENTS.md` (single source), `CLAUDE.md` → `@AGENTS.md`, `.github/copilot-instructions.md` → AGENTS.md |
| Agents | `.github/agents/`: Orchestrator (lead) with sub-agents Test Author, Implementer, Test Reviewer; plus Spec Writer and Code Reviewer |
| Skills | `.github/skills/`: approval-rules, python-tests, mutation-testing, pr-review, ai-log |
| Hooks | `.github/hooks/`: AI interaction logging (all events), ruff auto-format after edits, a guard that denies force-push / `--no-verify` / editing `.env`; plus a git `commit-msg` hook enforcing `type(scope): summary` + `Why:` |

## 3. Does the context file matter? (AGENTS.md experiment)

Same question, fresh chat, once with AGENTS.md hidden and once with it. Raw answers in `docs/context-experiment/`.

| Question | Without AGENTS.md | With AGENTS.md |
|---|---|---|
| Where does the check go? | `ApprovalService.approve` (found by reading code) | Domain, pure `evaluate_approval` policy, evaluated **before** any state change |
| Limits | **Invented** a single $1,000 limit from the unrelated UC-1 brief | Manager ≤ 50,000.00, Director ≤ 500,000.00, two approvers above 500,000.00 |
| Same-user comparison | Exact `!=` — the trap the brief warns about | Trim + case-insensitive |
| Test command | Not stated | `cd backend && pytest` |

**Conclusion:** without context the agent confidently built the wrong rule from the nearest document. With AGENTS.md it got every rule right.

## 4. Specification (Spec Kit)

Files: `.specify/memory/constitution.md`, `specs/001-invoice-approval-limits/` (spec, plan, research, data model, contracts, tasks), `docs/spec-analysis.md`.

Decisions I made before implementation (the brief leaves these open): limits inclusive; exactly 500,000.00 needs one Director;
first approver above 500,000 may be a Manager **(assumption — the brief only constrains the second approver)**; first approval →
`AwaitingSecondApproval` with decided fields empty; same user = trimmed + case-insensitive; refusal = 403 + reason + no write;
awaiting invoices can still be rejected; exact refusal-reason templates.

Problems I caught in the generated artifacts **before** any code was written:
- **FR-002 contradicted FR-005** (Manager refused for *any* amount above 50,000 vs. allowed as first approver above 500,000).
- Task T022 (and a spec edge case, flagged CRITICAL by `/speckit-analyze`) expected a **valid rejection to leave the invoice unchanged** — impossible.
- Increment-2 status leaked into the foundation phase; code tasks were ordered before their tests.

## 5. Implementation in self-standing commits

| # | Commit | What | Why |
|---|---|---|---|
| 1 | `chore(port)` | Port .NET app to Python/FastAPI, 7 tests ported | Work in my language; no behaviour change |
| 2 | `docs(agents)` | AGENTS.md, context experiment, agents, skills, hooks | Context and tooling before any feature work |
| 3 | `docs(spec)` | Spec Kit artifacts | Decide ambiguous rules before the agent could |
| 4 | `feat(approvals)` | **Step 1:** single-approver limits | Increment 1 |
| 5 | `feat(approvals)` | **Step 2:** two-approver rule | Increment 2 |
| 6 | `refactor(domain)` | JSON serialization moved out of the domain | Found by mutation testing (54 untested mutants) |
| 7 | `test(approvals)` | Hardened tests | Mutation score 81.0% → 96.0% of covered code |
| 8 | `test(e2e)` | Playwright test | Refusal visible end to end |
| 9 | `fix(review)` | Review findings fixed | Verdicts in the PR |
| 10 | `docs(review)` | PR description copy + final mutation report | Evidence in the repo |

Every commit passes `cd backend && pytest` on its own.

## 6. Tests

**Unit tests:** 32 passing (`backend/tests/`). Every rule has positive, negative and boundary tests; every refusal test asserts
the reason text, that `update_calls` did not increase, **and** that the stored invoice equals a snapshot taken before the call.

| Rule | Tests (examples) |
|---|---|
| Manager ≤ 50,000 | allowed at 50,000.00; refused at 50,000.01 with exact reason |
| Director ≤ 500,000 | allowed at 500,000.00; 500,000.01 becomes a first approval |
| Two approvers | first approval → AwaitingSecondApproval, decided fields empty; different Director completes it |
| **Negative: same user never both** | same Director exact / different case / surrounding whitespace — all refused, invoice unchanged |
| **Negative: second must be a Director** | Manager as second approver refused; two different Managers can never complete |
| Admin | refused with reason |
| Reject while awaiting | finalises as Rejected with reason, decided_by, decided_at |

Domain tests use **non-demo usernames** (e.g. `priya.sharma`), so they would catch roles being guessed from usernames.

**Playwright (e2e/):** `test_over_limit_rejection.py` — demo.manager tries to approve a 75,000 invoice in the UI, sees
"exceeds the Manager approval limit of 50,000.00", and the invoice stays Pending Approval. Page object + `get_by_role` /
`get_by_label` only. **Verified it fails** when `MANAGER_LIMIT` is raised.

## 7. Mutation testing (mutmut 3, scope `backend/src/invoice_app/domain`)

| Run | Mutants | Killed | Survived | No tests | Score |
|---|---|---|---|---|---|
| **Before** (agent's first-pass tests) | 180 | 102 | 24 | 54 | **56.7%** overall / **81.0%** of covered code |
| After test hardening + JSON moved out of domain | 126 | 121 | 5 | 0 | **96.0%** |
| After review fixes | 120 | 120 | 0 | 0 | **100%** |

Before (text):
```
180 mutants: 102 killed, 24 survived, 54 no tests
no tests:  54  invoice_app.domain.models.Invoice.to_api_dict
survived:  10  approval_policy.evaluate_approval
            5  approval_service.approve      4 reject     1 submit
            2  approval_service.__init__     1 _find      1 _ensure_approvable
```

After hardening (text): 126 mutants, 121 killed, 5 survived — all 5 in one branch of `evaluate_approval`
(`if approver.role not in {MANAGER, DIRECTOR}`), which was **unreachable** because Admin was refused just above. Equivalent
mutants; explained in `docs/mutation/survivors.md`. Removing the dead branch in the review fixes → 120/120 killed.

What it taught me: 54 "no tests" mutants were not missing tests but **web code in the wrong layer**; the survivors showed reason
texts and decided fields were not asserted exactly. **100% is not proof of correctness** — mutmut did not catch the float
threshold that the review agent found. Full reports in `docs/mutation/`.

## 8. Agent review and verdicts

Code Reviewer agent (`pr-review` skill) on `docs/pr.diff`, plus my own review. Full table in the PR description (`docs/pr-review.md`).

| # | Finding | Found by | Verdict |
|---|---|---|---|
| 1 | 500,000 threshold re-declared as a **float** in the service | Agent | **Fixed** |
| 2 | No tests just below the limits | Agent | **Dismissed** — at-limit and one-cent-above tests already pin the comparison; no boundary mutants survive; agent cited a diff line, not a file line |
| L1 | Reason text hard-codes "500,000.00" | Me | **Fixed** |
| L2 | Redundant Admin check → unreachable branch (the 5 survivors) | Me + mutmut | **Fixed** |

## 9. AI interaction log

- `ai-logs/ai-interactions.jsonl` — raw, one JSON object per event, written by `scripts/hooks/log_event.py` (secrets redacted).
- `docs/AI_LOG.md` — rendered: **587 events, 9 sessions**: 23 prompts, 269 pre-tool / 262 post-tool calls, 22 agent stops, 1 sub-agent stop.
- **Not captured by hooks** (they did not exist yet): the port prompt and the follow-up fix of the agent's `tests.fakes`
  import (session of 2026-10-31, before commit 2), and the first `with/without AGENTS.md` questions (saved verbatim in
  `docs/context-experiment/`).

## 10. Where the AI was wrong, and how I caught it

| # | What the AI did | How I caught it | Fix |
|---|---|---|---|
| 1 | Port: imported `tests.fakes` without making `tests` importable | pytest collection error | `pythonpath = ["src","tests"]` |
| 2 | Without context, invented a $1,000 limit and an exact-match username compare | Context experiment | AGENTS.md |
| 3 | Spec: FR-002 contradicted FR-005 | Reading the spec | Spec fixed before planning |
| 4 | Tasks: valid rejection expected to leave invoice unchanged; increment-2 work in foundation; code before tests | Reading tasks + `/speckit-analyze` (CRITICAL) | Tasks and spec fixed |
| 5 | **Mapped demo usernames to roles inside the domain** — every real user would be refused; tests passed because they only used demo names | Reading `approval_policy.py` | `Approver(username, role)` passed in; tests with non-demo names |
| 6 | Seed data and a service threshold used **floats** for money | `ruff` output / review agent | `Decimal` everywhere |
| 7 | Web serialization (`to_api_dict`) in the domain | Mutation testing (54 no-test mutants) | Moved to API layer |
| 8 | Redundant role check leaving dead code | Mutation testing (5 survivors) | Single check |
| 9 | e2e fixture as a session-scoped instance method (deprecated) | pytest warning | Moved to `conftest.py` |

Also noted: during `/speckit-analyze` the agent ran a Spec Kit script with a PowerShell execution-policy bypass; I allowed it
as it only read files. The Copilot CLI session runner failed once ("Unexpected generated prompt structure"); I switched to a
Local agent session.

**Honest limits of this work:** sub-agent use is visible only once in the log (1 `subagentStop`); most work ran in single
agent sessions. Copilot Free's request limits made me keep prompts to one per step.

## 11. How to run

```bash
cd backend && pip install -e ".[dev]" && pytest          # 32 passed
uvicorn invoice_app.api.main:app --app-dir src --port 5000   # http://localhost:5000
cd e2e && python -m playwright install chromium && pytest    # 1 passed
cd backend && mutmut run && mutmut results                   # Linux / WSL only
python scripts/render_ai_log.py                              # -> docs/AI_LOG.md
```

Demo accounts (not real credentials), password `ChangeMe123!`: `demo.manager`, `demo.director`, `demo.director2`, `demo.admin`.
