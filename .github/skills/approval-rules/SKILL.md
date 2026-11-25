---
name: approval-rules
description: Invoice approval limits by role (Manager 50,000, Director 500,000, two distinct approvers above 500,000 with a Director second). Use whenever writing, testing, reviewing or specifying approval logic.
---
# Approval rules

## Decision table (amounts are Decimal, limits inclusive)

| Amount | Existing approvals | Approver | Result | Status after |
|---|---|---|---|---|
| any | — | Admin (or unknown role) | Refuse: "Role Admin cannot approve invoices." | unchanged |
| ≤ 50,000.00 | none | Manager or Director | Approve (final) | Approved |
| 50,000.01 – 500,000.00 | none | Manager | Refuse: "...exceeds the Manager approval limit of 50,000.00." | unchanged |
| 50,000.01 – 500,000.00 | none | Director | Approve (final) | Approved |
| > 500,000.00 | none | Manager or Director | Record first approval (not final) | AwaitingSecondApproval |
| > 500,000.00 | 1 by user U | same user U (any case/whitespace) | Refuse: "...the same user cannot count as both approvers." | unchanged |
| > 500,000.00 | 1 by user U | different Manager | Refuse: "...need a Director as the second approver..." | unchanged |
| > 500,000.00 | 1 by user U | different Director | Approve (final) | Approved |

## Boundary values every test suite must use

`0.01`, `49,999.99`, `50,000.00`, `50,000.01`, `500,000.00`, `500,000.01`.

## Invariants

- Policy is evaluated **before** any new state is built. On refusal: no `repository.update`, invoice identical.
- `decided_by` / `decided_at` are set only when the approval is final; `decided_by` is the final approver.
- Usernames compare with `same_user(a, b)`: `a.strip().casefold() == b.strip().casefold()`.
- Refusal reasons are complete sentences that name the role and the limit.

## Where the code lives

`backend/src/invoice_app/domain/approval_policy.py` (`MANAGER_LIMIT`, `DIRECTOR_LIMIT`, `evaluate_approval`)
and `approval_service.py` (`ApprovalService.approve`). The API maps `ApprovalNotAllowed` to 403.
