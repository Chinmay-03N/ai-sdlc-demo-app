<!--
Sync Impact Report:
- Version change: template baseline -> 1.0.0
- Modified principles: none -> I. Domain-First Business Rules, II. Decimal Money & Inclusive Limits, III. Refusal-First State Safety, IV. Boundary-Driven Test Coverage, V. Delivery Quality & Mutation Readiness
- Added sections: Quality Gates, Delivery & Review
- Removed sections: none
- Deferred items: none.
-->

# Invoice Approval Demo Constitution

## Core Principles

### I. Domain-First Business Rules
Business rules MUST live only in backend/src/invoice_app/domain. Route handlers, API layer code, and UI logic MAY translate domain errors to HTTP or user messages, but they MUST NOT decide approval policy, limit logic, or invoice lifecycle transitions. This keeps the approval model consistent, reviewable, and testable independent from transport concerns.

### II. Decimal Money & Inclusive Limits
All monetary values in the domain MUST use Decimal, never float. Approval thresholds MUST be represented as named constants in the domain policy and evaluated with inclusive comparisons, so the rule boundary is explicit and the same in code and tests. This prevents silent rounding errors and makes the business meaning of each threshold unambiguous.

### III. Refusal-First State Safety
A refused approval or rejection attempt MUST be evaluated before any state change is built or persisted. The system MUST check the rule first, must not mutate the invoice while constructing the rejection reason, and must write only once after a valid transition is confirmed. A refusal MUST leave the invoice unchanged in status, approvals, and decision fields.

### IV. Boundary-Driven Test Coverage
Every approval rule MUST have a positive test, a negative test, and a boundary test on both sides of the limit. Refusal tests MUST assert that the stored invoice remains identical before and after the failed action and that repository update calls do not increase. The same-user rule MUST be tested with exact-match, different-case, and whitespace-padded usernames to prove the rule is enforced without ambiguity.

### V. Delivery Quality & Mutation Readiness
Each implementation step MUST be committed independently with passing tests and a commit message containing a clear Why: explanation. The domain package MUST be measured with mutation testing and the score MUST be reported; surviving mutants MUST be explained and, when practical, eliminated. This ensures that the business rules are not merely passing examples but remain resilient under deliberate fault injection.

## Quality Gates
The project MUST preserve the separation between domain logic and API/UI concerns. All business-rule changes MUST be accompanied by tests covering the positive path, the failing path, and exact threshold boundaries. Refusal tests MUST verify both the returned reason and the immutable invoice state. Mutation testing on the domain package MUST be treated as a required quality signal, not an optional extra.

## Delivery & Review
Implementation work MUST proceed in small, reviewable increments. Each step MUST be validated with the project's test suite and must be committed as a standalone change that explains the rationale in the message body. Reviews MUST confirm the domain-only rule placement, Decimal-based comparisons, refusal-before-write behavior, boundary coverage, and the mutation-reporting discipline before a change is considered complete.

## Governance
This constitution governs the approval demo repository and supersedes ad hoc rule interpretations that contradict these principles. Any amendment MUST document the decision, explain the rule impact, and preserve the non-negotiable requirements for domain ownership, Decimal money usage, refusal-before-write safety, and test quality.

Changes are versioned using semantic versioning:
- MAJOR: backward-incompatible governance or principle changes;
- MINOR: new principles or materially expanded guidance;
- PATCH: clarifications, wording updates, or non-semantic refinements.

Compliance reviews MUST check that the source of truth remains in the domain layer, that all thresholds are implemented as named constants with inclusive semantics, that refusal behavior leaves state untouched, and that the required boundary and mutation evidence is present before an implementation is accepted.

**Version**: 1.0.0 | **Ratified**: 2026-10-31 | **Last Amended**: 2026-10-31
