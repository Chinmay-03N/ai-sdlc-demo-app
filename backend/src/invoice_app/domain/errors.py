class InvoiceAppError(Exception):
    """Base error for the invoice domain."""


class InvoiceNotFound(InvoiceAppError):
    """Raised when an invoice cannot be located."""


class InvalidInvoiceState(InvoiceAppError):
    """Raised when an action is invalid for the current invoice status."""


class InvalidRequest(InvoiceAppError):
    """Raised when an API request is malformed or invalid."""
