import os, uuid, io, base64, secrets, re
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, jsonify, session, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, func, text
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
from pathlib import Path
from runtime_config import load_config
load_config(Path(__file__).resolve().parent)
ROLE = os.getenv('APP_ROLE', 'store')
app = Flask(__name__, static_folder='static')
app.config['SESSION_COOKIE_NAME'] = 'tiny_tale_admin' if ROLE == 'admin' else 'tiny_tale_store'
app.config.update(SECRET_KEY=os.getenv('SECRET_KEY') or secrets.token_hex(32), SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL','sqlite:///tiny-tale.db').replace('postgres://','postgresql+psycopg://').replace('postgresql://','postgresql+psycopg://'), MAX_CONTENT_LENGTH=6*1024*1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict', SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE','false').lower()=='true', PERMANENT_SESSION_LIFETIME=timedelta(hours=8))
if os.getenv('RENDER') and (not os.getenv('SECRET_KEY') or not os.getenv('DATABASE_URL')): raise RuntimeError('Set SECRET_KEY and DATABASE_URL on Render')
if os.getenv('RENDER'):
 from werkzeug.middleware.proxy_fix import ProxyFix
 app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1)
db = SQLAlchemy(app)
class Product(db.Model):
 id=db.Column(db.String(36),primary_key=True); name=db.Column(db.String(100),nullable=False); category=db.Column(db.String(40)); description=db.Column(db.String(500)); price=db.Column(db.Integer,nullable=False); sale=db.Column(db.Integer,nullable=False); stock=db.Column(db.Integer,default=20); image=db.Column(db.Text); active=db.Column(db.Boolean,default=True)
 def data(self,private=False):
  result={k:getattr(self,k) for k in ('id','name','category','description','price','sale','stock','image','active')}
  result['sizes']=[]
  for v in db.session.scalars(select(ProductSize).where(ProductSize.product_id==self.id).order_by(ProductSize.position)):
   if not private and not v.enabled: continue
   row=dict(size=v.size,stock=v.stock,enabled=v.enabled,availability='Available' if v.stock>0 else 'Restock soon')
   if private: row['low_stock']=v.enabled and v.stock<5
   result['sizes'].append(row)
  enabled=[v for v in result['sizes'] if v['enabled']]
  result['size_type']='one' if len(enabled)==1 and enabled[0]['size']=='One size' else 'age'
  return result
SIZE_OPTIONS=['0–3 months','3–6 months','6–9 months','9–12 months','One size']
class ProductSize(db.Model):
 product_id=db.Column(db.String(36),db.ForeignKey('product.id'),primary_key=True)
 size=db.Column(db.String(30),primary_key=True)
 stock=db.Column(db.Integer,nullable=False,default=0)
 enabled=db.Column(db.Boolean,nullable=False,default=True)
 position=db.Column(db.Integer,default=0)
def sync_stock(p):
 db.session.flush()
 p.stock=sum(v.stock for v in db.session.scalars(select(ProductSize).where(ProductSize.product_id==p.id,ProductSize.enabled==True)))
class Media(db.Model):
 id=db.Column(db.String(36),primary_key=True); content=db.Column(db.Text,nullable=False)
class Event(db.Model):
 id=db.Column(db.Integer,primary_key=True); sid=db.Column(db.String(36)); kind=db.Column(db.String(30)); value=db.Column(db.String(120)); device=db.Column(db.String(20)); browser=db.Column(db.String(30)); os=db.Column(db.String(30)); source=db.Column(db.String(120)); created=db.Column(db.DateTime,default=lambda:datetime.now(timezone.utc))
class Order(db.Model):
 id=db.Column(db.String(36),primary_key=True); customer=db.Column(db.JSON); items=db.Column(db.JSON); total=db.Column(db.Integer); discount=db.Column(db.Integer); shipping=db.Column(db.Integer); coupon=db.Column(db.String(30)); status=db.Column(db.String(30),default='Enquiry'); created=db.Column(db.DateTime,default=lambda:datetime.now(timezone.utc))
 def data(self):
  data=dict(id=self.id,customer=self.customer,items=self.items,total=self.total,discount=self.discount,shipping=self.shipping,coupon=self.coupon,status=self.status,created=self.created.isoformat())
  meta=db.session.get(PurchaseMeta,self.id)
  if meta:data.update(number=meta.number,payment_mode=meta.mode,payment_method=meta.payment_method,login_discount=meta.login_discount,delivery=meta.eta)
  return data
class Coupon(db.Model):
 code=db.Column(db.String(30),primary_key=True); percent=db.Column(db.Integer); minimum=db.Column(db.Integer); active=db.Column(db.Boolean,default=True)
class Attempt(db.Model):
 key=db.Column(db.String(64),primary_key=True); count=db.Column(db.Integer,default=0); started=db.Column(db.DateTime,default=datetime.utcnow)
with app.app_context():
 guard=db.engine.connect() if db.engine.dialect.name=='postgresql' else None
 try:
  if guard: guard.execute(text('SELECT pg_advisory_lock(846301)'))
  db.create_all()
  # Same seed IDs on both services; conflicts during startup safely retry.
  names=['Front Open Jabla','Knot Jabla','Side Open Jabla','Bib','Nappies','Mittens','Cap','Booties','Bath Towel','Swaddle','Quilt Bed Spread']
  for i,n in enumerate(names):
   if not db.session.get(Product,str(i+1)):
    db.session.add(Product(id=str(i+1),name=n,category='Jablas' if i<3 else 'Bath & Sleep' if i>7 else 'Accessories',description='A gentle everyday essential for your little one. Demo item; confirm fabric, fit and care with us before ordering.',price=[349,299,329,199,249,149,199,199,599,449,999][i],sale=[279,239,259,149,199,119,159,159,479,359,799][i],stock=25,image=f'/static/images/product-{i}.png'))
  for code,p,m in [('TINY10',10,0),('BABY15',15,1500)]:
   if not db.session.get(Coupon,code): db.session.add(Coupon(code=code,percent=p,minimum=m))
  try: db.session.commit()
  except Exception:
   db.session.rollback()
   if db.session.scalar(select(func.count()).select_from(Product))<11: raise
  for p in db.session.scalars(select(Product)):
   if not db.session.scalar(select(ProductSize).where(ProductSize.product_id==p.id)):
    db.session.add(ProductSize(product_id=p.id,size='One size',stock=p.stock,enabled=True,position=4))
  db.session.commit()
 finally:
  if guard:
   guard.execute(text('SELECT pg_advisory_unlock(846301)')); guard.close()
@app.after_request
def headers(r):
 r.headers['X-Content-Type-Options']='nosniff'; r.headers['X-Frame-Options']='DENY'; r.headers['Referrer-Policy']='strict-origin-when-cross-origin'
 if ROLE=='admin':r.headers['X-Robots-Tag']='noindex, nofollow'
 if request.path.startswith('/api/'): r.headers['Cache-Control']='no-store'
 return r
@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(413)
def err(e): return jsonify(error=str(e.description)),e.code
@app.route('/')
def home(): return send_from_directory('static','admin.html' if ROLE=='admin' else 'index.html')
@app.get('/health')
def health(): db.session.execute(select(1)); return jsonify(ok=True,role=ROLE,version='5.0-admin-studio',admin_password_configured=bool(os.getenv('ADMIN_PASSWORD') or os.getenv('ADMIN_PASSWORD_HASH')) if ROLE=='admin' else None)
def admin(fn):
 @wraps(fn)
 def wrapped(*a,**k):
  if ROLE!='admin': abort(404)
  if not session.get('admin'): return jsonify(error='Please sign in'),401
  if request.method!='GET' and not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),session.get('csrf','!')): return jsonify(error='Session expired. Sign in again.'),403
  return fn(*a,**k)
 return wrapped
@app.route('/api/admin/login',methods=['POST'])
def login():
 if ROLE!='admin': abort(404)
 password=os.getenv('ADMIN_PASSWORD',''); hashed=os.getenv('ADMIN_PASSWORD_HASH','')
 if not password and not hashed and not (request.get_json(silent=True) or {}).get('username'): return jsonify(error='Set ADMIN_PASSWORD in server environment before signing in.'),503
 import hashlib
 key=hashlib.sha256(request.remote_addr.encode()).hexdigest(); a=db.session.get(Attempt,key)
 if not a: a=Attempt(key=key,count=0,started=datetime.utcnow()); db.session.add(a)
 if datetime.utcnow()-a.started>timedelta(minutes=15): a.count=0; a.started=datetime.utcnow()
 if a.count>=10: return jsonify(error='Too many attempts. Try again in 15 minutes.'),429
 d=request.get_json() or {}; entered=str(d.get('password',''))
 username=str(d.get('username','')).strip().lower()
 staff=db.session.scalar(select(Staff).where(Staff.username==username)) if username else None
 valid=(bool(staff and staff.active and check_password_hash(staff.password_hash,entered)) if username else (check_password_hash(hashed,entered) if hashed else bool(password) and secrets.compare_digest(password,entered)))
 if not valid: a.count+=1; db.session.commit(); return jsonify(error='Incorrect password'),401
 a.count=0; db.session.commit(); session.clear(); session.permanent=True; session['admin']=True; session['staff_id']=staff.id if staff else None; session['staff_version']=staff.version if staff else None; session['csrf']=secrets.token_hex(24); return jsonify(csrf=session['csrf'],user=staff_identity())
@app.get('/api/admin/session')
@admin
def logged(): return jsonify(csrf=session['csrf'],user=staff_identity())
@app.post('/api/admin/logout')
@admin
def logout(): session.clear(); return jsonify(ok=True)
@app.get('/api/products')
def products(): return jsonify([p.data() for p in db.session.scalars(select(Product).where(Product.active==True).order_by(Product.name))])
@app.route('/api/admin/products',methods=['GET','POST'])
@admin
def manage_products():
 if request.method=='GET': return jsonify([p.data(private=True) for p in db.session.scalars(select(Product).order_by(Product.name))])
 d=request.get_json() or {}
 try:
  name=str(d['name']).strip(); price=int(d['price']); sale=int(d['sale']); stock=0; image=str(d.get('image',''))
  sizes=d['sizes']
  if not isinstance(sizes,list) or not 1<=len(sizes)<=5: raise ValueError()
  seen=set()
  for v in sizes:
   if v.get('size') not in SIZE_OPTIONS or v['size'] in seen or type(v.get('stock')) is not int or not 0<=v['stock']<=100000 or type(v.get('enabled',True)) is not bool: raise ValueError()
   seen.add(v['size'])
  enabled=[v for v in sizes if v.get('enabled',True)]
  if not enabled or (any(v['size']=='One size' for v in enabled) and len(enabled)>1): raise ValueError()
  if not name or len(name)>100 or price<1 or not 0<sale<=price or stock<0 or stock>100000 or price>1000000: raise ValueError()
  if not (image.startswith('/static/images/') or re.fullmatch(r'/media/[a-f0-9-]+',image)): raise ValueError('Upload an image first')
 except (KeyError,ValueError,TypeError) as e: return jsonify(error='Enter valid name, prices, stock and an uploaded image.'),400
 p=db.session.scalar(select(Product).where(Product.id==d.get('id')).with_for_update()) if d.get('id') else Product(id=str(uuid.uuid4()))
 if p is None: abort(404)
 for k,v in dict(name=name,price=price,sale=sale,stock=stock,image=image,category=str(d.get('category','Accessories'))[:40],description=str(d.get('description',''))[:500],active=bool(d.get('active',True))).items(): setattr(p,k,v)
 db.session.add(p); db.session.flush()
 for old in db.session.scalars(select(ProductSize).where(ProductSize.product_id==p.id)): old.enabled=False
 for v in sizes:
  row=db.session.get(ProductSize,(p.id,v['size'])) or ProductSize(product_id=p.id,size=v['size'])
  row.stock=v['stock']; row.enabled=v.get('enabled',True); row.position=SIZE_OPTIONS.index(v['size']); db.session.add(row)
 sync_stock(p); db.session.commit(); return jsonify(p.data(private=True))
@app.post('/api/admin/upload')
@admin
def upload():
 f=request.files.get('image')
 if not f: return jsonify(error='Choose an image'),400
 try:
  im=Image.open(f); im.load(); im.thumbnail((1200,1200)); im=im.convert('RGB'); buf=io.BytesIO(); im.save(buf,format='JPEG',quality=85)
 except Exception: return jsonify(error='Use a valid JPG, PNG or WebP image, maximum 5 MB.'),400
 m=Media(id=str(uuid.uuid4()),content=base64.b64encode(buf.getvalue()).decode()); db.session.add(m); db.session.commit(); return jsonify(url='/media/'+m.id)
@app.get('/media/<id>')
def media(id):
 m=db.get_or_404(Media,id); return app.response_class(base64.b64decode(m.content),mimetype='image/jpeg',headers={'Cache-Control':'public,max-age=86400'})
def quote(d,lock=False):
 lines=[]; subtotal=0; seen=set()
 if not isinstance(d.get('items'),list) or not 1<=len(d['items'])<=50: raise ValueError('Your cart is empty')
 for item in d['items']:
  pid=str(item.get('id','')); q=int(item.get('qty',0))
  size=str(item.get('size','')); key=(pid,size)
  if key in seen: raise ValueError('Duplicate cart item')
  seen.add(key); stmt=select(Product).where(Product.id==pid)
  if lock: stmt=stmt.with_for_update()
  p=db.session.scalar(stmt)
  v=db.session.get(ProductSize,(pid,size))
  if not p or not p.active or not v or not v.enabled or q<1 or q>v.stock: raise ValueError('An item is unavailable or exceeds stock. Refresh your cart.')
  lines.append(dict(id=p.id,name=p.name,size=size,qty=q,price=p.sale)); subtotal+=p.sale*q
 code=str(d.get('coupon','')).strip().upper(); discount=0
 if code:
  c=db.session.get(Coupon,code)
  if not c or not c.active: raise ValueError('Invalid or inactive coupon')
  if subtotal<c.minimum: raise ValueError(f'Coupon needs a subtotal of ₹{c.minimum}')
  discount=(subtotal*c.percent+50)//100
 shipping=0 if subtotal>=999 else 69
 login_discount=((subtotal-discount)*5+50)//100 if current_customer() else 0
 return dict(items=lines,subtotal=subtotal,discount=discount,login_discount=login_discount,shipping=shipping,total=subtotal-discount-login_discount+shipping,coupon=code)
@app.post('/api/quote')
def pricing():
 try: return jsonify(quote(request.get_json() or {}))
 except (ValueError,TypeError): return jsonify(error='Cart or coupon invalid. Check coupon minimum and available stock.'),400
@app.post('/api/orders')
def order():
 d=request.get_json() or {}; c=d.get('customer',{})
 if not isinstance(c,dict) or not all(str(c.get(k,'')).strip() for k in ['name','phone','address','city','state','pin']) or not re.fullmatch(r'[6-9]\d{9}',str(c.get('phone',''))) or not re.fullmatch(r'\d{6}',str(c.get('pin',''))): return jsonify(error='Complete your address, 10-digit Indian mobile number and 6-digit PIN.'),400
 try: q=quote(d)
 except (ValueError,TypeError) as e: return jsonify(error=str(e)),400
 # Enquiries do not reserve inventory or claim payment. Stock is deducted atomically only when admin confirms.
 o=Order(id=str(uuid.uuid4()),customer={k:str(c[k])[:500] for k in ['name','phone','address','city','state','pin']},items=q['items'],total=q['total'],discount=q['discount'],shipping=q['shipping'],coupon=q['coupon']); db.session.add(o); db.session.commit(); return jsonify(o.data()),201
@app.route('/api/admin/orders',methods=['GET','POST'])
@admin
def orders():
 if request.method=='GET': return jsonify([o.data() for o in db.session.scalars(select(Order).order_by(Order.created.desc()).limit(300))])
 d=request.get_json() or {}; o=db.session.scalar(select(Order).where(Order.id==d.get('id')).with_for_update())
 if not o: abort(404)
 status=d.get('status'); allowed={'Enquiry':['Confirmed','Cancelled'],'Confirmed':['Shipped','Cancelled'],'Shipped':['Delivered'],'Delivered':[],'Cancelled':[]}
 if status not in allowed.get(o.status,[]): return jsonify(error='Invalid status change'),400
 if status=='Confirmed' or (status=='Cancelled' and o.status=='Confirmed'):
  for item in sorted(o.items,key=lambda x:(x['id'],x.get('size','One size'))):
   p=db.session.scalar(select(Product).where(Product.id==item['id']).with_for_update())
   v=db.session.scalar(select(ProductSize).where(ProductSize.product_id==item['id'],ProductSize.size==item.get('size','One size')).with_for_update())
   if not p or not v or (status=='Confirmed' and (not p.active or not v.enabled or v.stock<item['qty'])):
    db.session.rollback(); return jsonify(error='Insufficient stock for the ordered size. Review the enquiry.'),409
   v.stock+=item['qty'] if status=='Cancelled' else -item['qty']
   sync_stock(p)
 o.status=status; db.session.commit(); return jsonify(o.data())
@app.route('/api/admin/coupons',methods=['GET','POST'])
@admin
def coupons():
 if request.method=='GET': return jsonify([dict(code=c.code,percent=c.percent,minimum=c.minimum,active=c.active) for c in db.session.scalars(select(Coupon))])
 d=request.get_json() or {}
 try:
  code=str(d['code']).strip().upper(); percent=int(d['percent']); minimum=int(d['minimum'])
  if not re.fullmatch(r'[A-Z0-9]{3,30}',code) or not 1<=percent<=80 or minimum<0: raise ValueError()
 except (KeyError,ValueError,TypeError): return jsonify(error='Use 3–30 letters/numbers, discount 1–80%, and minimum ≥ 0.'),400
 c=db.session.get(Coupon,code) or Coupon(code=code); c.percent=percent; c.minimum=minimum; c.active=bool(d.get('active',True)); db.session.add(c); db.session.commit(); return jsonify(ok=True)
@app.post('/api/events')
def events():
 d=request.get_json() or {}
 if d.get('consent') is not True: return jsonify(error='Analytics consent required'),400
 if d.get('kind') not in ['visit','view','search','add_cart','buy_now','checkout','coupon','whatsapp','order_enquiry','favourite','banner_click']: return jsonify(error='Invalid event'),400
 sid=str(d.get('sid',''))
 if not re.fullmatch(r'[a-f0-9-]{36}',sid): return jsonify(error='Invalid session'),400
 count=db.session.scalar(select(func.count()).select_from(Event).where(Event.sid==sid,Event.created>datetime.now(timezone.utc)-timedelta(hours=1)))
 if count>=200: return jsonify(ok=True),202
 ua=request.user_agent.string.lower(); device='Tablet' if 'ipad' in ua or ('android' in ua and 'mobile' not in ua) else 'Mobile' if 'mobile' in ua or 'iphone' in ua else 'Desktop'
 browser=next((n for key,n in [('edg','Edge'),('firefox','Firefox'),('chrome','Chrome'),('safari','Safari')] if key in ua),'Other'); osname=next((n for key,n in [('android','Android'),('iphone','iOS'),('ipad','iOS'),('windows','Windows'),('mac','macOS'),('linux','Linux')] if key in ua),'Other')
 from urllib.parse import urlparse
 source=urlparse(str(d.get('source',''))).hostname or 'Direct'; value=str(d.get('value',''))[:120]
 db.session.add(Event(sid=sid,kind=d['kind'],value=value,device=device,browser=browser,os=osname,source=source[:120])); db.session.commit(); return jsonify(ok=True),202
@app.get('/api/admin/analytics')
@admin
def analytics():
 try: days=min(365,max(1,int(request.args.get('days',30))))
 except ValueError: days=30
 since=datetime.now(timezone.utc)-timedelta(days=days)
 def group(col,kind=None):
  stmt=select(col,func.count()).where(Event.created>=since)
  if kind: stmt=stmt.where(Event.kind==kind)
  else: stmt=stmt.where(Event.kind=='visit')
  return [{'label':a or 'Unknown','count':b} for a,b in db.session.execute(stmt.group_by(col).order_by(func.count().desc()).limit(20))]
 rows=list(db.session.scalars(select(Order).where(Order.created>=since))); confirmed=[o for o in rows if o.status in ['Confirmed','Shipped','Delivered'] and not (db.session.get(PurchaseMeta,o.id) and db.session.get(PurchaseMeta,o.id).mode=='test')]
 return jsonify(days=days,sessions=db.session.scalar(select(func.count(func.distinct(Event.sid))).where(Event.created>=since)),events=[{'label':a,'count':b} for a,b in db.session.execute(select(Event.kind,func.count()).where(Event.created>=since).group_by(Event.kind))],products=group(Event.value,'view'),searches=group(Event.value,'search'),devices=group(Event.device),browsers=group(Event.browser),systems=group(Event.os),sources=group(Event.source),enquiries=len(rows),test_orders=sum(bool(db.session.get(PurchaseMeta,o.id) and db.session.get(PurchaseMeta,o.id).mode=='test') for o in rows),confirmed=len(confirmed),revenue=sum(o.total for o in confirmed),low_stock=[dict(id=p.id,name=p.name,size=v.size,stock=v.stock,status='Out of stock' if v.stock==0 else 'Low stock') for p,v in db.session.execute(select(Product,ProductSize).join(ProductSize).where(Product.active==True,ProductSize.enabled==True,ProductSize.stock<5).order_by(Product.name,ProductSize.position))])
import sys
from features import install
install(sys.modules[__name__])
from enhancements import install as install_enhancements
install_enhancements(sys.modules[__name__])
from management import install as install_management
install_management(sys.modules[__name__])
if __name__=='__main__': app.run(host='127.0.0.1',port=int(os.getenv('PORT','5000')))
