# Data Model: Invoice Approval Limits

## Core Entities

### Invoice

| Field | Type | Notes |
|---|---|---|
| id | string | Stable invoice identifier |
| customer_name | string | Customer or invoice owner name |
| amount | Decimal | Monetary value; never stored as float |
| status | InvoiceStatus | Draft, PendingApproval, AwaitingSecondApproval, Approved, Rejected |
| created_at | datetime | Creation timestamp |
| decided_by | Optional[str] | Final approver when the invoice is approved or rejected |
| decided_at | Optional[datetime] | Final decision timestamp |
| decision_note | Optional[str] | Rejection reason or final decision note |
| approvals | list[ApprovalRecord] | Valid approvals recorded for the invoice |

### ApprovalRecord

| Field | Type | Notes |
|---|---|---|
| username | str | Username of the approver |
| role | str | Manager, Director, or Admin if relevant to audit logging |
| approved_at | datetime | Timestamp when the approval was accepted |
| is_final | bool | True only for the last approval that finalizes the invoice |

### Approver

| Field | Type | Notes |
|---|---|---|
| username | str | Demo user or authenticated user id |
| role | str | Manager, Director, Admin |

### ApprovalDecision

| Field | Type | Notes |
|---|---|---|
| allowed | bool | Whether the requested approval is valid |
| status | Optional[InvoiceStatus] | The next invoice status if the decision is allowed |
| reason | Optional[str] | Clear human-readable refusal reason when `allowed` is false |
| approval_record | Optional[ApprovalRecord] | The approval record to append if accepted |

## Enum Values

### InvoiceStatus

- Draft
- PendingApproval
- AwaitingSecondApproval
- Approved
- Rejected

## Validation Rules

- Amount thresholds use `Decimal` comparisons with inclusive bounds at 50,000.00 and 500,000.00.
- A Manager may approve at amounts `<= 50,000.00`.
- A Director may approve at amounts `<= 500,000.00`.
- Amounts `> 500,000.00` require two approvals: first approver may be Manager or Director; second approver must be a different Director.
- Same-user identity is compared case-insensitively after trimming whitespace.
- Refused approval attempts must not mutate status, approvals, or final decision fields.

## State Transitions

```text
Draft -> PendingApproval -> Approved
    \-> Rejected
PendingApproval -> AwaitingSecondApproval -> Approved
                \-> Rejected
AwaitingSecondApproval -> Approved
                     \-> Rejected
```

The key difference is that `AwaitingSecondApproval` keeps `decidedBy` and `decidedAt` empty until the final approval. The second approval sets the final decision fields and closes the approval cycle.
