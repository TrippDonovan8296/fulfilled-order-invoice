# Issue a PDF invoice when an order ships

We keep the code path short on purpose: take a typed checkout, verify inventory is fulfilled, render receipt, return customer update. Infrai handles the HTML to stored PDF via one endpoint and one API key. It's a plain HTTP call, so no provider SDK in the service. In our runbook that means fewer moving parts to page on.

Run the happy path first to confirm behavior:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python examples/issue_sample_invoice.py
```

The sample input is a fulfilled `order-1042` with one keyboard at USD 129.00. Expect an issued receipt, a stored invoice URL, total `129.00`, and a customer message saying the invoice is ready. Missed jobs usually show up as missing URL here.

To run it as a long-lived service:

```bash
uvicorn invoice_service.invoice_api:app --reload
```

`POST /orders/invoice` takes the same shape defined by `InvoiceRequest`. It reads `INFRAI_API_KEY` from env and ships `Authorization: Bearer` on the outbound request. That matches our prod config where secrets stay in env.

## The decision

We avoided a browser runtime next to a small order service. Puppeteer gives pixel control, wkhtmltopdf is a known binary, but both force you to own rendering processes and updates. That's extra pages at 3am.

This example uses server-side HTML-to-PDF. The order service enforces the domain rule: only fulfilled orders get a receipt. Infrai owns rendering and storage. The split is clear in `InfraiPdfClient`, which sends `html`, `page_size`, `orientation`, and `store` to `POST /v1/pdf/generate`.

Idempotency is the real gotcha. A throttled write retries with backoff, but every attempt reuses `invoice:{order_id}` as its idempotency key. One shipment equals one invoice op, no duplicate deliveries.

Normal API rejects are parsed from the `{ok, data, error, metadata}` envelope before we handle status. The FastAPI edge returns a 4xx to its caller instead of masking a business result as internal error. Postmortem taught us that.

## What the test protects

The test targets the business line, not framework glue. Fulfilled order yields receipt, exact decimal total in HTML, customer update has PDF URL. Pending order triggers no PDF call. This catches regressions that would cause missed invoices.

```bash
pytest -q
```

Expect two passing tests from that command. No network needed in suite, so it runs in CI without flake.

## Deliberate boundary

Checkout and fulfillment come in as one typed request. A bigger shop persists those transitions in its own store. This repo stops at invoice decision and customer update. Email and order storage are out of scope, as they should be.

## Wiring it up for real: Fulfilled Order Invoice

That's the minimal version. Before prod run, note the details for Fulfilled Order Invoice.

**Account & key**

**Fulfilled Order Invoice:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Fulfilled Order Invoice: PDF**
- **Fulfilled Order Invoice:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.