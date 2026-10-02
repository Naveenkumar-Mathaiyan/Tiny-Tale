# Tiny Tale v4.1 — update and email setup

This is an update to the supplied v3 source. It has not been pushed to your GitHub repository or deployed to your Render account.

## 1. Fix email login on your existing Render service

Render does not re-prompt for new `sync: false` secrets when an existing Blueprint is updated. A normal Git push does not request your key. The previous YAML omitted Brevo variables; v4 declares them for new Blueprint creation, but existing services need this manual setup.

Open Render → **tiny-tale-store** → **Environment** → Add Environment Variable:

| Key | Value |
|---|---|
| BREVO_API_KEY | Paste the private **API key** from your Notepad (not an SMTP key) |
| BREVO_SENDER_EMAIL | mnk9522@gmail.com |
| BREVO_SENDER_NAME | Tiny Tale |
| SITE_URL | https://tiny-tale-store.onrender.com |

Choose **Save and deploy**. Keep the existing SECRET_KEY and DATABASE_URL. Do not recreate your services or database. The admin service does not need the Brevo key: login email is sent by the customer service.

After deploying v4 to both services, open admin → Email login setup. It reads safe configuration/delivery status from the shared database. Open the customer site → Login / Register → enter your email → Send code → enter the six-digit code. Codes expire in five minutes and can only be used once. After verification, checkout resumes and the extra 5% product discount applies after coupons.

If no email arrives, inspect Brevo → Transactional → Logs and Spam/Junk. Verify the sender, API key, transactional account activation, credits and any Brevo authorized-IP restrictions. The admin panel records safe HTTP status guidance, never the key or OTP. A successful API response means accepted for delivery, not guaranteed inbox placement. Missing settings are now caught before consuming OTP request limits.

Official references: https://render.com/docs/blueprint-spec ; https://render.com/docs/configure-environment-variables ; https://developers.brevo.com/docs/send-a-transactional-email

## 2. Apply the files without mixing folders

1. Back up your existing project and export/back up the database before deploying.
2. Extract the entire ZIP into a NEW temporary folder.
3. Run **APPLY-UPDATE.bat** in the extracted folder.
4. Choose your EXISTING Git repository folder. The updater prefers `Downloads\Tiny_Tale_Login_Fix_old` when its Git folder exists. This is the folder you previously used for `git push`.
5. The updater copies the complete application source. It preserves `.git`, `.env`, `.venv` and `instance`. It does not delete your old database or uploaded media. It does not push Git automatically.
6. Open Command Prompt in that same existing repository and run:

```bat
git status
git add app.py features.py enhancements.py runtime_config.py requirements.txt render.yaml static tests UPDATE_GUIDE.md README.md .env.example
git diff --cached --stat
git commit -m "Fix Brevo setup and add galleries banners marketing and favourites"
git push origin main
```

If your folder contains additional local changes, inspect them before committing. Do not add private `.env`, API keys or database files. `enhancements.py`, all changed `static` files and `render.yaml` MUST be pushed together.

Deploy the same commit on **tiny-tale-store AND tiny-tale-admin**. Do not reset the database. `/health` will identify `4.1-header-email`. Existing orders keep their old numbers; products, size stock, customers and media stay in their shared database. Refresh the browser after deployment.

## 3. What changed

- Email setup status in admin, updated Render YAML, missing-configuration checks and branded OTP emails. The customer button reads **Login / Register**.
- **Product galleries**: choose a product, upload multiple photos/GIFs/videos, edit full description/material/care, reorder/remove gallery items, then Save. Main product cover remains in Products & stock.
- **Offer banners**: upload image/GIF/video, enter title/copy/button, choose link, and activate. `login` opens OTP login; `#collection` goes shopping. Active banners shuffle per page visit and have manual Previous/Next controls. Videos have playback controls; no forced autoplay. When none are active, a built-in login-offer banner appears.
- Customer full product galleries, details, heart favourites, mobile menu, account order thumbnails and Buy again. Favourites are saved only on that browser, including before login; they do not sync across devices. Buy again uses current price and current size stock.
- **Order numbering**: optional prefix, YYMMDD date or no date, padding 4–8 and forward-only next lifetime sequence. India time is used. Existing numbers never change. No daily reset. Default remains YYMMDDXXXX, with more digits if needed.
- **Marketing graphs**: date/hour sessions, campaigns, source engagement, checkout reach, test completions, top products and shopping actions. Date/hour views use IST. Existing Customer journey still shows active browsing time, paths and errors. Analytics require consent; the updated notice asks previous visitors again.
- **Traffic details**: first-touch source/medium/campaign, time, landing path without query strings, IP and approximate country/state if configured. No age/gender inference. Raw-IP traffic rows expire after 90 days; cleanup runs on traffic ingestion/report viewing. Admin access and CSRF protection remain enforced.
- Size-specific availability remains public as Available or Restock soon. Low-stock alerts remain admin-only. No COD or automatic WhatsApp order redirect is added.

## 4. Location data and marketing links

Country/state are **Unknown by default**, because Render alone does not supply reliable location. Optional: obtain a licensed GeoLite2 City `.mmdb` database from MaxMind, make it available on the CUSTOMER service, set `GEOIP_DATABASE` to its absolute path, and redeploy. Update that file under its licensing terms. Do not commit a download license key. Admin reads stored location; raw IP is not sent to an external lookup API. A proxy/VPN can make IP location inaccurate. See https://dev.maxmind.com/geoip/geolite2-free-geolocation-data/ for setup.

Tag your own campaign links, for example:
`https://tiny-tale-store.onrender.com/?utm_source=instagram&utm_medium=social&utm_campaign=newborn_launch`

Source/referrer/UTM values can be missing or spoofed. Browser-session counts are not unique people. Active time is approximate and excludes background/idle tabs. Test completions are not revenue; use these graphs to identify where to investigate, not to claim a shopper's motivation.

## 5. Media limits and persistence

Uploads are stored in the shared database so they survive Render redeploys. Maximum 20 MB per file and 12 extra items per product. Accepted image formats: JPEG, PNG, WebP, GIF (up to 16 megapixels / 500 frames). Video: MP4/WebM with container signature checks; use MP4 H.264 for broad compatibility. Videos are not transcoded or scanned by this small-app build. Preview and test your own uploads. Database storage and bandwidth are finite: compress media, especially videos. Removing a gallery/banner reference does not immediately delete the underlying uploaded asset. Large catalog/video workloads should move to dedicated object storage in a future update.

## 6. Checkout remains a demonstration

Payments are still simulated credit/debit card, UPI and net banking. No money is collected. The test QR is informational, not a live payment QR. Orders stay Enquiry until seller confirmation; confirmation deducts stock. Do not treat the test checkout as a working live payment gateway. OTP proves access to an email address; it does not guarantee a human customer.

## 7. Verification performed

Disposable-database regression tests cover OTP expiration/attempts/replay/CSRF, four test payment methods, discount calculations, duplicate checkout prevention, order ownership, size stock/restock, delivery settings, order status transitions and preserving previous data. v4 tests cover missing email configuration, private diagnostics, GIF preservation, media validation, galleries, banners, numbering and consented attribution. Real Brevo delivery and your hosted PostgreSQL/Render deployment still require checking after configuration. No key is bundled. DOM tests also cover both sets of frontend scripts and the new UI controls. A visual-browser check could not be completed because the browser download was truncated in this environment; review the mobile layout and your uploaded video codecs after deployment.

Local development: install `requirements.txt` in your virtual environment, set local `.env` credentials, and run the existing start scripts. Separate store/admin processes must share the same database, as before.

## v4.1 screenshot fixes

The storefront header now has aligned brand, desktop links and account/bag controls. Menu is shown on smaller screens. Email login has a full-width input and buttons in a compact dialog.

If sending fails, Admin → Email login setup now identifies safe categories: EMAIL_AUTH (API authentication), EMAIL_IP (server-IP authorization), EMAIL_SENDER (sender rejection), EMAIL_PERMISSION (sending permission), EMAIL_LIMIT (quota/rate/credits), EMAIL_CONFIG (invalid formatting), or EMAIL_PROVIDER (other provider error). The private provider message and your key are not displayed. The customer sees a reference code to report.

This cannot repair credentials or authorization inside your Brevo account. Request a fresh code after deploying, then read the exact admin diagnostic and follow its instruction. For IP blocking, check Brevo's blocked/authorized IP list and verification email; authorize the server IP shown by Brevo. For API authentication, replace the customer service's BREVO_API_KEY with an active API key and Save and deploy. For sender rejection, verify mnk9522@gmail.com in Brevo and ensure the Render sender matches exactly.
