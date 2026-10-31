# Implementation Plan: Invoice Approval Limits

**Branch**: feature/approval-limits | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-invoice-approval-limits/spec.md`

## Summary

Add role-based approval limits and two-stage approval logic to the invoice approval domain while keeping business rules isolated from FastAPI routes and UI code. The implementation will introduce a pure policy module, extend the invoice state model to include `AwaitingSecondApproval` and a recorded `approvals` list, enforce refusal-before-write semantics, and make the approval tab surface high-value invoices awaiting a second reviewer.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: FastAPI, Pydantic, pytest, mutmut, Playwright for Python

**Storage**: In-memory repository used by the API layer; business logic remains repository-agnostic

**Testing**: pytest for unit coverage; mutmut for domain mutation testing; Playwright Python for UI smoke validation

**Target Platform**: Local web app running in the repo-backed FastAPI service

**Project Type**: Web service with a small static UI

**Performance Goals**: Approval decisions complete in a single synchronous domain evaluation; no database or network calls are introduced in the policy layer

**Constraints**: Business rules must live only under `backend/src/invoice_app/domain`; all money comparisons must use `Decimal`; invalid approvals must refuse before state mutation; same-user checks use trimmed, case-insensitive username comparison

**Scale/Scope**: Small in-memory demo app with a few status transitions and a small set of demo roles and invoices

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Domain-first business rules: PASS — all approval decisions will live in `backend/src/invoice_app/domain/approval_policy.py` and `ApprovalService` remains the lifecycle orchestrator.
- Decimal money and inclusive thresholds: PASS — thresholds are fixed constants evaluated with `Decimal`, including exact boundary values at 50,000.00 and 500,000.00.
- Refusal-before-write safety: PASS — invalid approval attempts will be evaluated before any state mutation and the repository will only be updated after a valid decision is confirmed.
- Boundary-driven tests: PASS — unit tests will cover both sides of each threshold and same-user identity edge cases.
- Delivery quality and mutation readiness: PASS — domain tests will be designed around refusal behavior and mutation testing will be used for the approval policy package.

## Project Structure

### Documentation (this feature)

```text
specs/001-invoice-approval-limits/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
├── checklists/
└── spec.md
```

### Source Code (repository root)

```text
backend/
├── src/
│   └── invoice_app/
│       ├── api/
│       │   ├── auth.py
│       │   ├── in_memory_repository.py
│       │   ├── main.py
│       │   └── static/
│       └── domain/
│           ├── approval_policy.py
│           ├── approval_service.py
│           ├── errors.py
│           ├── models.py
│           └── repository.py
└── tests/
    ├── conftest.py
    ├── fakes.py
    └── test_approval_service.py
```

**Structure Decision**: Keep the feature within the existing FastAPI service layout and add the domain policy module to the domain package; no new app-level service layer is introduced beyond `ApprovalService` and the existing API repository boundary.

## Complexity Tracking

No constitutional violations require a formal justification.
