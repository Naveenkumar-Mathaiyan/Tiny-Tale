import os,sys,json
from pathlib import Path
if os.environ.get('TINY_TALE_QA')!='1':raise SystemExit('This fixture is only for a disposable test database; set TINY_TALE_QA=1.')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as m
from werkzeug.security import generate_password_hash
with m.app.app_context():
 for role in ['store_manager','manager','supervisor','billing']:
  if not m.db.session.scalar(m.db.select(m.Staff).where(m.Staff.username==role)):
   m.db.session.add(m.Staff(id=role,name=role.title(),username=role,role=role,password_hash=generate_password_hash('staff-password-123'),active=True,version=1))
 m.db.session.commit()
def send(email,code):Path(os.environ.get('TINY_TALE_QA_OTP_FILE','/tmp/tiny-v7-otp.json')).write_text(json.dumps(dict(email=email,code=code)))
m.send_otp=send
m.app.run(host='127.0.0.1',port=int(os.environ['PORT']),threaded=True)
