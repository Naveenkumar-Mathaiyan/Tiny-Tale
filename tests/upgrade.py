"""Verify additive migration of a database made with the previous build."""
import os, subprocess, tempfile
from pathlib import Path
base=Path(__file__).resolve().parents[1]
old=Path(os.environ.get('TINY_TALE_PREVIOUS_BUILD',str(base.parent/'tiny-tale')))
if not old.exists():
 raise SystemExit('Place the previous tiny-tale build beside this folder to run this migration test.')
with tempfile.TemporaryDirectory() as tmp:
 env=dict(os.environ,DATABASE_URL='sqlite:///'+tmp+'/old.db',SECRET_KEY='upgrade-test',APP_ROLE='admin')
 seed="""
from app import app,db,Product,Order,Coupon,Media
with app.app_context():
 p=db.session.get(Product,'1');p.stock=7;p.name='Owner product';p.sale=211
 db.session.add(Order(id='legacy-enquiry',customer={},items=[dict(id='1',name=p.name,qty=2,price=211)],total=491,status='Enquiry'))
 db.session.add(Media(id='existing-image',content='saved-image-content'))
 db.session.get(Coupon,'TINY10').percent=12
 db.session.commit()
"""
 subprocess.run([os.sys.executable,'-c',seed],cwd=old,env=env,check=True)
 check="""
from app import app,db,Product,ProductSize,Order,Coupon,Media
with app.app_context():
 p=db.session.get(Product,'1');v=db.session.get(ProductSize,('1','One size'))
 assert (p.name,p.sale,p.stock,v.stock)==('Owner product',211,7,7)
 assert db.session.get(Order,'legacy-enquiry').items[0]['qty']==2
 assert db.session.get(Media,'existing-image').content=='saved-image-content'
 assert db.session.get(Coupon,'TINY10').percent==12
 assert ProductSize.query.filter_by(product_id='1').count()==1
"""
 for _ in range(2): subprocess.run([os.sys.executable,'-c',check],cwd=base,env=env,check=True)
print('PASS: old products, prices, stock, enquiry, uploaded media and coupon preserved; startup migration idempotent.')
