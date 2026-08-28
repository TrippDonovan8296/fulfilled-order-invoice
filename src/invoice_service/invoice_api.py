from fastapi import FastAPI, HTTPException

from .infrai_pdf import InfraiError, InfraiPdfClient
from .order_models import InvoiceRequest, OrderUpdate
from .receipt_workflow import OrderNotFulfilled, issue_receipt

app = FastAPI(title="Fulfilled order invoices")


@app.post("/orders/invoice", response_model=OrderUpdate)
async def create_invoice(order: InvoiceRequest) -> OrderUpdate:
    try:
        return await issue_receipt(order, InfraiPdfClient())
    except OrderNotFulfilled as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc

