from __future__ import annotations
import hashlib,json,os,sys
from pathlib import Path
OLD_VERSION="1.14.0 ShunCode MCP Fix 3.3.10.14"
NEW_VERSION="1.14.0 ShunCode MCP Fix 3.3.10.15"
OLD_MANIFEST_VERSION="1.14.0.19"
NEW_MANIFEST_VERSION="1.14.0.20"
MARKER="DPP_WEB_DIAG_KEY_331015"
EXPECTED={'content-scripts/content.js': 'F647EB21F644DF87898D2DF44152DBF43170C8C7A5F719497391E95E4E1FC5C5', 'content-scripts/main-world.js': '1C0EF80656DC4BFC626707DE1C85113A0A799AD9AF58CA935AA056EFFD25F6BD', 'manifest.json': '83D8F13274CE9C866C2D6D6A288B70C213D5A10A9BFF9ECBC2B4BE3E1A64D906', '_locales/en/messages.json': 'CF42215ED8744C145AEF411E8037CC2A855265AF78A2971EF90F03CBB4AE9F70', '_locales/zh_CN/messages.json': '3CE14B003430E0AE064BB3B94BE869B345E5A7B2932B5973A02A321CC5CBEC9C'}
OUTPUT_EXPECTED={'content-scripts/content.js': '7FECC173832CE58B39DCB118537CD2B42D70418418D51C0C5EC2B81EB9CB071E', 'content-scripts/main-world.js': '507E8A802E1367D08DDDDDB5CC94095CD9449D854AF0BF640C1C3202B97BC686', 'manifest.json': '9CE98F269394226CE8E72EDDCAF9EFE1B77C7B8BB9B9F997C942F38AFF569F33', '_locales/en/messages.json': '36F957EFD2821CAD1CA6C4DB7BD6D2F7D0321207662ADF7AF01D8F695A9A48A2', '_locales/zh_CN/messages.json': '620D15D7BA375CA3DB1477DC8A2A447E8C8D53884AA0429017A2BD07202F5D9C'}
OLD_FETCH='return to(e.call(this,t,p),f)'
NEW_FETCH='return to(e.call(this,t,p),{...f,dppRequestDiag331015:{route:a,rawBodyChars:n.body.length,augmentedBodyChars:(u?.body??n.body).length,descriptorCount:f.toolDescriptors.length,descriptorNames:f.toolDescriptors.map(e=>e?.invocationName??e?.name).filter(e=>typeof e==`string`).slice(0,12),chatSessionId:f.chatSessionId??null}})'
OLD_FIN='return e.suppressPageEvents?null:{requestId:e.requestId,text:o.getVisibleText(),originalPrompt:e.originalPrompt,agentTaskPrompt:e.agentTaskPrompt,chatSessionId:e.chatSessionId,parentMessageId:e.parentMessageId,assistantMessageId:n.responseMessageId,promptOptions:e.promptOptions}'
NEW_FIN='return e.suppressPageEvents?null:{requestId:e.requestId,text:o.getVisibleText(),originalPrompt:e.originalPrompt,agentTaskPrompt:e.agentTaskPrompt,chatSessionId:e.chatSessionId,parentMessageId:e.parentMessageId,assistantMessageId:n.responseMessageId,promptOptions:e.promptOptions,dppStreamFinished331015:n.finished===!0,dppRecoveredDsml331015:DPPRecoveredDsml,dppVisibleChars331015:o.getVisibleText().length}'
OLD_TO='async function to(e,t){let n=!1,r=()=>{n||(n=!0,U.onRequestTerminal({requestId:t.requestId}))},i;try{i=await e}catch(e){throw r(),e}if(!i.body)return r(),i;let a=i.body.getReader(),o=new TextDecoder,s=null,c=()=>(s??=eo(t),s),l=!1,u=!1,d=new ReadableStream({async pull(e){if(!(l||u))try{let{done:t,value:n}=await a.read();if(l)return;if(!t){c().append(o.decode(n,{stream:!0}),e);return}let i=o.decode();i&&c().append(i,e);let s=c().finish(e);s&&U.onResponseComplete(s),u=!0,e.close(),r()}catch(t){l=!0,s?.cancel();try{await a.cancel(t)}finally{try{e.error(t)}finally{r()}}}},async cancel(e){if(!(l||u)){l=!0,s?.cancel();try{await a.cancel(e)}finally{r()}}}},{highWaterMark:0}),f=new Headers(i.headers);f.delete(`content-length`),f.delete(`content-encoding`);let p=new Response(d,{headers:f,status:i.status,statusText:i.statusText});return i.url&&Object.defineProperty(p,`url`,{value:i.url,enumerable:!0,configurable:!0}),p}'
NEW_TO='async function to(e,t){let n=!1,r=e=>{n||(n=!0,U.onRequestTerminal({requestId:t.requestId,...e?{diag331015:e}:{}}))},i;try{i=await e}catch(e){let n=e instanceof Error?e:null;throw r({phase:`fetch_reject`,...(t.dppRequestDiag331015??{}),errorName:n?.name??`Error`,errorMessage:String(n?.message??e).slice(0,300)}),e}let a=i.headers.get(`content-type`)??``,o={...(t.dppRequestDiag331015??{}),httpStatus:i.status,httpOk:i.ok,contentType:a.slice(0,160)};if(!i.body)return r({...o,phase:`no_body`}),i;if(!i.ok||a.toLowerCase().includes(`json`))return r({...o,phase:!i.ok?`http_error_passthrough`:`json_passthrough`}),i;let s=i.body.getReader(),c=new TextDecoder,l=null,u=()=>(l??=eo(t),l),d=!1,f=!1,p=0,m=0,h=new ReadableStream({async pull(e){if(!(d||f))try{let{done:t,value:n}=await s.read();if(d)return;if(!t){n&&(p+=n.byteLength,m+=1),u().append(c.decode(n,{stream:!0}),e);return}let i=c.decode();i&&u().append(i,e);let a=u().finish(e);a&&U.onResponseComplete(a),f=!0,e.close(),r({...o,phase:`eof`,bytes:p,chunks:m,streamFinished:a?.dppStreamFinished331015??null,assistantMessageId:a?.assistantMessageId??null,recoveredDsml:a?.dppRecoveredDsml331015??0,visibleChars:a?.dppVisibleChars331015??0})}catch(t){d=!0,l?.cancel();let n=t instanceof Error?t:null;try{await s.cancel(t)}finally{try{e.error(t)}finally{r({...o,phase:`stream_error`,bytes:p,chunks:m,errorName:n?.name??`Error`,errorMessage:String(n?.message??t).slice(0,300)})}}}},async cancel(e){if(!(d||f)){d=!0,l?.cancel();try{await s.cancel(e)}finally{r({...o,phase:`consumer_cancel`,bytes:p,chunks:m})}}}},{highWaterMark:0}),g=new Headers(i.headers);g.delete(`content-length`),g.delete(`content-encoding`);let _=new Response(h,{headers:g,status:i.status,statusText:i.statusText});return i.url&&Object.defineProperty(_,`url`,{value:i.url,enumerable:!0,configurable:!0}),_}'
OLD_XHR='let u=c?.body??e;return o=ro(t,ja(u,{requestId:i.requestId,...c?.requestId?{requestId:c.requestId}:{},originalPrompt:c?.originalPrompt??i.originalPrompt,agentTaskPrompt:c?.agentTaskPrompt??i.agentTaskPrompt,toolDescriptors:l?[]:c?.toolDescriptors??s,...c?.promptOptions?{promptOptions:c.promptOptions}:{},...c?.activeLocalSkillDir===void 0?{}:{activeLocalSkillDir:c.activeLocalSkillDir}})),a.call(t,u)'
NEW_XHR='let u=c?.body??e,v=ja(u,{requestId:i.requestId,...c?.requestId?{requestId:c.requestId}:{},originalPrompt:c?.originalPrompt??i.originalPrompt,agentTaskPrompt:c?.agentTaskPrompt??i.agentTaskPrompt,toolDescriptors:l?[]:c?.toolDescriptors??s,...c?.promptOptions?{promptOptions:c.promptOptions}:{},...c?.activeLocalSkillDir===void 0?{}:{activeLocalSkillDir:c.activeLocalSkillDir}});return v.dppRequestDiag331015={route:r,rawBodyChars:e.length,augmentedBodyChars:u.length,descriptorCount:v.toolDescriptors.length,descriptorNames:v.toolDescriptors.map(e=>e?.invocationName??e?.name).filter(e=>typeof e==`string`).slice(0,12),chatSessionId:v.chatSessionId??null},o=ro(t,v),a.call(t,u)'
OLD_RO='function ro(e,t){let n=0,r=``,i=eo(t),a=!1,o=!1,s=()=>{o||(o=!0,U.onRequestTerminal({requestId:t.requestId}))},c=Object.getOwnPropertyDescriptor(XMLHttpRequest.prototype,`responseText`)||Object.getOwnPropertyDescriptor(Object.getPrototypeOf(XMLHttpRequest.prototype),`responseText`),l={enqueue(e){r+=new TextDecoder().decode(e)}},u=()=>{let t=c?.get?.call(e)||``,r=t.slice(n);n=t.length,r&&i.append(r,l)},d=()=>{if(a)return;u();let e=i.finish(l);a=!0,e&&U.onResponseComplete(e)},f=()=>{e.readyState===4&&e.status!==0&&d()};e.addEventListener(`readystatechange`,function(){(e.readyState===3||e.readyState===4)&&(u(),f())}),e.addEventListener(`load`,()=>{try{d()}finally{s()}},{once:!0});let p=()=>{i.cancel(),s()};return e.addEventListener(`abort`,p,{once:!0}),e.addEventListener(`error`,p,{once:!0}),e.addEventListener(`timeout`,p,{once:!0}),Object.defineProperty(e,`responseText`,{get(){return(e.readyState===3||e.readyState===4)&&u(),f(),r},configurable:!0}),Object.defineProperty(e,`response`,{get(){if(e.responseType===``||e.responseType===`text`)return(e.readyState===3||e.readyState===4)&&u(),f(),r},configurable:!0}),p}'
NEW_RO='function ro(e,t){let n=0,r=``,i=eo(t),a=!1,o=!1,s=null,c=()=>({...t.dppRequestDiag331015??{},httpStatus:e.status,httpOk:e.status>=200&&e.status<300,contentType:(e.getResponseHeader(`content-type`)??``).slice(0,160)}),l=t=>{o||(o=!0,U.onRequestTerminal({requestId:t.requestId,...t?{diag331015:t}:{}}))},u=Object.getOwnPropertyDescriptor(XMLHttpRequest.prototype,`responseText`)||Object.getOwnPropertyDescriptor(Object.getPrototypeOf(XMLHttpRequest.prototype),`responseText`),d={enqueue(e){r+=new TextDecoder().decode(e)}},f=()=>{let t=u?.get?.call(e)||``,r=t.slice(n);n=t.length,r&&i.append(r,d)},p=()=>{if(a)return;f();let e=i.finish(d);s=e,a=!0,e&&U.onResponseComplete(e)},m=()=>{e.readyState===4&&e.status!==0&&p()};e.addEventListener(`readystatechange`,function(){(e.readyState===3||e.readyState===4)&&(f(),m())}),e.addEventListener(`load`,()=>{try{p()}finally{l({...c(),phase:`xhr_load`,chars:n,streamFinished:s?.dppStreamFinished331015??null,assistantMessageId:s?.assistantMessageId??null,recoveredDsml:s?.dppRecoveredDsml331015??0,visibleChars:s?.dppVisibleChars331015??0})}},{once:!0});let h=t=>{i.cancel(),l({...c(),phase:t,chars:n})};return e.addEventListener(`abort`,()=>h(`xhr_abort`),{once:!0}),e.addEventListener(`error`,()=>h(`xhr_error`),{once:!0}),e.addEventListener(`timeout`,()=>h(`xhr_timeout`),{once:!0}),Object.defineProperty(e,`responseText`,{get(){return(e.readyState===3||e.readyState===4)&&f(),m(),r},configurable:!0}),Object.defineProperty(e,`response`,{get(){if(e.responseType===``||e.responseType===`text`)return(e.readyState===3||e.readyState===4)&&f(),m(),r},configurable:!0}),()=>h(`xhr_cleanup`)}'
HELPER='var DPP_WEB_DIAG_KEY_331015=`dpp_web_response_diag_331015`;async function DPP_RECORD_WEB_DIAG_331015(e){let t=e?.diag331015;if(!t||typeof t!=`object`||Array.isArray(t))return;try{let n=await chrome.storage.local.get(DPP_WEB_DIAG_KEY_331015),r=Array.isArray(n?.[DPP_WEB_DIAG_KEY_331015])?n[DPP_WEB_DIAG_KEY_331015]:[],i=e=>typeof e==`number`&&Number.isFinite(e)?e:null,a={ts:Date.now(),requestId:typeof e?.requestId==`string`?e.requestId.slice(0,100):``,chatSessionId:typeof t.chatSessionId==`string`?t.chatSessionId.slice(0,100):null,route:typeof t.route==`string`?t.route.slice(0,40):``,phase:typeof t.phase==`string`?t.phase.slice(0,60):``,httpStatus:i(t.httpStatus),httpOk:typeof t.httpOk==`boolean`?t.httpOk:null,contentType:typeof t.contentType==`string`?t.contentType.slice(0,160):``,rawBodyChars:i(t.rawBodyChars),augmentedBodyChars:i(t.augmentedBodyChars),descriptorCount:i(t.descriptorCount),descriptorNames:Array.isArray(t.descriptorNames)?t.descriptorNames.filter(e=>typeof e==`string`).slice(0,12).map(e=>e.slice(0,120)):[],bytes:i(t.bytes),chunks:i(t.chunks),streamFinished:typeof t.streamFinished==`boolean`?t.streamFinished:null,assistantMessageId:i(t.assistantMessageId),recoveredDsml:i(t.recoveredDsml),visibleChars:i(t.visibleChars),errorName:typeof t.errorName==`string`?t.errorName.slice(0,80):``,errorMessage:typeof t.errorMessage==`string`?t.errorMessage.slice(0,300):``};r.push(a),r.length>80&&(r=r.slice(-80)),await chrome.storage.local.set({[DPP_WEB_DIAG_KEY_331015]:r})}catch(e){console.error(`[DeepSeek++] web response diagnostics persistence failed`,e)}}'
OLD_TERM='case`REQUEST_TERMINAL`:{let t=e.payload?.requestId;if(typeof t!=`string`)break;DPP_MANUAL_FINISH_334(t),'
NEW_TERM='case`REQUEST_TERMINAL`:{let t=e.payload?.requestId;if(typeof t!=`string`)break;await DPP_RECORD_WEB_DIAG_331015(e.payload),DPP_MANUAL_FINISH_334(t),'
def sha256(data:bytes)->str:return hashlib.sha256(data).hexdigest().upper()
def replace_one(text,old,new,label):
 c=text.count(old)
 if c!=1:raise RuntimeError(f"{label}: expected one match, got {c}")
 return text.replace(old,new,1)
def stage_write(path,data):
 tmp=path.with_name(path.name+".fix331015.tmp");tmp.write_bytes(data);return tmp
def main(root_arg):
 root=Path(root_arg).resolve();paths={rel:root/rel for rel in EXPECTED}
 manifest=json.loads(paths["manifest.json"].read_text(encoding="utf-8-sig"))
 content=paths["content-scripts/content.js"].read_text(encoding="utf-8-sig")
 mainw=paths["content-scripts/main-world.js"].read_text(encoding="utf-8-sig")
 if manifest.get("version")==NEW_MANIFEST_VERSION and manifest.get("version_name")==NEW_VERSION and MARKER in content:
  for rel,expected in OUTPUT_EXPECTED.items():
   actual=sha256(paths[rel].read_bytes())
   if actual!=expected:raise RuntimeError(f"already-patched hash mismatch for {rel}: {actual}")
  print("APPLY_FIX331015_OK already-applied");return
 if manifest.get("version")!=OLD_MANIFEST_VERSION or manifest.get("version_name")!=OLD_VERSION:
  raise RuntimeError(f"expected {OLD_VERSION}, got {manifest.get('version_name')!r}")
 for rel,expected in EXPECTED.items():
  actual=sha256(paths[rel].read_bytes())
  if actual!=expected:raise RuntimeError(f"input hash mismatch for {rel}: {actual}")
 mainw=replace_one(mainw,OLD_FETCH,NEW_FETCH,"fetch request diagnostics")
 mainw=replace_one(mainw,OLD_FIN,NEW_FIN,"response finish diagnostics")
 mainw=replace_one(mainw,OLD_TO,NEW_TO,"fetch transport wrapper")
 mainw=replace_one(mainw,OLD_XHR,NEW_XHR,"xhr request diagnostics")
 mainw=replace_one(mainw,OLD_RO,NEW_RO,"xhr transport diagnostics")
 content=replace_one(content,'async function _Z(e){',HELPER+'async function _Z(e){',"web diagnostic recorder")
 content=replace_one(content,OLD_TERM,NEW_TERM,"terminal diagnostic persistence")
 manifest["version"]=NEW_MANIFEST_VERSION;manifest["version_name"]=NEW_VERSION
 outputs={
  "content-scripts/content.js":content.replace("\r\n","\n").replace("\n","\r\n").encode("utf-8"),
  "content-scripts/main-world.js":mainw.replace("\r\n","\n").replace("\n","\r\n").encode("utf-8"),
  "manifest.json":(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n").replace("\n","\r\n").encode("utf-8")}
 for rel in ("_locales/en/messages.json","_locales/zh_CN/messages.json"):
  text=paths[rel].read_text(encoding="utf-8-sig")
  outputs[rel]=text.replace("Fix 3.3.10.14","Fix 3.3.10.15").replace("\r\n","\n").replace("\n","\r\n").encode("utf-8")
 for rel,data in outputs.items():
  got=sha256(data);want=OUTPUT_EXPECTED[rel]
  if got!=want:raise RuntimeError(f"staged output hash mismatch for {rel}: {got} != {want}")
 staged=[]
 try:
  for rel,data in outputs.items():staged.append((stage_write(paths[rel],data),paths[rel]))
  for tmp,path in staged:os.replace(tmp,path)
 finally:
  for tmp,_ in staged:
   if tmp.exists():tmp.unlink()
 print("APPLY_FIX331015_OK")
 for rel in outputs:print(f"{rel} {sha256(paths[rel].read_bytes())}")
if __name__=="__main__":
 if len(sys.argv)!=2:raise SystemExit("usage: apply-fix331015.py <extension-root>")
 main(sys.argv[1])
