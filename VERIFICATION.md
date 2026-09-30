# Tiny Tale 2.1 verification

Passed in the build environment:
- Python compilation and JavaScript syntax checks.
- SQLite API smoke tests: existing product photos, admin authentication/CSRF, pricing/coupons, enquiries, confirmation/cancellation, image upload validation, consent analytics and storefront rejection of private admin APIs.
- Size example 12 / 3 / 0 / 8: customer availability labels, independent quantities, unavailable-size rejection, admin alerts below five, and no alert at exactly five.
- Chosen size saved in order lines; confirming and cancelling adjusts only its inventory.
- Public size records contain no low-stock flags; private analytics contain alerts.
- Migration from previous build: owner name/price/stock, existing enquiries, uploaded media and coupon changes preserved. Running startup twice did not duplicate/reset the migrated stock.
- Node DOM-stub tests: customer rendered labels, size selection, disabled sold-out buttons, cart quantity limit, size in cart/detail, no admin warning text.

Commands:
```sh
python tests/smoke.py
node tests/frontend.cjs
python tests/upgrade.py
```
The migration test needs the previous `tiny-tale` project beside this project (see its source). It uses a disposable database, not your own database.

Limits: full browser layout/interactions were not verified because the Chromium download failed in this environment. PostgreSQL deployment and concurrent row-lock behavior were not exercised against a live PostgreSQL server; integration tests used SQLite. The existing Render deployment was not changed by this build delivery.

Merged release: API and frontend logic tests passed again. Upgrade testing used a disposable database created by the uploaded old application, then loaded the merged application twice. Render settings, requirements, configuration loader, launcher, both startup scripts and product images match the uploaded old files byte-for-byte. Windows APPLY-UPDATE.bat was reviewed but could not be executed in this Linux environment.
