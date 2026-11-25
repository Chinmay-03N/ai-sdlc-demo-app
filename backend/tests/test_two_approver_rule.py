from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from invoice_app.domain.approval_service import ApprovalService
from invoice_app.domain.errors import ApprovalNotAllowed
from invoice_app.domain.models import ApprovalRecord, Approver, Invoice, InvoiceStatus, Role

from fakes import FakeInvoiceRepository

FIXED_NOW = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)


def make_service(invoice: Invoice) -> tuple[ApprovalService, FakeInvoiceRepository]:
    repository = FakeInvoiceRepository([invoice])
    service = ApprovalService(repository, clock=lambda: FIXED_NOW)
    return service, repository


def invoice_for(
    amount: str, invoice_id: str = "INV-2", status: InvoiceStatus = InvoiceStatus.PendingApproval
) -> Invoice:
    return Invoice(
        id=invoice_id,
        customer_name="Test School",
        amount=Decimal(amount),
        status=status,
    )


@pytest.mark.parametrize(
    ("approver_role", "approver_username"),
    [
        (Role.MANAGER, "maria.chen"),
        (Role.DIRECTOR, "sophia.ng"),
    ],
)
def test_first_approval_for_high_value_invoice_is_recorded_and_waits_for_second_approver(
    approver_role: Role, approver_username: str
) -> None:
    service, repository = make_service(invoice_for("500000.01"))
    approver = Approver(approver_username, approver_role)

    result = service.approve("INV-2", approver)

    assert result.status == InvoiceStatus.AwaitingSecondApproval
    assert result.decided_by is None
    assert result.decided_at is None
    assert len(result.approvals) == 1
    assert result.approvals[0].username == approver_username
    assert result.approvals[0].role == approver_role
    assert repository.update_calls == 1
    assert repository.get_by_id("INV-2") == result


def test_exactly_500000_still_requires_only_one_director() -> None:
    service, repository = make_service(invoice_for("500000.00"))
    approver = Approver("sophia.ng", Role.DIRECTOR)

    result = service.approve("INV-2", approver)

    assert result.status == InvoiceStatus.Approved
    assert result.decided_by == "sophia.ng"
    assert result.decided_at == FIXED_NOW
    assert repository.update_calls == 1


def test_second_approval_refuses_same_director_exact_match() -> None:
    invoice = invoice_for("500000.01")
    invoice.status = InvoiceStatus.AwaitingSecondApproval
    invoice.approvals = [
        ApprovalRecord(username="charlotte.ward", role=Role.DIRECTOR, approved_at=FIXED_NOW),
    ]
    service, repository = make_service(invoice)
    original = repository.get_by_id("INV-2")
    approver = Approver("charlotte.ward", Role.DIRECTOR)
    expected = "charlotte.ward has already approved invoice INV-2; the same user cannot count as both approvers."

    with pytest.raises(ApprovalNotAllowed, match=re.escape(expected)):
        service.approve("INV-2", approver)

    assert repository.update_calls == 0
    assert repository.get_by_id("INV-2") == original


def test_second_approval_refuses_same_director_with_different_case() -> None:
    invoice = invoice_for("500000.01")
    invoice.status = InvoiceStatus.AwaitingSecondApproval
    invoice.approvals = [
        ApprovalRecord(username="charlotte.ward", role=Role.DIRECTOR, approved_at=FIXED_NOW),
    ]
    service, repository = make_service(invoice)
    original = repository.get_by_id("INV-2")
    approver = Approver("CHARLOTTE.WARD", Role.DIRECTOR)
    expected = "CHARLOTTE.WARD has already approved invoice INV-2; the same user cannot count as both approvers."

    with pytest.raises(ApprovalNotAllowed, match=re.escape(expected)):
        service.approve("INV-2", approver)

    assert repository.update_calls == 0
    assert repository.get_by_id("INV-2") == original


def test_second_approval_refuses_same_director_with_surrounding_whitespace() -> None:
    invoice = invoice_for("500000.01")
    invoice.status = InvoiceStatus.AwaitingSecondApproval
    invoice.approvals = [
        ApprovalRecord(username="charlotte.ward", role=Role.DIRECTOR, approved_at=FIXED_NOW),
    ]
    service, repository = make_service(invoice)
    original = repository.get_by_id("INV-2")
    approver = Approver("  charlotte.ward  ", Role.DIRECTOR)
    expected = "charlotte.ward has already approved invoice INV-2; the same user cannot count as both approvers."

    with pytest.raises(ApprovalNotAllowed, match=re.escape(expected)):
        service.approve("INV-2", approver)

    assert repository.update_calls == 0
    assert repository.get_by_id("INV-2") == original


def test_second_approval_refuses_manager_second_approver() -> None:
    invoice = invoice_for("500000.01")
    invoice.status = InvoiceStatus.AwaitingSecondApproval
    invoice.approvals = [
        ApprovalRecord(username="maria.chen", role=Role.MANAGER, approved_at=FIXED_NOW),
    ]
    service, repository = make_service(invoice)
    original = repository.get_by_id("INV-2")
    approver = Approver("evan.morris", Role.MANAGER)
    expected = "Invoices above 500,000.00 need a Director as the second approver; evan.morris is a Manager."

    with pytest.raises(ApprovalNotAllowed, match=re.escape(expected)):
        service.approve("INV-2", approver)

    assert repository.update_calls == 0
    assert repository.get_by_id("INV-2") == original


def test_second_approval_refuses_two_different_managers() -> None:
    invoice = invoice_for("500000.01")
    invoice.status = InvoiceStatus.AwaitingSecondApproval
    invoice.approvals = [
        ApprovalRecord(username="maria.chen", role=Role.MANAGER, approved_at=FIXED_NOW),
    ]
    service, repository = make_service(invoice)
    original = repository.get_by_id("INV-2")
    approver = Approver("nina.patel", Role.MANAGER)
    expected = "Invoices above 500,000.00 need a Director as the second approver; nina.patel is a Manager."

    with pytest.raises(ApprovalNotAllowed, match=re.escape(expected)):
        service.approve("INV-2", approver)

    assert repository.update_calls == 0
    assert repository.get_by_id("INV-2") == original


def test_second_approver_must_be_a_different_director() -> None:
    invoice = invoice_for("500000.01")
    invoice.status = InvoiceStatus.AwaitingSecondApproval
    invoice.approvals = [
        ApprovalRecord(username="maria.chen", role=Role.MANAGER, approved_at=FIXED_NOW),
    ]
    service, repository = make_service(invoice)

    result = service.approve("INV-2", Approver("olivia.riggs", Role.DIRECTOR))

    assert result.status == InvoiceStatus.Approved
    assert result.decided_by == "olivia.riggs"
    assert result.decided_at == FIXED_NOW
    assert len(result.approvals) == 2
    assert repository.update_calls == 1


def test_awaiting_second_approval_can_be_rejected_by_director() -> None:
    invoice = invoice_for("500000.01")
    invoice.status = InvoiceStatus.AwaitingSecondApproval
    invoice.approvals = [
        ApprovalRecord(username="maria.chen", role=Role.MANAGER, approved_at=FIXED_NOW),
    ]
    service, repository = make_service(invoice)
    reason = "Budget not approved"

    result = service.reject("INV-2", Approver("sophia.ng", Role.DIRECTOR), reason)

    assert result.status == InvoiceStatus.Rejected
    assert result.decision_note == reason
    assert result.decided_by == "sophia.ng"
    assert result.decided_at == FIXED_NOW
    assert repository.update_calls == 1
