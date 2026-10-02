# Verification for v5

Passed on disposable SQLite with mock email:
- Existing OTP, CSRF, replay prevention, four simulated payment flows, discounts, checkout continuation, order numbering, size stock, restock requests, delivery/settings, stock transitions and SEO regressions.
- Owner, Admin and Store keeper login/permissions; server denies all restricted routes for keepers; account reset/disable revokes sessions; prices/content/size configuration cannot be changed through the stock-only endpoint.
- Gallery-only staff updates, GIF preservation, MP4 upload/range streaming, invalid media rejection, optional banner CTA validation and product destination links.
- Real PDF and XLSX bytes for orders, inventory, restock, traffic and journey reports; date validation and IST boundary inclusion; empty datasets; Excel formula protection.
- Multi-page PDF headings/footers; rendered PDF page inspected for layout.
- Real DOM script loading, role-specific navigation/editor controls, campaign dashboard, optional banner controls, gallery controls, report preview/download controls and existing customer UI behavior.
- Additive migration from v4 preserving products, prices, stocks, orders, uploaded images and coupons; repeated startup is idempotent.
- JavaScript syntax checks and ZIP CRC/complete extraction/byte equality checks.

Limits: no visual browser test (Chromium download truncated), no live Render/PostgreSQL or Brevo delivery test, and no Windows execution of updater. The PDF layout was rendered and inspected. Payments remain simulated. Country/state remains Unknown unless your optional IP-location database is configured. A configured shared database is required to synchronize both services.

Recommended deployment checks: log in as owner, create a Store keeper, verify restricted menus and edits, update stock and view the customer size availability, reorder media, publish a media-only banner and a product-linked banner, generate/download each report, and retest customer OTP/checkout.
