from v5 import *
from experience import safe_destination
for link in ['', 'login','#collection','#my-offer','/?product=2#collection','/offers?coupon=BABY15','https://example.com/sale?campaign=tiny','https://instagram.com/tiny_tale/']:
 assert safe_destination(link)==link
for link in ['javascript:alert(1)','data:text/html,test','http://example.com','//example.com','/\\example.com','https://user:pass@example.com','https://example.com/a b','https://example.com:bad','https://[bad','https://exa\nmple.com/','invalid words']:
 try:safe_destination(link)
 except ValueError:pass
 else:raise AssertionError(link)
assert admin.get('/api/admin/appearance').status_code==200
r=admin.post('/api/admin/appearance',json={'enabled':True,'speed':'slow','highlights':[{'text':'Knot Jabla offer','link':'/?product=2#collection'},{'text':'See our Instagram','link':'https://instagram.com/tiny_tale/'}]},headers=ah)
assert r.status_code==200,r.json
assert shop.get('/api/appearance').json['highlights'][0]['text']=='Knot Jabla offer'
assert admin.post('/api/admin/appearance',json={'enabled':True,'speed':'slow','highlights':[]},headers=ah).status_code==400
assert admin.post('/api/admin/appearance',json={'enabled':True,'speed':'slow','highlights':[{'text':'Test','link':'javascript:alert(1)'}]},headers=ah).status_code==400
assert admin.post('/api/admin/appearance',json={'enabled':'true','speed':'slow','highlights':[{'text':'Test','link':''}]},headers=ah).status_code==400
assert admin.post('/api/admin/appearance',json={'enabled':False,'speed':'fast','highlights':[{'text':'Offer without a link','link':''}]},headers=ah).status_code==200
assert shop.get('/api/appearance').json['enabled'] is False
# Staff access remains restricted for newly added settings, including direct API calls.
r=manager.get('/api/admin/appearance');assert r.status_code==200
keeper=app.test_client()
assert admin.post('/api/admin/accounts',json={'username':'keeper6','name':'Keeper','role':'store_keeper','password':'keeper6-password-123','active':True},headers=ah).status_code==200
r=keeper.post('/api/admin/login',json={'username':'keeper6','password':'keeper6-password-123'});kh={'X-CSRF-Token':r.json['csrf']}
assert keeper.get('/api/admin/appearance').status_code==403
assert keeper.post('/api/admin/appearance',json={},headers=kh).status_code==403
b=asset|dict(title='Custom offer',subtitle='',button='See offer',link='https://example.com/offer',new_tab=True,active=True)
r=admin.post('/api/admin/banners',json=b,headers=ah);assert r.status_code==200 and r.json['new_tab'] is True
assert any(x['link']=='https://example.com/offer' and x['new_tab'] for x in shop.get('/api/banners').json)
for link in ['javascript:alert(1)','//evil.test','http://evil.test']:
 assert admin.post('/api/admin/banners',json=b|{'link':link},headers=ah).status_code==400
assert admin.post('/api/admin/banners',json=b|{'new_tab':'yes'},headers=ah).status_code==400
assert admin.post('/api/admin/banners',json=b|{'link':'/offers?code=TINY10#collection','new_tab':False},headers=ah).status_code==200
print('PASS v6: custom internal/HTTPS destinations, new-tab persistence, unsafe URL rejection, public appearance sync, highlight validation, optional highlight links, hide/speed settings and store keeper access denial.')
