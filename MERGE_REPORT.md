# Merge report

Compared the two user-provided ZIPs directly.

Updated from the size-inventory build: `app.py`, `static/admin.html`, `static/admin.js`, `static/store.js`, `static/styles.css`.

Preserved byte-for-byte from your old folder: `render.yaml`, `requirements.txt`, `runtime_config.py`, `run_local.py`, both startup BAT files and all 11 product images. These files match the uploaded new build.

Added the new build's tests, `.gitignore`, `.env.example`, upgrade notes and verification notes. Corrected the README admin local URL to port 5002, matching your retained launcher. Replaced obsolete INSTALL instructions with directions for this release.

The old ZIP also contained `.env`, `.git`, `.venv` and a local database. Their contents are not redistributed in this release. The update script keeps those existing files on your computer by copying only the clean release into the existing repository without deleting anything.

The updater does not run Git commands, create services or touch Render. The Git commands in START_HERE explicitly stage the application files.
