"""Shared staff operations: variant labels, audited receipts and atomic counter sales."""
import hashlib, io, json, os, re, secrets, uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, send_file
from sqlalchemy import select, text, or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash
from experience import safe_destination

STOCK_ROLES={'store_keeper','store_manager','manager','supervisor'}
def capabilities(role):
 if role in {'super_admin','admin'}:return ['receive','sell','stock','labels','all_bills']
 if role in {'manager','supervisor'}:return ['receive','sell','stock','labels']
 if role in {'store_keeper','store_manager'}:return ['receive','stock','labels']
 if role=='billing':return ['sell','stock']
 return []
def can_access(role,endpoint,method):
 if role=='super_admin':return True
 if endpoint=='accounts':return False
 if role=='admin':return True
 if endpoint in {'session','logout','operations'}:return True
 if role in STOCK_ROLES:
  return endpoint in {'stock','upload','assets','merch'} or endpoint=='products' and method=='GET'
 return False

def valid_gtin(value):
 return bool(re.fullmatch(r'[0-9]{13}',value) and (10-sum(int(c)*(1 if i%2==0 else 3) for i,c in enumerate(value[:12]))%10)%10==int(value[-1]))

def install(m):
 app,db=m.app,m.db
 class Category(db.Model):
  name=db.Column(db.String(40),primary_key=True)
 class VariantCode(db.Model):
  id=db.Column(db.String(36),primary_key=True)
  product_id=db.Column(db.String(36),db.ForeignKey('product.id'),nullable=False)
  size=db.Column(db.String(30),nullable=False)
  code=db.Column(db.String(40),unique=True,nullable=False)
  gtin=db.Column(db.String(13),unique=True)
  __table_args__=(db.UniqueConstraint('product_id','size'),)
 class MobileToken(db.Model):
  digest=db.Column(db.String(64),primary_key=True)
  staff_id=db.Column(db.String(36),db.ForeignKey('staff.id'),nullable=False)
  version=db.Column(db.Integer,nullable=False)
  expires=db.Column(db.DateTime,nullable=False)
 class StockMovement(db.Model):
  id=db.Column(db.String(36),primary_key=True)
  product_id=db.Column(db.String(36),nullable=False)
  size=db.Column(db.String(30),nullable=False)
  delta=db.Column(db.Integer,nullable=False)
  kind=db.Column(db.String(20),nullable=False)
  reference=db.Column(db.String(36),nullable=False)
  staff_id=db.Column(db.String(36))
  created=db.Column(db.DateTime,default=datetime.utcnow,index=True)
 class Operation(db.Model):
  id=db.Column(db.String(36),primary_key=True)
  key=db.Column(db.String(64),unique=True,nullable=False)
  fingerprint=db.Column(db.String(64),nullable=False)
  staff_id=db.Column(db.String(36))
  result=db.Column(db.JSON,nullable=False)
 class Invoice(db.Model):
  id=db.Column(db.String(36),primary_key=True)
  number=db.Column(db.String(40),unique=True,nullable=False)
  staff_id=db.Column(db.String(36))
  staff_name=db.Column(db.String(100))
  items=db.Column(db.JSON,nullable=False)
  total=db.Column(db.Integer,nullable=False)
  method=db.Column(db.String(20),nullable=False)
  created=db.Column(db.DateTime,default=datetime.utcnow,index=True)
 m.Category=Category;m.VariantCode=VariantCode;m.Invoice=Invoice;m.StockMovement=StockMovement;m.MobileToken=MobileToken
 with app.app_context():
  guard=db.engine.connect() if db.engine.dialect.name=='postgresql' else None
  try:
   if guard:guard.execute(text('SELECT pg_advisory_lock(846307)'))
   db.create_all()
   for name in db.session.scalars(select(m.Product.category).distinct()):
    if name and not db.session.get(Category,name):db.session.add(Category(name=name))
   for staff in db.session.scalars(select(m.Staff).where(m.Staff.role=='store_keeper')):staff.role='store_manager';staff.version+=1
   if not db.session.get(m.Counter,'invoices'):db.session.add(m.Counter(key='invoices',value=0))
   db.session.commit()
  finally:
   if guard:guard.execute(text('SELECT pg_advisory_unlock(846307)'));guard.close()
 def error(message,status=400):return jsonify(error=message),status
 def staff_auth(fn):
  @wraps(fn)
  def wrapped(*args,**kw):
   if m.ROLE!='admin':return error('Use the admin service URL.',404)
   raw=request.headers.get('Authorization','')
   if not raw.startswith('Bearer '):return error('Please sign in.',401)
   token=db.session.get(MobileToken,hashlib.sha256(raw[7:].encode()).hexdigest())
   staff=db.session.get(m.Staff,token.staff_id) if token else None
   if not token or token.expires<=datetime.utcnow() or not staff or not staff.active or staff.version!=token.version:return error('Session expired. Please sign in.',401)
   from flask import g
   g.operator=dict(id=staff.id,name=staff.name,role=staff.role)
   return fn(*args,**kw)
  return wrapped
 @app.post('/api/staff/login')
 def staff_login():
  if m.ROLE!='admin':return error('Use the admin service URL.',404)
  d=request.get_json(silent=True) or {}
  if not isinstance(d,dict):return error('Use a JSON object.')
  username=str(d.get('username','')).strip().lower();password=d.get('password','')
  key=hashlib.sha256(('mobile:'+str(request.remote_addr)).encode()).hexdigest();a=db.session.get(m.Attempt,key)
  if not a:a=m.Attempt(key=key,count=0,started=datetime.utcnow());db.session.add(a)
  if datetime.utcnow()-a.started>timedelta(minutes=15):a.count=0;a.started=datetime.utcnow()
  if a.count>=10:return error('Too many attempts. Try again in 15 minutes.',429)
  staff=db.session.scalar(select(m.Staff).where(m.Staff.username==username))
  if not isinstance(password,str) or not staff or not staff.active or not check_password_hash(staff.password_hash,password):a.count+=1;db.session.commit();return error('Incorrect username or password.',401)
  a.count=0
  db.session.query(MobileToken).filter(MobileToken.expires<datetime.utcnow()).delete()
  raw=secrets.token_urlsafe(40);expiry=datetime.utcnow()+timedelta(hours=12)
  db.session.add(MobileToken(digest=hashlib.sha256(raw.encode()).hexdigest(),staff_id=staff.id,version=staff.version,expires=expiry));db.session.commit()
  return jsonify(token=raw,expires=expiry.isoformat()+'Z',user=dict(id=staff.id,name=staff.name,role=staff.role),capabilities=capabilities(staff.role))
 @app.post('/api/staff/logout')
 @staff_auth
 def staff_logout():
  db.session.delete(db.session.get(MobileToken,hashlib.sha256(request.headers['Authorization'][7:].encode()).hexdigest()));db.session.commit();return jsonify(ok=True)
 @app.get('/api/categories')
 def public_categories():return jsonify(list(db.session.scalars(select(Category.name).order_by(Category.name))))
 @app.route('/api/admin/categories',methods=['GET','POST'])
 @m.admin
 def categories():
  if request.method=='GET':return public_categories()
  d=request.get_json(silent=True) or {}
  if not isinstance(d,dict):return error('Use a JSON object.')
  name=str(d.get('name','')).strip();old=str(d.get('old',''))
  if not name or len(name)>40:return error('Category names need 1–40 characters.')
  if db.session.scalar(select(Category).where(db.func.lower(Category.name)==name.lower())):return error('This category already exists.')
  row=db.session.get(Category,old) if old else None
  if old and not row:return error('Category not found.',404)
  if row:
   for p in db.session.scalars(select(m.Product).where(m.Product.category==old).with_for_update()):p.category=name
   db.session.delete(row)
  db.session.add(Category(name=name));db.session.commit();return public_categories()
 hero_default=dict(enabled=True,eyebrow='The newborn edit',title='Small clothes. Beautiful beginnings.',description='From the first jabla to a cosy swaddle. Find everyday essentials for your little one.',image='/static/images/product-9.png',button='Explore the collection',link='#collection',interval=7)
 def hero_settings():
  row=db.session.get(m.Setting,'homepage');return {**hero_default,**(row.value if row else {})}
 @app.get('/api/homepage')
 def public_homepage():return jsonify(hero_settings())
 @app.route('/api/admin/homepage',methods=['GET','POST'])
 @m.admin
 def homepage():
  if request.method=='GET':return public_homepage()
  d=request.get_json(silent=True) or {}
  if not isinstance(d,dict):return error('Use a JSON object.')
  try:
   if type(d.get('enabled'))is not bool or type(d.get('interval'))is not int or not 4<=d['interval']<=30:raise ValueError('Choose visibility and a banner interval from 4–30 seconds.')
   data={k:str(d.get(k,'')).strip() for k in ['eyebrow','title','description','image','button','link']}
   if not 1<=len(data['title'])<=120 or len(data['eyebrow'])>60 or len(data['description'])>500 or len(data['button'])>40:raise ValueError('Use a title up to 120 characters, short label and description up to 500 characters.')
   if m.media_item({'url':data['image']})['kind']!='image':raise ValueError('Choose an image for the homepage introduction.')
   data['link']=safe_destination(data['link'])
   if bool(data['button'])!=bool(data['link']):raise ValueError('Add both button text and destination, or leave both empty.')
   images=d.get('images',[data['image']])
   if not isinstance(images,list) or not 1<=len(images)<=8:raise ValueError('Choose 1–8 homepage images.')
   if any(m.media_item({'url':url})['kind']!='image' for url in images):raise ValueError('The introduction slideshow uses images only. Add videos in Offer banners.')
   data.update(enabled=d['enabled'],interval=d['interval'],images=images,image=images[0])
  except ValueError as e:return error(str(e))
  row=db.session.get(m.Setting,'homepage')
  if row:row.value=data
  else:db.session.add(m.Setting(key='homepage',value=data))
  db.session.commit();return jsonify(data)
 def code_data(c):
  p=db.session.get(m.Product,c.product_id);v=db.session.get(m.ProductSize,(c.product_id,c.size))
  return dict(id=c.id,code=c.code,gtin=c.gtin or '',product_id=p.id,name=p.name,category=p.category,size=c.size,stock=v.stock,enabled=v.enabled,active=p.active,price=p.sale)
 def generate_codes():
  for v in db.session.scalars(select(m.ProductSize).where(m.ProductSize.enabled==True)):
   if not db.session.scalar(select(VariantCode).where(VariantCode.product_id==v.product_id,VariantCode.size==v.size)):
    db.session.add(VariantCode(id=str(uuid.uuid4()),product_id=v.product_id,size=v.size,code='TT-'+uuid.uuid4().hex[:16].upper()))
  db.session.flush()
 def invoice_data(row):return dict(id=row.id,number=row.number,staff=row.staff_name,items=row.items,total=row.total,method=row.method,created=row.created.isoformat()+'Z')
 def operate(user,path):
  caps=capabilities(user['role']);d=request.get_json(silent=True) or {}
  if not isinstance(d,dict):return error('Use a JSON object.')
  if request.method=='POST' and path not in {'codes','receive','sale'}:return error('Use GET for this action.',405)
  def require(cap):
   if cap not in caps:raise PermissionError('This action is not allowed for your role.')
  try:
   if path=='session':return jsonify(user=user,capabilities=caps)
   if path=='codes':
    require('labels')
    if request.method=='POST':
     if d.get('generate') is True:generate_codes();db.session.commit()
     else:
      if user['role'] not in {'admin','super_admin'}:raise PermissionError('Only an admin can change label codes.')
      c=db.session.get(VariantCode,d.get('id'))
      if not c:return error('Label not found.',404)
      code=str(d.get('code','')).strip().upper();gtin=str(d.get('gtin','')).strip()
      if not re.fullmatch(r'[A-Z0-9][A-Z0-9._-]{2,39}',code):raise ValueError('Internal codes need 3–40 letters, digits, dots, underscores or hyphens.')
      if gtin and (not valid_gtin(gtin) or d.get('licensed') is not True):raise ValueError('Use a valid licensed GTIN-13 and confirm that GS1 assigned it to your product.')
      other=db.session.scalar(select(VariantCode).where(VariantCode.id!=c.id,or_(VariantCode.code.in_([code,gtin]),VariantCode.gtin.in_([code,gtin]))))
      if other:raise ValueError('This internal code or GTIN is already used.')
      c.code=code;c.gtin=gtin or None;db.session.commit()
    return jsonify([code_data(c) for c in db.session.scalars(select(VariantCode).order_by(VariantCode.product_id,VariantCode.size))])
   if path=='stock':
    require('stock');rows=[]
    for p,v in db.session.execute(select(m.Product,m.ProductSize).join(m.ProductSize).where(m.ProductSize.enabled==True).order_by(m.Product.name)):
     rows.append(dict(product_id=p.id,name=p.name,category=p.category,size=v.size,stock=v.stock))
    return jsonify(rows)
   if path=='lookup':
    require('stock');value=request.args.get('code','').strip()
    if value.startswith('tiny-tale:'):value=value[len('tiny-tale:'):]
    c=db.session.scalar(select(VariantCode).where(or_(VariantCode.code==value.upper(),VariantCode.gtin==value)))
    if not c:return error('Unknown label. Generate labels in the admin panel first.',404)
    data=code_data(c)
    if not data['enabled'] or not data['active']:return error('This product or size is currently disabled.',409)
    if 'sell' not in caps:data.pop('price',None)
    return jsonify(data)
   if path in {'receive','sale'}:
    require('receive' if path=='receive' else 'sell')
    key=str(d.get('request_id',''))
    if not re.fullmatch(r'[a-f0-9-]{36}',key):raise ValueError('A unique request ID is required.')
    digest=hashlib.sha256(json.dumps({'path':path,'body':d},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    old=db.session.scalar(select(Operation).where(Operation.key==key))
    if old:
     if old.staff_id!=user.get('id') or old.fingerprint!=digest:return error('This request ID was used for a different operation.',409)
     return jsonify(old.result)
    lines=d.get('items')
    if not isinstance(lines,list) or not 1<=len(lines)<=100:raise ValueError('Add 1–100 distinct product sizes.')
    checked=[];seen=set()
    for line in lines:
     if not isinstance(line,dict):raise ValueError('Invalid item.')
     pid=str(line.get('product_id',''));size=str(line.get('size',''));qty=line.get('qty')
     if (pid,size) in seen or type(qty)is not int or not 1<=qty<=10000:raise ValueError('Use distinct sizes and quantities from 1–10,000.')
     seen.add((pid,size));checked.append((pid,size,qty))
    opid=str(uuid.uuid4());snapshots=[];products={}
    # Lock all parents in a stable order; website confirmation uses the same product locks.
    for pid in sorted({x[0] for x in checked}):
     p=db.session.scalar(select(m.Product).where(m.Product.id==pid).with_for_update())
     if not p or not p.active:raise ValueError('Product is missing or hidden.')
     products[pid]=p
    for pid,size,qty in sorted(checked):
     v=db.session.scalar(select(m.ProductSize).where(m.ProductSize.product_id==pid,m.ProductSize.size==size).with_for_update());p=products[pid]
     if not v or not v.enabled:raise ValueError('This size is disabled or missing.')
     delta=qty if path=='receive' else -qty
     if v.stock+delta<0:return db.session.rollback() or error(f'{p.name} / {size}: only {v.stock} available.',409)
     if v.stock+delta>100000:raise ValueError('Maximum stock is 100,000 per size.')
     v.stock+=delta
     snapshots.append(dict(product_id=pid,name=p.name,category=p.category,size=size,qty=qty,price=p.sale,stock=v.stock))
     db.session.add(StockMovement(id=str(uuid.uuid4()),product_id=pid,size=size,delta=delta,kind=path,reference=opid,staff_id=user.get('id')))
    for p in products.values():m.sync_stock(p)
    result=dict(ok=True,id=opid,items=snapshots)
    if path=='sale':
     method=d.get('method')
     if method not in ['cash','card','upi','netbank']:raise ValueError('Select cash, card, UPI or net banking received at the counter.')
     counter=db.session.scalar(select(m.Counter).where(m.Counter.key=='invoices').with_for_update());counter.value+=1
     number='POS-'+(datetime.utcnow()+timedelta(hours=5,minutes=30)).strftime('%y%m%d')+str(counter.value).zfill(6)
     total=sum(x['qty']*x['price'] for x in snapshots)
     if type(d.get('expected_total')) is not int or d['expected_total']!=total:db.session.rollback();return error('Prices changed. Refresh the scanned items and verify the amount before finalizing.',409)
     inv=Invoice(id=opid,number=number,staff_id=user.get('id'),staff_name=user['name'],items=snapshots,total=sum(x['qty']*x['price'] for x in snapshots),method=method)
     db.session.add(inv);db.session.flush();result=invoice_data(inv)|{'ok':True}
    db.session.add(Operation(id=opid,key=key,fingerprint=digest,staff_id=user.get('id'),result=result));db.session.commit();return jsonify(result),201
   if path=='bills':
    require('sell');query=select(Invoice)
    if 'all_bills' not in caps:query=query.where(Invoice.staff_id==user.get('id'))
    return jsonify([invoice_data(x) for x in db.session.scalars(query.order_by(Invoice.created.desc()).limit(200))])
   if path.startswith('receipt/'):
    require('sell');inv=db.session.get(Invoice,path.split('/')[1])
    if not inv:return error('Bill not found.',404)
    if 'all_bills' not in caps and inv.staff_id!=user.get('id'):raise PermissionError('You can view only your own bills.')
    return receipt_pdf(inv)
   if path=='labels':
    require('labels');return label_pdf()
   if path=='movements':
    require('receive');query=select(StockMovement)
    if user['role'] not in {'super_admin','admin'}:query=query.where(StockMovement.staff_id==user.get('id'),StockMovement.kind=='receive')
    return jsonify([dict(id=x.id,product_id=x.product_id,size=x.size,delta=x.delta,kind=x.kind,created=x.created.isoformat()+'Z') for x in db.session.scalars(query.order_by(StockMovement.created.desc()).limit(200))])
   return error('Action not found.',404)
  except PermissionError as e:return error(str(e),403)
  except (ValueError,TypeError,KeyError) as e:db.session.rollback();return error(str(e))
  except IntegrityError:
   db.session.rollback()
   if path in {'receive','sale'}:
    old=db.session.scalar(select(Operation).where(Operation.key==d.get('request_id')))
    if old and old.staff_id==user.get('id') and old.fingerprint==digest:return jsonify(old.result)
   return error('This code or request already exists. Refresh and try again.',409)
 def label_pdf():
  from reportlab.pdfgen import canvas
  from reportlab.graphics.barcode import code128,eanbc
  from reportlab.graphics.shapes import Drawing
  from reportlab.graphics import renderPDF
  from reportlab.lib.utils import ImageReader
  import qrcode
  ids=request.args.get('ids','').split(',');copies=int(request.args.get('copies','1'))
  if not 1<=copies<=100 or not 1<=len(ids)<=100:raise ValueError('Select up to 100 variants and 1–100 copies.')
  rows=[db.session.get(VariantCode,k) for k in ids]
  if any(c is None for c in rows):raise ValueError('Select existing label codes.')
  if len(rows)*copies>500:raise ValueError('Maximum 500 labels per printout.')
  use_gtin=request.args.get('type')=='gtin'
  if use_gtin and any(not c.gtin for c in rows):raise ValueError('Every selected variant needs a licensed GTIN-13.')
  out=io.BytesIO();pdf=canvas.Canvas(out,pagesize=(595.28,841.89));pdf.setTitle('Tiny Tale product labels')
  for i,c in enumerate([c for c in rows for _ in range(copies)]):
   if i and i%12==0:pdf.showPage()
   x=24+(i%2)*278;y=841-30-((i%12)//2)*130;data=code_data(c);value=c.gtin if use_gtin else c.code
   pdf.setFont('Helvetica-Bold',9);pdf.drawString(x,y,data['name'][:42]);pdf.setFont('Helvetica',8);pdf.drawString(x,y-14,data['size'])
   qr=io.BytesIO();qrcode.make(value if use_gtin else 'tiny-tale:'+value).save(qr,format='PNG');pdf.drawImage(ImageReader(qr),x+202,y-80,width=60,height=60)
   if use_gtin:
    b=eanbc.Ean13BarcodeWidget(value,barHeight=36,fontSize=8);drawing=Drawing(190,50);drawing.add(b);renderPDF.draw(drawing,pdf,x,y-72)
   else:
    b=code128.Code128(value,barHeight=32,barWidth=.65);scale=min(1,195/b.width);pdf.saveState();pdf.translate(x,y-60);pdf.scale(scale,1);b.drawOn(pdf,0,0);pdf.restoreState()
   pdf.drawString(x,y-96,value)
  pdf.save();out.seek(0);return send_file(out,mimetype='application/pdf',download_name='TinyTale-labels.pdf')
 def receipt_pdf(inv):
  from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer
  from reportlab.lib.styles import getSampleStyleSheet
  from html import escape
  out=io.BytesIO();styles=getSampleStyleSheet();story=[Paragraph('Tiny Tale · Counter receipt',styles['Title']),Paragraph(escape(inv.number),styles['Heading2']),Paragraph(escape(inv.created.isoformat()+' UTC · '+inv.method),styles['Normal']),Spacer(1,12)]
  rows=[['Product / size','Qty','Unit INR','Total INR']]
  for x in inv.items:rows.append([Paragraph(escape(x['name']+' / '+x['size']),styles['Normal']),x['qty'],x['price'],x['qty']*x['price']])
  rows.append(['Total','','',inv.total]);table=Table(rows,colWidths=[280,40,70,80],repeatRows=1);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),'#e8f3ef'),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),12)]));story.append(table)
  story.extend([Spacer(1,12),Paragraph('Recorded by '+escape(inv.staff_name)+'. This receipt records a counter sale; it does not process a bank payment. GST tax invoices require your business tax configuration.',styles['Normal'])])
  SimpleDocTemplate(out,title=inv.number).build(story);out.seek(0);return send_file(out,mimetype='application/pdf',download_name=inv.number+'.pdf')
 @app.route('/api/admin/operations/<path:path>',methods=['GET','POST'])
 @m.admin
 def admin_operations(path):
  if request.method=='GET' and path in {'receive','sale'}:return error('Use POST for stock movements.',405)
  return operate(m.staff_identity(),path)
 @app.route('/api/staff/<path:path>',methods=['GET','POST'])
 @staff_auth
 def mobile_operations(path):
  from flask import g
  if request.method=='GET' and path in {'receive','sale'}:return error('Use POST for stock movements.',405)
  return operate(g.operator,path)
