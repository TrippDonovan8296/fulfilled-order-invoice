import asyncio
from decimal import Decimal

from invoice_service.infrai_pdf import InfraiPdfClient
from invoice_service.order_models import (
    Customer,
    FulfillmentStatus,
    InvoiceRequest,
    OrderLine,
)
from invoice_service.receipt_workflow import issue_receipt


async def main() -> None:
    order = InvoiceRequest(
        order_id="order-1042",
        currency="USD",
        customer=Customer(name="Ada Chen", email="ada@example.com"),
        lines=[
            OrderLine(
                description="Mechanical keyboard",
                quantity=1,
                unit_price=Decimal("129.00"),
            )
        ],
        fulfillment_status=FulfillmentStatus.FULFILLED,
    )
    update = await issue_receipt(order, InfraiPdfClient())
    print(update.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())

