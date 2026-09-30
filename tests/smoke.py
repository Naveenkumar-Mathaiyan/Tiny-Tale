import os, sys, tempfile, io
os.environ['DATABASE_URL']='sqlite:///'+tempfile.mktemp(suffix='.db');os.environ['APP_ROLE']='admin';os.environ['ADMIN_PASSWORD']='test-secret-only';os.environ['SECRET_KEY']='test-key-only'
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
import app as module
from app import app,db,Product
from PIL import Image
c=app.test_client()
assert c.get('/api/admin/products').status_code==401
r=c.post('/api/admin/login',json={'password':'bad'});assert r.status_code==401
r=c.post('/api/admin/login',json={'password':'test-secret-only'});assert r.status_code==200
csrf={'X-CSRF-Token':r.json['csrf']}
ps=c.get('/api/products').json;assert len(ps)==11
for p in ps: assert c.get(p['image']).status_code==200
q=c.post('/api/quote',json={'items':[{'id':'1','size':'One size','qty':2}],'coupon':'TINY10'}).json
assert q['subtotal']==558 and q['discount']==56 and q['total']==571
assert c.post('/api/quote',json={'items':[{'id':'1','size':'One size','qty':2}],'coupon':'BABY15'}).status_code==400
assert c.post('/api/quote',json={'items':[{'id':'1','size':'One size','qty':26}]}).status_code==400
customer=dict(name='Demo User',phone='9876543210',address='Demo street',city='Chennai',state='Tamil Nadu',pin='600001')
o=c.post('/api/orders',json={'items':[{'id':'1','size':'One size','qty':2}],'customer':customer,'total':1}).json;assert o['total']==627
assert c.post('/api/admin/orders',json={'id':o['id'],'status':'Confirmed'}).status_code==403
assert c.post('/api/admin/orders',json={'id':o['id'],'status':'Confirmed'},headers=csrf).status_code==200
assert next(p for p in c.get('/api/products').json if p['id']=='1')['stock']==23
assert c.post('/api/admin/orders',json={'id':o['id'],'status':'Confirmed'},headers=csrf).status_code==400
assert c.post('/api/admin/orders',json={'id':o['id'],'status':'Cancelled'},headers=csrf).status_code==200
assert next(p for p in c.get('/api/products').json if p['id']=='1')['stock']==25
buf=io.BytesIO();Image.new('RGB',(20,20),'blue').save(buf,format='PNG');buf.seek(0)
u=c.post('/api/admin/upload',data={'image':(buf,'sample.png')},headers=csrf);assert u.status_code==200
assert c.get(u.json['url']).mimetype=='image/jpeg'
p=ps[0];p['image']=u.json['url'];p['sale']=p['price']+1
assert c.post('/api/admin/products',json=p,headers=csrf).status_code==400
p['sale']=100;p['name']='Changed';assert c.post('/api/admin/products',json=p,headers=csrf).status_code==200
assert any(x['name']=='Changed' for x in c.get('/api/products').json)
assert c.post('/api/admin/upload',data={'image':(io.BytesIO(b'<svg/>'),'x.svg')},headers=csrf).status_code==400
assert c.post('/api/events',json={'kind':'visit','sid':'11111111-1111-1111-1111-111111111111'}).status_code==400
assert c.post('/api/events',json={'kind':'view','value':'Jabla','sid':'11111111-1111-1111-1111-111111111111','consent':True}).status_code==202
assert c.get('/api/admin/analytics').json['products'][0]['label']=='Jabla'
# Size-specific availability and private alerts.
p=next(p for p in c.get('/api/admin/products').json if p['id']=='1')
p['sizes']=[dict(size=size,stock=stock,enabled=True) for size,stock in zip(module.SIZE_OPTIONS[:4],[12,3,0,8])]
assert c.post('/api/admin/products',json=p,headers=csrf).status_code==200
public=next(p for p in c.get('/api/products').json if p['id']=='1')
assert public['stock']==23
assert [v['availability'] for v in public['sizes']]==['Available','Available','Restock soon','Available']
assert all('low_stock' not in v for v in public['sizes'])
alerts=[v for v in c.get('/api/admin/analytics').json['low_stock'] if v['id']=='1']
assert [(v['size'],v['stock']) for v in alerts]==[('3–6 months',3),('6–9 months',0)]
assert c.post('/api/quote',json={'items':[{'id':'1','size':'6–9 months','qty':1}]}).status_code==400
assert c.post('/api/quote',json={'items':[{'id':'1','qty':1}]}).status_code==400
r=c.post('/api/orders',json={'items':[{'id':'1','size':'3–6 months','qty':2}], 'customer':customer})
assert r.status_code==201
size_order=r.json
assert size_order['items'][0]['size']=='3–6 months'
assert c.post('/api/admin/orders',json={'id':size_order['id'],'status':'Confirmed'},headers=csrf).status_code==200
public=next(p for p in c.get('/api/products').json if p['id']=='1')
assert [v['stock'] for v in public['sizes']]==[12,1,0,8]
assert c.post('/api/admin/orders',json={'id':size_order['id'],'status':'Cancelled'},headers=csrf).status_code==200
public=next(p for p in c.get('/api/products').json if p['id']=='1')
assert [v['stock'] for v in public['sizes']]==[12,3,0,8]
# Exactly five is not low stock.
p['sizes'][1]['stock']=5
assert c.post('/api/admin/products',json=p,headers=csrf).status_code==200
assert not any(v['id']=='1' and v['size']=='3–6 months' for v in c.get('/api/admin/analytics').json['low_stock'])
assert c.get('/api/products').headers['Cache-Control']=='no-store'
module.ROLE='store';assert c.get('/api/admin/products').status_code==404
print('PASS: catalog and all images; auth/CSRF; server pricing/coupons; enquiry; stock confirmation/cancellation; upload and validation; consent analytics; storefront admin isolation.')
