from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional


class InvoiceStatus(str, Enum):
    Draft = "Draft"
    PendingApproval = "PendingApproval"
    Approved = "Approved"
    Rejected = "Rejected"


@dataclass
class Invoice:
    id: str = ""
    customer_name: str = ""
    amount: Decimal = Decimal("0")
    status: InvoiceStatus = InvoiceStatus.Draft
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    decision_note: Optional[str] = None

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
