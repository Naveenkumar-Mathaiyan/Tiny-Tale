# Tiny Tale v6 — Store experience

Update for the existing Flask storefront and admin on Render. Keep your current project folder, images, database and environment settings. Read START_HERE.txt in the release ZIP.

## New in this build

- Cream, sage and deep teal design shared by the customer store and admin, with responsive headers, cards, forms and galleries.
- Scrolling offers/highlights at the top of the customer store. Admins can publish 1–8 messages, optional links, visibility and speed under Storefront content > Scrolling offer strip. Pause control, hover/focus pause, and reduced-motion support are included. Strip messages are display content; they do not change coupon/shipping rules.
- Offer banner buttons can use a product shortcut, a custom store path, an anchor, login, or a full HTTPS URL. Buttons remain optional. New-tab behaviour is configurable. Unsafe schemes and protocol-relative links are rejected.
- Smooth anchor scrolling, dialog entry, collection filtering and admin section changes. Rapid admin navigation is serialized to show the final selection. External full-page navigation remains normal browser navigation.
- Customer features: recently viewed products (browser-local, clearable), age/size, maximum price and in-stock filters, result counts, favourites count, gallery thumbnails and previous/next controls, product-level PIN estimate, and free-delivery progress in the bag. Delivery estimates remain indicative PIN-based estimates, not live courier serviceability.
- Background stock polling avoids open dialogs and active inputs; unchanged data does not repaint the page.
- Mobile admin: collapsible Sections menu and stock/product cards with visible Edit controls.

## Existing features retained

Owner/Admin/Store keeper permissions, stock by size, One Size products, restricted gallery/stock editing, media and video uploads, restock requests, coupons, analytics, order numbering and PDF/Excel reports. Store keepers cannot change banner links or the offer strip. Owner login uses the existing password with username left blank.

No new API key or secret is required. Keep your working Brevo settings and shared DATABASE_URL. Deploy both Render services and hard refresh. Health version: 6.0-store-experience. The appearance setting is added through the existing settings table; old records are preserved.

## Validation

Backend regressions and permissions: python tests/v6.py; python tests/v4.py; python tests/email_errors.py.
Frontend logic: node tests/frontend.cjs. Optional jsdom: node tests/dom.cjs.
Migration: TINY_TALE_PREVIOUS_BUILD=/path/to/previous python tests/upgrade.py.
Browser harness: tests/browser.cjs requires optional Playwright, disposable local store/admin servers and local mock mail. Never use test fixture passwords/OTP bypasses in production. The release application contains no OTP bypass; the QA mock exists only in the temporary test server outside the release.

Desktop/mobile Chromium QA completed locally with SQLite and mock email, including OTP continuation and a simulated UPI checkout. Live Render/PostgreSQL, real Brevo delivery and Windows updater execution are not covered by these local checks. Payments remain simulated. PREVIEWS screenshots show the local QA build, not your live store; dummy QA data is not included in your database update.
