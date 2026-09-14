#!/usr/bin/env python3
from pathlib import Path
import sys,json,hashlib
EXPECTED={
 'content-scripts/content.js':'BD65AA73CE2AA73DE1A1A23C0797212DF9E0A213BF05CF8C5A755CD75143DF79',
 'manifest.json':'7BB0FC29DE14E5D402D2EA8DF472E56F618E846643DDF7E10BF06A61A48B26C6',
 '_locales/en/messages.json':'FBD72F7467C33B7B23B5D3B415F9AA657E43CC08F9084FB020706F80FBB80572',
 '_locales/zh_CN/messages.json':'CBD5C157BEB1B3E6E68D9FB2046616E5CFE47DEBB01B5EDDC0E987BF96F8C49D',
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
 if m.get('version')!='1.14.0.4' or m.get('version_name')!='1.14.0 ShunCode MCP Fix 3.3.9':raise RuntimeError('expected Fix 3.3.9 manifest')
 s=paths['content-scripts/content.js'].read_text(encoding='utf8')
 anchor='function kR(e){return new AR(ct(e).invocationNames)}'
 insert=r'''function DPP_CONTROL_NOISE_LINE_3310(e,t){let n=0,r=e.replace(/<\s*\/\s*(?:invoke|parameter)\s*>/gi,()=>{n+=1;return``}).replace(/<\s*\/\s*[|｜]{1,2}\s*DSML\s*[|｜]{1,2}\s*(?:parameter|invoke|calls|tool_calls)\s*>/gi,()=>{n+=1;return``}).replace(/<\s*\/\s*([A-Za-z_][A-Za-z0-9_.:-]*)\s*>/g,(e,r)=>t.has(r)?(n+=1,``):e);return{drop:n>0&&!r.trim(),count:n}}function DPP_CONTROL_NOISE_FILTER_3310(e){return new DPP_CONTROL_NOISE_3310(ct(e).invocationNames)}var DPP_CONTROL_NOISE_LIMIT_3310=24;var DPP_CONTROL_NOISE_3310=class{names;pending=``;visible=``;inFence=!1;noiseCount=0;storm=!1;constructor(e){this.names=new Set(e)}append(e){if(!e)return this.visible;this.pending+=e;for(;;){let e=this.pending.indexOf(`\n`);if(e===-1)break;let t=this.pending.slice(0,e+1);this.pending=this.pending.slice(e+1),this.consumeLine(t)}return this.visible}flush(){return this.pending&&(this.consumeLine(this.pending),this.pending=``),this.visible}consumeLine(e){let t=(e.match(/```/g)||[]).length;if(!this.inFence&&t===0){let t=DPP_CONTROL_NOISE_LINE_3310(e,this.names);if(t.drop){this.noiseCount+=t.count,this.noiseCount>=DPP_CONTROL_NOISE_LIMIT_3310&&(this.storm=!0);return}}this.visible+=e,t%2===1&&(this.inFence=!this.inFence)}isStorm(){return this.storm}};function DPP_STABLE_TOOL_VALUE_3310(e){if(e===null||typeof e!=`object`)return JSON.stringify(e);if(Array.isArray(e))return`[${e.map(DPP_STABLE_TOOL_VALUE_3310).join(`,`)}]`;let t=Object.keys(e).sort();return`{${t.map(t=>`${JSON.stringify(t)}:${DPP_STABLE_TOOL_VALUE_3310(e[t])}`).join(`,`)}}`}function DPP_TOOL_SIGNATURE_3310(e){return`${e.invocationName??e.name??``}\n${DPP_STABLE_TOOL_VALUE_3310(e.payload??{})}`}'''
 s=one(s,anchor,insert+anchor,'kR')
 s=one(s,'let l={chatSessionId:n.chatSessionId,parentMessageId:n.parentMessageId,modelType:o.modelType??s.id??null,prompt:r(c),refFileIds:o.refFileIds,thinkingEnabled:o.thinkingEnabled,searchEnabled:o.searchEnabled},u=kR(a),h=vR(a),g=``,_=null,v=null,y=``,b=0,x=``,S=!1,','let l={chatSessionId:n.chatSessionId,parentMessageId:n.parentMessageId,modelType:o.modelType??s.id??null,prompt:r(c),refFileIds:o.refFileIds,thinkingEnabled:o.thinkingEnabled,searchEnabled:o.searchEnabled},u=kR(a),h=vR(a),DPPNoise=DPP_CONTROL_NOISE_FILTER_3310(a),DPPVisibleLen=0,DPPStreamSigs=new Set,g=``,_=null,v=null,y=``,b=0,x=``,S=!1,','VR-locals')
 s=one(s,'te=e=>{let t=i(e,b);b+=1;let n=f.content.length;f.content.push({type:`toolCall`,id:t.id,name:t.name,arguments:{}}),p({type:`toolcall_start`,contentIndex:n,partial:m()}),f.content[n]=t,p({type:`toolcall_end`,contentIndex:n,toolCall:t,partial:m()})},','te=(e,t=`stream`)=>{let n=DPP_TOOL_SIGNATURE_3310(e);if(t===`fallback-legacy`&&DPPStreamSigs.has(n))return;t===`stream`&&DPPStreamSigs.add(n);let r=i(e,b);b+=1;let a=f.content.length;f.content.push({type:`toolCall`,id:r.id,name:r.name,arguments:{}}),p({type:`toolcall_start`,contentIndex:a,partial:m()}),f.content[a]=r,p({type:`toolcall_end`,contentIndex:a,toolCall:r,partial:m()})},','te')
 s=one(s,'re=e=>{for(let t of e.completed)te({name:t.name,invocationName:t.invocationName??t.name,payload:t.payload});for(let t of e.failed)te({name:t.name,invocationName:t.invocationName??t.name,payload:t.payload})},','re=e=>{for(let t of e.completed)te({name:t.name,invocationName:t.invocationName??t.name,payload:t.payload},`stream`);for(let t of e.failed)te({name:t.name,invocationName:t.invocationName??t.name,payload:t.payload},`stream-failed`)},','re')
 s=one(s,'ie=await t(l,{onTextChunk(e){S||(x.length+e.length>12e4?(S=!0,x=``):x+=e),ee(u.append(e)),re(h.append(e))},onReasoningChunk(e,t){ne(t)},onTokenSpeed(t){e.onTokenSpeed?.(t)}},d);','ie=await t(l,{onTextChunk(e){S||(x.length+e.length>12e4?(S=!0,x=``):x+=e);let t=u.append(e),n=t.slice(DPPVisibleLen);DPPVisibleLen=t.length,ee(DPPNoise.append(n)),re(h.append(e));if(DPPNoise.isStorm())throw Error(`DeepSeek emitted repeated malformed tool-control markup; stopped this turn to prevent a continuation loop.`)},onReasoningChunk(e,t){ne(t)},onTokenSpeed(t){e.onTokenSpeed?.(t)}},d);','onText')
 s=one(s,'if(n.setParentMessageId(ie.responseMessageId),re(h.flush()),ee(u.flush()),!S&&x&&(x.includes(`\\uff5cDSML\\uff5c`)||b===0&&x.includes(`<`)))for(let e of Ea(x,{descriptors:a}))te({name:e.name,invocationName:e.invocationName??e.name,payload:e.payload});','if(n.setParentMessageId(ie.responseMessageId),re(h.flush()),(()=>{let e=u.flush(),t=e.slice(DPPVisibleLen);DPPVisibleLen=e.length,ee(DPPNoise.append(t)),ee(DPPNoise.flush())})(),!S&&x){let e=x.includes(`\\uff5cDSML\\uff5c`),t=e?Oa(x,ct(a)):b===0&&x.includes(`<`)?Da(x,ct(a)):[];for(let n of t)te({name:n.name,invocationName:n.invocationName??n.name,payload:n.payload},e?`fallback-legacy`:`fallback-direct`)}','fallback')
 m['version']='1.14.0.5';m['version_name']='1.14.0 ShunCode MCP Fix 3.3.10'
 out={'content-scripts/content.js':s,'manifest.json':json.dumps(m,ensure_ascii=False,indent=2)+'\n'}
 for rel in ['_locales/en/messages.json','_locales/zh_CN/messages.json']:
  o=json.loads(paths[rel].read_text(encoding='utf8'))
  for v in o.values():
   if isinstance(v,dict) and isinstance(v.get('message'),str):v['message']=v['message'].replace('Fix 3.3.9','Fix 3.3.10')
  out[rel]=json.dumps(o,ensure_ascii=False,indent=2)+'\n'
 return out
def main():
 root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
 try:out=transform(root)
 except Exception as e:print(f'APPLY_FIX3310_FAIL: {e}',file=sys.stderr);return 1
 for rel,text in out.items():(root/rel).write_text(text,encoding='utf8',newline='')
 print('APPLY_FIX3310_PASS');return 0
if __name__=='__main__':raise SystemExit(main())