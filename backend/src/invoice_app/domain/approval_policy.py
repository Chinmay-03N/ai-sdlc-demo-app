from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .models import Approver, Invoice, Role

MANAGER_LIMIT = Decimal("50000.00")
DIRECTOR_LIMIT = Decimal("500000.00")


@dataclass(frozen=True)
class ApprovalDecision:
    allowed: bool
    reason: str | None = None


def _format_amount(value: Decimal) -> str:
    return f"{value:,.2f}"


def evaluate_approval(invoice: Invoice, approver: Approver) -> ApprovalDecision:
    role_name = approver.role.value

    if approver.role == Role.ADMIN:
        return ApprovalDecision(False, f"Role {role_name} cannot approve invoices.")

    if approver.role not in {Role.MANAGER, Role.DIRECTOR}:
        return ApprovalDecision(False, f"Role {role_name} cannot approve invoices.")

    if approver.role == Role.MANAGER and invoice.amount > MANAGER_LIMIT:
        amount_text = _format_amount(invoice.amount)
        limit_text = _format_amount(MANAGER_LIMIT)
        return ApprovalDecision(
            False,
            f"Invoice amount {amount_text} exceeds the Manager approval limit of {limit_text}.",
        )

    if approver.role == Role.DIRECTOR and invoice.amount > DIRECTOR_LIMIT:
        amount_text = _format_amount(invoice.amount)
        limit_text = _format_amount(DIRECTOR_LIMIT)
        return ApprovalDecision(
            False,
            f"Invoice amount {amount_text} exceeds the Director approval limit of {limit_text}.",
        )

    return ApprovalDecision(True)
