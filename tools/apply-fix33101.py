#!/usr/bin/env python3
from pathlib import Path
import sys,json,hashlib
EXPECTED={
 'content-scripts/content.js':'DA3E11B93B578D1D5BDA1A9F1793859DCE9EED7A4058E6FDC7F22AFBAE4FB231',
 'manifest.json':'8C9EDEB70CC11A2DB50293EF6C6D37050602689711A74B7FF08AA46CECEE4A57',
 '_locales/en/messages.json':'F91759A53E05497A6E5AF0FF48E7C444A24C5F1E8AAD86510B07D2E9BD4913C6',
 '_locales/zh_CN/messages.json':'63166D6BCA41B4524B23CBD8F85322D81D1F641AA0F8A768CFF45192A0291BA1',
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
 if m.get('version')!='1.14.0.5' or m.get('version_name')!='1.14.0 ShunCode MCP Fix 3.3.10':raise RuntimeError('expected Fix 3.3.10 manifest')
 s=paths['content-scripts/content.js'].read_text(encoding='utf8')
 s=one(s,'let l={chatSessionId:n.chatSessionId,parentMessageId:n.parentMessageId,modelType:o.modelType??s.id??null,prompt:r(c),refFileIds:o.refFileIds,thinkingEnabled:o.thinkingEnabled,searchEnabled:o.searchEnabled},u=kR(a),h=vR(a),DPPNoise=DPP_CONTROL_NOISE_FILTER_3310(a),DPPVisibleLen=0,DPPStreamSigs=new Set,g=``,_=null,v=null,y=``,b=0,x=``,S=!1,','let l={chatSessionId:n.chatSessionId,parentMessageId:n.parentMessageId,modelType:o.modelType??s.id??null,prompt:r(c),refFileIds:o.refFileIds,thinkingEnabled:o.thinkingEnabled,searchEnabled:o.searchEnabled},u=kR(a),h=vR(a),DPPNoise=DPP_CONTROL_NOISE_FILTER_3310(a),DPPVisibleLen=0,DPPStreamSigs=new Set,DPPControlQuarantine=!1,g=``,_=null,v=null,y=``,b=0,x=``,S=!1,','locals')
 s=one(s,'ie=await t(l,{onTextChunk(e){S||(x.length+e.length>12e4?(S=!0,x=``):x+=e);let t=u.append(e),n=t.slice(DPPVisibleLen);DPPVisibleLen=t.length,ee(DPPNoise.append(n)),re(h.append(e));if(DPPNoise.isStorm())throw Error(`DeepSeek emitted repeated malformed tool-control markup; stopped this turn to prevent a continuation loop.`)},onReasoningChunk(e,t){ne(t)},onTokenSpeed(t){e.onTokenSpeed?.(t)}},d);','ie=await t(l,{onTextChunk(e){if(DPPControlQuarantine)return;S||(x.length+e.length>12e4?(S=!0,x=``):x+=e);let t=u.append(e),n=t.slice(DPPVisibleLen);DPPVisibleLen=t.length,ee(DPPNoise.append(n)),re(h.append(e));if(DPPNoise.isStorm())DPPControlQuarantine=!0,S=!0,x=``},onReasoningChunk(e,t){ne(t)},onTokenSpeed(t){e.onTokenSpeed?.(t)}},d);','onText')
 s=one(s,'if(n.setParentMessageId(ie.responseMessageId),re(h.flush()),(()=>{let e=u.flush(),t=e.slice(DPPVisibleLen);DPPVisibleLen=e.length,ee(DPPNoise.append(t)),ee(DPPNoise.flush())})(),!S&&x){let e=x.includes(`\\uff5cDSML\\uff5c`),t=e?Oa(x,ct(a)):b===0&&x.includes(`<`)?Da(x,ct(a)):[];for(let n of t)te({name:n.name,invocationName:n.invocationName??n.name,payload:n.payload},e?`fallback-legacy`:`fallback-direct`)}','if(n.setParentMessageId(ie.responseMessageId),re(h.flush()),(()=>{let e=u.flush(),t=e.slice(DPPVisibleLen);DPPVisibleLen=e.length,ee(DPPNoise.append(t)),ee(DPPNoise.flush())})(),!DPPControlQuarantine&&!S&&x){let e=x.includes(`\\uff5cDSML\\uff5c`),t=e?Oa(x,ct(a)):b===0&&x.includes(`<`)?Da(x,ct(a)):[];for(let n of t)te({name:n.name,invocationName:n.invocationName??n.name,payload:n.payload},e?`fallback-legacy`:`fallback-direct`)}','fallback')
 m['version']='1.14.0.6';m['version_name']='1.14.0 ShunCode MCP Fix 3.3.10.1'
 out={'content-scripts/content.js':s,'manifest.json':json.dumps(m,ensure_ascii=False,indent=2)+'\n'}
 for rel in ['_locales/en/messages.json','_locales/zh_CN/messages.json']:
  o=json.loads(paths[rel].read_text(encoding='utf8'))
  for v in o.values():
   if isinstance(v,dict) and isinstance(v.get('message'),str):v['message']=v['message'].replace('Fix 3.3.10','Fix 3.3.10.1')
  out[rel]=json.dumps(o,ensure_ascii=False,indent=2)+'\n'
 return out
def main():
 root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
 try:out=transform(root)
 except Exception as e:print(f'APPLY_FIX33101_FAIL: {e}',file=sys.stderr);return 1
 for rel,text in out.items():(root/rel).write_text(text,encoding='utf8',newline='')
 print('APPLY_FIX33101_PASS');return 0
if __name__=='__main__':raise SystemExit(main())