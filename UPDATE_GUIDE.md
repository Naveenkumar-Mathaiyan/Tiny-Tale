# Updating Tiny Tale

Follow START_HERE.txt in order. Use the existing Git folder and the existing two Render services; keep their database and working Brevo settings. The update script excludes Git history, .env files, virtual environments, instance data and database files. It does not delete your existing image directory. Back up the project and database before updating.

New runtime file: `operations.py`. Existing files changed: `app.py`, `management.py`, `enhancements.py`, admin/store HTML and admin scripts. New frontend files: `admin-v7.js`, `store-v7.js`, `operations.css`. The `mobile-scanner` directory is a separate Expo source project; Render still runs the Python app from the repository root.

The startup migration creates new category, variant-code, native-token, invoice, operation and stock-movement tables. Existing products, assets, variants, enquiries, coupons, business settings and email configuration remain in place. Old Store Keeper accounts become Store Manager. All currently signed-in legacy stock staff must sign in again.

After both deployments reach health version `7.0-stock-billing`, refresh the store/admin and test one product, one small stock arrival, one counter bill, PDF labels and your own real email OTP delivery. Printed labels must match your production codes; PREVIEWS contains test screenshots only.

If rollback is needed, stop scanner/counter writes, retain the upgraded database and redeploy your previous Git commit. New tables are additive. Older versions do not recognize new staff roles; only the owner/Admin should use an older build. Do not restore an old database snapshot over new sales without reconciling those sales and stock movements first.
