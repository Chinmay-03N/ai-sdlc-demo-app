from playwright.sync_api import Page, expect

from pages.invoice_app_page import InvoiceAppPage


def test_manager_cannot_approve_invoice_above_limit(page: Page, base_url: str) -> None:
    customer_name = "Over-limit approval customer"
    invoice_app = InvoiceAppPage(page)

    invoice_app.open(base_url)
    invoice_app.sign_in("demo.manager", "ChangeMe123!")
    invoice_app.create_invoice(customer_name, "75000")
    invoice_app.submit_invoice(customer_name)
    invoice_app.open_approvals()
    invoice_app.approve_invoice(customer_name)

    expect(invoice_app.decision_alert()).to_contain_text(
        "exceeds the Manager approval limit of 50,000.00"
    )

    invoice_app.open_invoices()
    expect(invoice_app.invoice_status(customer_name)).to_be_visible()
