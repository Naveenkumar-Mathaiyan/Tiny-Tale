"""Storefront presentation settings shared through the existing database."""
import re
from urllib.parse import urlsplit
from flask import request, jsonify

def safe_destination(value):
 if not isinstance(value,str):raise ValueError('Use a text URL for the destination.')
 value=value.strip()
 if not value:return ''
 if len(value)>500 or re.search(r'[\s\\\x00-\x1f\x7f]',value):raise ValueError('Use a URL up to 500 characters, without spaces or backslashes.')
 if value=='login':return value
 u=urlsplit(value)
 if value.startswith('#') and len(value)>1:return value
 if value.startswith('/') and not value.startswith('//') and not u.scheme and not u.netloc:return value
 if u.scheme=='https' and u.hostname and not u.username and not u.password:
  try:u.port
  except ValueError:raise ValueError('Enter a valid HTTPS URL.')
  return value
 raise ValueError('Choose a product, a store path starting with /, an anchor starting with #, login, or a full https:// URL.')

def install(m):
 app,db=m.app,m.db
 defaults=dict(enabled=True,speed='normal',highlights=[dict(text='Free delivery from ₹999',link='#collection'),dict(text='Login for an extra 5% on products',link='login'),dict(text='Choose the right size for your little one',link='#collection')])
 def settings():
  row=db.session.get(m.Setting,'appearance');return {**defaults,**(row.value if row else {})}
 @app.get('/api/appearance')
 def appearance():return jsonify(settings())
 @app.route('/api/admin/appearance',methods=['GET','POST'])
 @m.admin
 def admin_appearance():
  if request.method=='GET':return jsonify(settings())
  d=request.get_json(silent=True)
  try:
   if not isinstance(d,dict) or type(d.get('enabled'))is not bool or d.get('speed') not in ['slow','normal','fast']:raise ValueError('Choose a valid visibility and scrolling speed.')
   highlights=d.get('highlights')
   if not isinstance(highlights,list) or not 1<=len(highlights)<=8:raise ValueError('Add 1–8 highlights.')
   rows=[]
   for x in highlights:
    if not isinstance(x,dict) or not isinstance(x.get('text'),str) or not 1<=len(x['text'].strip())<=140:raise ValueError('Each highlight needs 1–140 characters.')
    rows.append(dict(text=x['text'].strip(),link=safe_destination(x.get('link',''))))
   data=dict(enabled=d['enabled'],speed=d['speed'],highlights=rows)
  except ValueError as e:return jsonify(error=str(e)),400
  row=db.session.get(m.Setting,'appearance')
  if row:row.value=data
  else:db.session.add(m.Setting(key='appearance',value=data))
  db.session.commit();return jsonify(data)
