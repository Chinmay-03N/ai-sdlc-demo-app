from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone

from invoice_app.domain.models import Invoice, InvoiceStatus
from invoice_app.domain.repository import InvoiceRepository


class InMemoryInvoiceRepository(InvoiceRepository):
    """Simple in-memory repository for the demo app."""

    def __init__(self) -> None:
        self._next_number = 1006
        now = datetime.now(timezone.utc)
        self._invoices = [
            Invoice(id="INV-1001", customer_name="Lakeside School District", amount=4250.00, status=InvoiceStatus.PendingApproval),
            Invoice(id="INV-1002", customer_name="Hilltop Academy", amount=980.50, status=InvoiceStatus.PendingApproval),
            Invoice(
                id="INV-1003",
                customer_name="Riverside Charter",
                amount=12300.00,
                status=InvoiceStatus.Approved,
                decided_by="demo.approver",
                decided_at=now - timedelta(days=2),
            ),
            Invoice(id="INV-1004", customer_name="Oakwood Independent", amount=615.75, status=InvoiceStatus.PendingApproval),
            Invoice(id="INV-1005", customer_name="Maple Grove Prep", amount=310.00, status=InvoiceStatus.Draft),
        ]

    def get_all(self) -> list[Invoice]:
        return [deepcopy(invoice) for invoice in self._invoices]

    def get_by_id(self, invoice_id: str) -> Invoice | None:
        for invoice in self._invoices:
            if invoice.id == invoice_id:
                return deepcopy(invoice)
        return None

    def add(self, invoice: Invoice) -> Invoice:
        if not invoice.id:
            invoice.id = f"INV-{self._next_number}"
            self._next_number += 1
        self._invoices.append(deepcopy(invoice))
        return deepcopy(invoice)

    def update(self, invoice: Invoice) -> None:
        for index, current in enumerate(self._invoices):
            if current.id == invoice.id:
                self._invoices[index] = deepcopy(invoice)
                return

    def remove(self, invoice_id: str) -> bool:
        for index, invoice in enumerate(self._invoices):
            if invoice.id == invoice_id:
                del self._invoices[index]
                return True
        return False
