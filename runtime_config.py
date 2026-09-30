"""Explicit local config loading; hosted environment settings retain priority."""
import io
import os
from pathlib import Path
from dotenv import dotenv_values

def load_config(base):
    base = Path(base).resolve()
    path = base / '.env'
    if not path.is_file():
        return {'path': str(path), 'exists': False, 'password': bool(os.getenv('ADMIN_PASSWORD') or os.getenv('ADMIN_PASSWORD_HASH'))}
    raw = path.read_bytes()
    encoding = 'utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
    values = dotenv_values(stream=io.StringIO(raw.decode(encoding)), interpolate=False)
    for key in ('ADMIN_PASSWORD', 'ADMIN_PASSWORD_HASH', 'SECRET_KEY', 'DATABASE_URL', 'COOKIE_SECURE'):
        value = values.get(key)
        if value:
            if not os.getenv('RENDER') or not os.getenv(key):
                os.environ[key] = value
    return {'path': str(path), 'exists': True, 'password': bool(os.getenv('ADMIN_PASSWORD') or os.getenv('ADMIN_PASSWORD_HASH'))}
