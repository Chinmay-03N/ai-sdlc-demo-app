import re

from playwright.sync_api import Locator, Page


class InvoiceAppPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self, base_url: str) -> None:
        self.page.goto(base_url)

    def sign_in(self, username: str, password: str) -> None:
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Sign in").click()

    def create_invoice(self, customer_name: str, amount: str) -> None:
        self.page.get_by_label("Customer name").fill(customer_name)
        self.page.get_by_label("Amount").fill(amount)
        self.page.get_by_role("button", name="Create invoice").click()

    def submit_invoice(self, customer_name: str) -> None:
        invoice_row = self.page.get_by_role("row").filter(has_text=customer_name)
        invoice_row.get_by_role("button", name=re.compile(r"Submit invoice .* for approval")).click()

    def open_approvals(self) -> None:
        self.page.get_by_role("tab", name="Approvals").click()

    def approve_invoice(self, customer_name: str) -> None:
        invoice_item = self.page.get_by_role("listitem").filter(has_text=customer_name)
        invoice_item.get_by_role("button", name=re.compile(r"Approve invoice .*")).click()

    def open_invoices(self) -> None:
        self.page.get_by_role("tab", name="Invoices").click()

    def decision_alert(self) -> Locator:
        return self.page.get_by_role("tabpanel", name="Approvals").get_by_role("alert")

    def invoice_status(self, customer_name: str) -> Locator:
        invoice_row = self.page.get_by_role("row").filter(has_text=customer_name)
        return invoice_row.get_by_role("cell", name="Pending Approval")
