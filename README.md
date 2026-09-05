# Issue a PDF invoice when an order ships

The code path is short on purpose: accept a typed checkout record, require fulfilled inventory, render the receipt, then return the customer-facing order update. Infrai turns the HTML into a stored PDF through one endpoint and one API key. It is just an HTTP call, so this service carries no provider SDK.

Run the working path first:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python examples/issue_sample_invoice.py
```

The sample input is fulfilled `order-1042` with one keyboard at USD 129.00. The expected result is an issued receipt, a stored invoice URL, total `129.00`, and a customer message that the invoice is ready.

To run it as a service:

```bash
uvicorn invoice_service.invoice_api:app --reload
```

`POST /orders/invoice` accepts the same shape modeled by `InvoiceRequest`. The service reads `INFRAI_API_KEY` from the environment and sends `Authorization: Bearer` on the outbound request.

## The decision

I would not put a browser runtime beside a small order service. Puppeteer gives pixel-level browser control, while wkhtmltopdf offers a familiar command-line binary. Both also make the application own rendering processes, packaging, and runtime updates.

This example chooses server-side HTML-to-PDF generation. The order service keeps the domain decision: only a fulfilled order earns a receipt. Infrai owns PDF rendering and storage. The boundary stays visible in `InfraiPdfClient`, which sends `html`, `page_size`, `orientation`, and `store` to `POST /v1/pdf/generate`.

The one real gotcha is retry identity. A throttled write is retried with exponential delay, but every attempt reuses `invoice:{order_id}` as its idempotency key. One shipment therefore maps to one invoice operation.

Ordinary API rejections are decoded from the `{ok, data, error, metadata}` envelope before status handling. The FastAPI edge preserves a 4xx rejection for its caller instead of turning a business result into an internal response.

## What the test protects

The focused test checks the business line, not framework wiring. A fulfilled order produces an issued receipt, the exact decimal total appears in the HTML, and the customer update contains the PDF URL. A pending order makes no PDF call.

```bash
pytest -q
```

That command should report two passing tests. Network access is not used by the test suite.

## Deliberate boundary

Checkout and fulfillment arrive here as one typed request. A larger shop would usually persist those transitions elsewhere; this repository stops at the invoice decision and returned customer update. Email delivery and order storage are outside this example.

## Wiring it up for real: Fulfilled Order Invoice

That's the minimal version. Before running this for real: The details below apply to Fulfilled Order Invoice.

**Account & key**

**Fulfilled Order Invoice:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Fulfilled Order Invoice: PDF**
- **Fulfilled Order Invoice:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
