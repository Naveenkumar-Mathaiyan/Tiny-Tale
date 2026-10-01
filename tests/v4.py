"""Regression coverage for v4 using disposable SQLite and mocked email."""
from smoke import *
m.ROLE='admin'
assert admin.get('/api/admin/email-status').status_code==200
assert 'test-secret' not in admin.get('/api/admin/email-status').text
# Missing config does not create OTP records or trap shoppers in the cooldown.
key=os.environ.pop('BREVO_API_KEY')
c=other.get('/api/account').json;hdr={'X-Customer-CSRF':c['csrf']}
assert other.post('/api/auth/request',json={'email':'missing@example.com'},headers=hdr).status_code==503
with app.app_context():assert not db.session.scalar(select(m.OTP).where(m.OTP.email=='missing@example.com'))
os.environ['BREVO_API_KEY']=key
# GIF bytes must be preserved, and video streaming supports ranges.
buf=io.BytesIO();Image.new('RGB',(8,8),'red').save(buf,format='GIF');gif=buf.getvalue()
r=admin.post('/api/admin/assets',data={'file':(io.BytesIO(gif),'offer.gif')},headers=ah);assert r.status_code==201,r.json
asset=r.json;assert shop.get(asset['url']).data==gif and shop.get(asset['url']).mimetype=='image/gif'
assert admin.post('/api/admin/assets',data={'file':(io.BytesIO(b'<svg/>'),'bad.svg')},headers=ah).status_code==400
assert admin.post('/api/admin/assets',data={'file':(io.BytesIO(b'bad'),'bad.mp4')},headers=ah).status_code==400
assert shop.post('/api/admin/assets',data={'file':(io.BytesIO(gif),'x.gif')}).status_code==401
extra=dict(gallery=[asset|{'alt':'Test & image'}],details='Full <details>',material='Cotton',care='Gentle wash')
assert admin.post('/api/admin/merch/1',json=extra,headers=ah).status_code==200
p=next(p for p in shop.get('/api/products').json if p['id']=='1');assert p['gallery'][0]['url']==asset['url'] and p['material']=='Cotton'
assert admin.post('/api/admin/merch/1',json=extra|{'gallery':[{'url':'javascript:alert(1)'}]},headers=ah).status_code==400
b=asset|dict(title='Login offer',subtitle='5%',button='Login',link='login',active=True)
r=admin.post('/api/admin/banners',json=b,headers=ah);assert r.status_code==200
assert len(shop.get('/api/banners').json)==1
assert admin.post('/api/admin/banners',json=b|{'link':'https://evil.test'},headers=ah).status_code==400
assert admin.post('/api/admin/banners',json=r.json|{'active':False},headers=ah).status_code==200
assert shop.get('/api/banners').json==[]
# Sequence cannot decrease. Existing numbers stay immutable.
n=admin.get('/api/admin/numbering').json
assert admin.post('/api/admin/numbering',json=dict(prefix='TT-',date=True,padding=5,next=n['next']+10),headers=ah).status_code==200
assert admin.post('/api/admin/numbering',json=dict(prefix='',date=True,padding=4,next=1),headers=ah).status_code==400
with app.app_context():assert db.session.get(m.PurchaseMeta,orders[0]['id']).number==orders[0]['number']
# Authenticate and verify the next new order uses changed numbering.
account=shop.get('/api/account').json;ch={'X-Customer-CSRF':account['csrf']}
r=shop.post('/api/auth/request',json={'email':'v4@example.com'},headers=ch)
r=shop.post('/api/auth/verify',json={'challenge':r.json['challenge'],'code':codes['v4@example.com']},headers=ch);ch={'X-Customer-CSRF':r.json['csrf']}
q=shop.post('/api/quote',json=dict(items=items)).json
r=shop.post('/api/orders',json=dict(items=items,expected_total=q['total'],customer=address,payment=dict(method='upi',outcome='success'),request_key=str(uuid.uuid4())),headers=ch)
assert r.status_code==201,r.json
assert r.json['number'].startswith('TT-') and r.json['number'].endswith(str(n['next']+10).zfill(5))
# First-touch attribution cannot be overwritten; no fabricated geolocation.
t=dict(sid=str(uuid.uuid4()),consent=True,source='instagram',campaign='launch',medium='social',landing='/?private=secret')
assert shop.post('/api/traffic',json=t|{'consent':False}).status_code==400
assert shop.post('/api/traffic',json=t).status_code==202
assert shop.post('/api/traffic',json=t|{'source':'changed'}).status_code==202
report=admin.get('/api/admin/marketing').json
assert report['sessions']==1 and report['sources'][0]['source']=='instagram'
assert report['recent'][0]['country']=='Unknown' and report['recent'][0]['landing']=='/'
assert shop.get('/api/admin/marketing').status_code==401
print('PASS v4: diagnostics; missing credentials; uploads/GIF; media validation; galleries; banners; protected reports; sequence settings and next order; consent/attribution.')
video=(Path(__file__).parent/'fixtures/sample.mp4').read_bytes()
r=admin.post('/api/admin/assets',data={'file':(io.BytesIO(video),'sample.mp4')},headers=ah)
assert r.status_code==201 and r.json['kind']=='video'
stream=shop.get(r.json['url'],headers={'Range':'bytes=0-23'})
assert stream.status_code==206 and stream.data==video[:24] and stream.mimetype=='video/mp4'
print('PASS: actual MP4 upload and partial-content streaming.')
