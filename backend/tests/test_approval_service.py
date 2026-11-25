from __future__ import annotations

import re
from datetime import UTC, datetime

import pytest

from invoice_app.domain.approval_policy import ApprovalDecision
from invoice_app.domain.approval_service import ApprovalService
from invoice_app.domain.errors import ApprovalNotAllowed, InvalidInvoiceState, InvalidRequest, InvoiceNotFound
from invoice_app.domain.models import Approver, Invoice, InvoiceStatus, Role

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

    expected = "Invoice INV-1 is Approved; only drafts can be submitted."
    with pytest.raises(InvalidInvoiceState, match=f"^{re.escape(expected)}$"):
        service.submit("INV-1")


def test_approve_sets_status_approver_and_timestamp() -> None:
    fixed_time = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)
    invoice = invoice_with("INV-1", InvoiceStatus.PendingApproval)
    invoice.decision_note = "Previous decision"
    service = service_for(invoice, fixed_time=fixed_time)
    approver = Approver("demo.manager", Role.MANAGER)

    result = service.approve("INV-1", approver)

    assert result.status == InvoiceStatus.Approved
    assert result.decided_by == "demo.manager"
    assert result.decided_at == fixed_time
    assert result.decision_note is None
    assert result.approvals[0].approved_at == fixed_time


def test_approve_rejects_invoice_that_is_still_a_draft() -> None:
    service = service_for(invoice_with("INV-1", InvoiceStatus.Draft))

    expected = "Invoice INV-1 is Draft; only pending invoices can be decided."
    with pytest.raises(InvalidInvoiceState, match=f"^{re.escape(expected)}$"):
        service.approve("INV-1", Approver("demo.manager", Role.MANAGER))


def test_approve_throws_when_invoice_does_not_exist() -> None:
    service = service_for()

    with pytest.raises(InvoiceNotFound, match=f"^{re.escape('Invoice INV-404 was not found.')}$"):
        service.approve("INV-404", Approver("demo.manager", Role.MANAGER))


def test_approve_uses_utc_clock_when_no_clock_is_injected() -> None:
    repository = FakeInvoiceRepository([invoice_with("INV-1", InvoiceStatus.PendingApproval)])
    service = ApprovalService(repository)

    result = service.approve("INV-1", Approver("demo.manager", Role.MANAGER))

    assert result.decided_at is not None
    assert result.decided_at.tzinfo == UTC
    assert result.approvals[0].approved_at is not None
    assert result.approvals[0].approved_at.tzinfo == UTC


def test_approve_uses_fallback_reason_when_policy_reason_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    invoice = invoice_with("INV-1", InvoiceStatus.PendingApproval)
    repository = FakeInvoiceRepository([invoice])
    service = ApprovalService(repository)
    original = repository.get_by_id("INV-1")
    monkeypatch.setattr(
        "invoice_app.domain.approval_service.evaluate_approval",
        lambda *_: ApprovalDecision(False),
    )
    expected = "Approval is not allowed."

    with pytest.raises(ApprovalNotAllowed, match=f"^{re.escape(expected)}$"):
        service.approve("INV-1", Approver("demo.manager", Role.MANAGER))

    assert repository.update_calls == 0
    assert repository.get_by_id("INV-1") == original


def test_reject_records_reason_and_approver() -> None:
    service = service_for(invoice_with("INV-1", InvoiceStatus.PendingApproval))

    result = service.reject("INV-1", Approver("demo.manager", Role.MANAGER), "Duplicate invoice")

    assert result.status == InvoiceStatus.Rejected
    assert result.decision_note == "Duplicate invoice"


def test_reject_requires_a_reason() -> None:
    service = service_for(invoice_with("INV-1", InvoiceStatus.PendingApproval))

    expected = "A reason is required to reject an invoice."
    with pytest.raises(InvalidRequest, match=f"^{re.escape(expected)}$"):
        service.reject("INV-1", Approver("demo.manager", Role.MANAGER), "  ")
