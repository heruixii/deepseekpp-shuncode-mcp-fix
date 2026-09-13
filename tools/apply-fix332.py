from pathlib import Path
import hashlib,json,os,sys
EXPECTED={
 'content':'ACD898FDA2AF699095C6E8A64427ACE056179ECD8B79C7900E0790F3E6406DB0',
 'manifest':'9956EDF5F32F053784EDE2F315D318DD9F897BA57C14F57E6BFE0B394ABECF90',
 'en':'10CD9567BD5C696A34EEBFBDA87EA5E853E8CA8B92CAD273CCBCEC1A6DF1D04C',
 'zh':'DAA3C7653E6819B0A1D73FEF080AF0A48E723F47765CB5533F802A784EE6AB96',
 'ux':'bca9524b6c938f6c5ae425fffd47bf3949a788c22422e4dd99c92724f28948e6',
}
OLD_VERSION='1.14.0 ShunCode MCP Fix 3.3.1'
NEW_VERSION='1.14.0 ShunCode MCP Fix 3.3.2'
OLD_NAME='DeepSeek++ ShunCode MCP Fix 3.3.1'
NEW_NAME='DeepSeek++ ShunCode MCP Fix 3.3.2'
START='function UX(){'; END='function WX(){'
NEW_UX='''var DPP_SAFE_DOM_332=!0;function UX(){let e=iq({dispatch:_Z}),t=aq({reportError:KX}),n=nq({handleAugmentRequestBody:bZ,handleMainWorldMessage:e.handle,syncRuntimeState:c0,disconnectRuntimeState:yZ,reportError(e,t){t===void 0?console.error(e):console.error(e,t)}});return _X=n,[WX(),n,GX(`mutation-hub`,e=>t.start(e),()=>t.stop()),GX(`tool`,e=>tZ(e,t),nZ),GX(`inline-agent`,e=>rZ(e,t),iZ),e]}'''
def hbytes(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def htxt(s):return hashlib.sha256(s.encode()).hexdigest()
def stage_atomic(payload):
 staged=[]
 try:
  for p,t in payload:
   q=p.with_name(p.name+'.fix332.tmp'); q.write_text(t,encoding='utf-8',newline=''); staged.append((q,p))
  for q,p in staged: os.replace(q,p)
 finally:
  for q,_ in staged:
   try:q.unlink()
   except FileNotFoundError:pass
def main(root):
 root=Path(root); cp=root/'content-scripts/content.js'; mp=root/'manifest.json'; ep=root/'_locales/en/messages.json'; zp=root/'_locales/zh_CN/messages.json'
 s=cp.read_text(encoding='utf-8-sig'); m=json.loads(mp.read_text(encoding='utf-8-sig')); en=json.loads(ep.read_text(encoding='utf-8-sig')); zh=json.loads(zp.read_text(encoding='utf-8-sig'))
 if m.get('version_name')==NEW_VERSION and 'DPP_SAFE_DOM_332' in s:
  print('APPLY_FIX332_ALREADY_APPLIED'); return 0
 if m.get('version_name')!=OLD_VERSION: raise RuntimeError('expected Fix 3.3.1 manifest')
 for label,p,key in [('content',cp,'content'),('manifest',mp,'manifest'),('en',ep,'en'),('zh',zp,'zh')]:
  got=hbytes(p)
  if got!=EXPECTED[key]: raise RuntimeError(f'{label} file hash mismatch {got} != {EXPECTED[key]}')
 if s.count(START)!=1 or s.count(END)!=1: raise RuntimeError('UX boundary count mismatch')
 i=s.index(START); j=s.index(END,i); old=s[i:j]
 if htxt(old)!=EXPECTED['ux']: raise RuntimeError('UX block hash mismatch')
 if en.get('extension_name',{}).get('message')!=OLD_NAME or zh.get('extension_name',{}).get('message')!=OLD_NAME: raise RuntimeError('locale baseline mismatch')
 out=s[:i]+NEW_UX+s[j:]
 # Floating chat remains available on other sites, but must never inject into DeepSeek itself.
 entries=[x for x in m.get('content_scripts',[]) if 'content-scripts/floating-chat.js' in x.get('js',[])]
 if len(entries)!=1: raise RuntimeError(f'floating-chat manifest entry count={len(entries)}')
 ent=entries[0]
 if ent.get('matches')!=['<all_urls>'] or ent.get('run_at')!='document_idle': raise RuntimeError('floating-chat baseline mismatch')
 ent['exclude_matches']=['*://chat.deepseek.com/*']
 m['version_name']=NEW_VERSION
 for d in (en,zh):
  d['extension_name']['message']=NEW_NAME
  if 'extension_action_title' in d: d['extension_action_title']['message']=NEW_NAME
 payload=[(cp,out),(mp,json.dumps(m,ensure_ascii=False,indent=2)+'\n'),(ep,json.dumps(en,ensure_ascii=False,indent=2)+'\n'),(zp,json.dumps(zh,ensure_ascii=False,indent=2)+'\n')]
 stage_atomic(payload)
 print('APPLY_FIX332_PASS')
 return 0
if __name__=='__main__':
 try:sys.exit(main(sys.argv[1]))
 except Exception as e:print('APPLY_FIX332_FAIL:',e,file=sys.stderr);sys.exit(1)