# Existing project update

Use the release ZIP START_HERE.txt and APPLY-UPDATE.bat. Apply to the original folder containing app.py and .git. This update reuses static/images; it is not a standalone replacement for an empty directory.

Copy the code, push to the existing GitHub main branch, and deploy BOTH tiny-tale-store and tiny-tale-admin. Their existing environment variables and shared PostgreSQL database must remain unchanged. Requirements now include reportlab and openpyxl; Render installs these from requirements.txt during the build.

After deployment check /health on both services for version 5.0-admin-studio. Hard refresh the browser (Ctrl+F5) so the new admin-v5.js and CSS load.

Owner: leave username blank, use the existing admin password. Administration > Staff accounts > Create staff account. Choose Store keeper, enter a unique username and password of at least 12 characters, save. Sign out and verify that account sees only Products & stock and Product photos & videos. Editing/disabling accounts revokes existing sessions.

Banner example: Storefront content > Offer banners > upload Knot Jabla media > optional button destination Knot Jabla > button text Get Knot Jabla Offer > Save. No button: choose No button; label/link is omitted.

Analytics: Performance dashboard is the summary; Checkout journey shows stages and dated sessions; Product & audience insights shows products, searches and device/browser counts. Traffic sources identify where visits arrived from. Campaigns only group links tagged with a campaign name; create a promotion link on the dashboard and share it externally. “Direct / source unavailable” and “No campaign tag” are missing attribution, not proof of poor performance.

Reports: choose type and dates > Generate report > PDF preview and downloads. Current inventory ignores dates because it is a snapshot at generation time. Test payments are not real revenue. Country/state requires the existing optional geolocation database; Unknown is not replaced with invented locations.
