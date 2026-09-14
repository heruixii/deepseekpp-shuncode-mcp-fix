#!/usr/bin/env python3
from pathlib import Path
import sys,json,hashlib
EXPECTED={
 'content-scripts/content.js':'BE313679C61165EC7489E0C2B7D727FE6451D10738FF3A2596C526FE6BF441C5',
 'manifest.json':'71F1C51A7044B5213209D9612668317B92409916E5EC05E341EE1DA9AC4C1735',
 '_locales/en/messages.json':'0EDC7FB4A7A28B43599409E5CF5A712C1348AC49B4D8C21158B03FDED6D02055',
 '_locales/zh_CN/messages.json':'34600D6F2D4CCA4D64E7C48F49E9A39186439DCE40731E7E25B7704DE609C99B',
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def one(s,a,b,label):
 c=s.count(a)
 if c!=1:raise RuntimeError(f'{label} anchor count {c}')
 return s.replace(a,b,1)
def transform(root):
 paths={k:root/Path(k) for k in EXPECTED}
 for k,p in paths.items():
  if not p.is_file():raise RuntimeError(f'missing {k}')
  got=sha(p)
  if got!=EXPECTED[k]:raise RuntimeError(f'{k} hash mismatch {got} != {EXPECTED[k]}')
 m=json.loads(paths['manifest.json'].read_text(encoding='utf8'))
 if m.get('version')!='1.14.0.7' or m.get('version_name')!='1.14.0 ShunCode MCP Fix 3.3.10.2':raise RuntimeError('expected Fix 3.3.10.2 manifest')
 s=paths['content-scripts/content.js'].read_text(encoding='utf8')
 anchor='function VR(e){let{submitTurn:t,session:n,serializePrompt:r,mapToolCall:i,toolDescriptors:a,turnDefaults:o}=e;'
 s=one(s,anchor,'function DPP_PARENT_FALLBACK_33103(e,t,n){return e?.dppInvalidMessageId339===!0&&t!==null&&t!==void 0&&t!==n?t:null}'+anchor,'VR')
 s=one(s,'f={chatSessionId:s,parentMessageId:t.parentMessageId,setParentMessageId:e=>{f.parentMessageId=e}}','f={chatSessionId:s,parentMessageId:t.parentMessageId,previousParentMessageId:null,setParentMessageId:(e,t=f.parentMessageId)=>{f.previousParentMessageId=t,f.parentMessageId=e}}','session')
 old='re=e=>{for(let t of e.completed)te({name:t.name,invocationName:t.invocationName??t.name,payload:t.payload},`stream`);for(let t of e.failed)te({name:t.name,invocationName:t.invocationName??t.name,payload:t.payload},`stream-failed`)},ie=await t(l,{onTextChunk(e){if(DPPControlQuarantine)return;S||(x.length+e.length>12e4?(S=!0,x=``):x+=e);let t=u.append(e),n=t.slice(DPPVisibleLen);DPPVisibleLen=t.length,ee(DPPNoise.append(n)),re(h.append(e));if(DPPNoise.isStorm())DPPControlQuarantine=!0,S=!0,x=``},onReasoningChunk(e,t){ne(t)},onTokenSpeed(t){e.onTokenSpeed?.(t)}},d);'
 new='re=e=>{for(let t of e.completed)te({name:t.name,invocationName:t.invocationName??t.name,payload:t.payload},`stream`);for(let t of e.failed)te({name:t.name,invocationName:t.invocationName??t.name,payload:t.payload},`stream-failed`)},DPPHandlers={onTextChunk(e){if(DPPControlQuarantine)return;S||(x.length+e.length>12e4?(S=!0,x=``):x+=e);let t=u.append(e),n=t.slice(DPPVisibleLen);DPPVisibleLen=t.length,ee(DPPNoise.append(n)),re(h.append(e));if(DPPNoise.isStorm())DPPControlQuarantine=!0,S=!0,x=``},onReasoningChunk(e,t){ne(t)},onTokenSpeed(t){e.onTokenSpeed?.(t)}},ie;try{ie=await t(l,DPPHandlers,d)}catch(DPPParentError){let DPPFallbackParent=DPP_PARENT_FALLBACK_33103(DPPParentError,n.previousParentMessageId,l.parentMessageId);if(DPPFallbackParent===null)throw DPPParentError;l={...l,parentMessageId:DPPFallbackParent},ie=await t(l,DPPHandlers,d)};'
 s=one(s,old,new,'submit')
 s=one(s,'if(n.setParentMessageId(ie.responseMessageId),re(h.flush()),','if(n.setParentMessageId(ie.responseMessageId,l.parentMessageId),re(h.flush()),','setParent')
 m['version']='1.14.0.8';m['version_name']='1.14.0 ShunCode MCP Fix 3.3.10.3'
 out={'content-scripts/content.js':s,'manifest.json':json.dumps(m,ensure_ascii=False,indent=2)+'\n'}
 for rel in ['_locales/en/messages.json','_locales/zh_CN/messages.json']:
  o=json.loads(paths[rel].read_text(encoding='utf8'))
  for v in o.values():
   if isinstance(v,dict) and isinstance(v.get('message'),str):v['message']=v['message'].replace('Fix 3.3.10.2','Fix 3.3.10.3')
  out[rel]=json.dumps(o,ensure_ascii=False,indent=2)+'\n'
 return out
def main():
 root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
 try:out=transform(root)
 except Exception as e:print(f'APPLY_FIX33103_FAIL: {e}',file=sys.stderr);return 1
 for rel,text in out.items():(root/rel).write_text(text,encoding='utf8',newline='')
 print('APPLY_FIX33103_PASS');return 0
if __name__=='__main__':raise SystemExit(main())