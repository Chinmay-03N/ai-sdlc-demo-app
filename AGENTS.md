# Project conventions for AI agents

Invoice approval demo app: **Python 3.11 + FastAPI** API with a small static web UI and an in-memory store.
Read this whole file before changing anything. If something here conflicts with a prompt, stop and ask.

## Approval rules (the business rules you must not get wrong)

| Rule | Detail |
|---|---|
| R1 Manager limit | A Manager may approve invoices with `amount <= 50,000.00` (inclusive). |
| R2 Director limit | A Director may approve invoices with `amount <= 500,000.00` (inclusive). One Director is enough at exactly 500,000.00. |
| R3 Two approvers | `amount > 500,000.00` needs two approvals. The first may be a Manager or a Director and moves the invoice to `AwaitingSecondApproval`. The **second must be a Director**. Only then is it `Approved`. |
| R4 Distinct users | The same user may **never** count as both approvers. Compare usernames **case-insensitively after trimming**. |
| R5 Refusal | A refused attempt raises `ApprovalNotAllowed` with a clear, human-readable reason. The API returns **403** with `{"error": reason}`. **Nothing about the invoice changes**: no repository write, same status, same approvals, same decided fields. |
| R6 Roles | `Manager`, `Director`, `Admin`. Admin cannot approve (but may delete). |
| R7 Money | Always `Decimal` in the domain. Never `float` for comparisons. Limits are named constants in `domain/approval_policy.py`. |

Lifecycle: `Draft -> PendingApproval -> (AwaitingSecondApproval) -> Approved | Rejected`.
Pending and AwaitingSecondApproval invoices can be rejected (reason required).

## Layout and layering

- `backend/src/invoice_app/domain/` — business rules only. No FastAPI, no I/O.
  - `approval_policy.py` — pure function `evaluate_approval(invoice, approver) -> ApprovalDecision`. All limit logic lives here.
  - `approval_service.py` — `ApprovalService` owns the lifecycle. It **evaluates the policy before building any new state**, then writes once with `repository.update`.
  - `models.py`, `errors.py`, `repository.py` (Protocol).
- `backend/src/invoice_app/api/` — FastAPI routes (`main.py`), demo sign-in (`auth.py`), in-memory repository, and the web UI in `static/`.
  Routes translate domain errors to HTTP; they never decide business rules.
- `backend/tests/` — pytest. `fakes.py` has `FakeInvoiceRepository` (stores deep copies, counts `update_calls`). Fixed clock in `conftest.py`.
- `e2e/` — Playwright for Python: page objects in `pages/`, tests in `tests/`.
- `specs/` and `.specify/` — Spec Kit specification, plan and tasks. Implement only what the current task asks.
- `.github/agents`, `.github/skills`, `.github/hooks`, `scripts/hooks` — agent tooling. Do not edit `ai-logs/` by hand.

## Commands

All commands from the repo root unless stated.

- Install: `cd backend && pip install -e ".[dev]"`
- **Unit tests: `cd backend && pytest`** (must pass before you say you are done)
- Lint/format: `cd backend && ruff format . && ruff check .`
- Run the app: `cd backend && uvicorn invoice_app.api.main:app --app-dir src --port 5000` then open http://localhost:5000
- E2E: `cd e2e && python -m playwright install chromium && pytest`
- Mutation testing (Linux/WSL): `cd backend && mutmut run && mutmut results`

Demo accounts (not real credentials), password `ChangeMe123!`: `demo.manager` (Manager), `demo.director` and `demo.director2` (Director), `demo.admin` (Admin).

## Testing expectations

- Every rule R1–R5 has a positive test, a negative test and **boundary tests on both sides** (e.g. 50,000.00 and 50,000.01).
- Every refusal test asserts **the stored invoice is unchanged** (`repository.stored(id) == before`) **and** `update_calls` did not increase, and checks the reason text with `match=`.
- The same-user rule is tested with an exact match, a different-case username and a whitespace-padded username.
- Use the fixed clock; assert exact timestamps. Use `pytest.mark.parametrize` for boundaries.
- Write tests from the spec, not from the implementation. One behaviour per test, named `test_<who>_<can/cannot>_<what>`.
- E2E tests use page objects and role/label locators (`get_by_role`, `get_by_label`), never CSS or XPath.

## Working style for agents

- Work in small steps; one task from `specs/001-approval-limits/tasks.md` at a time. Never implement the whole feature in one go.
- Run `cd backend && pytest` after each change and show the result.
- Do not weaken or delete a failing test to make it pass; explain the failure instead.
- Commit messages: `type(scope): summary` (types: feat, fix, test, docs, chore, refactor, ci), blank line, body with `What:` and `Why:`.
- End every implementation response with:

  ```
  ## Implementation summary
  - Task(s): <ids from tasks.md>
  - Files changed: <list>
  - Tests added/changed: <list>
  - Test result: <paste the pytest summary line>
  - Risks / open questions: <list or "none">
  ```

## Review expectations

A change is ready only when: rules live in the domain; limits are constants; refusals happen before any state change;
both negative rules have tests that would fail if the rule were removed; all tests pass; no `float` money; no
new business logic in `main.py` or `static/`. Reviews report each finding as
`| # | file:line | severity (High/Medium/Low) | finding | suggested fix |` and the human gives every finding a verdict:
**Fixed**, **Dismissed (reason)** or **Deferred (reason)**.

## Never

- Commit real credentials, tokens or customer data.
- Put business rules in routes, `auth.py` or the UI.
- Mutate an invoice and then raise.
- Edit `ai-logs/ai-interactions.jsonl` or bypass git hooks (`--no-verify`).
