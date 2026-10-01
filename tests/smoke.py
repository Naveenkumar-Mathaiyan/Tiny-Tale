import os,sys,tempfile,io,uuid
from datetime import datetime,timedelta,timezone
from pathlib import Path
os.environ.update(DATABASE_URL='sqlite:///'+tempfile.mktemp(suffix='.db'),APP_ROLE='admin',ADMIN_PASSWORD='test-password',SECRET_KEY='test-only-secret',BREVO_API_KEY='test-secret',BREVO_SENDER_EMAIL='sender@example.test')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as m
from sqlalchemy import select
from PIL import Image
from werkzeug.security import generate_password_hash
app,db=m.app,m.db
admin=app.test_client();shop=app.test_client();other=app.test_client()
assert admin.get('/api/admin/products').status_code==401
login=admin.post('/api/admin/login',json={'password':'test-password'});assert login.status_code==200
ah={'X-CSRF-Token':login.json['csrf']}
account=shop.get('/api/account').json;ch={'X-Customer-CSRF':account['csrf']}
assert shop.post('/api/orders',json={},headers=ch).status_code==401
assert shop.post('/api/auth/request',json={'email':'x@example.com'}).status_code==403
codes={}
def send(email,code):codes[email]=code
m.send_otp=send
r=shop.post('/api/auth/request',json={'email':'test@example.com'},headers=ch);assert r.status_code==201
assert 'code' not in r.json and 'test-secret' not in str(r.json)
assert shop.post('/api/auth/request',json={'email':'test@example.com'},headers=ch).status_code==429
challenge=r.json['challenge']
assert shop.post('/api/auth/verify',json={'challenge':challenge,'code':'abcdef'},headers=ch).status_code==400
r=shop.post('/api/auth/verify',json={'challenge':challenge,'code':codes['test@example.com']},headers=ch);assert r.status_code==200
ch={'X-Customer-CSRF':r.json['csrf']}
assert shop.post('/api/auth/verify',json={'challenge':challenge,'code':codes['test@example.com']},headers=ch).status_code==400
assert shop.get('/api/account').json['customer']['email']=='test@example.com'
ps=shop.get('/api/products').json;assert len(ps)==11
for p in ps:assert shop.get(p['image']).status_code==200
items=[dict(id='1',size='One size',qty=2)]
q=shop.post('/api/quote',json={'items':items,'coupon':'TINY10'}).json
assert (q['subtotal'],q['discount'],q['login_discount'],q['total'])==(558,56,25,546)
assert other.post('/api/quote',json={'items':items,'coupon':'TINY10'}).json['login_discount']==0
assert shop.post('/api/quote',json={'items':[dict(id='1',size='One size',qty=26)]}).status_code==400
# Settings, policy approval and PIN validation.
s=admin.get('/api/admin/business').json;assert not s['policies_published']
s['dispatch_pin']='600001';s['address']='Owner entered address';s['factory_address']='Owner factory';s['map_url']='https://maps.google.com/?q=Chennai'
assert admin.post('/api/admin/business',json=s,headers=ah).status_code==200
bad={**s,'same_pin_min':8,'same_pin_max':2};assert admin.post('/api/admin/business',json=bad,headers=ah).status_code==400
assert admin.post('/api/admin/business',json={**s,'map_url':'javascript:alert(1)'},headers=ah).status_code==400
eta=shop.get('/api/delivery?pin=600001');assert eta.status_code==200 and eta.json['available']
assert shop.get('/api/delivery?pin=000000').status_code==400
# All four methods, duplicate prevention and private customer ownership.
address=dict(name='QA User',phone='9876543210',address='Test street',city='Chennai',state='Tamil Nadu',pin='600001')
orders=[]
for method in ['credit_card','debit_card','upi','net_banking']:
 data=dict(items=items,coupon='TINY10',expected_total=546,customer=address,payment=dict(method=method,outcome='success'),request_key=str(uuid.uuid4()),sid='11111111-1111-1111-1111-111111111111',consent=True)
 r=shop.post('/api/orders',json=data,headers=ch);assert r.status_code==201,r.json
 assert r.json['number'].startswith(datetime.now(timezone(timedelta(hours=5,minutes=30))).strftime('%y%m%d')) and len(r.json['number'])==10
 assert r.json['total']==546 and r.json['payment_mode']=='test' and r.json['status']=='Enquiry'
 orders.append(r.json)
 retry=shop.post('/api/orders',json=data,headers=ch);assert retry.status_code==200 and retry.json['id']==r.json['id']
 data['customer']={**address,'name':'Changed'};assert shop.post('/api/orders',json=data,headers=ch).status_code==409
bad_total=dict(items=items,coupon='TINY10',expected_total=1,customer=address,payment=dict(method='upi',outcome='success'),request_key=str(uuid.uuid4()))
assert shop.post('/api/orders',json=bad_total,headers=ch).status_code==409
assert len(set(o['number'] for o in orders))==4
assert len(shop.get('/api/account/orders').json)==4
assert other.get('/api/account/orders').status_code==401
for outcome in ['failed','cancelled']:
 data=dict(items=items,customer=address,payment=dict(method='upi',outcome=outcome),request_key=str(uuid.uuid4()))
 assert shop.post('/api/orders',json=data,headers=ch).status_code==402
assert len(shop.get('/api/account/orders').json)==4
bad={**data,'payment':dict(method='cod',outcome='success')};assert shop.post('/api/orders',json=bad,headers=ch).status_code==400
bad={**data,'payment':dict(method='credit_card',outcome='success',cvv='123')};assert shop.post('/api/orders',json=bad,headers=ch).status_code==400
qr=shop.post('/api/test-payment-qr',json={'items':items,'coupon':'TINY10'},headers=ch);assert qr.status_code==200 and qr.mimetype=='image/svg+xml'
# Specific size inventory and restock deduplication.
p=next(p for p in admin.get('/api/admin/products').json if p['id']=='1')
p['sizes']=[dict(size=size,stock=stock,enabled=True) for size,stock in zip(m.SIZE_OPTIONS[:4],[12,3,0,8])]
assert admin.post('/api/admin/products',json=p,headers=ah).status_code==200
public=next(p for p in shop.get('/api/products').json if p['id']=='1')
assert [v['availability'] for v in public['sizes']]==['Available','Available','Restock soon','Available']
assert all('low_stock' not in v for v in public['sizes'])
assert shop.post('/api/restock',json=dict(id='1',size='6–9 months',phone='9876543210',qty=2),headers=ch).status_code==201
assert shop.post('/api/restock',json=dict(id='1',size='6–9 months',phone='9876543210',qty=4),headers=ch).status_code==201
requests=admin.get('/api/admin/restock').json;assert requests[0]['people']==1 and requests[0]['quantity']==4
assert admin.post('/api/admin/restock',json=dict(id=requests[0]['requests'][0]['id'],status='Closed'),headers=ah).status_code==200
assert admin.get('/api/admin/restock').json[0]['people']==0
p['sizes'].append(dict(size='One size',stock=5,enabled=True));assert admin.post('/api/admin/products',json=p,headers=ah).status_code==400
p['sizes']=[dict(size='One size',stock=5,enabled=True)];assert admin.post('/api/admin/products',json=p,headers=ah).status_code==200
assert next(p for p in shop.get('/api/products').json if p['id']=='1')['size_type']=='one'
o=orders[0]
assert admin.post('/api/admin/orders',json=dict(id=o['id'],status='Confirmed'),headers=ah).status_code==200
assert next(p for p in shop.get('/api/products').json if p['id']=='1')['stock']==3
analytics=admin.get('/api/admin/analytics').json;assert analytics['revenue']==0 and analytics['test_orders']==4
assert admin.post('/api/admin/orders',json=dict(id=o['id'],status='Cancelled'),headers=ah).status_code==200
assert next(p for p in shop.get('/api/products').json if p['id']=='1')['stock']==5
assert not any(x['id']=='1' and x['size']=='One size' for x in admin.get('/api/admin/analytics').json['low_stock'])
# Upload still works.
buf=io.BytesIO();Image.new('RGB',(20,20),'blue').save(buf,format='PNG');buf.seek(0)
u=admin.post('/api/admin/upload',data={'image':(buf,'sample.png')},headers=ah);assert u.status_code==200
assert shop.get(u.json['url']).mimetype=='image/jpeg'
# Consented active time and ordered funnel, not payment revenue.
sid='22222222-2222-2222-2222-222222222222'
for stage in ['home','product','cart','checkout','payment']:
 assert shop.post('/api/journey',json=dict(sid=sid,consent=True,stage=stage,kind='navigate')).status_code==202
 assert shop.post('/api/journey',json=dict(sid=sid,consent=True,stage=stage,kind='active',seconds=15)).status_code==202
assert shop.post('/api/journey',json=dict(sid=sid,consent=False,stage='home',kind='active',seconds=15)).status_code==400
assert shop.post('/api/journey',json=dict(sid=sid,consent=True,stage='home',kind='test_payment_success')).status_code==400
report=admin.get('/api/admin/journey').json;assert report['active_seconds']==75 and report['test_successes']==4
assert report['funnel'][-2]['count']==1 and report['funnel'][-1]['count']==0
# SEO and drafts escape owner content and block inactive products.
m.ROLE='store'
assert shop.get('/').status_code==200 and b'rel="canonical"' in shop.get('/').data
assert shop.get('/product/1').status_code==200 and b'application/ld+json' in shop.get('/product/1').data
assert shop.get('/sitemap.xml').status_code==200
assert b'Draft policies' in shop.get('/policies').data
assert b'Sitemap:' in shop.get('/robots.txt').data
assert admin.get('/api/admin/products').status_code==404
assert shop.post('/api/auth/logout',json={},headers=ch).status_code==200
assert shop.get('/api/account/orders').status_code==401
# Expiry and lockout are enforced server-side, even with a correctly shaped code.
for email,expire in [('expired@example.com',True),('attempts@example.com',False)]:
 r=other.get('/api/account');hdr={'X-Customer-CSRF':r.json['csrf']}
 r=other.post('/api/auth/request',json={'email':email},headers=hdr);assert r.status_code==201
 challenge=r.json['challenge']
 if expire:
  with app.app_context():
   token=db.session.get(m.OTP,challenge);token.expires=datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(seconds=1);db.session.commit()
  assert other.post('/api/auth/verify',json={'challenge':challenge,'code':codes[email]},headers=hdr).status_code==400
 else:
  wrong='999999' if codes[email]!='999999' else '000000'
  for _ in range(5):assert other.post('/api/auth/verify',json={'challenge':challenge,'code':wrong},headers=hdr).status_code==400
  assert other.post('/api/auth/verify',json={'challenge':challenge,'code':codes[email]},headers=hdr).status_code==400
print('PASS: OTP/CSRF/replay; four test payments; discount; idempotency; ownership; sizes/restock; delivery/settings; stock transitions; test revenue exclusion; uploads; consent/funnel; SEO; logout.')
