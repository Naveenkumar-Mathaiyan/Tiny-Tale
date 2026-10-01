# Upgrade to 3.0

Use START_HERE.txt and the bundled APPLY-UPDATE.bat. Your existing repository is currently named Tiny_Tale_Login_Fix_old; the updater detects that folder first.

Back up your database before upgrade. Stop local app windows while copying files. Do not remove .git, .env, .venv or instance. Deploy the SAME commit to both existing Render services; keep the same database. Avoid stock edits/order confirmation until both deployments finish.

The upgrade creates supplementary tables for customer auth, OTP, order metadata/counter, restock, settings and journey metrics. No existing columns are removed or changed. Existing orders receive readable order numbers; pre-upgrade customer orders are not automatically linked to newly registered accounts.

Original images and Render settings are retained. A new features.py module, admin-extra.js and qrcode dependency are required—push the complete update, including requirements.txt.

See README.md for email credentials, shipping rules, policy setup, payment simulation and test limitations. /health version must be 3.0-checkout-otp on both services.
