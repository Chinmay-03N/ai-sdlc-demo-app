# Approval API Contract

## Approval endpoint

### POST /api/approvals/{invoice_id}/approve

**Purpose**: Validate and record a user approval decision for an invoice.

**Request context**:
- Authenticated session is required.
- Username and role are available from the session.

**Success response**:
- HTTP 200
- Body: invoice JSON with the updated status and approval state

**Failure response**:
- HTTP 403
- Body: `{ "error": "<clear reason>" }`

**Rules**:
- Manager approvals are accepted only for amounts `<= 50,000.00`.
- Director approvals are accepted only for amounts `<= 500,000.00` when the invoice is not already awaiting a second approval.
- Invoices above `500,000.00` require a different Director as the second approver.
- Same-user identity is normalized by trimming and lowercasing before comparison.
- Refusal leaves the invoice otherwise unchanged.

## Rejection endpoint

### POST /api/approvals/{invoice_id}/reject

**Purpose**: Reject a pending or awaiting-second-approval invoice with a required reason.

**Request**:
- JSON body containing a non-empty `reason` field

**Success response**:
- HTTP 200
- Updated invoice payload with a rejected status

**Failure response**:
- HTTP 400 for missing/blank reason
- HTTP 403 for unauthorized or invalid approval context after policy evaluation

## Invoice retrieval

### GET /api/invoices

**Purpose**: Return invoice records, including those in `AwaitingSecondApproval`.

**Behavior**:
- The UI filter must include `AwaitingSecondApproval` among visible approval states.
- The endpoint returns the domain status strings and the approval history list if present.
