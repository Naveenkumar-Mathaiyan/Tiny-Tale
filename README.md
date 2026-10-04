# Tiny Tale v7

An additive update for the existing Flask storefront and admin, with an Expo Android/iOS **staff scanner source project**. Uses the existing shared PostgreSQL database on Render. Website payment methods remain simulations; the staff billing feature records payments collected separately at the counter.

Read START_HERE.txt for the exact Windows update, Git push and Render steps. Read `mobile-scanner/README.md` for mobile build instructions. This update intentionally reuses existing `static/images` and does not distribute environment secrets, databases or installed dependencies.

## Customer storefront

- Admin-managed homepage introduction, optional button and 1–8 welcome images.
- Automatic welcome/offer slideshows with pause controls, reduced-motion handling and complete images rather than zoom cropping. Offer videos pause automatic advancement while playing.
- Aligned search/sort/age/price filters and categories populated from the shared database.
- Existing OTP login, gallery, favourites, size-specific availability, restock requests and simulated checkout preserved.

## Admin and staff

- Add/rename product categories; rename updates product categories as well.
- Multiple images/GIFs/videos directly in product editing, with image thumbnail selection; cover and gallery save atomically.
- Searchable product picker in the gallery editor. Existing gallery ordering remains available.
- Internal product-size codes, Code 128 + QR labels, optional licensed GTIN-13/EAN-13 and bulk A4 PDF printing. Codes stay out of customer product responses.
- Incoming stock batches, server-calculated counter receipts, overselling prevention, operation ledger and idempotent retries.
- Date-filtered counter sales and scanned stock movements added to PDF/Excel reports.
- Expiring staff bearer sessions for native clients; tokens are stored hashed in the database and in SecureStore on the device. Account edits/disabling invalidate web and native sessions.

| Role | Access |
| --- | --- |
| Super Admin | All sections and staff creation; existing owner login |
| Admin | Full operations/settings/reports, all counter receipts; no staff administration |
| Store Manager | Existing stock/media, incoming scans, stock lookup, label printing |
| Manager | Store Manager access plus counter sales and own receipts |
| Supervisor | Store Manager access plus counter sales and own receipts |
| Billing staff | Stock lookup, counter sales and own receipts |

Manager/Supervisor permissions deliberately exclude website orders, financial analytics, price changes, policies and staff account creation. Legacy `store_keeper` accounts migrate to `store_manager` and their sessions are revoked.

## Inventory and transaction behaviour

Labels identify product **and size**, not just category. Category totals are derived from the corresponding product sizes. A scan looks up a variant and adds a confirmed quantity to a batch; it does not immediately change inventory. Finalizing an arrival adds units; finalizing a counter sale deducts units once and creates a POS receipt. Repeated identical request IDs return the original result. Changed payloads with the same ID are rejected. Disabled variants and hidden products cannot be scanned into operations.

The server locks product rows and enabled variants in stable order and updates total stock within the same database transaction. Sale prices come from the server; a changed total rejects the whole sale for cashier review. Counter receipts use a separate global `POS-YYMMDDXXXXXX` sequence. Website order numbering/settings remain unchanged. Website enquiries/test orders retain their existing confirmation/cancellation stock flow.

Counter records are not settlement confirmations or GST invoices. No payment-provider integration, taxes, refunds/voids, offline sales, Bluetooth thermal-printer SDK or returns inventory flow has been added. Receipt printing uses PDF/browser printing or the native platform print dialog. Native access requires connectivity; saved batches support retry rather than unverified offline stock changes.

Internal codes are business-local identifiers. For registered retail identifiers use GTINs assigned through [GS1](https://www.gs1.org/services/activate/how-to-create-a-GTIN). The app validates GTIN-13 length/check digit and requires the administrator to confirm assignment; it cannot independently verify a GS1 licence. It does not claim that the internal QR labels implement GS1 Digital Link.

## Development checks

Install `requirements.txt` plus `pypdf` for test inspection, then run `tests/v7.py`, `tests/v6.py`, `tests/v4.py` and `tests/email_errors.py`. Tests use disposable SQLite databases and mock email delivery. For migration validation set `TINY_TALE_PREVIOUS_BUILD` to the v6 source and run `tests/upgrade.py`. Browser QA and native source checks are described in VERIFICATION.md. Deploy through the two existing Render services; do not replace your existing database.
