# Tiny Tale v4

Flask storefront and separate admin for a small baby clothing catalog.

**Start with [UPDATE_GUIDE.md](UPDATE_GUIDE.md)** for the existing-project update, Git push and required Render/Brevo setup.

New: email diagnostics, multiple product media, offer banners, favourites, mobile menu, marketing charts, consented traffic attribution and future-order numbering controls.

Payment methods are demonstrations only. Production email delivery needs your private Brevo API key on the customer Render service. Country/state analytics require an optional local geolocation database. Uploaded media and application records use the existing shared SQL database.

Tests: `python tests/v4.py`, `node tests/frontend.cjs`; migration: `TINY_TALE_PREVIOUS_BUILD=/path/to/previous python tests/upgrade.py`.
