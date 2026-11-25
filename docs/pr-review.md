## Approval limits by role

Spec: `specs/001-invoice-approval-limits/spec.md` · Tasks: `specs/001-invoice-approval-limits/tasks.md`

### What changed
- Manager may approve up to 50,000.00; Director up to 500,000.00 (inclusive, `Decimal` constants); Admin cannot approve.
- Above 500,000.00: two distinct approvers. First may be a Manager or Director (invoice → `AwaitingSecondApproval`);
  the second must be a **different Director**. Same user compared case-insensitively after trimming.
- Every refused approval returns **403** with a clear reason and leaves the invoice unchanged (no repository write).
- An invoice awaiting its second approval can still be rejected. The UI lists awaiting invoices and who has approved.

### Commits
1. `chore(port)` port the .NET app to Python/FastAPI (7 original tests ported)
2. `docs(agents)` AGENTS.md, context experiment, 6 agents, 5 skills, hooks
3. `docs(spec)` Spec Kit constitution, spec, plan, tasks, analyze report
4. `feat(approvals)` Increment 1: single-approver limits
5. `feat(approvals)` Increment 2: two-approver rule
6. `refactor(domain)` move JSON serialization out of the domain (found by mutation testing)
7. `test(approvals)` harden tests after test review and mutation run
8. `test(e2e)` Playwright test: rejected over-limit approval
9. `fix(review)` address review findings below

### Evidence
| Check | Result |
|---|---|
| Unit tests (`cd backend && pytest`) | 32 passed |
| E2E (`cd e2e && pytest`) | 1 passed; verified it **fails** when `MANAGER_LIMIT` is raised |
| Mutation score, domain (mutmut) | before 56.7% overall / 81.0% of covered code → after hardening 96.0% → after review fixes **100%** (120/120) |

### Mutation runs
| Run | Mutants | Killed | Survived | No tests | Score |
|---|---|---|---|---|---|
| Before (agent's first tests) | 180 | 102 | 24 | 54 | 56.7% overall / 81.0% of covered code |
| After test hardening + JSON moved out of domain | 126 | 121 | 5 | 0 | 96.0% |
| After review fixes (dead branch removed) | 120 | 120 | 0 | 0 | 100% |

Reports: `docs/mutation/mutation-before.txt`, `mutation-after.txt`, `mutation-after-review.txt`, `survivors.md`.
100% does not mean the tests are perfect: mutation testing did not catch the float threshold (finding 1), which the review agent did.

### Review findings and verdicts
Review by the Code Reviewer agent (`pr-review` skill) on `docs/pr.diff`, plus my own review.

| # | File | Sev | Finding | Found by | Verdict | Reason / commit |
|---|---|---|---|---|---|---|
| 1 | `domain/approval_service.py:42` | Medium | 500,000 threshold re-declared as a **float** instead of `DIRECTOR_LIMIT` | Agent | **Fixed** | Duplicated rule and float money break R7. Fixed in `fix(review)` |
| 2 | `tests/test_approval_policy_increment_1.py` | Medium | No tests just below the limits (49,999.99 / 499,999.99) | Agent | **Dismissed** | At-limit (allowed) and one-cent-above (refused) tests already pin the comparison; mutation testing shows no surviving boundary mutants. The agent cited a diff line (1706), not a file line |
| L1 | `domain/approval_policy.py` | Low | Second-approver reason hard-codes "500,000.00" | Me | **Fixed** | Message would lie if the limit changed. Now formats `DIRECTOR_LIMIT` |
| L2 | `domain/approval_policy.py` | Low | Separate Admin check made the `not in {Manager, Director}` branch unreachable; caused all 5 surviving mutants | Me + mutmut | **Fixed** | One role check, no dead code. Mutation score 96.0% → 100% |

Neither reviewer alone found everything: the agent caught the float threshold that I and mutation testing missed;
I caught L1 and L2, which the agent missed.

### Earlier issues caught during development (fixed before this review)
- Agent mapped demo usernames to roles inside the domain (any real user refused); fixed by passing `Approver(username, role)`.
- Seed data used float amounts; changed to `Decimal`.
- `Invoice.to_api_dict` (web serialization) lived in the domain: 54 untested mutants; moved to the API layer.
- Spec Kit spec had FR-002 contradicting FR-005, and a task that expected a valid rejection to leave the invoice unchanged.
- e2e fixture defined as a session-scoped instance method (deprecated); moved to `e2e/conftest.py`.
