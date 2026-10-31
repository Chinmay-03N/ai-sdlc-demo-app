from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from .errors import InvalidInvoiceState, InvalidRequest, InvoiceNotFound
from .models import Invoice, InvoiceStatus
from .repository import InvoiceRepository


class ApprovalService:
    def __init__(self, repository: InvoiceRepository, clock: Callable[[], datetime] | None = None):
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def submit(self, invoice_id: str) -> Invoice:
        invoice = self._find(invoice_id)
        if invoice.status != InvoiceStatus.Draft:
            raise InvalidInvoiceState(f"Invoice {invoice_id} is {invoice.status}; only drafts can be submitted.")

        invoice.status = InvoiceStatus.PendingApproval
        self._repository.update(invoice)
        return invoice

    def approve(self, invoice_id: str, approver: str) -> Invoice:
        invoice = self._find(invoice_id)
        self._ensure_pending(invoice)

        invoice.status = InvoiceStatus.Approved
        invoice.decided_by = approver
        invoice.decided_at = self._clock()
        self._repository.update(invoice)
        return invoice

    def reject(self, invoice_id: str, approver: str, reason: str) -> Invoice:
        if not reason or not reason.strip():
            raise InvalidRequest("A reason is required to reject an invoice.")

        invoice = self._find(invoice_id)
        self._ensure_pending(invoice)

        invoice.status = InvoiceStatus.Rejected
        invoice.decided_by = approver
        invoice.decided_at = self._clock()
        invoice.decision_note = reason
        self._repository.update(invoice)
        return invoice

    def _find(self, invoice_id: str) -> Invoice:
        invoice = self._repository.get_by_id(invoice_id)
        if invoice is None:
            raise InvoiceNotFound(f"Invoice {invoice_id} was not found.")
        return invoice

    @staticmethod
    def _ensure_pending(invoice: Invoice) -> None:
        if invoice.status != InvoiceStatus.PendingApproval:
            raise InvalidInvoiceState(f"Invoice {invoice.id} is {invoice.status}; only pending invoices can be decided.")
