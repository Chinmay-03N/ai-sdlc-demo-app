---
name: python-tests
description: How unit and end-to-end tests are written in this repo (pytest fixtures, FakeInvoiceRepository, fixed clock, unchanged-invoice assertions, Playwright page objects). Use when writing or reviewing any test.
---
# Writing tests here

## Unit tests (`backend/tests/`)

- Build services with the `make_service` fixture from `conftest.py`; it returns `(service, repository)` with a fixed clock (`FIXED_NOW`).
- Approvers: `MANAGER`, `DIRECTOR`, `OTHER_DIRECTOR`, `ADMIN` from `conftest.py`. Invoices: `pending_invoice("50000.01")`.
- Parametrise boundaries:

```python
@pytest.mark.parametrize("amount", ["0.01", "49999.99", "50000.00"])
def test_manager_can_approve_up_to_and_including_50000(make_service, amount): ...
```

- Refusal pattern (use it for EVERY refusal):

```python
original = pending_invoice("50000.01")
service, repository = make_service(original)
with pytest.raises(ApprovalNotAllowed, match="exceeds the Manager approval limit"):
    service.approve("INV-1", MANAGER)
assert repository.update_calls == 0
assert repository.stored("INV-1") == original
```

- For refusals after a first approval, snapshot first: `after_first = repository.stored("INV-1")`, then assert equality after the refused call.
- Assert exact values (`decided_at == FIXED_NOW`, `decided_by == DIRECTOR.username`), never just `is not None`.
- Name tests `test_<who>_<can|cannot>_<what>`; docstring cites the requirement id.

## End-to-end tests (`e2e/`)

- Page objects in `e2e/pages/`; tests only call page-object methods and `expect(...)`.
- Locators: `get_by_role`, `get_by_label` only. No CSS, XPath or `wait_for_timeout`.
- Assert both the visible reason and that the invoice status is still `Pending Approval`.

## Before you finish

Run `cd backend && pytest` (and `cd e2e && pytest` if you touched e2e) and paste the summary line.
