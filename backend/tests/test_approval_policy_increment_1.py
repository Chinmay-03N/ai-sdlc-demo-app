from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from invoice_app.api.auth import SessionStore, UserSession
from invoice_app.api.in_memory_repository import InMemoryInvoiceRepository
from invoice_app.api.main import app
from invoice_app.domain.approval_service import ApprovalService
from invoice_app.domain.errors import ApprovalNotAllowed
from invoice_app.domain.models import Approver, Invoice, InvoiceStatus, Role

from fakes import FakeInvoiceRepository

FIXED_NOW = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)


def make_service(invoice: Invoice) -> tuple[ApprovalService, FakeInvoiceRepository]:
    repository = FakeInvoiceRepository([invoice])
    service = ApprovalService(repository, clock=lambda: FIXED_NOW)
    return service, repository


def invoice_for(amount: str, invoice_id: str = "INV-1") -> Invoice:
    return Invoice(
        id=invoice_id,
        customer_name="Test School",
        amount=Decimal(amount),
        status=InvoiceStatus.PendingApproval,
    )


def test_manager_can_approve_up_to_and_including_50000() -> None:
    """FR-001: Manager approval within the 50,000.00 limit."""
    service, repository = make_service(invoice_for("0.01"))
    approver = Approver("priya.sharma", Role.MANAGER)

    result = service.approve("INV-1", approver)

    assert result.status == InvoiceStatus.Approved
    assert result.decided_by == "priya.sharma"
    assert result.decided_at == FIXED_NOW
    assert repository.update_calls == 1


@pytest.mark.parametrize("amount", ["50000.00"])
def test_manager_can_approve_boundary_amount(amount: str) -> None:
    """FR-001: Manager can approve the exact 50,000.00 boundary."""
    service, repository = make_service(invoice_for(amount))
    approver = Approver("priya.sharma", Role.MANAGER)

    result = service.approve("INV-1", approver)

    assert result.status == InvoiceStatus.Approved
    assert result.decided_by == "priya.sharma"
    assert result.decided_at == FIXED_NOW
    assert repository.update_calls == 1


def test_manager_cannot_approve_amount_above_limit() -> None:
    """FR-002: Manager approval is refused above 50,000.00."""
    invoice = invoice_for("50000.01")
    service, repository = make_service(invoice)
    original = repository.get_by_id("INV-1")
    approver = Approver("priya.sharma", Role.MANAGER)
    expected = "Invoice amount 50,000.01 exceeds the Manager approval limit of 50,000.00."

    with pytest.raises(ApprovalNotAllowed, match=re.escape(expected)):
        service.approve("INV-1", approver)

    assert repository.update_calls == 0
    assert repository.get_by_id("INV-1") == original


def test_director_can_approve_up_to_and_including_500000() -> None:
    """FR-003: Director approval within the 500,000.00 limit."""
    service, repository = make_service(invoice_for("500000.00"))
    approver = Approver("rajesh.lee", Role.DIRECTOR)

    result = service.approve("INV-1", approver)

    assert result.status == InvoiceStatus.Approved
    assert result.decided_by == "rajesh.lee"
    assert result.decided_at == FIXED_NOW
    assert repository.update_calls == 1


def test_director_approval_above_limit_starts_second_approval_flow() -> None:
    """FR-003 / FR-008: A Director can begin the second-approval flow above 500,000.00."""
    invoice = invoice_for("500000.01")
    service, repository = make_service(invoice)
    approver = Approver("rajesh.lee", Role.DIRECTOR)

    result = service.approve("INV-1", approver)

    assert result.status == InvoiceStatus.AwaitingSecondApproval
    assert result.decided_by is None
    assert result.decided_at is None
    assert len(result.approvals) == 1
    assert repository.update_calls == 1


def test_admin_cannot_approve_invoice() -> None:
    """FR-012: Admin users are refused every approval attempt."""
    invoice = invoice_for("100.00")
    service, repository = make_service(invoice)
    original = repository.get_by_id("INV-1")
    approver = Approver("alex.chen", Role.ADMIN)
    expected = "Role Admin cannot approve invoices."

    with pytest.raises(ApprovalNotAllowed, match=re.escape(expected)):
        service.approve("INV-1", approver)

    assert repository.update_calls == 0
    assert repository.get_by_id("INV-1") == original


def test_admin_approval_above_director_limit_is_refused() -> None:
    """FR-012: Admin users are still refused even when the invoice is above 500,000.00."""
    invoice = invoice_for("500000.01")
    service, repository = make_service(invoice)
    original = repository.get_by_id("INV-1")
    approver = Approver("alex.chen", Role.ADMIN)

    with pytest.raises(ApprovalNotAllowed):
        service.approve("INV-1", approver)

    assert repository.update_calls == 0
    assert repository.get_by_id("INV-1") == original


def test_manager_refusal_returns_403_and_error_payload() -> None:
    """FR-014: API returns 403 with the refusal reason on a Manager limit breach."""
    app.state.session_store = SessionStore()
    app.state.repository = InMemoryInvoiceRepository()
    app.state.approval_service = ApprovalService(app.state.repository, clock=lambda: FIXED_NOW)

    invoice = Invoice(
        id="INV-API-1",
        customer_name="Test School",
        amount=Decimal("50000.01"),
        status=InvoiceStatus.PendingApproval,
    )
    app.state.repository.add(invoice)
    token = app.state.session_store.create(UserSession(username="priya.sharma", role=Role.MANAGER))
    expected = {"error": "Invoice amount 50,000.01 exceeds the Manager approval limit of 50,000.00."}

    client = TestClient(app)
    response = client.post(
        f"/api/approvals/{invoice.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json() == expected
