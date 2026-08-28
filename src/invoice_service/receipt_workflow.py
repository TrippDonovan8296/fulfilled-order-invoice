from decimal import Decimal
from html import escape
from typing import Protocol

from .order_models import (
    FulfillmentStatus,
    InvoiceRequest,
    OrderUpdate,
    ReceiptStatus,
)


class PdfGenerator(Protocol):
    async def generate(self, html: str, order_id: str) -> dict[str, object]:
        """Generate and store the invoice document."""


class OrderNotFulfilled(Exception):
    pass


def order_total(order: InvoiceRequest) -> Decimal:
    return sum(
        (line.unit_price * line.quantity for line in order.lines),
        start=Decimal("0"),
    )


def render_invoice(order: InvoiceRequest) -> str:
    total = order_total(order)
    rows = "".join(
        "<tr>"
        f"<td>{escape(line.description)}</td>"
        f"<td>{line.quantity}</td>"
        f"<td>{line.unit_price:.2f}</td>"
        "</tr>"
        for line in order.lines
    )
    return (
        "<!doctype html><html><body>"
        f"<h1>Invoice {escape(order.order_id)}</h1>"
        f"<p>Bill to: {escape(order.customer.name)}</p>"
        "<table><thead><tr><th>Item</th><th>Qty</th><th>Unit</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        f"<strong>Total: {escape(order.currency.upper())} {total:.2f}</strong>"
        "</body></html>"
    )


async def issue_receipt(order: InvoiceRequest, pdf: PdfGenerator) -> OrderUpdate:
    if order.fulfillment_status != FulfillmentStatus.FULFILLED:
        raise OrderNotFulfilled("invoice creation requires a fulfilled order")

    result = await pdf.generate(render_invoice(order), order.order_id)
    invoice_url = str(result["url"])
    return OrderUpdate(
        order_id=order.order_id,
        receipt_status=ReceiptStatus.ISSUED,
        customer_message=f"Your invoice for order {order.order_id} is ready.",
        invoice_url=invoice_url,
        total=order_total(order),
    )
