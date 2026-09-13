from pathlib import Path
import hashlib,json,os,sys
EXPECTED={
 'CI':'69634c714576f990744792d49c4c782732fba4759017de25e264dd4da5f5687c',
 'UI':'31e22724db28c9cbbca815c64bc21b99661bb8beb0d48ca501f2cc7fc156fe32',
}
RANGES={
 'CI':('function DPP_STREAM_DIAG_FRAME_33','function wI('),
 'UI':('function DPP_STREAM_FINISHED_33','function WI('),
}
NEW={}
NEW['CI']="""function DPP_STREAM_DIAG_FRAME_33(e,t){let n={event:typeof t?.type==`string`?t.type:`message`};if(typeof e?.p==`string`&&(n.p=e.p.slice(0,96)),typeof e?.o==`string`&&(n.o=e.o.slice(0,32)),(e?.p===`response/status`||e?.p===`quasi_status`)&&(`string`==typeof e?.v||`number`==typeof e?.v||`boolean`==typeof e?.v)&&(n.v=String(e.v).slice(0,32)),Array.isArray(e?.v)){let t=e.v.slice(0,12).map(e=>{if(!e||typeof e!=`object`)return null;let t={};return typeof e.p==`string`&&(t.p=e.p.slice(0,96)),typeof e.o==`string`&&(t.o=e.o.slice(0,32)),(e.p===`response/status`||e.p===`quasi_status`)&&(`string`==typeof e.v||`number`==typeof e.v||`boolean`==typeof e.v)&&(t.v=String(e.v).slice(0,32)),Object.keys(t).length?t:null}).filter(Boolean);t.length&&(n.batch=t)}return n}function DPP_STREAM_DIAG_PUSH_33(e,t,n){if(!Array.isArray(e?.dppStreamEvents))return;let r=DPP_STREAM_DIAG_FRAME_33(t,n);e.dppStreamEvents.push(r),e.dppStreamEvents.length>8&&e.dppStreamEvents.splice(0,e.dppStreamEvents.length-8)}function CI(e,t,n,r,i){DPP_STREAM_DIAG_PUSH_33(n,e,t),ZI(e,n),r.onParsed?.(e,t);let a=RI(e,PI(n));a.text&&(i.push(a.text),r.retainAssistantText!==!1&&(n.assistantText+=a.text)),a.reasoning&&(n.assistantReasoningText+=a.reasoning,r.onReasoningChunk?.(a.reasoning,n.assistantReasoningText)),UI(e,t)&&(n.finished=!0)}"""
NEW['UI']="""function DPP_STREAM_FINISHED_33(e,t=0,n={count:0}){if(t>8||n.count>=128||!e||typeof e!=`object`)return!1;if(n.count+=1,!Array.isArray(e)){let t=e.p,r=e.v;if((t===`response/status`||t===`quasi_status`)&&typeof r==`string`&&r.toUpperCase()===`FINISHED`)return!0}if(Array.isArray(e)){for(let r of e)if(DPP_STREAM_FINISHED_33(r,t+1,n))return!0;return!1}for(let r of Object.values(e))if(r&&typeof r==`object`&&DPP_STREAM_FINISHED_33(r,t+1,n))return!0;return!1}function DPP_STREAM_ERROR_331(e,t=0,n={count:0}){if(t>8||n.count>=128||e==null||typeof e!=`object`)return!1;if(n.count+=1,Array.isArray(e)){for(let r of e)if(DPP_STREAM_ERROR_331(r,t+1,n))return!0;return!1}let r=String(e.p??``).toLowerCase(),i=String(e.o??``).toLowerCase(),a=e.v,o=/^(?:error|failed|failure|aborted|cancelled|canceled|timeout|timed_out|interrupted)$/i;if(o.test(i))return!0;if(/(?:status|state|error|reason)/i.test(r)&&typeof a==`string`&&o.test(a.trim()))return!0;for(let[r,i]of Object.entries(e)){let a=String(r).toLowerCase();if(/(?:^|_)(?:error|errors|failure|failed|exception)(?:$|_)/.test(a)){if(typeof i==`boolean`&&i)return!0;if(typeof i==`number`&&i!==0)return!0;if(typeof i==`string`&&i.trim()&&!/^(?:none|null|false|0)$/i.test(i.trim()))return!0;if(i&&typeof i==`object`&&Object.keys(i).length>0)return!0}if(i&&typeof i==`object`&&DPP_STREAM_ERROR_331(i,t+1,n))return!0}return!1}function DPP_STREAM_TERMINAL_331(e,t){if(DPP_STREAM_FINISHED_33(e))return!0;let n=String(t?.type??``).trim().toLowerCase();return n===`close`&&!DPP_STREAM_ERROR_331(e)}function UI(e,t){return DPP_STREAM_TERMINAL_331(e,t)}"""
def sha(x):return hashlib.sha256(x.encode()).hexdigest()
def rr(s,a,b):
 if s.count(a)!=1: raise RuntimeError(f'{a} count={s.count(a)}')
 i=s.index(a); j=s.index(b,i+len(a)); return i,j,s[i:j]
def write_atomic(p,text):
 q=p.with_name(p.name+'.fix331.tmp'); q.write_text(text,encoding='utf-8',newline=''); os.replace(q,p)
def main(root):
 root=Path(root); cp=root/'content-scripts'/'content.js'; mp=root/'manifest.json'; ep=root/'_locales/en/messages.json'; zp=root/'_locales/zh_CN/messages.json'
 s=cp.read_text(encoding='utf-8-sig'); m=json.loads(mp.read_text(encoding='utf-8-sig')); en=json.loads(ep.read_text(encoding='utf-8-sig')); zh=json.loads(zp.read_text(encoding='utf-8-sig'))
 if m.get('version_name')=='1.14.0 ShunCode MCP Fix 3.3.1' and 'DPP_STREAM_TERMINAL_331' in s:
  print('APPLY_FIX331_ALREADY_APPLIED'); return 0
 if m.get('version_name')!='1.14.0 ShunCode MCP Fix 3.3': raise RuntimeError('expected Fix 3.3 manifest')
 if en.get('extension_name',{}).get('message')!='DeepSeek++ ShunCode MCP Fix 3.3' or zh.get('extension_name',{}).get('message')!='DeepSeek++ ShunCode MCP Fix 3.3': raise RuntimeError('locale extension_name baseline mismatch')
 vals={}
 for n,(a,b) in RANGES.items():
  i,j,x=rr(s,a,b); h=sha(x)
  if h!=EXPECTED[n]: raise RuntimeError(f'{n} hash mismatch {h} != {EXPECTED[n]}')
  vals[n]=(i,j)
 out=s
 for n,(a,b) in RANGES.items():
  i=out.index(a); j=out.index(b,i+len(a)); out=out[:i]+NEW[n]+out[j:]
 m['version_name']='1.14.0 ShunCode MCP Fix 3.3.1'
 for d in (en,zh):
  d['extension_name']['message']='DeepSeek++ ShunCode MCP Fix 3.3.1'
  if 'extension_action_title' in d:d['extension_action_title']['message']='DeepSeek++ ShunCode MCP Fix 3.3.1'
 payload=[(cp,out),(mp,json.dumps(m,ensure_ascii=False,indent=2)+'\n'),(ep,json.dumps(en,ensure_ascii=False,indent=2)+'\n'),(zp,json.dumps(zh,ensure_ascii=False,indent=2)+'\n')]
 staged=[]
 try:
  for p,t in payload:
   q=p.with_name(p.name+'.fix331.tmp'); q.write_text(t,encoding='utf-8',newline=''); staged.append((q,p))
  for q,p in staged:os.replace(q,p)
 finally:
  for q,_ in staged:
   try:q.unlink()
   except FileNotFoundError:pass
 print('APPLY_FIX331_PASS')
 return 0
if __name__=='__main__':
 try:sys.exit(main(sys.argv[1]))
 except Exception as e:print('APPLY_FIX331_FAIL:',e,file=sys.stderr);sys.exit(1)