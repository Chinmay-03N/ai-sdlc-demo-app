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
    AwaitingSecondApproval = "AwaitingSecondApproval"
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
