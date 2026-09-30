# Tiny Tale 2.1 — Customer store + separate admin

**Already deployed? Follow [UPGRADE.md](UPGRADE.md).** Keep the existing database and update both services.

A runnable baby clothing sales demo with all 11 requested products and bundled AI-generated illustrative photos. Replace the photos, prices, size information and business policies before live selling.

## What works
- Product catalog, search, categories, sorting, details, size selection, stock by size, customer availability labels.
- Persistent browser cart, quantity controls, Buy Now, coupon validation and server-calculated totals.
- WhatsApp to **+91 98652 44212**, delivery address and saved order enquiries.
- Separate password-protected admin app: products, original/discount price, uploaded photos, stock by size, admin-only alerts below five units, visibility, coupons, order statuses and analytics.
- Analytics with opt-in consent: views, searches, cart/checkout actions, WhatsApp clicks, mobile/tablet/desktop, browser, OS and referring website.
- SQLite locally; shared PostgreSQL on Render. Uploaded images are stored in the database so they survive deploys; suitable for a small demo catalog.

## Important behavior
Online payment is **not connected**. Orders start as enquiries; opening WhatsApp cannot prove a message was sent. Admin confirmation reduces stock; cancelling a confirmed order restores stock. Confirmed order value is not payment revenue. Visitors are anonymous sessions, not verified people. Exact phone model, demographics and location are not collected. Only consented activity appears in browsing reports.

Store and admin have separate URLs and processes, with no customer-facing admin link. They intentionally share the backend code and database. The storefront process rejects admin API requests. Both processes serve public product/image APIs; private management APIs require the admin role, login and CSRF token.

## 1. Run locally on Windows
Install Python 3.11 or 3.12. Extract this folder. Open Command Prompt **inside tiny-tale**:

```bat
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
```
Open `.env` in Notepad. Set a strong `ADMIN_PASSWORD` and unique `SECRET_KEY` (at least 32 random characters). Keep `DATABASE_URL=sqlite:///tiny-tale.db` and `COOKIE_SECURE=false` for localhost.

Double-click **start-store.bat** and **start-admin.bat**. Leave both windows open.

- Customer: http://127.0.0.1:5000
- Admin: http://127.0.0.1:5002
- Sign in using the password you put in `.env`.

Do not double-click index.html. This application needs the Python server to load the catalog. Both processes use `instance/tiny-tale.db` locally.

On macOS/Linux, install the requirements in a virtual environment, then run in separate terminals:
```sh
APP_ROLE=store PORT=5000 python app.py
APP_ROLE=admin PORT=5001 python app.py
```

## 2. Push to GitHub
Create an empty repository on https://github.com/new (do not initialize a README). In the extracted **tiny-tale** directory:

```sh
git init
git add .
git commit -m "Add Tiny Tale storefront and admin"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/tiny-tale.git
git push -u origin main
```
Replace YOUR_USERNAME with yours. GitHub may ask you to sign in through Git Credential Manager. `.env`, databases and virtual environments are excluded. Make sure `app.py`, `requirements.txt`, `static/`, `render.yaml` and this README are at the repository root. If you upload files through GitHub's UI, enable hidden files so `.gitignore` is included.

## 3. Deploy on Render — guided manual option
This is **two Python Web Services**, not a Static Site.

### A. Create PostgreSQL
1. Render Dashboard → New → Postgres.
2. Name: `tiny-tale-db`; pick a region. Use the same region for both services.
3. Create the database. Copy its **Internal Database URL** privately.
4. Choose a suitable plan. Render's current free PostgreSQL expires after 30 days. Free web services can sleep; consult the current free-tier documentation before demonstrating.

### B. Customer Web Service
1. New → Web Service → connect GitHub → select your repository.
2. Name: `tiny-tale-store`. Runtime: Python. Root Directory: blank if app.py is at root.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4`
5. Add environment variables:

| Variable | Value |
|---|---|
| APP_ROLE | store |
| DATABASE_URL | database Internal Database URL |
| SECRET_KEY | unique random secret, at least 32 characters |
| COOKIE_SECURE | true |
| PYTHON_VERSION | 3.12.8 |

6. Deploy. Wait for `/health` to return `ok: true`. Open the assigned URL.

### C. Admin Web Service
Repeat with name `tiny-tale-admin`, same build/start commands, and these variables:

| Variable | Value |
|---|---|
| APP_ROLE | admin |
| DATABASE_URL | **same** database Internal Database URL |
| SECRET_KEY | a different unique random secret |
| ADMIN_PASSWORD | strong, unique password; only enter in Render |
| COOKIE_SECURE | true |
| PYTHON_VERSION | 3.12.8 |

Deploy and open the admin service's separate URL. Sign in with ADMIN_PASSWORD. Keep this URL with your team. Do not commit passwords, database URLs, or .env to GitHub.

## Alternative: Blueprint
Render → New → Blueprint → select your repository. `render.yaml` defines both services and the database. Review the plans shown before creating resources, and supply ADMIN_PASSWORD when prompted. SECRET_KEY values are generated separately for each service. The blueprint uses Render's free demo plans; change the database plan before its free period ends if you want persistent continued access.

## 4. Demonstrate
1. Open customer URL; allow analytics if you want to demonstrate browsing reports.
2. Browse product details, search `Jabla`, add an item and view the bag.
3. Apply `TINY10`; try `BABY15` below ₹1,500 to see validation.
4. Complete address and save an enquiry; send WhatsApp manually.
5. Open the separate admin URL → Order enquiries → Confirm order. Stock drops.
6. Products & stock → Edit → upload your own JPG/PNG/WebP → Save.
7. Refresh customer page to see the new image and price.
8. Overview & analytics → Refresh. Review top products/searches/devices.

## Troubleshooting
- No products: open the server URL, not the HTML file. Check `/health` and Render logs; confirm DATABASE_URL on both services.
- Broken photos: ensure all `static/images/product-0.png` through `product-10.png` were committed. Paths are root-relative and served by Flask.
- Admin unavailable: APP_ROLE must be `admin`; ADMIN_PASSWORD must be set. Store service intentionally blocks admin endpoints.
- Login loop: COOKIE_SECURE=true is for HTTPS on Render; use false on local HTTP.
- Data missing after deploy: use PostgreSQL on Render, never local SQLite there. Both services must point to the same DB.
- First load slow: free Render services may wake from idle.
- Changes not visible: save in admin, refresh store, and check that both services use the same database.

## Technical notes and demo limits
Stack: HTML/CSS/JavaScript frontend, Flask + SQLAlchemy API, PostgreSQL/SQLite, Pillow uploads, Gunicorn server. No Node build required. Photos are AI-generated demo mockups (product-mockup prompts: each named baby item, cotton fabric, blue/yellow star print, pale blue studio flat lay, no text/logos), not evidence of actual merchandise. They were generated with the built-in image tool and are bundled under static/images/.

Admin cookies are HttpOnly, SameSite=Strict, secure on HTTPS, and expire after eight hours. Writes require CSRF tokens. Login is throttled. Uploaded raster images are decoded and re-encoded; HTML/SVG uploads are not accepted. Prices, coupons, stock and totals are validated server-side. PostgreSQL uses row locks for order confirmation.

For live selling, add payment gateway verification/webhooks, shipping and return policies, backups, stronger account management/MFA, external image storage for a larger catalog, privacy/retention procedures and abuse controls. Demo enquiries can be duplicated if someone resubmits or retries; review before confirming. Never enter card details into this demo.

## Official deployment references
- https://render.com/docs/deploy-flask
- https://render.com/docs/free
- https://render.com/docs/configure-environment-variables
- https://render.com/docs/postgresql-creating-connecting
