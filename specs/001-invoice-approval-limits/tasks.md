# Tasks: Invoice Approval Limits

**Input**: Design documents from `/specs/001-invoice-approval-limits/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by delivery increment to support the requested two-step rollout: Increment 1 for single-approver limits and Increment 2 for the two-approver rule.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure the feature starts from the repo’s current FastAPI domain structure and testing conventions.

- [ ] T001 Create shared feature folder structure under `specs/001-invoice-approval-limits/` and confirm the plan, spec, data model, contract, and quickstart artifacts are in place
- [ ] T002 [P] Review `backend/src/invoice_app/domain/models.py`, `approval_service.py`, `errors.py`, and the repository contract to confirm the current domain model and error boundaries before changing behavior
- [ ] T003 [P] Review `backend/tests/test_approval_service.py` and `backend/tests/fakes.py` to standardize the test pattern for boundary assertions, unchanged-invoice checks, and repository update-call validation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prepare the domain and API foundations needed before either approval increment can be implemented.

- [ ] T004 [P] Update `backend/src/invoice_app/api/auth.py` so demo users align with the role model that includes Manager, Director, and Admin, while keeping auth behavior outside the business rules
- [ ] T005 [P] Review `backend/src/invoice_app/api/main.py` to confirm the API translation layer maps `ApprovalNotAllowed` to HTTP 403 with `{"error": reason}` without embedding business logic in the route layer
- [ ] T006 Review `backend/src/invoice_app/domain/models.py` and confirm `Invoice.approvals: list[ApprovalRecord]` is the only model change needed for the first increment while preserving existing invoice fields and Decimal usage
- [ ] T007 Review `backend/tests/test_approval_service.py` and `backend/tests/fakes.py` to standardize the test pattern for boundary assertions, unchanged-invoice checks, and repository update-call validation

**Checkpoint**: Foundation ready - approval increment work can now begin in parallel.

---

## Phase 3: Increment 1 - Single-Approver Limits (Priority: P1) 🎯 MVP

**Goal**: Implement the single-approver thresholds and refusal rules for Manager and Director approval decisions up to 500,000.00, including inclusive boundary checks and unchanged-invoice refusal semantics.

**Independent Test**: A pending invoice can be approved by a Manager at 50,000.00, by a Director at 500,000.00, and any invalid approval above a role threshold is refused without changing the invoice.

### Tests for Increment 1 (MUST be written first) ⚠️

- [ ] T010 [P] [US1] Add boundary tests in `backend/tests/test_approval_limits.py` for 50,000.00 and 50,000.01 and assert the successful approval and refusal outcomes with unchanged invoice state and update-call counts
- [ ] T011 [P] [US1] Add director threshold tests in `backend/tests/test_approval_limits.py` for 500,000.00 and 500,000.01, covering the inclusive limit and the over-limit refusal path while preserving invoice immutability
- [ ] T012 [P] [US1] Add invalid-role tests in `backend/tests/test_approval_limits.py` for Admin attempts and ensure refusal reasons are asserted with `match=` and repository update counts stay unchanged
- [ ] T013 [P] [US1] Add API test in `backend/tests/test_api_approvals.py` that a Manager approving 75,000 gets HTTP 403 with the reason and the invoice stays unchanged

### Implementation for Increment 1

- [ ] T014 [US1] Implement the Manager limit logic in `backend/src/invoice_app/domain/approval_policy.py` using `Decimal` thresholds and inclusive comparisons (`amount <= 50,000.00`)
- [ ] T015 [US1] Implement the Director single-approver logic in `backend/src/invoice_app/domain/approval_policy.py` for `amount <= 500,000.00`, preserving the rule that exactly 500,000.00 is valid
- [ ] T016 [US1] Add refusal logic in `backend/src/invoice_app/domain/approval_policy.py` for Manager approvals above 50,000.00 and at most 500,000.00, returning a clear `ApprovalNotAllowed` reason before any state mutation
- [ ] T017 [US1] Wire the service layer in `backend/src/invoice_app/domain/approval_service.py` so `approve()` calls the policy result before building any new state and only updates the repository once on a valid approval
- [ ] T018 [US1] Add the single-approver validation to the API layer in `backend/src/invoice_app/api/main.py` so approval refusals become HTTP 403 with `{"error": reason}` and leave the invoice unchanged
- [ ] T019 [US1] Validate the UI approval flow in `backend/src/invoice_app/api/static/app.js` and `backend/src/invoice_app/api/static/index.html` so the approvals tab and status handling remain aligned with the new single-approver rules

**Checkpoint**: Increment 1 should be independently testable: manager and director thresholds work, refusals are preserved, and the API contract is correct.

---

## Phase 4: Increment 2 - Two-Approver Rule (Priority: P1) 🎯 MVP

**Goal**: Implement the high-value approval path where invoices above 500,000.00 require two distinct approvers, the first may be Manager or Director, and the second must be a different Director.

**Independent Test**: An invoice above 500,000.00 is moved to `AwaitingSecondApproval` after the first valid approval, only a different Director can complete approval, same-user or invalid-role attempts are refused unchanged, and a rejection while in `AwaitingSecondApproval` finalises the invoice instead of leaving it unchanged.

### Tests for Increment 2 (MUST be written first) ⚠️

- [ ] T020 [P] [US2] Add first-approval tests in `backend/tests/test_two_approver_rule.py` for the high-value path where the first approver may be a Manager or Director and the invoice enters `AwaitingSecondApproval` with `decidedBy`/`decidedAt` still empty; include the case that exactly 500,000.00 still requires only one Director
- [ ] T021 [P] [US2] Add same-user boundary tests in `backend/tests/test_two_approver_rule.py` for exact match, different letter case, and surrounding whitespace with unchanged-invoice assertions and update-call checks
- [ ] T022 [P] [US2] Add second-approval refusal tests in `backend/tests/test_two_approver_rule.py` for non-Director second approvers, Admin attempts, and the successful final approval by a different Director
- [ ] T023 [P] [US2] Add two different Managers cannot complete a >500,000 invoice test in `backend/tests/test_two_approver_rule.py`
- [ ] T024 [P] [US2] Add rejection tests in `backend/tests/test_two_approver_rule.py` for an invoice in `AwaitingSecondApproval` that is rejected by a Manager or Director; this is a final rejection, not a refusal, and the assertions are status `Rejected`, `decision_note = reason`, `decided_by = the rejecting user`, and `decided_at` set

### Implementation for Increment 2

- [ ] T025 [US2] Extend `backend/src/invoice_app/domain/approval_policy.py` with the two-approver rule: `amount > 500,000.00` requires a first approval followed by a distinct second Director approval, and same-user comparisons are trimmed and case-insensitive
- [ ] T026 [US2] Add the `AwaitingSecondApproval` transition and approval audit tracking in `backend/src/invoice_app/domain/models.py` so the first approval is stored without final `decidedBy`/`decidedAt` and the second approval completes the final decision
- [ ] T027 [US2] Update `backend/src/invoice_app/domain/approval_service.py` to handle the first approval state transition and the final approval state transition without mutating state when a refusal is raised
- [ ] T028 [US2] Add the API-side contract enforcement in `backend/src/invoice_app/api/main.py` for the final approval and refusal cases so HTTP 403 + `{"error": reason}` remains consistent for invalid second approvals and same-user attempts
- [ ] T029 [US2] Update the approval tab in `backend/src/invoice_app/api/static/app.js` to include `AwaitingSecondApproval` invoices and keep the UI aligned with the state lifecycle and approval history
- [ ] T030 [US2] Ensure unknown roles are refused in the same way as Admin attempts in `backend/src/invoice_app/api/auth.py` and `backend/src/invoice_app/domain/approval_policy.py`, with a clear reason and no invoice mutation

**Checkpoint**: Increment 2 should be independently testable: high-value invoices require two distinct Director approvals and refusals leave state untouched.

---

## Phase 5: Final Validation & Quality Gates

**Purpose**: Confirm the feature meets the project’s rule and evidence expectations before completion.

- [ ] T031 [P] Run `cd backend && pytest` to validate the boundary tests, refusal assertions, and approval state transitions for both increments
- [ ] T032 [P] Run `cd backend && mutmut run && mutmut results` to measure mutation quality on the domain package and report surviving mutants if any remain
- [ ] T033 [P] Add one Playwright for Python test in `e2e/tests/` where `demo.manager` approves a 75,000 invoice in the UI, sees the refusal reason, and the invoice stays `PendingApproval` using page objects and only `get_by_role`/`get_by_label` selectors
- [ ] T034 [P] Perform an agent review for the approval logic and confirm the domain-only placement, Decimal checks, refusal-before-write behavior, and exact update semantics as required by AGENTS.md

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1): No dependencies.
- Foundational (Phase 2): Depends on Setup completion and blocks all increment work.
- Increment 1 (Phase 3): Depends on Foundational completion.
- Increment 2 (Phase 4): Depends on Increment 1 completion and the second-stage approval requirements.
- Final Validation (Phase 5): Depends on both increments being complete.

### User Story Dependencies

- **US1**: Single-approver limits and boundary rules; independent of US2 after the foundational phase.
- **US2**: Two-approver rule; depends on US1 being stable and uses the same approval policy contract.

### Parallel Opportunities

- Setup and foundational tasks marked [P] can run in parallel.
- The Unit tests for each increment marked [P] can be written in parallel.
- The final validation tasks can be scheduled in parallel after both increments are complete.

---

## Parallel Example: Increment 1

```bash
# Run the boundary test tasks together before implementation:
Task: "Add boundary tests for Manager approvals in backend/tests/test_approval_limits.py"
Task: "Add director threshold tests in backend/tests/test_approval_limits.py"
Task: "Add invalid-role tests in backend/tests/test_approval_limits.py"
Task: "Add API approval test in backend/tests/test_api_approvals.py"
```

---

## Implementation Strategy

### MVP First (Increment 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Increment 1 (single-approver limits).
3. Run `cd backend && pytest` and confirm the spec-driven boundary cases pass.
4. Stop and validate before moving to the two-step approval rule.

### Incremental Delivery

1. Complete the foundation and implement the single-approver rules.
2. Add the two-approver rule and same-user validation.
3. Validate the domain and UI behavior end-to-end.
4. Complete final mutation and Playwright checks.

---

## Notes

- [P] tasks are different files or independent validation steps without dependency conflicts.
- [US1]/[US2] labels map directly to the two product increments requested in the specification.
- Each task includes an exact file path and is detailed enough to be executed without extra context.
- The implementation order deliberately places tests before code within each increment, matching the project requirement to validate with pytest after each change.
