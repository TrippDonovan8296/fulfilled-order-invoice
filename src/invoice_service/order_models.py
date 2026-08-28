from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class FulfillmentStatus(StrEnum):
    PENDING = "pending"
    FULFILLED = "fulfilled"


class ReceiptStatus(StrEnum):
    PENDING = "pending"
    ISSUED = "issued"


class Customer(BaseModel):
    name: str
    email: str


class OrderLine(BaseModel):
    description: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class InvoiceRequest(BaseModel):
    order_id: str
    currency: str = Field(min_length=3, max_length=3)
    customer: Customer
    lines: list[OrderLine] = Field(min_length=1)
    fulfillment_status: FulfillmentStatus


class OrderUpdate(BaseModel):
    order_id: str
    receipt_status: ReceiptStatus
    customer_message: str
    invoice_url: str
    total: Decimal

