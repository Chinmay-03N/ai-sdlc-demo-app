# Research: Invoice Approval Limits

## Decision: Centralize approval policy in a pure domain function

**Decision**: Implement `evaluate_approval(invoice, approver) -> ApprovalDecision` in `backend/src/invoice_app/domain/approval_policy.py` and keep all role/limit checks in that module.

**Rationale**: The feature is fundamentally business logic. A pure decision function allows the service to evaluate the approval before any state mutation, keeps the API layer thin, and supports precise tests for thresholds, same-user validation, and refusal semantics.

**Alternatives considered**:
- Inlining decision logic directly in `ApprovalService` only: rejected because it increases branching complexity and couples lifecycle handling to business rules.
- Putting policy checks in API routes: rejected because the project constitution expressly forbids route-level business logic and obscures domain safety guarantees.

## Decision: Use explicit domain enums and approval records

**Decision**: Extend `InvoiceStatus` with `AwaitingSecondApproval` and add `Invoice.approvals: list[ApprovalRecord]` to preserve the audit trail of valid approvals.

**Rationale**: The second-stage approval flow requires a state that distinguishes “first approval taken but final decision pending” from “approved”. The event list also preserves the sequence of approvers for later UI display and validation.

**Alternatives considered**:
- Reusing only `decided_by`/`decided_at`: rejected because it discards the first approval’s audit trail and cannot represent two distinct approvers cleanly.
- Storing approvals in the API layer: rejected because the domain model should own the invoice lifecycle and its recorded approvals.

## Decision: Refusal is a domain error mapped by the API

**Decision**: `ApprovalNotAllowed` remains a domain error raised before any repository write; the API maps it to HTTP 403 with `{"error": reason}`.

**Rationale**: This matches the requirement that refusals leave the invoice completely unchanged while still producing a clear human-readable reason.

**Alternatives considered**:
- Returning non-HTTP error objects from the service: rejected because the API contract must surface the reason in a transport-safe format.
- Mutating invoice state before raising: rejected because it violates the constitution and fails the “nothing changes on refusal” requirement.

## Decision: Split implementation into two increments

**Decision**: Deliver the feature as a progressive change: first single-approver rules and threshold checks, then the second approver path and same-user enforcement.

**Rationale**: The spec explicitly calls for a staged delivery and the repo instructions prefer small, reviewable increments.

**Alternatives considered**:
- Implementing the full multi-step flow in one patch: rejected because it mixes validation and lifecycle changes, making review and debugging harder.

## Additional findings

- Existing demo auth still uses a generic `Approver` role; the rule expansion to `Manager` and `Director` will be handled in the domain and web auth mapping.
- The UI currently exposes invoice status filters and approval actions; the approvals tab should include `AwaitingSecondApproval` invoices, ensuring the second-stage state remains visible without changing the invoice record on refusal.
- The in-memory repo is already repository-agnostic enough for the policy layer to remain pure and testable.
