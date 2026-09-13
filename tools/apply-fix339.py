#!/usr/bin/env python3
from pathlib import Path
import sys, json, hashlib, re
EXPECTED={
 'content-scripts/content.js':'158512C6BF235DD1968D152FD959308C8280A7A550E4824FD66EA3F9964B7A50',
 'manifest.json':'D0993E3F33B169E0E0C0F231BCE7673591CF9A6C2FB582F22FBC7A1ADE4E9371',
 '_locales/en/messages.json':'15304236C6E702523F0D5A707BBE0CFBFE37A8C5E338CCE370B806E9855E59A8',
 '_locales/zh_CN/messages.json':'F20173889A87AC56BDAC714D9470C9A6E9BFB36380035D1F379E8B9C2504A7D7',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def one(s,a,b,label):
    c=s.count(a)
    if c!=1: raise RuntimeError(f'{label} anchor count {c}')
    return s.replace(a,b,1)
def transform(root):
    paths={k:root/Path(k) for k in EXPECTED}
    for k,p in paths.items():
        if not p.is_file(): raise RuntimeError(f'missing {k}')
        got=sha(p)
        if got!=EXPECTED[k]: raise RuntimeError(f'{k} hash mismatch {got} != {EXPECTED[k]}')
    m=json.loads(paths['manifest.json'].read_text(encoding='utf8'))
    if m.get('version')!='1.14.0.3' or m.get('version_name')!='1.14.0 ShunCode MCP Fix 3.3.8': raise RuntimeError('expected Fix 3.3.8 manifest')
    s=paths['content-scripts/content.js'].read_text(encoding='utf8')
    s=one(s,"function hI(){return{assistantText:``,assistantReasoningText:``,responseMessageId:null,requestMessageId:null,finished:!1,dppStreamEvents:[],dppStreamBytes:0,dppStreamChunks:0,dppHttpStatus:null,dppContentType:``,dppAttempt:1,dppFreshPow:!1}}","function hI(){return{assistantText:``,assistantReasoningText:``,responseMessageId:null,requestMessageId:null,finished:!1,dppStreamEvents:[],dppStreamBytes:0,dppStreamChunks:0,dppHttpStatus:null,dppContentType:``,dppAttempt:1,dppFreshPow:!1,dppResponseMessageIdRank:0,dppResponseMessageIdSource:``,dppResponseMessageIdCandidates:0,dppRequestMessageIdRank:0,dppRequestMessageIdSource:``,dppRequestMessageIdCandidates:0}}",'hI')
    pat=r"function ZI\(e,t\)\{.*?\}function QI\(\.\.\.e\)"
    mm=re.search(pat,s)
    if not mm: raise RuntimeError('ZI anchor missing')
    zi=r'''function DPP_MESSAGE_ID_SET_339(e,t,n,r,i){let a=QI(n);if(a===null)return;let o=t===`response`?`responseMessageId`:`requestMessageId`,s=t===`response`?`dppResponseMessageIdRank`:`dppRequestMessageIdRank`,c=t===`response`?`dppResponseMessageIdSource`:`dppRequestMessageIdSource`,l=t===`response`?`dppResponseMessageIdCandidates`:`dppRequestMessageIdCandidates`;e[l]=(e[l]??0)+1;let u=Number(e[s]??0),d=QI(e[o]);if(r>u||r===u&&(d===null||a>d))e[o]=a,e[s]=r,e[c]=String(i??``).slice(0,160)}function DPP_MESSAGE_ID_PATH_339(e,t){if(typeof e!=`string`)return!1;let n=e.toLowerCase().replace(/\./g,`/`),r=t===`response`?`response_message_id`:`request_message_id`;return n===r||n.endsWith(`/`+r)}function ZI(e,t,n=0,r=`root`){if(n>8||!e||typeof e!=`object`)return;let i=e,a=n===0?4:1;DPP_MESSAGE_ID_SET_339(t,`response`,i.response_message_id??i.responseMessageId,a,`${r}.response_message_id`),DPP_MESSAGE_ID_SET_339(t,`request`,i.request_message_id??i.requestMessageId,a,`${r}.request_message_id`);if(typeof i.p==`string`){DPP_MESSAGE_ID_PATH_339(i.p,`response`)&&DPP_MESSAGE_ID_SET_339(t,`response`,i.v,3,`${r}.p:${i.p}`),DPP_MESSAGE_ID_PATH_339(i.p,`request`)&&DPP_MESSAGE_ID_SET_339(t,`request`,i.v,3,`${r}.p:${i.p}`)}if(i.o===`BATCH`&&Array.isArray(i.v))for(let[e,a]of i.v.entries())ZI(a,t,n+1,`${r}.batch[${e}]`);else if(Array.isArray(i.v))for(let[e,a]of i.v.entries())ZI(a,t,n+1,`${r}.v[${e}]`);else i.v&&typeof i.v==`object`&&ZI(i.v,t,n+1,`${r}.v`);if(i.response&&typeof i.response==`object`)ZI(i.response,t,n+1,`${r}.response`)}function QI(...e)'''
    s=s[:mm.start()]+zi+s[mm.end():]
    old="function DPP_JSON_COMPLETION_ERROR_337(e,t){let n=null;try{let e=JSON.parse(t);if(e&&typeof e==`object`&&!Array.isArray(e))n=e}catch{}let r=n?DPP_JSON_FIELD_337(n,[`biz_code`,`code`,`error.code`,`data.biz_code`,`data.code`]):null,i=n?DPP_JSON_FIELD_337(n,[`biz_msg`,`msg`,`message`,`error.message`,`data.biz_msg`,`data.msg`,`data.message`]):null,a=i?i.replace(/\\s+/g,` `).slice(0,240):null,o=[`DeepSeek completion returned JSON instead of an SSE stream (HTTP ${e.status}).`];return r&&o.push(`code=${r}`),a&&o.push(`message=${a}`),o.join(` `)}"
    new="function DPP_JSON_COMPLETION_META_339(e){let t=null;try{let n=JSON.parse(e);if(n&&typeof n==`object`&&!Array.isArray(n))t=n}catch{}let n=t?DPP_JSON_FIELD_337(t,[`biz_code`,`code`,`error.code`,`data.biz_code`,`data.code`]):null,r=t?DPP_JSON_FIELD_337(t,[`biz_msg`,`msg`,`message`,`error.message`,`data.biz_msg`,`data.msg`,`data.message`]):null;return{code:n,message:r?r.replace(/\\s+/g,` `).slice(0,240):null}}function DPP_INVALID_MESSAGE_ID_339(e){return e?.code===`0`&&typeof e?.message==`string`&&e.message.trim().toLowerCase()===`invalid message id`}function DPP_JSON_COMPLETION_ERROR_337(e,t){let n=DPP_JSON_COMPLETION_META_339(t),r=[`DeepSeek completion returned JSON instead of an SSE stream (HTTP ${e.status}).`];return n.code&&r.push(`code=${n.code}`),n.message&&r.push(`message=${n.message}`),r.join(` `)}"
    s=one(s,old,new,'json-meta')
    old="if(/(?:application|text)\\/(?:[A-Za-z0-9.+-]*\\+)?json(?:\\s*;|$)/i.test(a)){let e=await nL(r,`DeepSeek completion`),t=new AL(DPP_JSON_COMPLETION_ERROR_337(r,e),{retryable:!1});throw t.dppNoRetry337=!0,t}"
    new="if(/(?:application|text)\\/(?:[A-Za-z0-9.+-]*\\+)?json(?:\\s*;|$)/i.test(a)){let e=await nL(r,`DeepSeek completion`),n=DPP_JSON_COMPLETION_META_339(e),t=new AL(DPP_JSON_COMPLETION_ERROR_337(r,e),{retryable:!1});throw t.dppNoRetry337=!0,DPP_INVALID_MESSAGE_ID_339(n)&&(t.dppInvalidMessageId339=!0),t}"
    s=one(s,old,new,'json-marker')
    old="async function HR(e,t,n,r){let i=n??new AbortController().signal,a=!1;for(let n=1;n<=zR;n++){"
    new="function DPP_RETRY_INVALID_MESSAGE_339(e,t,n,r,i){return e?.dppInvalidMessageId339===!0&&!t&&!n&&r<i}function DPP_INVALID_MESSAGE_BACKOFF_339(e){if(e.aborted)return Promise.resolve();let t=RR(7e3,12e3);return new Promise(n=>{let r=setTimeout(i,t),a=()=>i();function i(){clearTimeout(r),e.removeEventListener(`abort`,a),n()}e.addEventListener(`abort`,a,{once:!0})})}async function HR(e,t,n,r){let i=n??new AbortController().signal,a=!1,c339=!1;for(let n=1;n<=zR;n++){"
    s=one(s,old,new,'HR-head')
    old="}catch(e){if(i.aborted)throw e;if(e?.dppNoRetry337===!0)throw e;let t=o.timedOut();"
    new="}catch(e){if(i.aborted)throw e;if(e?.dppInvalidMessageId339===!0&&!a&&!c339&&n<zR){c339=!0,await DPP_INVALID_MESSAGE_BACKOFF_339(i);if(i.aborted)throw e;continue}if(e?.dppNoRetry337===!0)throw e;let t=o.timedOut();"
    s=one(s,old,new,'HR-catch')
    old="streamDiagnostics:{attempt:n,httpStatus:s.dppHttpStatus,contentType:s.dppContentType,bytes:s.dppStreamBytes,chunks:s.dppStreamChunks,freshPow:s.dppFreshPow}"
    new="streamDiagnostics:{attempt:n,httpStatus:s.dppHttpStatus,contentType:s.dppContentType,bytes:s.dppStreamBytes,chunks:s.dppStreamChunks,freshPow:s.dppFreshPow,invalidMessageRetry:c339,responseMessageIdSource:s.dppResponseMessageIdSource,responseMessageIdCandidates:s.dppResponseMessageIdCandidates,requestMessageIdSource:s.dppRequestMessageIdSource,requestMessageIdCandidates:s.dppRequestMessageIdCandidates}"
    s=one(s,old,new,'diagnostics')
    m['version']='1.14.0.4'; m['version_name']='1.14.0 ShunCode MCP Fix 3.3.9'
    outputs={'content-scripts/content.js':s,'manifest.json':json.dumps(m,ensure_ascii=False,indent=2)+'\n'}
    for rel in ['_locales/en/messages.json','_locales/zh_CN/messages.json']:
        o=json.loads(paths[rel].read_text(encoding='utf8'))
        for v in o.values():
            if isinstance(v,dict) and isinstance(v.get('message'),str): v['message']=v['message'].replace('Fix 3.3.8','Fix 3.3.9')
        outputs[rel]=json.dumps(o,ensure_ascii=False,indent=2)+'\n'
    return outputs

def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
    try: out=transform(root)
    except Exception as e:
        print(f'APPLY_FIX339_FAIL: {e}',file=sys.stderr); return 1
    # all validation complete before first write
    for rel,text in out.items(): (root/rel).write_text(text,encoding='utf8',newline='')
    print('APPLY_FIX339_PASS'); return 0
if __name__=='__main__': raise SystemExit(main())