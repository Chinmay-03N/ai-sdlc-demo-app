from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .models import Approver, Invoice, InvoiceStatus, Role

MANAGER_LIMIT = Decimal("50000.00")
DIRECTOR_LIMIT = Decimal("500000.00")


@dataclass(frozen=True)
class ApprovalDecision:
    allowed: bool
    reason: str | None = None


def _format_amount(value: Decimal) -> str:
    return f"{value:,.2f}"


def _normalized_username(value: str) -> str:
    return value.strip().casefold()


def _already_approved(invoice: Invoice, username: str) -> bool:
    normalized = _normalized_username(username)
    return any(_normalized_username(record.username) == normalized for record in invoice.approvals)


def evaluate_approval(invoice: Invoice, approver: Approver) -> ApprovalDecision:
    role_name = approver.role.value
    username = approver.username.strip()

    if approver.role == Role.ADMIN:
        return ApprovalDecision(False, f"Role {role_name} cannot approve invoices.")

    if approver.role not in {Role.MANAGER, Role.DIRECTOR}:
        return ApprovalDecision(False, f"Role {role_name} cannot approve invoices.")

    if invoice.status == InvoiceStatus.AwaitingSecondApproval:
        if _already_approved(invoice, username):
            return ApprovalDecision(
                False,
                f"{username} has already approved invoice {invoice.id}; the same user cannot count as both approvers.",
            )
        if approver.role != Role.DIRECTOR:
            return ApprovalDecision(
                False,
                f"Invoices above 500,000.00 need a Director as the second approver; {username} is a {role_name}.",
            )
        return ApprovalDecision(True)

    if approver.role == Role.MANAGER and invoice.amount > DIRECTOR_LIMIT:
        return ApprovalDecision(True)

    if approver.role == Role.MANAGER and invoice.amount > MANAGER_LIMIT:
        amount_text = _format_amount(invoice.amount)
        limit_text = _format_amount(MANAGER_LIMIT)
        return ApprovalDecision(
            False,
            f"Invoice amount {amount_text} exceeds the Manager approval limit of {limit_text}.",
        )

    return ApprovalDecision(True)
