# Quickstart: Approval Limits Validation

## Prerequisites

1. Install project dependencies from the repo root:
   `cd backend && pip install -e ".[dev]"`
2. Start the FastAPI application:
   `cd backend && uvicorn invoice_app.api.main:app --app-dir src --port 5000`
3. Use the demo accounts defined in the repo constitution and confirm the role assignment is aligned with Manager/Director/Admin expectations for the approval feature.

## Validation scenarios

### Single-approver checks

- Approve a 50,000.00 invoice as a Manager and confirm the invoice is approved.
- Attempt a 50,000.01 approval by a Manager and confirm a 403 response with a clear refusal reason.
- Approve a 500,000.00 invoice as a Director and confirm the invoice is approved.
- Attempt a 500,000.01 approval by a Director and confirm the first approval is recorded while the invoice enters `AwaitingSecondApproval`.

### Two-step approval checks

- Approve a 500,000.01 invoice first as a Manager or Director, then complete the second stage with a different Director and confirm the invoice becomes approved.
- Attempt the second approval by the same Director with different casing or surrounding whitespace and confirm the invoice remains unchanged.
- Attempt the second approval with a different Manager or an Admin and confirm a refusal with no mutation.

### Rejection checks

- Reject an invoice while it is in `AwaitingSecondApproval` and confirm the reason is recorded without changing the underlying approval state.
- Confirm invalid approval attempts do not change status, approvals, or decision fields.

## Expected outcomes

- All valid thresholds are inclusive and explicit.
- All refusal attempts return a clear human-readable reason and a 403 error.
- No repository update occurs when the approval is refused.
- The UI lists invoices in `AwaitingSecondApproval` under the approvals tab.
