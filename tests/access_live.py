"""Public anahtarla gerçek Supabase negatif güvenlik kontrolleri."""
import json,sys,urllib.request,urllib.error
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/'config/access.public.json').read_text(encoding='utf-8'))
def request(path,body=None,origin=None,bearer=None):
    headers={'apikey':d['publishable_key'],'Content-Type':'application/json'}
    if origin:headers['Origin']=origin
    if bearer:headers['Authorization']='Bearer '+bearer
    req=urllib.request.Request(d['supabase_url']+path,headers=headers,data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req,timeout=15) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as ex:
        try:body=json.load(ex)
        except Exception:body={}
        return ex.code,body
rows=[]
def check(name,fn):
    try:assert fn();rows.append({'name':name,'status':'PASS'})
    except Exception as ex:rows.append({'name':name,'status':'FAIL','error':type(ex).__name__})
endpoint='/functions/v1/thaimcp-access'
check('Invalid API key rejected',lambda:request(endpoint,{'action':'verify','key':'Invalid00000'})==(200,{'valid':False}))
check('Admin without JWT rejected',lambda:request(endpoint,{'action':'list'})[0]==401)
check('Forged admin JWT rejected',lambda:request(endpoint,{'action':'create','label':'test'},bearer='invalid.forged.token')[0]==401)
check('Wrong origin rejected',lambda:request(endpoint,{'action':'verify','key':'Invalid00000'},'https://evil.com')[0]==403)
for table in ['thaimcp_api_keys','thaimcp_admins','thaimcp_usage']:
    check('Publishable cannot read '+table,lambda table=table:request('/rest/v1/'+table+'?select=*')[0] in (401,403))
check('Publishable cannot invoke trusted RPC',lambda:request('/rest/v1/rpc/thaimcp_access',{'p_action':'list'})[0] in (401,403))
print(json.dumps(rows,ensure_ascii=True,indent=2));sys.exit(0 if all(r['status']=='PASS' for r in rows) else 1)
