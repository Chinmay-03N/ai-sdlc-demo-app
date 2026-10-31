from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import Invoice


@runtime_checkable
class InvoiceRepository(Protocol):
    def get_all(self) -> list[Invoice]:
        ...

    def get_by_id(self, invoice_id: str) -> Invoice | None:
        ...

    def add(self, invoice: Invoice) -> Invoice:
        ...

    def update(self, invoice: Invoice) -> None:
        ...

    def remove(self, invoice_id: str) -> bool:
        ...
