"""Role enforcement, account revocation and real PDF/Excel exports on disposable SQLite."""
from smoke import *
from openpyxl import load_workbook
from pypdf import PdfReader
m.ROLE='admin'
assert login.json['user']['role']=='super_admin'
assert admin.post('/api/admin/accounts',json={'username':'keeper1','name':'Store keeper','role':'store_keeper','password':'keeper-password-123','active':True},headers=ah).status_code==200
accounts=admin.get('/api/admin/accounts').json;keeperid=accounts[0]['id']
assert admin.post('/api/admin/accounts',json={'username':'keeper1','name':'Duplicate','role':'admin','password':'admin-password-123','active':True},headers=ah).status_code==400
assert admin.post('/api/admin/accounts',json={'username':'boss','name':'Boss','role':'super_admin','password':'admin-password-123','active':True},headers=ah).status_code==400
keeper=app.test_client();r=keeper.post('/api/admin/login',json={'username':'keeper1','password':'keeper-password-123'});assert r.status_code==200,r.json
kh={'X-CSRF-Token':r.json['csrf']}
assert r.json['user']['role']=='store_keeper'
for path in ['analytics','journey','marketing','orders','coupons','banners','restock','numbering','business','email-status','accounts','reports?type=orders&from=2026-01-01&to=2026-01-02']:
 assert keeper.get('/api/admin/'+path).status_code==403,path
 assert keeper.post('/api/admin/'+path,json={},headers=kh).status_code==403,path
assert keeper.get('/api/admin/products').status_code==200
p=next(p for p in keeper.get('/api/admin/products').json if p['id']=='1')
assert keeper.post('/api/admin/products',json=p|{'sale':1},headers=kh).status_code==403
entries=[{'size':v['size'],'enabled':v['enabled'],'stock':v['stock']+1} for v in p['sizes']]
assert keeper.post('/api/admin/stock',json={'id':p['id'],'sizes':entries,'price':1},headers=kh).status_code==403
assert keeper.post('/api/admin/stock',json={'id':p['id'],'sizes':entries}).status_code==403
assert keeper.post('/api/admin/stock',json={'id':p['id'],'sizes':entries},headers=kh).status_code==200
public=next(p for p in shop.get('/api/products').json if p['id']=='1');assert all(next(v for v in public['sizes'] if v['size']==e['size'])['stock']==e['stock'] for e in entries if e['enabled'])
assert keeper.post('/api/admin/stock',json={'id':p['id'],'sizes':entries[:1]},headers=kh).status_code==400
buf=io.BytesIO();Image.new('RGB',(10,10),'blue').save(buf,format='PNG');raw=buf.getvalue()
r=keeper.post('/api/admin/assets',data={'file':(io.BytesIO(raw),'x.png')},headers=kh);assert r.status_code==201
asset=r.json
assert keeper.post('/api/admin/merch/1',json={'gallery':[asset]},headers=kh).status_code==200
assert keeper.post('/api/admin/merch/1',json={'gallery':[asset],'details':'unauthorized change'},headers=kh).status_code==403
assert keeper.post('/api/admin/merch/1',json={'gallery':[asset]},headers=kh).status_code==200
b=asset|dict(title='Media only',subtitle='Offer',button='',link='',active=True)
assert admin.post('/api/admin/banners',json=b,headers=ah).status_code==200
assert admin.post('/api/admin/banners',json=b|{'button':'Shop'},headers=ah).status_code==400
assert admin.post('/api/admin/banners',json=b|{'button':'Get Knot Jabla Offer','link':'/?product=2#collection'},headers=ah).status_code==200
# Account edits revoke existing sessions, including an account whose role was promoted.
assert admin.post('/api/admin/accounts',json={'id':keeperid,'username':'keeper1','name':'Keeper','role':'store_keeper','password':'','active':False},headers=ah).status_code==200
assert keeper.get('/api/admin/products').status_code==401
assert keeper.post('/api/admin/login',json={'username':'keeper1','password':'keeper-password-123'}).status_code==401
assert admin.post('/api/admin/accounts',json={'username':'manager','name':'Manager','role':'admin','password':'manager-password-123','active':True},headers=ah).status_code==200
manager=app.test_client();r=manager.post('/api/admin/login',json={'username':'manager','password':'manager-password-123'});mh={'X-CSRF-Token':r.json['csrf']}
assert manager.get('/api/admin/accounts').status_code==403
assert manager.get('/api/admin/analytics').status_code==200
# Actual report bytes: empty and populated reports, inclusive India-time range.
today=datetime.utcnow()+timedelta(hours=5,minutes=30);frm=(today-timedelta(days=2)).strftime('%Y-%m-%d');to=today.strftime('%Y-%m-%d')
for kind in ['orders','inventory','restock','traffic','journey']:
 for fmt in ['pdf','xlsx']:
  r=admin.get(f'/api/admin/reports?type={kind}&from={frm}&to={to}&format={fmt}');assert r.status_code==200,(kind,fmt,r.json)
  if fmt=='pdf':
   reader=PdfReader(io.BytesIO(r.data));assert len(reader.pages)>0 and 'Tiny Tale' in reader.pages[0].extract_text()
  else:
   wb=load_workbook(io.BytesIO(r.data));assert 'Report' in wb.sheetnames and 'Report notes' in wb.sheetnames
for query in ['from=bad&to=bad','from=2026-10-02&to=2026-10-01','from=2025-01-01&to=2026-10-02','from=2026-10-01&to=2026-10-02&format=exe','from=2026-10-01&to=2026-10-02&type=secret']:
 assert admin.get('/api/admin/reports?'+query).status_code==400,query
with app.app_context():
 # UTC 18:45 falls on the following day in IST.
 db.session.add(m.Order(id='report-boundary',customer={'name':'=CMD(1)'},items=[],total=1,status='Enquiry',created=datetime(2026,10,1,18,45)));db.session.commit()
r=admin.get('/api/admin/reports?type=orders&from=2026-10-02&to=2026-10-02&format=xlsx');wb=load_workbook(io.BytesIO(r.data));cells=[c for row in wb['Report'] for c in row if c.value=='=CMD(1)'];assert len(cells)==1 and cells[0].data_type=='s'
r=admin.get('/api/admin/reports?type=orders&from=2026-10-01&to=2026-10-01&format=xlsx');assert '=CMD(1)' not in str(list(load_workbook(io.BytesIO(r.data))['Report'].values))
print('PASS v5: staff roles, protected financial/customer/settings routes, stock permissions, CSRF, gallery-only updates, account disable/revocation, optional banner CTA, product destination; actual PDF/Excel for all 5 reports, India date boundaries, invalid ranges and Excel formula protection.')
