# v6 verification

Passed:
- v6 backend suite: owner/admin/store keeper permissions, account session revocation, stock/media restrictions, real PDF/Excel bytes, IST report date boundaries, Excel formula protection; custom banner links/new-tab persistence; unsafe URL rejection; editable public offer-strip settings; validation and staff-access denial.
- Existing v4/v5 regression suites: OTP/CSRF/replay/rate checks with mock mail, four simulated payment methods, discounts, stock by size/One Size, restock requests, order numbers and stock transitions, GIF preservation, actual MP4/range streaming, consent/analytics and SEO.
- Additive migration from v5: products, prices, stock, orders, uploaded images and coupons preserved; repeated initialization is idempotent.
- Frontend and real DOM checks with all new scripts loaded.
- Local Chromium desktop/mobile checks: no uncaught JavaScript errors or document overflow; filters/reset; recently viewed; product PIN estimate; shipping progress; mock email OTP -> UPI test checkout; offer-strip admin save -> customer refresh; custom banner product link; gallery thumbnails/arrows; PDF/Excel controls; restricted store keeper menus; reduced-motion behaviour.
- Desktop and mobile screenshots visually reviewed. PDF layout was verified in v5 and report exports remain covered by v6 backend tests.
- JavaScript syntax, ZIP CRC, full extraction and byte equality.

Limits:
Local browser testing uses a disposable SQLite database and mock mail outside the release app. Live Render/PostgreSQL and real Brevo email delivery have not been tested by this build environment. Windows updater is inspected but not executed on Windows. Payment methods remain simulated. Country/state depends on your optional IP-location database. Delivery estimates are indicative, not carrier-verified.
