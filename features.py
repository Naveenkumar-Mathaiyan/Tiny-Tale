"""Additive v3 features. No existing table columns are changed."""
import os, re, uuid, secrets, hashlib, json, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from functools import wraps
from urllib.parse import urlparse
from flask import request, jsonify, session, abort, render_template_string
from sqlalchemy import select, func, text
from werkzeug.security import generate_password_hash, check_password_hash

def install(m):
 app,db=m.app,m.db
 Product,Variant,Order=m.Product,m.ProductSize,m.Order
 now=lambda:datetime.now(timezone.utc).replace(tzinfo=None)
 class Customer(db.Model):
  id=db.Column(db.String(36),primary_key=True); email=db.Column(db.String(254),unique=True,nullable=False); created=db.Column(db.DateTime,default=now)
 class OTP(db.Model):
  id=db.Column(db.String(36),primary_key=True); email=db.Column(db.String(254),index=True); digest=db.Column(db.Text); ip=db.Column(db.String(64),index=True); created=db.Column(db.DateTime,default=now); expires=db.Column(db.DateTime); attempts=db.Column(db.Integer,default=0); used=db.Column(db.Boolean,default=False); delivered=db.Column(db.Boolean,default=False)
 class Counter(db.Model):
  key=db.Column(db.String(20),primary_key=True); value=db.Column(db.Integer,nullable=False,default=0)
 class PurchaseMeta(db.Model):
  order_id=db.Column(db.String(36),db.ForeignKey('order.id'),primary_key=True); number=db.Column(db.String(30),unique=True); customer_id=db.Column(db.String(36),index=True); request_key=db.Column(db.String(36),unique=True); fingerprint=db.Column(db.String(64)); payment_method=db.Column(db.String(30)); mode=db.Column(db.String(10),default='legacy'); login_discount=db.Column(db.Integer,default=0); eta=db.Column(db.JSON)
 class Setting(db.Model):
  key=db.Column(db.String(30),primary_key=True); value=db.Column(db.JSON)
 class Restock(db.Model):
  id=db.Column(db.String(36),primary_key=True); customer_id=db.Column(db.String(36),index=True); product_id=db.Column(db.String(36),index=True); size=db.Column(db.String(30)); phone=db.Column(db.String(10)); qty=db.Column(db.Integer); status=db.Column(db.String(20),default='Open'); created=db.Column(db.DateTime,default=now)
  __table_args__=(db.UniqueConstraint('customer_id','product_id','size'),)
 class Journey(db.Model):
  id=db.Column(db.Integer,primary_key=True); sid=db.Column(db.String(36),index=True); stage=db.Column(db.String(30)); kind=db.Column(db.String(30)); seconds=db.Column(db.Integer,default=0); detail=db.Column(db.String(120)); created=db.Column(db.DateTime,default=now,index=True)
 m.PurchaseMeta=PurchaseMeta
 m.Customer=Customer;m.OTP=OTP;m.Counter=Counter;m.Restock=Restock;m.Journey=Journey;m.Setting=Setting
 defaults=dict(about='Tiny Tale brings together newborn clothing and everyday baby essentials. Explore our collection and choose the sizes that suit your little one.',address='',factory_address='',map_url='',factory_map_url='',dispatch_pin='',processing_days=1,same_pin_min=1,same_pin_max=3,near_min=2,near_max=4,other_min=4,other_max=8,return_policy='Sample policy for testing: contact Tiny Tale with your order number to request a return. Eligibility, request period, item condition and return shipping terms must be confirmed by the store before live selling.',refund_policy='Sample policy for testing: approved refunds are returned through the original payment method after review. Refund timing and deductions must be confirmed by the store. Test payments do not collect money and cannot generate actual refunds.',policies_published=False)
 def settings():
  row=db.session.get(Setting,'business');return {**defaults,**(row.value if row else {})}
 def india_date(dt): return (dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt).astimezone(timezone(timedelta(hours=5,minutes=30)))
 def number(dt,counter):
  config=db.session.get(Setting,'numbering');cfg=config.value if config else {}
  while True:
   counter.value+=1
   candidate=cfg.get('prefix','')+(india_date(dt).strftime('%y%m%d') if cfg.get('date',True) else '')+str(counter.value).zfill(cfg.get('padding',4))
   if not db.session.scalar(select(PurchaseMeta).where(PurchaseMeta.number==candidate)):return candidate
 with app.app_context():
  guard=db.engine.connect() if db.engine.dialect.name=='postgresql' else None
  try:
   if guard:guard.execute(text('SELECT pg_advisory_lock(846302)'))
   db.create_all()
   counter=db.session.get(Counter,'orders')
   if not counter:counter=Counter(key='orders',value=0);db.session.add(counter)
   for o in db.session.scalars(select(Order).order_by(Order.created,Order.id)):
    if not db.session.get(PurchaseMeta,o.id):db.session.add(PurchaseMeta(order_id=o.id,number=number(o.created,counter),mode='legacy',login_discount=0))
   if not db.session.get(Setting,'business'):db.session.add(Setting(key='business',value=defaults))
   db.session.commit()
  finally:
   if guard:guard.execute(text('SELECT pg_advisory_unlock(846302)'));guard.close()
 def current():return db.session.get(Customer,session.get('customer_id')) if session.get('customer_id') else None
 m.current_customer=current
 def protect(fn):
  @wraps(fn)
  def inner(*a,**k):
   if request.method!='GET' and not secrets.compare_digest(request.headers.get('X-Customer-CSRF',''),session.get('customer_csrf','!')):return jsonify(error='Refresh the page and try again.'),403
   return fn(*a,**k)
  return inner
 def need_customer(fn):
  @wraps(fn)
  @protect
  def inner(*a,**k):
   if not current():return jsonify(error='Verify your email to continue.'),401
   return fn(*a,**k)
  return inner
 @app.get('/api/account')
 def account():
  session.setdefault('customer_csrf',secrets.token_hex(24));c=current()
  return jsonify(customer=dict(email=c.email) if c else None,csrf=session['customer_csrf'],otp_ready=bool(os.getenv('BREVO_API_KEY','').strip() and os.getenv('BREVO_SENDER_EMAIL','').strip()))
 def send_otp(email,code):
  key=os.getenv('BREVO_API_KEY','').strip();sender=os.getenv('BREVO_SENDER_EMAIL','').strip()
  if not key or not sender:raise RuntimeError('Email login is not configured. Please contact the store.')
  if any(ord(c) in [10,13,34,39] for c in key) or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',sender):
   m.record_email_status(False,'EMAIL_CONFIG: Invalid key formatting or sender email. In Render enter the raw API key without quotes or line breaks and a valid sender email.')
   raise RuntimeError('Email delivery unavailable (EMAIL_CONFIG). Please contact Tiny Tale.')
  body=dict(sender=dict(name=os.getenv('BREVO_SENDER_NAME','Tiny Tale'),email=sender),to=[dict(email=email)],subject='Your Tiny Tale login code',textContent=f'Your Tiny Tale verification code is {code}. It expires in 5 minutes. If you did not request it, ignore this email. Never share this code.')
  body['htmlContent']=f'<div style="font-family:Arial;max-width:520px;margin:auto;padding:32px;color:#163e50"><h1>Tiny Tale</h1><h2>Your login code</h2><p style="font-size:36px;letter-spacing:8px">{code}</p><p>This code can only be used once and expires in 5 minutes.</p><p>If you did not request this code, ignore this email. Never share it.</p></div>'
  req=urllib.request.Request('https://api.brevo.com/v3/smtp/email',data=json.dumps(body).encode(),headers={'api-key':key,'Content-Type':'application/json','Accept':'application/json'},method='POST')
  try:
   with urllib.request.urlopen(req,timeout=12) as response:
    if response.status not in (200,201,202):raise RuntimeError('Email delivery is temporarily unavailable.')
  except urllib.error.HTTPError as exc:
   try:provider=json.loads(exc.read(8192).decode('utf-8','replace'))
   except (ValueError,TypeError):provider={}
   if not isinstance(provider,dict):provider={}
   hint=str(provider.get('message','')).lower();code=str(provider.get('code',''))
   if not re.fullmatch(r'[a-z_]{1,50}',code):code='unknown'
   if 'ip' in hint and any(x in hint for x in ['unauthor','not author','block','whitelist','unknown','unrecognised','unrecognized']):
    ref='EMAIL_IP';guidance='Brevo blocked the server IP. Review Brevo SMTP & API → Authorized IPs and the unknown-IP verification email. Authorize the Render outbound IP shown by Brevo.'
   elif 'sender' in hint or ('from' in hint and 'email' in hint):
    ref='EMAIL_SENDER';guidance='Brevo rejected the sender. Verify the exact BREVO_SENDER_EMAIL in Brevo → Senders, and ensure transactional sending is active.'
   elif 'credit' in hint or 'quota' in hint or 'limit' in hint or exc.code==429:
    ref='EMAIL_LIMIT';guidance='Brevo reported a quota/rate/credit limit. Check account credits and sending limits, then retry after the limit resets.'
   elif exc.code==401 or code=='unauthorized':
    ref='EMAIL_AUTH';guidance='Brevo rejected API authentication. Set a valid active API key (not an SMTP key) in the customer Render service. Check Brevo account/IP verification and save/deploy the environment.'
   elif exc.code==403 or code=='permission_denied':
    ref='EMAIL_PERMISSION';guidance='Brevo denied sending permission. Check transactional account activation, API permissions and Authorized IPs.'
   else:
    ref='EMAIL_PROVIDER';guidance='Brevo rejected this request. Review Brevo Transactional logs, sender verification and account status.'
   m.record_email_status(False,f'{ref}: HTTP {exc.code}; provider code {code}. {guidance}')
   raise RuntimeError(f'Email delivery unavailable ({ref}). Please contact Tiny Tale or try again later.') from None
  except (urllib.error.URLError,TimeoutError):
   m.record_email_status(False,'Brevo connection timeout or network error.')
   raise RuntimeError('Email delivery timed out. Please try again shortly.') from None
  m.record_email_status(True,'Brevo accepted the login email. Check Transactional logs if delivery is delayed.')
 m.send_otp=send_otp
 m.brevo_send_otp=send_otp
 @app.post('/api/auth/request')
 @protect
 def request_otp():
  d=request.get_json(silent=True) or {};email=str(d.get('email','')).strip().lower()
  if not os.getenv('BREVO_API_KEY','').strip() or not os.getenv('BREVO_SENDER_EMAIL','').strip():
   m.record_email_status(False,'Missing BREVO_API_KEY or BREVO_SENDER_EMAIL on customer store service.')
   return jsonify(error='Email login is temporarily unavailable. The store needs to finish email setup.'),503
  if len(email)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):return jsonify(error='Enter a valid email address.'),400
  ip=hashlib.sha256((request.remote_addr or 'unknown').encode()).hexdigest();since=now()-timedelta(minutes=15)
  # A transaction-scoped lock serializes concurrent requests from one IP in PostgreSQL.
  if db.engine.dialect.name=='postgresql':db.session.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':int(ip[:15],16)})
  recent=list(db.session.scalars(select(OTP).where(OTP.email==email,OTP.created>=since)))
  ip_count=db.session.scalar(select(func.count()).select_from(OTP).where(OTP.ip==ip,OTP.created>=since))
  if len(recent)>=3 or ip_count>=10:return jsonify(error='Too many code requests. Try again in 15 minutes.'),429
  if recent and max(o.created for o in recent)>now()-timedelta(seconds=60):return jsonify(error='Please wait 60 seconds before requesting another code.'),429
  code=str(secrets.randbelow(1000000)).zfill(6)
  otp=OTP(id=str(uuid.uuid4()),email=email,ip=ip,digest=generate_password_hash(code),expires=now()+timedelta(minutes=5),attempts=0,used=False,delivered=False)
  db.session.add(otp);db.session.commit()
  try:m.send_otp(email,code)
  except RuntimeError as e:return jsonify(error=str(e)),503
  otp.delivered=True;db.session.commit();return jsonify(challenge=otp.id,message='Check your email for the six-digit code.',resend_seconds=60),201
 @app.post('/api/auth/verify')
 @protect
 def verify_otp():
  d=request.get_json(silent=True) or {};otp=db.session.scalar(select(OTP).where(OTP.id==str(d.get('challenge',''))).with_for_update());code=str(d.get('code',''))
  if not otp or not otp.delivered or otp.used or otp.expires<=now() or otp.attempts>=5:return jsonify(error='Code expired or unavailable. Request a new code.'),400
  otp.attempts+=1
  if not re.fullmatch(r'\d{6}',code) or not check_password_hash(otp.digest,code):db.session.commit();return jsonify(error='Incorrect code. Check your email and try again.'),400
  if db.engine.dialect.name=='postgresql':db.session.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':int(hashlib.sha256(otp.email.encode()).hexdigest()[:15],16)})
  c=db.session.scalar(select(Customer).where(Customer.email==otp.email))
  if not c:c=Customer(id=str(uuid.uuid4()),email=otp.email);db.session.add(c)
  otp.used=True;db.session.commit()
  session.clear();session.permanent=True;session['customer_id']=c.id;session['customer_csrf']=secrets.token_hex(24)
  return jsonify(customer=dict(email=c.email),csrf=session['customer_csrf'])
 @app.post('/api/auth/logout')
 @need_customer
 def customer_logout():session.clear();return jsonify(ok=True)
 @app.get('/api/account/orders')
 @need_customer
 def customer_orders():return jsonify([o.data() for o in db.session.scalars(select(Order).join(PurchaseMeta).where(PurchaseMeta.customer_id==current().id).order_by(Order.created.desc()).limit(100))])
 @app.get('/api/business')
 def business():return jsonify(settings())
 def estimate(pin):
  s=settings();origin=s['dispatch_pin']
  if not re.fullmatch(r'[1-9]\d{5}',str(pin)):raise ValueError('Enter a valid six-digit PIN code.')
  if not origin:return dict(available=False,message='Delivery estimate will be available after the store configures its dispatch location.')
  prefix='same_pin' if pin==origin else 'near' if pin[:3]==origin[:3] else 'other'
  today=india_date(now()).date();processing=s['processing_days']
  return dict(available=True,earliest=(today+timedelta(days=processing+s[prefix+'_min'])).isoformat(),latest=(today+timedelta(days=processing+s[prefix+'_max'])).isoformat(),message='Indicative delivery estimate; subject to seller confirmation and courier serviceability.')
 @app.get('/api/delivery')
 def delivery():
  try:return jsonify(estimate(request.args.get('pin','')))
  except ValueError as e:return jsonify(error=str(e)),400
 @app.route('/api/admin/business',methods=['GET','POST'])
 @m.admin
 def manage_business():
  if request.method=='GET':return jsonify(settings())
  d=request.get_json(silent=True) or {};s=settings()
  try:
   for key in ['about','address','factory_address','return_policy','refund_policy']:
    if key in d:s[key]=str(d[key]).strip()[:6000]
   for key in ['map_url','factory_map_url']:
    url=str(d.get(key,s[key])).strip();parts=urlparse(url)
    if url and (parts.scheme!='https' or not parts.hostname or not(parts.hostname in ['maps.app.goo.gl','maps.google.com','www.google.com','google.com','goo.gl'])):raise ValueError('Use an HTTPS Google Maps link.')
    s[key]=url
   pin=str(d.get('dispatch_pin',s['dispatch_pin'])).strip()
   if pin and not re.fullmatch(r'[1-9]\d{5}',pin):raise ValueError('Enter a valid dispatch PIN.')
   s['dispatch_pin']=pin
   for key in ['processing_days','same_pin_min','same_pin_max','near_min','near_max','other_min','other_max']:
    val=d.get(key,s[key]);val=int(val)
    if not 0<=val<=60:raise ValueError('Delivery days must be between 0 and 60.')
    s[key]=val
   for prefix in ['same_pin','near','other']:
    if s[prefix+'_min']>s[prefix+'_max']:raise ValueError('Minimum delivery days must not exceed maximum.')
   s['policies_published']=d.get('policies_published',s['policies_published']) is True
   if s['policies_published'] and (not s['return_policy'] or not s['refund_policy']):raise ValueError('Enter both approved policies before publishing.')
  except (ValueError,TypeError) as e:return jsonify(error=str(e)),400
  row=db.session.get(Setting,'business');row.value=s;db.session.commit();return jsonify(s)
 @app.post('/api/restock')
 @need_customer
 def notify():
  d=request.get_json(silent=True) or {};pid=str(d.get('id',''));size=str(d.get('size',''));p=db.session.get(Product,pid);v=db.session.get(Variant,(pid,size));phone=str(d.get('phone','')).strip();qty=d.get('qty')
  if not p or not p.active or not v or not v.enabled or v.stock!=0:return jsonify(error='Choose a sold-out size. This item may already be available.'),409
  if type(qty) is not int or not 1<=qty<=1000 or not re.fullmatch(r'[6-9]\d{9}',phone):return jsonify(error='Enter quantity 1–1000 and a 10-digit Indian WhatsApp number.'),400
  c=current()
  if db.engine.dialect.name=='postgresql':db.session.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':int(hashlib.sha256((c.id+pid+size).encode()).hexdigest()[:15],16)})
  r=db.session.scalar(select(Restock).where(Restock.customer_id==c.id,Restock.product_id==pid,Restock.size==size))
  if not r:r=Restock(id=str(uuid.uuid4()),customer_id=c.id,product_id=pid,size=size);db.session.add(r)
  r.phone=phone;r.qty=qty;r.status='Open';r.created=now();db.session.commit();return jsonify(message='Your request is saved. Tiny Tale can see it in the restock list.'),201
 @app.route('/api/admin/restock',methods=['GET','POST'])
 @m.admin
 def restock_list():
  if request.method=='POST':
   d=request.get_json(silent=True) or {};r=db.get_or_404(Restock,d.get('id'))
   if d.get('status') not in ['Open','Contacted','Closed']:return jsonify(error='Invalid request status.'),400
   r.status=d['status'];db.session.commit();return jsonify(ok=True)
  rows=list(db.session.execute(select(Restock,Product,Customer).join(Product,Product.id==Restock.product_id).join(Customer,Customer.id==Restock.customer_id).order_by(Restock.created.desc())))
  groups={}
  for r,p,c in rows:
   key=(p.id,r.size)
   group=groups.setdefault(key,dict(product_id=p.id,name=p.name,size=r.size,people=0,quantity=0,requests=[]))
   if r.status!='Closed':group['people']+=1;group['quantity']+=r.qty
   group['requests'].append(dict(id=r.id,email=c.email,phone=r.phone,qty=r.qty,status=r.status,created=r.created.isoformat()))
  return jsonify(list(groups.values()))
 stages=['home','product','cart','checkout','payment','success']
 allowed=['navigate','active','coupon_attempt','coupon_success','coupon_error','payment_selected','test_payment_failed','test_payment_cancelled','checkout_error','login_success']
 def record(sid,stage,kind,seconds=0,detail=''):
  db.session.add(Journey(sid=sid,stage=stage,kind=kind,seconds=seconds,detail=str(detail)[:120]))
 @app.post('/api/journey')
 def journey():
  d=request.get_json(silent=True) or {};sid=str(d.get('sid',''));stage=d.get('stage');kind=d.get('kind');seconds=d.get('seconds',0)
  if d.get('consent') is not True or not re.fullmatch(r'[a-f0-9-]{36}',sid) or stage not in stages or kind not in allowed or type(seconds) is not int or not 0<=seconds<=30:return jsonify(error='Invalid analytics event.'),400
  if db.session.scalar(select(func.count()).select_from(Journey).where(Journey.sid==sid,Journey.created>=now()-timedelta(hours=1)))>=500:return jsonify(ok=True),202
  record(sid,stage,kind,seconds if kind=='active' else 0,d.get('detail',''));db.session.commit();return jsonify(ok=True),202
 @app.get('/api/admin/journey')
 @m.admin
 def journey_report():
  try:days=min(365,max(1,int(request.args.get('days',30))))
  except ValueError:days=30
  rows=list(db.session.scalars(select(Journey).where(Journey.created>=now()-timedelta(days=days)).order_by(Journey.created,Journey.id)))
  journeys={};duration={};errors={}
  for r in rows:
   j=journeys.setdefault(r.sid,dict(sid=r.sid[:8],started=(r.created+timedelta(hours=5,minutes=30)).isoformat(),stages=[],seconds=0,last=r.stage))
   if r.kind!='active' and (r.stage!='success' or r.kind=='test_payment_success') and (not j['stages'] or j['stages'][-1]!=r.stage):j['stages'].append(r.stage)
   j['seconds']+=r.seconds;j['last']=r.stage;duration[r.stage]=duration.get(r.stage,0)+r.seconds
   if r.kind.endswith('error') or r.kind.endswith('failed') or r.kind.endswith('cancelled'):errors[r.kind]=errors.get(r.kind,0)+1
  # Ordered paths; skipping required stages is reported separately in reach.
  eligible={sid:-1 for sid in journeys};funnel=[]
  for stage in stages:
   matched={}
   for sid,index in eligible.items():
    try:matched[sid]=journeys[sid]['stages'].index(stage,index+1)
    except ValueError:pass
   eligible=matched;funnel.append(dict(stage=stage,count=len(eligible)))
  return jsonify(sessions=len(journeys),active_seconds=sum(j['seconds'] for j in journeys.values()),average_seconds=round(sum(j['seconds'] for j in journeys.values())/max(1,len(journeys))),funnel=funnel,reach=[dict(stage=s,count=sum(s in j['stages'] for j in journeys.values())) for s in stages],duration=[dict(stage=k,seconds=v) for k,v in duration.items()],errors=[dict(kind=k,count=v) for k,v in errors.items()],recent=list(journeys.values())[-50:][::-1],test_successes=sum(r.kind=='test_payment_success' for r in rows))
 def checkout():
  c=current();d=request.get_json(silent=True) or {};address=d.get('customer',{});payment=d.get('payment',{});key=str(d.get('request_key',''))
  if not isinstance(address,dict) or not all(str(address.get(k,'')).strip() for k in ['name','phone','address','city','state','pin']) or not re.fullmatch(r'[6-9]\d{9}',str(address.get('phone',''))) or not re.fullmatch(r'[1-9]\d{5}',str(address.get('pin',''))):return jsonify(error='Complete the address, mobile number and PIN.'),400
  if not re.fullmatch(r'[a-f0-9-]{36}',key) or not isinstance(payment,dict) or payment.get('method') not in ['credit_card','debit_card','upi','net_banking'] or payment.get('outcome') not in ['success','failed','cancelled']:return jsonify(error='Choose a valid test payment method and outcome.'),400
  # Never accept card numbers, CVV, bank passwords or live UPI credentials.
  if set(payment)-{'method','outcome'}:return jsonify(error='Only test payment choices are accepted. Do not send payment credentials.'),400
  payload=dict(items=d.get('items'),coupon=d.get('coupon',''),customer=address,payment=payment,expected_total=d.get('expected_total'))
  fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
  if db.engine.dialect.name=='postgresql':db.session.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':int(hashlib.sha256(key.encode()).hexdigest()[:15],16)})
  old=db.session.scalar(select(PurchaseMeta).where(PurchaseMeta.request_key==key))
  if old:
   if old.customer_id!=c.id or old.fingerprint!=fingerprint:return jsonify(error='Checkout request changed. Start a new checkout.'),409
   return jsonify(db.session.get(Order,old.order_id).data()),200
  if payment['outcome']!='success':return jsonify(error='Test payment '+payment['outcome']+'. No order or charge was created.'),402
  try:q=m.quote(d);eta=estimate(str(address['pin']))
  except (ValueError,TypeError) as e:return jsonify(error=str(e)),400
  if type(d.get('expected_total')) is not int or d['expected_total']!=q['total']:return jsonify(error='Your order total changed. Review the order again before continuing.'),409
  o=Order(id=str(uuid.uuid4()),customer={**{k:str(address[k]).strip()[:500] for k in ['name','phone','address','city','state','pin']},'email':c.email},items=q['items'],total=q['total'],discount=q['discount']+q['login_discount'],shipping=q['shipping'],coupon=q['coupon'],status='Enquiry')
  counter=db.session.scalar(select(Counter).where(Counter.key=='orders').with_for_update())
  meta=PurchaseMeta(order_id=o.id,number=number(now(),counter),customer_id=c.id,request_key=key,fingerprint=fingerprint,payment_method=payment['method'],mode='test',login_discount=q['login_discount'],eta=eta)
  db.session.add(o);db.session.flush();db.session.add(meta)
  sid=str(d.get('sid',''))
  if d.get('consent') is True and re.fullmatch(r'[a-f0-9-]{36}',sid):record(sid,'success','test_payment_success',detail=payment['method'])
  db.session.commit();return jsonify(o.data()),201
 app.view_functions['order']=need_customer(checkout)
 @app.post('/api/test-payment-qr')
 @need_customer
 def test_qr():
  import qrcode,qrcode.image.svg,io
  try:q=m.quote(request.get_json(silent=True) or {})
  except (ValueError,TypeError) as e:return jsonify(error=str(e)),400
  # Informational test QR deliberately cannot initiate a real UPI transfer.
  payload=f'TINY TALE TEST PAYMENT | INR {q["total"]:.2f} | NO MONEY TRANSFER'
  out=io.BytesIO();qrcode.make(payload,image_factory=qrcode.image.svg.SvgPathImage).save(out)
  return app.response_class(out.getvalue(),mimetype='image/svg+xml',headers={'Cache-Control':'no-store'})
 # Crawlable public product and policy pages; static admin is never indexed.
 def public_url():return os.getenv('SITE_URL',request.url_root.rstrip('/')).rstrip('/')
 original_home=app.view_functions['home']
 def seo_home():
  if m.ROLE=='admin':return original_home()
  html=(m.Path(app.root_path)/'static/index.html').read_text()
  html=html.replace('</head>','<link rel="canonical" href="{{ canonical }}"><meta property="og:title" content="Tiny Tale · Baby essentials"><meta property="og:description" content="Newborn clothing and baby essentials at Tiny Tale."><meta property="og:url" content="{{ canonical }}"></head>')
  return render_template_string(html,canonical=public_url()+'/')
 app.view_functions['home']=seo_home
 @app.get('/robots.txt')
 def robots():return app.response_class('User-agent: *\nDisallow: /\n' if m.ROLE=='admin' else 'User-agent: *\nDisallow: /api/\nDisallow: /static/admin\nSitemap: '+public_url()+'/sitemap.xml\n',mimetype='text/plain')
 @app.get('/sitemap.xml')
 def sitemap():
  if m.ROLE=='admin':abort(404)
  urls=[public_url()+'/',public_url()+'/policies']+[public_url()+'/product/'+p.id for p in db.session.scalars(select(Product).where(Product.active==True))]
  return app.response_class(render_template_string('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{% for url in urls %}<url><loc>{{url}}</loc></url>{% endfor %}</urlset>',urls=urls),mimetype='application/xml')
 @app.get('/product/<pid>')
 def product_page(pid):
  if m.ROLE=='admin':abort(404)
  p=db.get_or_404(Product,pid)
  if not p.active:abort(404)
  data=p.data();canonical=public_url()+'/product/'+p.id
  schema={'@context':'https://schema.org','@type':'Product','name':p.name,'description':p.description,'image':public_url()+p.image,'offers':{'@type':'Offer','priceCurrency':'INR','price':p.sale,'availability':'https://schema.org/InStock' if p.stock>0 else 'https://schema.org/OutOfStock','url':canonical}}
  return render_template_string('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{p.name}} | Tiny Tale</title><meta name="description" content="{{p.description}}"><link rel="canonical" href="{{canonical}}"><link rel="stylesheet" href="/static/styles.css"><link rel="stylesheet" href="/static/experience.css"><script type="application/ld+json">{{schema|tojson}}</script></head><body class="customer-app"><main class="section"><a href="/">Tiny Tale · Home</a><h1>{{p.name}}</h1><img src="{{p.image}}" alt="{{p.name}}" style="max-width:400px;width:100%"><p>{{p.description}}</p><p>₹{{p.sale}}</p><ul>{% for v in data.sizes %}<li>{{'One Size' if v.size=='One size' else v.size}} · {{v.availability}}</li>{% endfor %}</ul><a class="button" href="/?product={{p.id}}#collection">Choose size & shop</a></main></body></html>''',p=p,data=data,canonical=canonical,schema=schema)
 @app.get('/policies')
 def policies():
  if m.ROLE=='admin':abort(404)
  return render_template_string('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Returns & refunds | Tiny Tale</title><link rel="stylesheet" href="/static/styles.css"><link rel="stylesheet" href="/static/experience.css"></head><body class="customer-app"><main class="section"><a href="/">Tiny Tale · Home</a><h1>Returns & refunds</h1>{% if not s.policies_published %}<p class="notice">Draft policies for demonstration. Final store terms have not been published.</p>{% endif %}<h2>Return policy</h2><p style="white-space:pre-wrap">{{s.return_policy}}</p><h2>Refund policy</h2><p style="white-space:pre-wrap">{{s.refund_policy}}</p></main></body></html>''',s=settings())
