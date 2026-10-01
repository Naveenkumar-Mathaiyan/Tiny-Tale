# Tiny Tale 3.0 verification

Passed:
- Python compilation and all three JavaScript syntax checks.
- SQLite integration: mandatory OTP checkout, customer CSRF, hashed codes, invalid codes, expiry, five-attempt lockout, reuse rejection, cooldown, session login/logout and customer-owned history.
- OTP delivery mocked in tests; no code is exposed in API responses and no real email was sent.
- Coupon + 5% login calculation; unauthenticated quotes receive no login discount.
- Credit/debit/UPI/net-banking test methods; failure/cancellation create no order; COD and raw credentials are rejected; retries return the same order, changed retries are rejected.
- Unique readable order numbers and server-generated QR; business/PIN/day/map validation and delivery estimate responses.
- One Size / age size validation; selected-size availability; zero-stock restrictions; restock deduplication, counts and closing requests.
- Stock confirmation/cancellation and exclusion of simulated orders from confirmed value; image uploads still work.
- Analytics consent, active seconds, ordered path funnel and server-only test-success event.
- Canonical home page, product structured data, sitemap, draft policy page and store rejection of private admin endpoints.
- Node DOM-stub tests: One Size labels, Notify me, cart limits, OTP continuation preserving cart, sample card/expiry/CVV/UPI/bank validation, credential-free payment request, confirmation/ETA and no WhatsApp redirect.
- Migration from both uploaded original application and previously merged v2.1 build: existing names/prices/stock/enquiries/media/coupons preserved; readable number added; repeated startup does not reset data.

Run:
```sh
python tests/smoke.py
node tests/frontend.cjs
# Point at an unpacked previous application to test a disposable migration.
TINY_TALE_PREVIOUS_BUILD=/path/to/previous/build python tests/upgrade.py
```

Not verified: live Brevo email delivery (no API key supplied), PostgreSQL concurrent requests, real courier delivery, full browser layout/interactions or Windows updater execution. Payments are local simulations rather than a provider sandbox. The included frontend tests stub the DOM and do not substitute for browser testing.
