# Feature Specification: Invoice Approval Limits

**Feature Branch**: feature/approval-limits

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "Add approval limits by role to the invoice approval service.
- A Manager may approve invoices up to 50,000.
- A Director may approve invoices up to 500,000.
- Anything above 500,000 needs two distinct approvers, and the second approver must be a Director.
- The same user may never count as both approvers on one invoice.
- A refused approval attempt returns a clear reason, and the invoice remains unchanged.
- Rejecting an invoice in AwaitingSecondApproval finalises it as Rejected, sets decision_note to the rejection reason, sets decided_by to the rejecting user, and sets decided_at to the rejection time.
Clarifications already decided:
- Limits are inclusive (50,000.00 and 500,000.00 are within limit). Exactly 500,000.00 needs one Director.
- Above 500,000.00 the first approver may be a Manager or a Director; the second must be a different user who is a Director.
- After the first of two approvals the invoice is AwaitingSecondApproval; the approval is recorded; decidedBy/decidedAt stay empty until final.
- Same user = case-insensitive comparison of trimmed usernames.
- Refusal: HTTP 403 with {"error": reason}; no repository write; status, approvals and decided fields unchanged.
- Rejection of an invoice in AwaitingSecondApproval: final status is Rejected, decision_note = rejection reason, decided_by = rejecting user, decided_at = rejection time.
- Roles: Manager, Director, Admin. Admin cannot approve. Demo users demo.manager, demo.director, demo.director2, demo.admin.
- Out of scope: bulk approval (UC-1), partial approval (UC-2), notifications.
Deliver in two increments: (1) single-approver limits, (2) the two-approver rule."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manager approval within role limit (Priority: P1)

A manager can approve an invoice when the amount is within the manager threshold, and the invoice moves to the next valid state without any extra approval steps.

**Why this priority**: This is the baseline approval path for the most common daily invoices and reflects the business rule that determines which roles are eligible at lower amounts.

**Independent Test**: A pending invoice for 50,000.00 can be reviewed by a manager and successfully approved without requiring additional reviewers.

**Acceptance Scenarios**:

1. **Given** a pending invoice valued at 50,000.00, **When** a manager approves it, **Then** the invoice is approved and the approval is recorded as valid.
2. **Given** a pending invoice valued at 50,000.01, **When** a manager attempts approval, **Then** the attempt is refused with a clear reason and the invoice remains unchanged.

---

### User Story 2 - Director approval at and below the higher threshold (Priority: P1)

A director can approve invoices up to the director limit, including the exact threshold, and can act as a single approver for invoices that remain within that ceiling.

**Why this priority**: This rule defines the second approval threshold and ensures the business does not unnecessarily force a second approval for invoices that remain within the higher role limit.

**Independent Test**: A director can approve a 500,000.00 invoice without a second approver and a director cannot approve a larger invoice without additional approval requirements.

**Acceptance Scenarios**:

1. **Given** a pending invoice valued at 500,000.00, **When** a director approves it, **Then** the invoice is approved and the decision is valid.
2. **Given** a pending invoice valued at 500,000.01, **When** a director approves it, **Then** the director's approval is recorded as the first approval, the invoice moves to AwaitingSecondApproval, and decidedBy/decidedAt stay empty.

---

### User Story 3 - High-value invoice requires two distinct approvers (Priority: P1)

Invoices above the director limit require a second approval step, with the first approver being either a manager or a director and the second approver being a different director.

**Why this priority**: This is the highest-risk approval scenario because it protects against high-value mistakes and prevents the same user from counting twice on the same invoice.

**Independent Test**: An invoice over 500,000.00 can be moved to AwaitingSecondApproval after the first valid approval, and only a different director can complete the final approval.

**Acceptance Scenarios**:

1. **Given** a pending invoice valued at 500,000.01, **When** a manager approves it first, **Then** the invoice enters AwaitingSecondApproval and the approval is recorded while the final decision fields remain empty.
2. **Given** an invoice awaiting a second approval, **When** a different director approves it, **Then** the invoice becomes approved, the second approver is recorded as decidedBy, and decidedAt is set.
3. **Given** an invoice awaiting a second approval, **When** the same director approves it again, **Then** the attempt is refused with a clear reason and the stored invoice is unchanged.
4. **Given** an invoice awaiting a second approval, **When** the same director approves it again using a different letter case in the username, **Then** the attempt is refused with a clear reason and the stored invoice is unchanged.
5. **Given** an invoice awaiting a second approval, **When** the same director approves it again with surrounding whitespace in the username, **Then** the attempt is refused with a clear reason and the stored invoice is unchanged.
6. **Given** an invoice awaiting a second approval, **When** a different manager attempts the second approval, **Then** the attempt is refused with a clear reason and the stored invoice is unchanged.
7. **Given** an invoice awaiting a second approval, **When** an admin attempts any approval, **Then** the attempt is refused with a clear reason and the stored invoice is unchanged.

---

### Edge Cases

- 50,000.00 is within the Manager limit and may be approved by a Manager.
- 50,000.01 is above the Manager limit and must be refused for a Manager approval attempt.
- 500,000.00 is within the Director limit and may be approved by a single Director.
- 500,000.01 requires a second approval, and the second approver must be a different Director.
- A same-user second approval attempt is refused even when the username differs only by letter case or surrounding whitespace.
- An Admin approval attempt is refused with a clear reason and leaves the invoice unchanged.
- An invoice in AwaitingSecondApproval may be rejected by a Manager or Director with a reason; this finalises the invoice as Rejected and records the rejecting user and rejection time.

### Refusal reasons

- Role without authority: "Role {role} cannot approve invoices."
- Over limit: "Invoice amount {amount} exceeds the {role} approval limit of {limit}."
- Same user: "{username} has already approved invoice {id}; the same user cannot count as both approvers."
- Second approver not a Director: "Invoices above 500,000.00 need a Director as the second approver; {username} is a {role}."

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow a Manager to approve an invoice when the amount is less than or equal to 50,000.00.
- **FR-002**: The system MUST refuse a Manager approval attempt when the amount is greater than 50,000.00 and at most 500,000.00.
- **FR-003**: The system MUST allow a Director to approve an invoice when the amount is less than or equal to 500,000.00.
- **FR-004**: The system MUST require a second approval for any invoice amount greater than 500,000.00.
- **FR-005**: The system MUST allow the first approver for a high-value invoice to be either a Manager or a Director.
- **FR-006**: The system MUST require the second approver for a high-value invoice to be a different user who is a Director.
- **FR-007**: The system MUST treat the same user as invalid for both approvals on the same invoice, using a case-insensitive comparison after trimming usernames.
- **FR-008**: A Director's approval of an amount greater than 500,000.00 is recorded as the first approval and moves the invoice to AwaitingSecondApproval.
- **FR-009**: An invoice in AwaitingSecondApproval MAY be rejected by a Manager or Director with a reason; the rejection MUST finalise the invoice as Rejected, set decision_note to the rejection reason, set decided_by to the rejecting user, and set decided_at to the rejection time.
- **FR-010**: When the second approval completes, the system MUST set decidedBy to the second approver and set decidedAt to the time of the final approval.
- **FR-011**: Unknown roles are refused in the same way as Admin users, with a clear reason and no invoice mutation.
- **FR-012**: The system MUST refuse any approval attempt by an Admin user with a clear reason.
- **FR-013**: The system MUST return a clear refusal reason for any invalid approval attempt and MUST leave the invoice unchanged in status, approval history, and decision fields. Only refused approval attempts leave the invoice unchanged; a rejection of an invoice in AwaitingSecondApproval finalises the invoice instead.
- **FR-014**: The system MUST return a 403 error response with the refusal reason when an approval attempt is refused.
- **FR-015**: The system MUST ensure no repository write occurs when an approval attempt is refused.
- **FR-016**: The system MUST support the delivery in two increments: single-approver limits first, then the two-approver rule for invoices above 500,000.00.

### Key Entities

- **Invoice**: A pending or in-flight approval record that carries its total amount, approval state, and any recorded approvals.
- **Approver**: A user with a role of Manager, Director, or Admin. Approval rights depend on both role and invoice amount.
- **Approval Decision**: A valid or refused approval action, including the user, role, result, and whether it advances the invoice to a second-approval state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of invoices at or below 50,000.00 are approved by a Manager without a second approval requirement.
- **SC-002**: 100% of invoices at or below 500,000.00 are approved by a Director without a second approval requirement.
- **SC-003**: 100% of invoices above 500,000.00 require two distinct approvers, and the final approver is always a different Director.
- **SC-004**: 100% of refused approval attempts leave the invoice unchanged in state, approval history, and final decision fields.
- **SC-005**: 100% of invalid approval attempts produce a clear refusal reason that explains why the request was denied.
- **SC-006**: Approvers can complete the required approval flows without ambiguity or rework, and staff can reliably distinguish between single-approver and two-stage approval paths.

## Assumptions

- Users are known to the system by username and role, and the role assigned to a user is authoritative for approval eligibility.
- Invoice values are treated as precise monetary amounts and threshold comparisons are inclusive on the exact boundary values specified.
- The approval service is expected to handle only the approval lifecycle described here; bulk approval, partial approval, and notification workflows are explicitly out of scope.
- The demo environment includes the user accounts demo.manager, demo.director, demo.director2, and demo.admin with the roles described in the business rules.
