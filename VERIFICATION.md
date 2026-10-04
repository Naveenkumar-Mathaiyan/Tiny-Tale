# v7 verification — 4 October 2026

Completed locally against disposable SQLite databases:

- Existing customer OTP/CSRF, replay and rate checks with mock email, four simulated payment methods, discounts, size/restock availability, delivery settings, order numbers, confirmation/cancellation stock flow, test-revenue exclusion and SEO checks.
- Existing media regression: image/GIF validation, actual MP4 upload/range streaming, galleries and safe banner links.
- Owner/Admin permissions and legacy staff migration; new Store Manager, Manager, Supervisor and Billing account roles; server route restrictions and staff session revocation.
- Native staff password login, bearer authentication, logout, invalid/disabled session rejection and role restrictions.
- Category creation/renaming including product updates; editable hero settings and invalid URL/interval/JSON rejection.
- Variant-code generation, uniqueness across internal codes/GTINs, GTIN checksum/assignment-confirmation validation and invalid label parameters.
- Incoming stock increases, counter sale deductions, server price/expected-total validation, identical-request replay, changed-request rejection, no negative stock and transaction rollback on invalid batches/payments.
- Receipt ownership: other staff cannot read a cashier's receipts; owner can inspect all receipts.
- Atomic stock/cover/gallery save, image-thumbnail selection, rejected video thumbnails and invalid gallery rollback.
- Actual PDF label and receipt bytes; date-filtered counter/movement PDF and Excel exports. Existing five report types, IST date boundaries and Excel formula protection also passed.
- Additive v6 → v7 migration preserved product name/price/stock, existing enquiry/media/coupon; repeated startup stayed idempotent.

Completed local Chromium checks at desktop 1365×1000 and phone 390×844:

- Admin hero text/multiple images save and customer reflection; automatic welcome and offer slideshows, full-frame image rendering, reduced-motion offer pause and aligned desktop filters.
- Dynamic categories, multiple product image upload, cover selection and customer detail-gallery thumbnails.
- Searchable product media picker, PDF label preview, incoming scan batch, counter billing and receipt preview.
- Role-specific menus for Store Manager, Manager, Supervisor and Billing staff; restricted analytics/orders/accounts hidden; no document overflow in the tested phone layouts.
- Mock email OTP → customer login → address review → UPI simulated order confirmation.
- No uncaught JavaScript errors during the tested flow. Screenshots visually inspected.

Label QA: generated Code 128 + QR and EAN-13 + QR PDFs were rendered to images and decoded digitally; each barcode and QR pair identified the same code. Label/receipt page layouts were visually inspected. This does not replace scanning an actual printed label under real lighting and printer settings.

Mobile source QA: TypeScript and Expo lint passed with zero warnings. SDK dependencies checked against the installed Expo SDK 57 compatibility manifest (offline check; online compatibility lookup was unavailable). Android and iOS production JavaScript/Hermes bundles exported successfully. No signed Android APK/iOS IPA was compiled, installed or published. Native camera permissions, physical scans, platform print dialog, secure storage and restart recovery require tests on actual Android/iOS devices.

Not exercised here: live Render deployment, production PostgreSQL concurrency, real Brevo inbox delivery, Windows execution of the updater, actual label/receipt printers, device installation/signing or payment collection. The existing website gateway remains simulated; counter billing records declared payments and is not a GST tax-invoice engine.

Reproduce backend tests using a virtual environment with requirements.txt and pypdf. Run tests/v7.py, tests/v6.py, tests/v4.py and tests/email_errors.py. For migration, set TINY_TALE_PREVIOUS_BUILD to the v6 source and run tests/upgrade.py.

The v7 browser test is tests/browser-v7.cjs with tests/run_browser.py and tests/qa_server.py. Install Playwright separately and make it available to Node (NODE_PATH if necessary). Install a supported Chromium browser or set PLAYWRIGHT_CHROMIUM_EXECUTABLE. Run the Python browser orchestrator in the same environment so both disposable servers and the browser share network access. qa_server.py refuses to run unless the orchestrator enables TINY_TALE_QA=1; it must never be used as your production server. Older frontend/DOM/browser files are retained for historical regression and are not the v7 visual acceptance test.

Release packaging checks: ZIP CRC, full extraction and byte equality are required before delivery. Installed dependencies, secrets, local databases, caches, nested Git history and existing store product images are excluded from the update package. PREVIEWS contains a test store's screenshots, not production data or printable inventory labels.
