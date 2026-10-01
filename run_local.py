import getpass
import os
from pathlib import Path
import socket
import sys
from runtime_config import load_config

base = Path(__file__).resolve().parent
os.chdir(base)
role = sys.argv[1] if len(sys.argv)>1 else 'store'
if role not in ('store','admin'):
    raise SystemExit('Use run_local.py store or run_local.py admin')
port = 5002 if role=='admin' else 5000
os.environ['APP_ROLE'] = role
os.environ['PORT'] = str(port)
print('Tiny Tale 3.0', flush=True)
print('Application folder:',base,flush=True)
try:
    state = load_config(base)
except (UnicodeError, OSError) as exc:
    raise SystemExit('Could not read .env. Save it as UTF-8 in Notepad and try again.') from exc
print('Configuration file found:',state['exists'],flush=True)
if role=='admin' and not state['password']:
    print('No admin password loaded. Enter a password for this run; typing is hidden.',flush=True)
    password = getpass.getpass('Admin password: ')
    if not password.strip(): raise SystemExit('Password cannot be empty. Restart and enter a password.')
    os.environ['ADMIN_PASSWORD'] = password
print('Admin password configured:',bool(os.getenv('ADMIN_PASSWORD') or os.getenv('ADMIN_PASSWORD_HASH')),flush=True)
os.environ['COOKIE_SECURE']='false'
with socket.socket() as sock:
    try: sock.bind(('127.0.0.1',port))
    except OSError: raise SystemExit(f'Port {port} is already occupied. Stop the existing Tiny Tale {role} server and try again.')
print(f'Open http://127.0.0.1:{port} in your browser. Keep this window open.',flush=True)
from app import app
app.run(host='127.0.0.1',port=port,use_reloader=False)
