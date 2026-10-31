from __future__ import annotations

from datetime import datetime, timezone

import pytest

from invoice_app.domain.approval_service import ApprovalService
from invoice_app.domain.errors import InvalidInvoiceState, InvalidRequest, InvoiceNotFound
from invoice_app.domain.models import Invoice, InvoiceStatus
from fakes import FakeInvoiceRepository


def invoice_with(invoice_id: str, status: InvoiceStatus) -> Invoice:
    return Invoice(id=invoice_id, customer_name="Test School", amount=100, status=status)


def service_for(*invoices: Invoice, fixed_time: datetime | None = None) -> ApprovalService:
    clock = (lambda: fixed_time) if fixed_time is not None else None
    return ApprovalService(FakeInvoiceRepository(list(invoices)), clock=clock)


def test_submit_moves_draft_to_pending_approval() -> None:
    invoice = invoice_with("INV-1", InvoiceStatus.Draft)

    result = service_for(invoice).submit("INV-1")

    assert result.status == InvoiceStatus.PendingApproval


def test_submit_rejects_invoice_that_is_not_a_draft() -> None:
    service = service_for(invoice_with("INV-1", InvoiceStatus.Approved))

    with pytest.raises(InvalidInvoiceState):
        service.submit("INV-1")


def test_approve_sets_status_approver_and_timestamp() -> None:
    fixed_time = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
    service = service_for(invoice_with("INV-1", InvoiceStatus.PendingApproval), fixed_time=fixed_time)

    result = service.approve("INV-1", "demo.approver")

    assert result.status == InvoiceStatus.Approved
    assert result.decided_by == "demo.approver"
    assert result.decided_at == fixed_time


def test_approve_rejects_invoice_that_is_still_a_draft() -> None:
    service = service_for(invoice_with("INV-1", InvoiceStatus.Draft))

    with pytest.raises(InvalidInvoiceState):
        service.approve("INV-1", "demo.approver")


def test_approve_throws_when_invoice_does_not_exist() -> None:
    service = service_for()

    with pytest.raises(InvoiceNotFound):
        service.approve("INV-404", "demo.approver")


def test_reject_records_reason_and_approver() -> None:
    service = service_for(invoice_with("INV-1", InvoiceStatus.PendingApproval))

    result = service.reject("INV-1", "demo.approver", "Duplicate invoice")

    assert result.status == InvoiceStatus.Rejected
    assert result.decision_note == "Duplicate invoice"


def test_reject_requires_a_reason() -> None:
    service = service_for(invoice_with("INV-1", InvoiceStatus.PendingApproval))

    with pytest.raises(InvalidRequest):
        service.reject("INV-1", "demo.approver", "  ")
