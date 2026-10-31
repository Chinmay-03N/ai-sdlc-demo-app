from __future__ import annotations

from copy import deepcopy

from invoice_app.domain.models import Invoice


class FakeInvoiceRepository:
    def __init__(self, invoices: list[Invoice] | None = None) -> None:
        self._invoices = {invoice.id: deepcopy(invoice) for invoice in (invoices or [])}
        self.update_calls = 0

    def get_all(self) -> list[Invoice]:
        return [deepcopy(invoice) for invoice in self._invoices.values()]

    def get_by_id(self, invoice_id: str) -> Invoice | None:
        invoice = self._invoices.get(invoice_id)
        return deepcopy(invoice) if invoice is not None else None

    def add(self, invoice: Invoice) -> Invoice:
        saved = deepcopy(invoice)
        if not saved.id:
            saved.id = f"INV-{len(self._invoices) + 1}"
        self._invoices[saved.id] = deepcopy(saved)
        return deepcopy(saved)

    def update(self, invoice: Invoice) -> None:
        self.update_calls += 1
        self._invoices[invoice.id] = deepcopy(invoice)

    def remove(self, invoice_id: str) -> bool:
        return self._invoices.pop(invoice_id, None) is not None
