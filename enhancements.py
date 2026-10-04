"""v4 additive media, merchandising, diagnostics and consented attribution."""
import io, os, re, uuid, ipaddress, warnings
from collections import Counter as Counts, defaultdict
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from flask import request, jsonify, send_file
from sqlalchemy import select, text, delete
from sqlalchemy.exc import IntegrityError
from PIL import Image
from experience import safe_destination

def install(m):
 app,db=m.app,m.db
 now=lambda:datetime.now(timezone.utc).replace(tzinfo=None)
 app.config['MAX_CONTENT_LENGTH']=21*1024*1024
 @app.errorhandler(413)
 def too_large(error):return jsonify(error='Upload too large. Maximum file size is 20 MB.'),413
 class Asset(db.Model):
  id=db.Column(db.String(36),primary_key=True); mime=db.Column(db.String(60)); content=db.Column(db.LargeBinary,nullable=False); created=db.Column(db.DateTime,default=now)
 class Merch(db.Model):
  product_id=db.Column(db.String(36),db.ForeignKey('product.id'),primary_key=True); content=db.Column(db.JSON,nullable=False)
 class Banner(db.Model):
  id=db.Column(db.String(36),primary_key=True); content=db.Column(db.JSON,nullable=False)
 class Traffic(db.Model):
  sid=db.Column(db.String(36),primary_key=True); created=db.Column(db.DateTime,default=now,index=True); source=db.Column(db.String(120)); campaign=db.Column(db.String(120)); medium=db.Column(db.String(80)); country=db.Column(db.String(80)); state=db.Column(db.String(100)); ip=db.Column(db.String(45)); landing=db.Column(db.String(160))
 class EmailStatus(db.Model):
  key=db.Column(db.String(20),primary_key=True); content=db.Column(db.JSON)
 with app.app_context():
  guard=db.engine.connect() if db.engine.dialect.name=='postgresql' else None
  try:
   if guard:guard.execute(text('SELECT pg_advisory_lock(846303)'))
   db.create_all()
  finally:
   if guard:guard.execute(text('SELECT pg_advisory_unlock(846303)'));guard.close()
 m.Asset=Asset;m.Merch=Merch;m.Banner=Banner;m.Traffic=Traffic
 def record_email_status(ok,message):
  row=db.session.get(EmailStatus,'store')
  value=dict(geo_configured=bool(os.getenv('GEOIP_DATABASE')),ok=ok,message=message,checked=now().isoformat(),role=m.ROLE,configured=bool(os.getenv('BREVO_API_KEY','').strip() and os.getenv('BREVO_SENDER_EMAIL','').strip()))
  if row:row.content=value
  else:db.session.add(EmailStatus(key='store',content=value))
  db.session.commit()
 m.record_email_status=record_email_status
 # Store and admin services have separate environments; persist only safe status to their shared DB.
 if m.ROLE=='store':
  with app.app_context():record_email_status(False,'Email delivery has not yet been attempted since this deployment.')
 @app.get('/api/admin/email-status')
 @m.admin
 def email_status():
  row=db.session.get(EmailStatus,'store')
  return jsonify(status=row.content if row else None,instructions='Render → tiny-tale-store → Environment: add BREVO_API_KEY (API key, not SMTP key), BREVO_SENDER_EMAIL=mnk9522@gmail.com and BREVO_SENDER_NAME=Tiny Tale. Save and deploy. Existing Blueprints do not prompt for new secrets. Then request a code in the customer store and refresh this panel.')
 @app.post('/api/admin/assets')
 @m.admin
 def upload_asset():
  f=request.files.get('file')
  if not f:return jsonify(error='Choose an image, GIF, MP4 or WebM.'),400
  data=f.read(20*1024*1024+1)
  if len(data)>20*1024*1024:return jsonify(error='Maximum file size is 20 MB; compress videos before uploading.'),400
  ext=(f.filename or '').rsplit('.',1)[-1].lower();mime=None
  if ext in ['mp4','webm']:
   if ext=='mp4' and len(data)>=24 and data[4:8]==b'ftyp':mime='video/mp4'
   if ext=='webm' and data[:4]==b'\x1aE\xdf\xa3' and b'webm' in data[:4096]:mime='video/webm'
  else:
   try:
    with warnings.catch_warnings():
     warnings.simplefilter('error',Image.DecompressionBombWarning)
     im=Image.open(io.BytesIO(data));fmt=im.format
     if fmt not in ['JPEG','PNG','WEBP','GIF'] or im.width*im.height>16000000 or getattr(im,'n_frames',1)>500:raise ValueError()
     im.verify();mime=Image.MIME[fmt]
   except Exception:return jsonify(error='Invalid image. Use JPG, PNG, WebP or GIF up to 16 megapixels and 500 frames.'),400
  if not mime:return jsonify(error='Unsupported or invalid media file.'),400
  a=Asset(id=str(uuid.uuid4()),mime=mime,content=data);db.session.add(a);db.session.commit()
  return jsonify(url='/assets/'+a.id,kind='video' if mime.startswith('video') else 'image'),201
 @app.get('/assets/<aid>')
 def asset(aid):
  a=db.get_or_404(Asset,aid)
  r=send_file(io.BytesIO(a.content),mimetype=a.mime,conditional=True,etag=a.id,max_age=86400)
  r.headers['X-Content-Type-Options']='nosniff';return r
 def media_item(d):
  if not isinstance(d,dict):raise ValueError('Invalid media entry.')
  url=str(d.get('url',''));kind='image'
  if url.startswith('/assets/'):
   a=db.session.get(Asset,url.removeprefix('/assets/'))
   if not a:raise ValueError('Upload the media first.')
   kind='video' if a.mime.startswith('video/') else 'image'
  elif re.fullmatch(r'/static/images/[A-Za-z0-9_.-]+',url):
   if not os.path.isfile(os.path.join(app.static_folder,'images',url.rsplit('/',1)[-1])):raise ValueError('Image not found.')
  elif url.startswith('/media/'):
   if not db.session.get(m.Media,url.removeprefix('/media/')):raise ValueError('Image not found.')
  else:raise ValueError('Use uploaded media or a bundled product image.')
  return dict(url=url,kind=kind,alt=str(d.get('alt',''))[:150])
 m.media_item=media_item
 old_data=m.Product.data
 def product_data(p,private=False):
  d=old_data(p,private);row=db.session.get(Merch,p.id);extra=row.content if row else {}
  d.update(gallery=extra.get('gallery',[]),details=extra.get('details',''),care=extra.get('care',''),material=extra.get('material',''))
  return d
 m.Product.data=product_data
 @app.route('/api/admin/merch/<pid>',methods=['GET','POST'])
 @m.admin
 def merch(pid):
  db.get_or_404(m.Product,pid);row=db.session.get(Merch,pid)
  if request.method=='GET':return jsonify(row.content if row else dict(gallery=[],details='',care='',material=''))
  d=request.get_json(silent=True) or {}
  try:
   if not isinstance(d.get('gallery'),list) or len(d['gallery'])>12:raise ValueError('Use at most 12 gallery items.')
   data=dict(gallery=[media_item(x) for x in d['gallery']],**{k:str(d.get(k,''))[:6000] for k in ['details','care','material']})
   if m.staff_identity()['role'] in ['store_keeper','store_manager','manager','supervisor']:
    old=row.content if row else {}
    if any(k in d and d[k]!=old.get(k,'') for k in ['details','care','material']):return jsonify(error='Store managers may update media only.'),403
    data.update({k:old.get(k,'') for k in ['details','care','material']})
  except ValueError as e:return jsonify(error=str(e)),400
  if row:row.content=data
  else:db.session.add(Merch(product_id=pid,content=data))
  db.session.commit();return jsonify(data)
 @app.get('/api/banners')
 def banners():return jsonify([b.content|{'id':b.id} for b in db.session.scalars(select(Banner)) if b.content.get('active')])
 @app.route('/api/admin/banners',methods=['GET','POST'])
 @m.admin
 def admin_banners():
  if request.method=='GET':return jsonify([b.content|{'id':b.id} for b in db.session.scalars(select(Banner))])
  d=request.get_json(silent=True) or {};bid=str(d.get('id',''))
  row=db.session.get(Banner,bid) if bid else None
  if d.get('delete') is True:
   if row:db.session.delete(row);db.session.commit()
   return jsonify(ok=True)
  try:
   media=media_item(d);link=str(d.get('link','')).strip();button=str(d.get('button','')).strip()
   link=safe_destination(link)
   if type(d.get('new_tab',False))is not bool:raise ValueError('Choose whether the button opens a new tab.')
   if bool(button)!=bool(link):raise ValueError('Choose both a button label and destination, or leave both empty for an image-only banner.')
   value=media|dict(title=str(d.get('title',''))[:100],subtitle=str(d.get('subtitle',''))[:250],button=button[:40],link=link,new_tab=d.get('new_tab',False),active=d.get('active') is True)
  except ValueError as e:return jsonify(error=str(e)),400
  if row:row.content=value
  else:row=Banner(id=str(uuid.uuid4()),content=value);db.session.add(row)
  db.session.commit();return jsonify(value|{'id':row.id})
 @app.route('/api/admin/numbering',methods=['GET','POST'])
 @m.admin
 def numbering():
  counter=db.session.scalar(select(m.Counter).where(m.Counter.key=='orders').with_for_update());row=db.session.get(m.Setting,'numbering');cfg=row.value if row else dict(prefix='',date=True,padding=4)
  if request.method=='POST':
   d=request.get_json(silent=True) or {}
   try:
    prefix=str(d.get('prefix','')).upper();padding=d.get('padding',4);n=d.get('next');dated=d.get('date')
    if not re.fullmatch('[A-Z0-9-]{0,8}',prefix) or type(padding)is not int or not 4<=padding<=8 or type(n)is not int or not counter.value<n<=99999999 or type(dated)is not bool:raise ValueError('Use a prefix up to 8 letters/digits/hyphens, padding 4–8, and a next sequence greater than the last used sequence (maximum 99999999).')
    cfg=dict(prefix=prefix,date=dated,padding=padding)
    # Old identifiers cannot be reused, even after changing format.
    candidate=prefix+((now()+timedelta(hours=5,minutes=30)).strftime('%y%m%d') if dated else '')+str(n).zfill(padding)
    if db.session.scalar(select(m.PurchaseMeta).where(m.PurchaseMeta.number==candidate)):raise ValueError('That order number already exists.')
    counter.value=n-1
    if row:row.value=cfg
    else:db.session.add(m.Setting(key='numbering',value=cfg))
    db.session.commit()
   except (ValueError,TypeError) as e:return jsonify(error=str(e)),400
  return jsonify(**cfg,next=counter.value+1,last=counter.value)
 def location_for(ip):
  # Optional local GeoLite2 City database. No IP is sent to an external service.
  path=os.getenv('GEOIP_DATABASE','')
  if not path:return 'Unknown','Unknown'
  try:
   import maxminddb
   with maxminddb.open_database(path) as reader:data=reader.get(ip) or {}
   return data.get('country',{}).get('names',{}).get('en','Unknown'),next(iter(data.get('subdivisions',[])),{}).get('names',{}).get('en','Unknown')
  except Exception:return 'Unknown','Unknown'
 @app.post('/api/traffic')
 def traffic():
  d=request.get_json(silent=True) or {};sid=str(d.get('sid',''))
  if d.get('consent') is not True or not re.fullmatch(r'[a-f0-9-]{36}',sid):return jsonify(error='Analytics permission required.'),400
  # Bounded retention, including raw IPs; traffic is first-touch per browser session.
  db.session.execute(delete(Traffic).where(Traffic.created<now()-timedelta(days=90)))
  if db.session.get(Traffic,sid):db.session.commit();return jsonify(ok=True),202
  ip=request.remote_addr or ''
  try:ip=str(ipaddress.ip_address(ip))
  except ValueError:ip=''
  # Bound event abuse per address without treating IP as a unique customer.
  if db.session.scalar(select(db.func.count()).select_from(Traffic).where(Traffic.ip==ip,Traffic.created>now()-timedelta(hours=1)))>=60:return jsonify(ok=True),202
  country,state=location_for(ip)
  try:ref=urlparse(str(d.get('referrer',''))).hostname or ''
  except ValueError:ref=''
  if ref==request.host.split(':')[0]:ref=''
  row=Traffic(sid=sid,ip=ip,country=country,state=state,source=str(d.get('source') or ref or 'Direct / unknown')[:120],medium=str(d.get('medium',''))[:80],campaign=str(d.get('campaign',''))[:120],landing=str(d.get('landing','/')).split('?')[0][:160]);db.session.add(row)
  try:db.session.commit()
  except IntegrityError:db.session.rollback()
  return jsonify(ok=True),202
 @app.get('/api/admin/marketing')
 @m.admin
 def marketing():
  try:days=min(90,max(1,int(request.args.get('days',30))))
  except ValueError:days=30
  since=now()-timedelta(days=days)
  db.session.execute(delete(Traffic).where(Traffic.created<now()-timedelta(days=90)));db.session.commit()
  rows=list(db.session.scalars(select(Traffic).where(Traffic.created>=since).order_by(Traffic.created)))
  events=list(db.session.scalars(select(m.Journey).where(m.Journey.created>=since)))
  events_by=defaultdict(list)
  for e in events:events_by[e.sid].append(e)
  sources=defaultdict(lambda:dict(sessions=0,seconds=0,checkout=0,test_orders=0));daily=Counts();hours=Counts();countries=Counts();states=Counts();campaigns=Counts()
  for r in rows:
   dt=r.created+timedelta(hours=5,minutes=30);daily[dt.strftime('%Y-%m-%d')]+=1;hours[dt.strftime('%H')]+=1;countries[r.country]+=1;states[r.country+' / '+r.state]+=1;campaigns[r.campaign or '(none)']+=1
   s=sources[r.source];s['sessions']+=1;s['seconds']+=sum(e.seconds for e in events_by[r.sid]);s['checkout']+=any(e.stage=='checkout' for e in events_by[r.sid]);s['test_orders']+=sum(e.kind=='test_payment_success' for e in events_by[r.sid])
  first=(now()+timedelta(hours=5,minutes=30)).date()-timedelta(days=days-1)
  return jsonify(sessions=len(rows),daily=[dict(label=str(first+timedelta(days=i)),count=daily[str(first+timedelta(days=i))]) for i in range(days)],hours=[dict(label=str(i).zfill(2),count=hours[str(i).zfill(2)]) for i in range(24)],countries=[dict(label=k,count=v) for k,v in countries.most_common()],states=[dict(label=k,count=v) for k,v in states.most_common()],campaigns=[dict(label=k,count=v) for k,v in campaigns.most_common()],sources=[dict(source=k,**v) for k,v in sources.items()],recent=[dict(time=(r.created+timedelta(hours=5,minutes=30)).isoformat(),source=r.source,campaign=r.campaign,medium=r.medium,country=r.country,state=r.state,ip=r.ip,landing=r.landing) for r in rows[-100:][::-1]],geo_configured=bool((db.session.get(EmailStatus,'store').content if db.session.get(EmailStatus,'store') else {}).get('geo_configured')))
