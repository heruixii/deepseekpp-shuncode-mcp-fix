#!/usr/bin/env python3
from pathlib import Path
import sys,json,hashlib
EXPECTED={
 'content-scripts/main-world.js':'2FD210B8165F695BAC74F31847036383C320F599620A04B3DEAD4B1525D70D66',
 'manifest.json':'48872CD5A72BC96398FE9FB673EFBD7EC6449EFFE81C231E0863D3ED119733F1',
 '_locales/en/messages.json':'E85A9A260BC9F1C49022FC557903DE37B1C7934A8134F69E31C9333FEA6CC075',
 '_locales/zh_CN/messages.json':'E53196A4D542F023A016CB9E217D061215853A80F49910853F84B1326C8D7578',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def one(s,a,b,label):
 c=s.count(a)
 if c!=1: raise RuntimeError(f'{label} anchor count {c}')
 return s.replace(a,b,1)
def transform(root):
 ps={k:root/Path(k) for k in EXPECTED}
 for k,p in ps.items():
  if not p.is_file(): raise RuntimeError(f'missing {k}')
  got=sha(p)
  if got!=EXPECTED[k]: raise RuntimeError(f'{k} hash mismatch {got} != {EXPECTED[k]}')
 m=json.loads(ps['manifest.json'].read_text(encoding='utf8'))
 if m.get('version')!='1.14.0.8' or m.get('version_name')!='1.14.0 ShunCode MCP Fix 3.3.10.3':
  raise RuntimeError('expected Fix 3.3.10.3 manifest')
 s=ps['content-scripts/main-world.js'].read_text(encoding='utf8')
 anchor='function Er(e,t,n){let r=e.filter(e=>!oi(e));r.length!==e.length&&e.splice(0,e.length,...r);let i=0,a=Mr(r);r.forEach((e,r)=>{let o=Nr(e,a),s=!o;ci(e),ti(e,{replaceTaskComplete:o});let c=jr(e,n),l=Ar(e,r,Pr(e)||c?i++:null),u=kr(e,r);if(typeof e.content==`string`&&I(e.content,n)){if(s){let r=zr(e.content,`${u}:content`,n,l);r&&t.push(r)}e.content=Vr(e.content,n)}Dr(e.fragments,u,t,n,l,s)})}'
 helper='function DPP_HISTORY_CONTROL_FILTER_33104(e,t){if(typeof e!=`string`||!e)return e;let n=new Set(P(t).invocationNames),r={inFence:!1};return DPP_PAGE_CONTROL_FILTER_33102(e,n,r)}function DPP_HISTORY_FRAGMENT_FILTER_33104(e,t){if(!Array.isArray(e))return;let n=new Set(P(t).invocationNames),r={inFence:!1};for(let i of e)if(i&&typeof i.content==`string`)i.content=DPP_PAGE_CONTROL_FILTER_33102(i.content,n,r)}'
 new='function Er(e,t,n){let r=e.filter(e=>!oi(e));r.length!==e.length&&e.splice(0,e.length,...r);let i=0,a=Mr(r);r.forEach((e,r)=>{let o=Nr(e,a),s=!o;ci(e),ti(e,{replaceTaskComplete:o});let c=jr(e,n),l=Ar(e,r,Pr(e)||c?i++:null),u=kr(e,r);if(typeof e.content==`string`){if(I(e.content,n)){if(s){let r=zr(e.content,`${u}:content`,n,l);r&&t.push(r)}e.content=Vr(e.content,n)}Pr(e)&&(e.content=DPP_HISTORY_CONTROL_FILTER_33104(e.content,n))}Dr(e.fragments,u,t,n,l,s),Pr(e)&&DPP_HISTORY_FRAGMENT_FILTER_33104(e.fragments,n)})}'
 s=one(s,anchor,helper+new,'history Er')
 m['version']='1.14.0.9';m['version_name']='1.14.0 ShunCode MCP Fix 3.3.10.4'
 out={'content-scripts/main-world.js':s,'manifest.json':json.dumps(m,ensure_ascii=False,indent=2)+'\n'}
 for rel in ['_locales/en/messages.json','_locales/zh_CN/messages.json']:
  o=json.loads(ps[rel].read_text(encoding='utf8'))
  for v in o.values():
   if isinstance(v,dict) and isinstance(v.get('message'),str):
    v['message']=v['message'].replace('Fix 3.3.10.3','Fix 3.3.10.4')
  out[rel]=json.dumps(o,ensure_ascii=False,indent=2)+'\n'
 return out
def main():
 root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
 try: out=transform(root)
 except Exception as e:
  print(f'APPLY_FIX33104_FAIL: {e}',file=sys.stderr);return 1
 for rel,text in out.items(): (root/rel).write_text(text,encoding='utf8',newline='')
 print('APPLY_FIX33104_PASS');return 0
if __name__=='__main__': raise SystemExit(main())