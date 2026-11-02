from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum


class Role(StrEnum):
    MANAGER = "Manager"
    DIRECTOR = "Director"
    ADMIN = "Admin"


class InvoiceStatus(StrEnum):
    Draft = "Draft"
    PendingApproval = "PendingApproval"
    Approved = "Approved"
    Rejected = "Rejected"


@dataclass(frozen=True)
class Approver:
    username: str
    role: Role


@dataclass(frozen=True)
class ApprovalRecord:
    username: str
    role: Role
    approved_at: datetime


@dataclass
class Invoice:
    id: str = ""
    customer_name: str = ""
    amount: Decimal = Decimal(0)
    status: InvoiceStatus = InvoiceStatus.Draft
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    decided_by: str | None = None
    decided_at: datetime | None = None
    decision_note: str | None = None
    approvals: list[ApprovalRecord] = field(default_factory=list)

    def to_api_dict(self) -> dict:
        return {
            "id": self.id,
            "customerName": self.customer_name,
            "amount": float(self.amount),
            "status": self.status.value,
            "createdAt": self.created_at.isoformat().replace("+00:00", "Z"),
            "decidedBy": self.decided_by,
            "decidedAt": self.decided_at.isoformat().replace("+00:00", "Z") if self.decided_at else None,
            "decisionNote": self.decision_note,
        }
