from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from invoice_app.api.auth import SessionStore, UserSession, auth_router, require_role
from invoice_app.api.in_memory_repository import InMemoryInvoiceRepository
from invoice_app.domain.approval_service import ApprovalService
from invoice_app.domain.errors import ApprovalNotAllowed, InvalidInvoiceState, InvalidRequest, InvoiceNotFound
from invoice_app.domain.models import Approver, Invoice, InvoiceStatus


class CreateInvoiceRequest(BaseModel):
    customer_name: str = Field(alias="customerName")
    amount: Decimal

    model_config = ConfigDict(populate_by_name=True)


class RejectRequest(BaseModel):
    reason: str


app = FastAPI(title="Invoice Approvals")
app.state.session_store = SessionStore()
app.state.repository = InMemoryInvoiceRepository()
app.state.approval_service = ApprovalService(app.state.repository)
app.include_router(auth_router)


@app.middleware("http")
async def session_middleware(request: Request, call_next):
    if request.url.path.startswith("/api") and request.url.path != "/api/auth/login":
        token = None
        header = request.headers.get("authorization", "")
        if header.startswith("Bearer "):
            token = header.split(" ", 1)[1]
        session = request.app.state.session_store.get(token) if request.app.state.session_store else None
        if session is None:
            return JSONResponse(status_code=401, content={})
        request.state.session = session
    return await call_next(request)


@app.exception_handler(InvoiceNotFound)
async def invoice_not_found_handler(_, exc: InvoiceNotFound):
    return JSONResponse(status_code=404, content={"error": str(exc)})


@app.exception_handler(InvalidInvoiceState)
async def invalid_invoice_state_handler(_, exc: InvalidInvoiceState):
    return JSONResponse(status_code=409, content={"error": str(exc)})


@app.exception_handler(InvalidRequest)
async def invalid_request_handler(_, exc: InvalidRequest):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(ApprovalNotAllowed)
async def approval_not_allowed_handler(_, exc: ApprovalNotAllowed):
    return JSONResponse(status_code=403, content={"error": str(exc)})


static_dir = Path(__file__).resolve().parent / "static"


@app.get("/")
async def serve_root() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/index.html")
async def serve_index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/app.js")
async def serve_app_js() -> FileResponse:
    return FileResponse(static_dir / "app.js")


@app.get("/styles.css")
async def serve_styles() -> FileResponse:
    return FileResponse(static_dir / "styles.css")


def to_api_dict(invoice: Invoice) -> dict[str, Any]:
    return invoice.to_api_dict()


@app.get("/api/invoices")
def get_invoices(status: str | None = None):
    invoices = app.state.repository.get_all()
    if status:
        try:
            parsed_status = InvoiceStatus(status)
        except ValueError as exc:
            raise InvalidRequest(f"Unknown status '{status}'.") from exc
        invoices = [invoice for invoice in invoices if invoice.status == parsed_status]
    return [to_api_dict(invoice) for invoice in invoices]


@app.get("/api/invoices/{invoice_id}")
def get_invoice(invoice_id: str):
    invoice = app.state.repository.get_by_id(invoice_id)
    if invoice is None:
        raise InvoiceNotFound(f"Invoice {invoice_id} was not found.")
    return to_api_dict(invoice)


@app.post("/api/invoices", status_code=201)
def create_invoice(payload: CreateInvoiceRequest):
    customer_name = payload.customer_name.strip() if payload.customer_name else ""
    if not customer_name:
        raise InvalidRequest("Customer name is required.")
    if payload.amount <= 0:
        raise InvalidRequest("Amount must be greater than zero.")

    invoice = Invoice(customer_name=customer_name, amount=payload.amount)
    created = app.state.repository.add(invoice)
    response = JSONResponse(content=to_api_dict(created), status_code=201)
    response.headers["Location"] = f"/api/invoices/{created.id}"
    return response


@app.post("/api/invoices/{invoice_id}/submit")
def submit_invoice(invoice_id: str):
    invoice = app.state.approval_service.submit(invoice_id)
    return to_api_dict(invoice)


@app.delete("/api/invoices/{invoice_id}")
def delete_invoice(invoice_id: str, session: UserSession = Depends(require_role("Admin"))):
    deleted = app.state.repository.remove(invoice_id)
    if not deleted:
        raise InvoiceNotFound(f"Invoice {invoice_id} was not found.")
    return Response(status_code=204)


@app.post("/api/approvals/{invoice_id}/approve")
def approve_invoice(invoice_id: str, session: UserSession = Depends(require_role("Manager", "Director", "Admin"))):
    approver = Approver(session.username, session.role)
    invoice = app.state.approval_service.approve(invoice_id, approver)
    return to_api_dict(invoice)


@app.post("/api/approvals/{invoice_id}/reject")
def reject_invoice(
    invoice_id: str,
    payload: RejectRequest,
    session: UserSession = Depends(require_role("Manager", "Director", "Admin")),
):
    approver = Approver(session.username, session.role)
    invoice = app.state.approval_service.reject(invoice_id, approver, payload.reason)
    return to_api_dict(invoice)
