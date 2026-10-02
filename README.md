# Tiny Tale v5 — Admin studio

An update for the existing Flask storefront/admin on Render, using the same shared database.
Start with START_HERE.txt in the release ZIP. Keep your existing Git repository, .env, database, uploaded media and static/images.

New: grouped management navigation; owner/admin/store keeper roles; stock/media-only permissions enforced on the server; staff creation, reset/disable and immediate session revocation; clearer performance graphs and checkout-drop investigation; campaign link builder; IST session timestamps; optional banner buttons and product destination dropdown; Move left/Move right gallery controls; PDF preview and Excel/PDF exports for orders, current inventory, restock requests, traffic and journeys.

Owner login remains the existing ADMIN_PASSWORD / ADMIN_PASSWORD_HASH, with username left blank. Owner is the super admin and can create Admin and Store keeper accounts. An Admin cannot create accounts. A Store keeper cannot create products, change sizes, prices or descriptions, or access orders, analytics, reports, policies or banners.

Reports use inclusive India-time dates (maximum 366 days, 5,000 source records). Inventory is a current snapshot, not historic stock. Traffic is retained 90 days. Reports distinguish simulated payments; order value is not a bank/payment settlement report. Excel exports are real .xlsx files and customer values are stored as text to prevent formulas. PDF previews include a new-tab link for browsers without embedded PDF viewing.

The existing OTP integration and Render environment settings remain in use. Do not replace a working Brevo key. Both Render services need the same DATABASE_URL, and the admin service needs APP_ROLE=admin. No new secret is needed for this release. New staff table creation is additive at startup.

Verification: python tests/v5.py; python tests/v4.py; python tests/email_errors.py; node tests/frontend.cjs; optional jsdom: node tests/dom.cjs. Migration: TINY_TALE_PREVIOUS_BUILD=/path/to/previous python tests/upgrade.py.
Tests use disposable SQLite and mocked email. No live Render/PostgreSQL or Brevo delivery test was performed by this build environment. Browser installation was blocked by truncated downloads, so visual browser QA remains required after deployment. Windows updater has been inspected, not executed on Windows.
