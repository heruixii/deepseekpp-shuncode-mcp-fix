from pathlib import Path
import hashlib,json,os,sys
EXPECTED={
 'content':'3CEA0B3E7FFB7CCA9B5D040B6F6B2EA59D2EA20C4FD0C677645E5B451528F2F7',
 'background':'25EC9AFCC431A039CACE0C110BEBAA451BCBBABDB92E5022D8907DA049939A78',
 'manifest':'F158B620947D3955191447BBF3EE37F63A33C649C28551445A15BAEB6AEB5427',
 'en':'595CB3AC72EDF341DC1178E20A3ADFAEC7B4FF56A3987060BC1CEAF354129783',
 'zh':'B2159032A7D6E74D9A3FD52DE8814AA15DC89902DE52D4D52F4942E5214B7A4F',
}
OLD_VERSION='1.14.0 ShunCode MCP Fix 3.3.2'
NEW_VERSION='1.14.0 ShunCode MCP Fix 3.3.3'
OLD_NAME='DeepSeek++ ShunCode MCP Fix 3.3.2'
NEW_NAME='DeepSeek++ ShunCode MCP Fix 3.3.3'

def hbytes(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def replace_one(s,old,new,label):
    c=s.count(old)
    if c!=1: raise RuntimeError(f'{label} expected exactly once, found {c}')
    return s.replace(old,new,1)
def stage_atomic(payload):
    staged=[]
    try:
        for p,t in payload:
            q=p.with_name(p.name+'.fix333.tmp')
            q.write_text(t,encoding='utf-8',newline='')
            staged.append((q,p))
        for q,p in staged: os.replace(q,p)
    finally:
        for q,_ in staged:
            try:q.unlink()
            except FileNotFoundError:pass

def main(root):
    root=Path(root)
    cp=root/'content-scripts/content.js'; bp=root/'background.js'; mp=root/'manifest.json'
    ep=root/'_locales/en/messages.json'; zp=root/'_locales/zh_CN/messages.json'
    s=cp.read_text(encoding='utf-8-sig'); bg=bp.read_text(encoding='utf-8-sig')
    m=json.loads(mp.read_text(encoding='utf-8-sig')); en=json.loads(ep.read_text(encoding='utf-8-sig')); zh=json.loads(zp.read_text(encoding='utf-8-sig'))
    if m.get('version_name')==NEW_VERSION and 'DPP_AGENT_CHECKPOINT_333' in s and 'DPP_HISTORY_TEXT_333' in bg:
        print('APPLY_FIX333_ALREADY_APPLIED'); return 0
    if m.get('version_name')!=OLD_VERSION: raise RuntimeError('expected Fix 3.3.2 manifest')
    for label,p in [('content',cp),('background',bp),('manifest',mp),('en',ep),('zh',zp)]:
        got=hbytes(p)
        if got!=EXPECTED[label]: raise RuntimeError(f'{label} file hash mismatch {got} != {EXPECTED[label]}')
    if en.get('extension_name',{}).get('message')!=OLD_NAME or zh.get('extension_name',{}).get('message')!=OLD_NAME:
        raise RuntimeError('locale baseline mismatch')

    old='function kU(e=Zo(DU)){let t=Qo({label:`inlineAgentTraces`,createDefault:()=>[],codec:yU,storage:e});return{read:()=>t.read(),async upsert(e,n=Date.now()){await wi(async()=>{let r=yU.decode([e],`inlineAgentTraces.upsert`)[0],i=[...(await t.readAlreadyLocked()).filter(e=>e.id!==r.id),r].filter(e=>n-e.createdAt<OU).slice(-100);await t.writeAfterReadAlreadyLocked(i)})}}}'
    new='function DPP_AGENT_TRACE_BYTES_333(e){try{return new TextEncoder().encode(JSON.stringify(e)).length}catch{return Number.POSITIVE_INFINITY}}function DPP_TRIM_AGENT_TRACES_333(e,t=262144){let n=[...e];for(;n.length>1&&DPP_AGENT_TRACE_BYTES_333(n)>t;)n.shift();return n}function kU(e=Zo(DU)){let t=Qo({label:`inlineAgentTraces`,createDefault:()=>[],codec:yU,storage:e});return{read:()=>t.read(),async upsert(e,n=Date.now()){await wi(async()=>{let r=yU.decode([e],`inlineAgentTraces.upsert`)[0],i=[...(await t.readAlreadyLocked()).filter(e=>e.id!==r.id),r].filter(e=>n-e.createdAt<OU).slice(-100);i=DPP_TRIM_AGENT_TRACES_333(i),await t.writeAfterReadAlreadyLocked(i)})}}}'
    s=replace_one(s,old,new,'agent trace byte cap')

    old='var jH=4e3,MH=8e3,NH=`\n...[truncated]`;function PH(e,t={}){return{name:e.name,provider:e.provider,descriptorId:e.descriptorId,result:LH(e.result,t)}}function FH(e){return{name:e.name,provider:e.provider,descriptorId:e.descriptorId,result:IH(e.result)}}function IH(e){return{...e,output:zH(e.output)}}function LH(e,t){let n=t.detailMaxLength??jH,r=t.outputMaxLength??MH;return{...e,detail:HH(e.detail,n),output:RH(e.output,r)}}function RH(e,t){if(e===void 0)return;let n=VH(e);return n.length<=t?e:HH(n,t)}function zH(e){if(typeof e!=`string`)return e;let t=e.trim();if(!t.startsWith(`{`))return e;try{let n=JSON.parse(t);return BH(n)?n:e}catch{return e}}function BH(e){if(!e||typeof e!=`object`||Array.isArray(e))return!1;let t=e.kind;return t===`artifact`||t===`skill_draft`||t===`memory_import_preview`}function VH(e){try{return JSON.stringify(e)}catch{return String(e)}}function HH(e,t){return e&&(e.length>t?`${e.slice(0,t)}${NH}`:e)}'
    new='var jH=4e3,MH=8e3,NH=`\n...[truncated]`;function DPP_TEXT_PAYLOAD_333(e){if(Array.isArray(e)){if(e.length===0)return null;let t=[];for(let n of e){if(!n||typeof n!=`object`||Array.isArray(n)||n.type!==`text`||typeof n.text!=`string`)return null;t.push(n.text)}return t.join(String.fromCharCode(10)).trim()}if(typeof e!=`string`)return null;let t=e.trim();if(!t)return null;if(t[0]===`[`||t[0]===`{`||t[0]===`"`)try{return DPP_TEXT_PAYLOAD_333(JSON.parse(t))}catch{}return t}function DPP_DUPLICATE_TEXT_333(e,t){let n=DPP_TEXT_PAYLOAD_333(e),r=DPP_TEXT_PAYLOAD_333(t);return n!==null&&r!==null&&n===r}function PH(e,t={}){return{name:e.name,provider:e.provider,descriptorId:e.descriptorId,result:LH(e.result,t)}}function FH(e){return{name:e.name,provider:e.provider,descriptorId:e.descriptorId,result:IH(e.result)}}function IH(e){return{...e,output:zH(e.output)}}function LH(e,t){let n=t.detailMaxLength??jH,r=t.outputMaxLength??MH,i=HH(e.detail,n),a=RH(e.output,r);return DPP_DUPLICATE_TEXT_333(e.detail,e.output)&&(a=void 0),{...e,detail:i,output:a}}function RH(e,t){if(e===void 0)return;let n=VH(e);return n.length<=t?e:HH(n,t)}function zH(e){if(typeof e!=`string`)return e;let t=e.trim();if(!t.startsWith(`{`))return e;try{let n=JSON.parse(t);return BH(n)?n:e}catch{return e}}function BH(e){if(!e||typeof e!=`object`||Array.isArray(e))return!1;let t=e.kind;return t===`artifact`||t===`skill_draft`||t===`memory_import_preview`}function VH(e){try{return JSON.stringify(e)}catch{return String(e)}}function HH(e,t){return e&&(e.length>t?`${e.slice(0,t)}${NH}`:e)}'
    s=replace_one(s,old,new,'content result dedupe')

    old='function s1(e){e.loopId!==LY||!Q||(o1(),WY.delete(e.stepIndex),IY=tV(e.stepIndex),QB(Q,{phase:`running`,stepNumber:e.stepIndex,toolCount:cX,totalSteps:0,totalTools:0,elapsedSeconds:IX()},NX()),C0(t=>w0(t,{index:e.stepIndex,status:`streaming`,text:``,toolExecutions:[],responseMessageId:null,collapsed:!1})))}function c1(e){if(e.loopId!==LY||!Q)return;let t=ZB(Q);t&&IY&&PV(t,e.stepIndex,e.call,NX()),cX+=1,C0(t=>T0(t,e.stepIndex,{status:`executing_tools`}))}function l1(e){e.loopId!==LY||!IY||(UY=e,HY===null&&(HY=requestAnimationFrame(()=>{HY=null;let e=UY;UY=null,e&&d1(e)})))}function u1(e){if(e.loopId!==LY||!Q||!e.fullText)return;let t=ZB(Q),n=IY,r=e.fullText;if(n&&n.parentElement===t){let e=aV(n);e&&iV(e,r)}else WY.set(e.stepIndex,r),n&&t&&n.parentElement!==t&&nV(n,t,NX(),r);C0(t=>T0(t,e.stepIndex,{reasoning:r}))}function d1(e){if(e.loopId!==LY||!IY||!Q)return;let t=IY,n=x0(t),r=a0(mB(e.fullText,iX)||n,$q)??``;if(r){let e=ZB(Q);e&&nV(t,e,NX())}let i=WY.get(e.stepIndex);if(i){let e=aV(t);e&&iV(e,i)}lV(t,r),f1(t),C0(t=>T0(t,e.stepIndex,{text:r,...r?{status:`streaming`}:{}}))}'
    new='function s1(e){e.loopId!==LY||!Q||(o1(),WY.delete(e.stepIndex),IY=tV(e.stepIndex),QB(Q,{phase:`running`,stepNumber:e.stepIndex,toolCount:cX,totalSteps:0,totalTools:0,elapsedSeconds:IX()},NX()),C0(t=>w0(t,{index:e.stepIndex,status:`streaming`,text:``,toolExecutions:[],responseMessageId:null,collapsed:!1}),{persist:!1}))}function c1(e){if(e.loopId!==LY||!Q)return;let t=ZB(Q);t&&IY&&PV(t,e.stepIndex,e.call,NX()),cX+=1,C0(t=>T0(t,e.stepIndex,{status:`executing_tools`}),{persist:!1})}function l1(e){e.loopId!==LY||!IY||(UY=e,HY===null&&(HY=requestAnimationFrame(()=>{HY=null;let e=UY;UY=null,e&&d1(e)})))}function u1(e){if(e.loopId!==LY||!Q||!e.fullText)return;let t=ZB(Q),n=IY,r=e.fullText;if(n&&n.parentElement===t){let e=aV(n);e&&iV(e,r)}else WY.set(e.stepIndex,r),n&&t&&n.parentElement!==t&&nV(n,t,NX(),r);C0(t=>T0(t,e.stepIndex,{reasoning:r}),{persist:!1})}function d1(e){if(e.loopId!==LY||!IY||!Q)return;let t=IY,n=x0(t),r=a0(mB(e.fullText,iX)||n,$q)??``;if(r){let e=ZB(Q);e&&nV(t,e,NX())}let i=WY.get(e.stepIndex);if(i){let e=aV(t);e&&iV(e,i)}lV(t,r),f1(t),C0(t=>T0(t,e.stepIndex,{text:r,...r?{status:`streaming`}:{}}),{persist:!1})}'
    s=replace_one(s,old,new,'transient agent persistence')

    old='function h1(e){if(e.loopId!==LY||!IY||!Q)return;p1();let t=ZB(Q);for(let n of e.toolExecutions)t&&FV(t,e.stepIndex,n,NX());QB(Q,{phase:`running`,stepNumber:e.stepIndex,toolCount:cX,totalSteps:0,totalTools:0,elapsedSeconds:IX()},NX()),uV(IY,`complete`);let n=x0(IY);C0(t=>T0(t,e.stepIndex,{status:`complete`,text:n,toolExecutions:e.toolExecutions,responseMessageId:e.responseMessageId,collapsed:!0}),{immediate:!0}),IY=null}'
    new='function DPP_AGENT_CHECKPOINT_333(e){return(e+1)%4===0}function h1(e){if(e.loopId!==LY||!IY||!Q)return;p1();let t=ZB(Q);for(let n of e.toolExecutions)t&&FV(t,e.stepIndex,n,NX());QB(Q,{phase:`running`,stepNumber:e.stepIndex,toolCount:cX,totalSteps:0,totalTools:0,elapsedSeconds:IX()},NX()),uV(IY,`complete`);let n=x0(IY),r=DPP_AGENT_CHECKPOINT_333(e.stepIndex);C0(t=>T0(t,e.stepIndex,{status:`complete`,text:n,toolExecutions:e.toolExecutions,responseMessageId:e.responseMessageId,collapsed:!0}),r?{immediate:!0}:{persist:!1}),IY=null}'
    s=replace_one(s,old,new,'agent checkpoint cadence')

    old='function RV(e){let t=[];if(e.ok)t.push(e.summary),e.detail&&t.push(zV(e.detail,2e3));else{let n=e.detail?.trim()||e.error?.message.trim()||``;!n||n===e.summary.trim()?t.push(e.summary):t.push(`${e.summary}\\n${n}`),e.error&&t.push(`error: ${zV(JSON.stringify(e.error),2e3)}`)}return e.output!==void 0&&t.push(`output: ${zV(JSON.stringify(e.output),4e3)}`),t.filter(Boolean).join(`\n`)}'
    new='function RV(e){let t=[];if(e.ok)t.push(e.summary),e.detail&&t.push(zV(e.detail,2e3));else{let n=e.detail?.trim()||e.error?.message.trim()||``;!n||n===e.summary.trim()?t.push(e.summary):t.push(`${e.summary}\\n${n}`),e.error&&t.push(`error: ${zV(JSON.stringify(e.error),2e3)}`)}return e.output!==void 0&&!DPP_DUPLICATE_TEXT_333(e.detail,e.output)&&t.push(`output: ${zV(JSON.stringify(e.output),4e3)}`),t.filter(Boolean).join(`\n`)}'
    s=replace_one(s,old,new,'agent DOM duplicate output')

    old='function Iz(e){let t=DPP_CAPABILITY_WINDOW_32(e),n=t===null?(e.result.output===void 0?void 0:JSON.stringify(e.result.output)):JSON.stringify(t),r=DPP_MODEL_RESULT_BUDGET_3(e.name);return{tool:e.name,provider:e.provider?.displayName,ok:e.result.ok,summary:e.result.summary,detail:zz(e.result.detail,3500),error:Rz(e.result.error),output:zz(n,r),...DPP_RESULT_HINT_33(e),...t?{capabilityCatalog:!0}:{},contextCompacted:typeof n==`string`&&n.length>r,truncated:e.result.truncated===!0}}function Lz(e){let t=DPP_CAPABILITY_WINDOW_32(e);return{tool:e.name,provider:e.provider?.displayName,ok:e.result.ok,summary:zz(e.result.summary,400),error:Rz(e.result.error),...DPP_RESULT_HINT_33(e),...t?{capabilityWindow:t}:{},windowed:!0,truncated:e.result.truncated===!0}}'
    new='function Iz(e){let t=DPP_CAPABILITY_WINDOW_32(e),n=t===null?(e.result.output===void 0?void 0:JSON.stringify(e.result.output)):JSON.stringify(t),r=DPP_MODEL_RESULT_BUDGET_3(e.name),i=zz(e.result.detail,3500),a=zz(n,r),o=t===null&&DPP_DUPLICATE_TEXT_333(e.result.detail,e.result.output);return o&&(a=void 0),{tool:e.name,provider:e.provider?.displayName,ok:e.result.ok,summary:e.result.summary,detail:i,error:Rz(e.result.error),output:a,...DPP_RESULT_HINT_33(e),...t?{capabilityCatalog:!0}:{},contextCompacted:!o&&typeof n==`string`&&n.length>r,truncated:e.result.truncated===!0}}function Lz(e){let t=DPP_CAPABILITY_WINDOW_32(e);return{tool:e.name,provider:e.provider?.displayName,ok:e.result.ok,summary:zz(e.result.summary,400),error:Rz(e.result.error),...DPP_RESULT_HINT_33(e),...t?{capabilityWindow:t}:{},windowed:!0,truncated:e.result.truncated===!0}}'
    s=replace_one(s,old,new,'model context duplicate output')

    old='var DPP_AGENT_RULES_33=[`[Fix 3.3 UTF-8 safety] On Windows PowerShell 5.1, never read UTF-8 text that may lack a BOM with bare Get-Content -Raw before writing it back. Use Get-Content -Encoding UTF8 -Raw or [System.IO.File]::ReadAllText(path,[System.Text.Encoding]::UTF8).`,`[Fix 3.3 workspace] ShunCode read_files/find_files/search_files/list_directory are scoped to the current ShunCode workspace. If an explicit target is outside that workspace, use run_command with the absolute path instead of inventing a workspace-relative path.`,`[Fix 3.3 stdout] For non-interactive read/check commands where stdout is needed, prefer run_command execution=direct; do not retry mutating commands merely because PTY stdout is empty.`].join(`\\n`);'
    new='var DPP_AGENT_RULES_33=[`[Fix 3.3 UTF-8 safety] On Windows PowerShell 5.1, never read UTF-8 text that may lack a BOM with bare Get-Content -Raw before writing it back. Use Get-Content -Encoding UTF8 -Raw or [System.IO.File]::ReadAllText(path,[System.Text.Encoding]::UTF8).`,`[Fix 3.3 workspace] ShunCode read_files/find_files/search_files/list_directory are scoped to the current ShunCode workspace. If an explicit target is outside that workspace, use run_command with the absolute path instead of inventing a workspace-relative path.`,`[Fix 3.3 stdout] For non-interactive read/check commands where stdout is needed, prefer run_command execution=direct; do not retry mutating commands merely because PTY stdout is empty.`,`[Fix 3.3.3 targeted discovery] On Windows, when asked for Obsidian or vault notes, resolve registered vaults from %APPDATA%\\obsidian\\obsidian.json and inspect the selected vault/.obsidian before recursive drive scans. Treat an Obsidian installation directory as an application install unless it contains the requested vault. Once a trusted config or project note identifies the vault, stop broad drive discovery and continue inside that target. In general prefer exact config/index lookup and bounded directory listing over recursive whole-drive scans.`].join(`\\n`);'
    s=replace_one(s,old,new,'targeted filesystem discovery rule')

    old='function L_(e){return{...e,detail:z_(e.detail,4e3),output:e.output===void 0?void 0:z_(JSON.stringify(e.output),8e3),error:e.error?{...e.error,message:z_(e.error.message,2e3)??``,details:e.error.details?R_(e.error.details,2e3):void 0}:void 0}}'
    new='function DPP_HISTORY_TEXT_333(e){if(Array.isArray(e)){if(e.length===0)return null;let t=[];for(let n of e){if(!n||typeof n!=`object`||Array.isArray(n)||n.type!==`text`||typeof n.text!=`string`)return null;t.push(n.text)}return t.join(String.fromCharCode(10)).trim()}if(typeof e!=`string`)return null;let t=e.trim();if(!t)return null;if(t[0]===`[`||t[0]===`{`||t[0]===`"`)try{return DPP_HISTORY_TEXT_333(JSON.parse(t))}catch{}return t}function DPP_HISTORY_DUP_333(e,t){let n=DPP_HISTORY_TEXT_333(e),r=DPP_HISTORY_TEXT_333(t);return n!==null&&r!==null&&n===r}function L_(e){let t=z_(e.detail,4e3),n=e.output===void 0?void 0:z_(JSON.stringify(e.output),8e3);return DPP_HISTORY_DUP_333(e.detail,e.output)&&(n=void 0),{...e,detail:t,output:n,error:e.error?{...e.error,message:z_(e.error.message,2e3)??``,details:e.error.details?R_(e.error.details,2e3):void 0}:void 0}}'
    bg=replace_one(bg,old,new,'background history duplicate output')
    old='function V_(){let e=chrome.storage.local.QUOTA_BYTES??10485760;return Math.floor(e*O_)}'
    new='function V_(){let e=chrome.storage.local.QUOTA_BYTES??10485760;return Math.min(Math.floor(e*O_),262144)}'
    bg=replace_one(bg,old,new,'background history byte cap')

    m['version_name']=NEW_VERSION
    for d in (en,zh):
        d['extension_name']['message']=NEW_NAME
        if 'extension_action_title' in d: d['extension_action_title']['message']=NEW_NAME
    payload=[(cp,s),(bp,bg),(mp,json.dumps(m,ensure_ascii=False,indent=2)+'\n'),(ep,json.dumps(en,ensure_ascii=False,indent=2)+'\n'),(zp,json.dumps(zh,ensure_ascii=False,indent=2)+'\n')]
    stage_atomic(payload)
    print('APPLY_FIX333_PASS')
    return 0

if __name__=='__main__':
    try: sys.exit(main(sys.argv[1]))
    except Exception as e:
        print('APPLY_FIX333_FAIL:',e,file=sys.stderr); sys.exit(1)