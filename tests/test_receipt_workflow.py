from decimal import Decimal

import pytest

from invoice_service.order_models import (
    Customer,
    FulfillmentStatus,
    InvoiceRequest,
    OrderLine,
    ReceiptStatus,
)
from invoice_service.receipt_workflow import OrderNotFulfilled, issue_receipt


class RecordingPdf:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def generate(self, html: str, order_id: str) -> dict[str, object]:
        self.calls.append((html, order_id))
        return {"url": "https://documents.example/invoice-order-1042.pdf"}


def sample_order(status: FulfillmentStatus) -> InvoiceRequest:
    return InvoiceRequest(
        order_id="order-1042",
        currency="USD",
        customer=Customer(name="Ada Chen", email="ada@example.com"),
        lines=[
            OrderLine(
                description="Mechanical keyboard",
                quantity=2,
                unit_price=Decimal("129.00"),
            )
        ],
        fulfillment_status=status,
    )


@pytest.mark.asyncio
async def test_fulfilled_order_issues_receipt_and_customer_update() -> None:
    pdf = RecordingPdf()

    update = await issue_receipt(sample_order(FulfillmentStatus.FULFILLED), pdf)

    assert update.receipt_status == ReceiptStatus.ISSUED
    assert update.total == Decimal("258.00")
    assert update.invoice_url.endswith("invoice-order-1042.pdf")
    assert pdf.calls[0][1] == "order-1042"
    assert "USD 258.00" in pdf.calls[0][0]


@pytest.mark.asyncio
async def test_pending_order_does_not_create_invoice() -> None:
    pdf = RecordingPdf()

    with pytest.raises(OrderNotFulfilled):
        await issue_receipt(sample_order(FulfillmentStatus.PENDING), pdf)

    assert pdf.calls == []

