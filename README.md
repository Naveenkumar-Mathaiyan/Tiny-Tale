# Tiny Tale 3.0

Customer store and separate admin, upgraded from the supplied Tiny Tale 2.1 project.

## Start here

Already deployed? Follow `START_HERE.txt`. Update BOTH existing Render services using the same existing database. Do not create another Blueprint or database.

## Included

- Email OTP login/register through Brevo; required before checkout and restock requests. Browsing, product details and the cart are public. Login preserves the cart. Phone/SMS OTP is not integrated in this release.
- Additional 5% verified-login discount on product value after coupons, excluding delivery. Free shipping still uses the pre-discount product subtotal of ₹999 or more.
- Admin size type: Age sizes / One Size. Independent stock per enabled size, customer Available / Restock soon labels, admin-only alerts below five units. Store inventory refreshes every 20 seconds while visible, and on focus.
- Readable order number: India date YYMMDD + global sequential counter, padded to at least four digits. Existing saved orders receive numbers during migration; their internal UUIDs remain unchanged. The sequence does not reset daily; after 9,999 orders it expands beyond four digits instead of wrapping.
- No automatic WhatsApp redirect at checkout. Successful test checkout shows order number, payment mode and indicative delivery range; seller confirmation is still pending.
- Credit/debit card, UPI and net banking test checkout, success/failure/cancellation simulation and server-side idempotency. No COD. This is NOT a live payment gateway.
- Only predefined sample payment data is accepted in the frontend. Raw card numbers/CVV and banking credentials are never sent to the backend. The server accepts only method/outcome choices and always marks new payments as test.
- UPI informational QR includes the final amount but deliberately cannot initiate a real transfer. It is not a live UPI QR.
- Customer-owned order history. Another customer cannot fetch your history through account endpoints.
- Notify me for sold-out sizes: verified email account, WhatsApp phone and requested quantity. Admin restock table counts people/quantity and lets the owner mark requests Open, Contacted or Closed. Repeated requests update that account's quantity. Admin sees requests in the application; no automatic email/WhatsApp notification is sent to admin or waiting customers.
- Business address, factory address, Google Maps links, dispatch PIN, delivery-day rules and return/refund text editable in admin. Unknown addresses are not fabricated. Social buttons are clearly labelled placeholders.
- Customer journey analytics with consent: active visible browsing time, ordered stage funnel, reach, time per stage, recent paths and coupon/checkout/test-payment errors. Time stops for hidden or idle tabs. These are session observations, not proof of customers' intentions. Server-recorded simulated successes are separate from financial totals.
- Crawlable product pages, canonical URLs, product structured data, sitemap, public policy page and robots rules. Admin responses are noindex. SEO does not guarantee ranking.

## Email setup on Render

Configure these on the CUSTOMER service, `tiny-tale-store`, under Environment:

| Variable | Value |
|---|---|
| BREVO_API_KEY | Your privately saved normal Brevo API key |
| BREVO_SENDER_EMAIL | mnk9522@gmail.com |
| BREVO_SENDER_NAME | Tiny Tale |
| SITE_URL | Your full customer URL, e.g. https://tiny-tale-store.onrender.com |

Do not paste the key into Git, JavaScript, this README or the admin form. No key is bundled. Existing ADMIN_PASSWORD, SECRET_KEY, DATABASE_URL, APP_ROLE and COOKIE_SECURE settings stay in place. Both services continue sharing DATABASE_URL.

Without configured email credentials, OTP requests return a clear unavailable message. There is no production test-code bypass. Sender verification, account approval and Brevo deliverability must be validated in your own account after deployment. A verified Gmail sender may be rewritten by Brevo; migrate to an authenticated business domain for ongoing use.

The OTP is a cryptographically generated six-digit code; stored as a password hash, expires in five minutes, has five verification attempts and can be used once. Requests have a 60-second cooldown, three requests per email / 15 minutes and ten per IP / 15 minutes. Those limits can also affect people on shared networks. Email OTP verifies access to an email address; it does not guarantee a genuine shopper or eliminate all bots.

## Admin setup after deploy

1. Products & stock > Edit: choose Age sizes or One Size and enter real quantities. Do not double-count inventory when changing size type. Hidden old size allocations are kept for legacy order cancellation.
2. Business & delivery: enter your actual dispatch PIN and processing/transit rules. Until then, checkout shows that delivery timing is not yet available.
3. Enter business/factory addresses and Google Maps links.
4. Replace draft return/refund text with approved terms and tick Publish these approved policies. The defaults are demonstration text, not final business terms.
5. Customer journey and Restock requests are new admin screens. Browsing reports need customer consent.

## Delivery estimate meaning

Rules compare exact PIN, first three PIN digits, or other PINs, then add processing days and configured minimum/maximum transit calendar days to India's current date. This is an approximate rule-based range, not verified distance, courier coverage or a guaranteed delivery date. No courier API is connected.

## Local Windows use

Keep your original `.env`, `.venv`, `instance` and `.git`. Update requirements using your virtual environment. For OTP locally, add the same BREVO variables privately to `.env`; runtime_config loads them. Start with `start-store.bat` and `start-admin.bat`.

Customer: http://127.0.0.1:5000 · Admin: http://127.0.0.1:5002

## Validation and limitations

See `VERIFICATION.md`. Integration/migration checks use SQLite. Real Brevo delivery, live PostgreSQL concurrency and browser layout were not tested here. The included Windows updater is reviewed but not executed on this Linux build host.

All new checkout payments are simulated. Confirming a test order in admin still reduces size inventory; cancelling a confirmed order restores it. Enquiries do not reserve stock. No live payment/refund transfer, SMS OTP, automatic restock messages, staff accounts or product video gallery is included in this release.
