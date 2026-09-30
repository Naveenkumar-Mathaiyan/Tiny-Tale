# Upgrade to Tiny Tale 2.1 — size inventory

This build adds customer size selection, independent stock per size, “Available” / “Restock soon” customer labels, and admin-only alerts below five units. Cart, order enquiries and WhatsApp messages include the chosen size. Stock changes on order confirmation or cancellation affect that size only.

## Update your existing GitHub / Render deployment

1. Back up your existing database before updating. Keep your existing database and Render environment variables.
2. Extract the ZIP. Copy the CONTENTS of the `tiny-tale` folder into your existing repository folder:
   `C:\Users\NaveenkumarMathaiya\Downloads\Tiny_Tale_Login_Fix`
   Replace matching application files. Do not put the extracted folder inside the repository as a nested folder.
3. Keep your existing `.env`, `.venv`, `instance` folder and `.git` folder. This ZIP contains no passwords or customer database.
4. Open Command Prompt in that repository folder and run:

```bat
git status
git add app.py static tests README.md UPGRADE.md VERIFICATION.md requirements.txt runtime_config.py run_local.py start-admin.bat start-store.bat .gitignore .env.example
git commit -m "Add size inventory and admin-only low-stock alerts"
git push origin main
```

Do not replace your customized `render.yaml` with the bundled demo blueprint if you have changed its plans or configuration. This update does not require blueprint changes or new services.

5. Deploy the SAME commit to BOTH existing Render web services (customer and admin). Both services must continue using the SAME database. If automatic deployment is disabled, deploy the latest commit manually on each service. During the update, avoid editing stock or confirming orders until both services have completed deployment.
6. Open each service's `/health`. The version must be `2.1-size-inventory`. Hard-refresh both browser pages with Ctrl+F5.

## Assign existing stock to sizes

The upgrade adds a new table; it does not reset existing products, prices, photos, orders, coupons or stock. Every existing product initially keeps its previous total under **One size**. Age-size stock cannot be inferred from the old total.

Admin → Products & stock → Edit the product. Enable the age sizes sold and enter your actual quantities. Disable **One size** once you have distributed that product's stock by age. Do not duplicate the old quantity across sizes. Accessories that do not have age sizes may keep One size.

Example for Front Open Jabla:

| Size | Stock | Customer sees | Admin sees |
|---|---:|---|---|
| 0–3 months | 12 | Available | 12 |
| 3–6 months | 3 | Available | Low stock: 3 |
| 6–9 months | 0 | Restock soon | Out of stock: 0 |
| 9–12 months | 8 | Available | 8 |

The customer's page does not show admin warnings or stock counts. A sold-out size cannot be added to the cart. Exactly five units does not trigger a low-stock alert.

Old browser carts must be reselected once because they did not record size. Existing saved enquiries without a size keep their original One size allocation. Review those enquiries before disabling One size; the app will refuse to confirm them if their original size is disabled. Cancellation of an already confirmed legacy order restores its original allocation.

## Local use

Stop both running application windows before replacing files, then restart using the existing `.bat` files. Keep your original `.env` and `instance/tiny-tale.db`. No dependency changes are required.

## Scope of this release

This release covers size selection, stock by size and admin-only alerts. The earlier wishlist (new order numbering, notify-me requests, staff accounts, galleries/videos, payment testing and delivery estimates) is not included yet. “Restock soon” does not send a notification.
