#!/usr/bin/env python3
"""Reproducible .48 from .36 via the locked .47 chain. No permission or replay-gate changes."""
import argparse,hashlib,importlib.util,json,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
VERSION='1.14.0.53';NAME='1.14.0 ShunCode MCP Fix 3.3.10.48'
def sha(b):return hashlib.sha256(b).hexdigest()
def once(s,a,b):
    if s.count(a)!=1:raise ValueError('Expected unique edit: '+a[:140]+' count='+str(s.count(a)))
    return s.replace(a,b,1)
def transform(values):
    values=dict(values);c=values['content-scripts/content.js'].decode();mw=values['content-scripts/main-world.js'].decode();bg=values['background.js'].decode()
    # Initialize once more only before dispatch; reservation/fingerprint/consumption gates remain byte-identical.
    bg=once(bg,'async function Fu(e,t,n={}){',(HERE/'dspp-mcp-init-v48.js').read_text('utf-8')+'\nasync function Fu(e,t,n={}){')
    bg=once(bg,'return await Mo(i,t,{signal:n.signal}),Po(i,t,','return await DPP_MCP_INITIALIZE_331048(()=>Mo(i,t,{signal:n.signal}),n.signal),Po(i,t,')
    bg=once(bg,'retryable:typeof i.retryable==`boolean`?i.retryable:!0,details:i.details&&typeof i.details==`object`?i.details:void 0','retryable:!1,details:{stage:`initialize`,externalOutcome:`not_dispatched`,retrySafe:!1,action:`inspect_connection_then_new_authorized_call`}')
    # No content-layer retries of an already-consumed MCP capability, irrespective of tool name.
    c=once(c,'function DPP_WEB_SAFE_RETRY_3(e,t){','function DPP_WEB_SAFE_RETRY_3(e,t){if(e?.provider?.kind===`mcp`||t?.provider?.kind===`mcp`||String(e?.descriptorId??t?.descriptorId??``).startsWith(`mcp:`)||String(e?.invocationName??``).startsWith(`mcp_`)||String(t?.error?.code??``).startsWith(`mcp_`))return!1;')
    # Outer verification retry must honor outcome uncertainty as well; no fresh-ID bypass after tools/call ambiguity.
    c=once(c,'return n?.ok===!1&&n?.error?.retryable===!0&&DPP_TOOL_EFFECT_31(e,t)===`verification`','return n?.ok===!1&&n?.error?.retryable===!0&&n?.error?.details?.externalOutcome===`not_dispatched`&&n?.error?.details?.retrySafe===!0&&DPP_TOOL_EFFECT_31(e,t)===`verification`')
    c=once(c,'function kU(e=Zo(DU)){',(HERE/'dspp-runtime-v48.js').read_text('utf-8')+'\nfunction kU(e=Zo(DU)){')
    c=once(c,'async function i2(e,t){','async function i2(e,t){e=DPP_SEARCH_CALL_331048(e);')
    c=once(c,'o=DPP_NORMALIZE_RUN_COMMAND_RESULT_33108(i,s2(a));','o=DPP_SEARCH_RESULT_331048(i,DPP_NORMALIZE_RUN_COMMAND_RESULT_33108(i,s2(a)));')
    c=once(c,'DPPRecoveryCompact331020?DPP_COMPACT_DESCRIPTORS_331020(r.descriptors):r.descriptors','DPPRecoveryCompact331020?DPP_COMPACT_DESCRIPTORS_331020(r.descriptors):DPP_BUDGET_DESCRIPTORS_331048(r.descriptors)')
    # Atomic read-modify-write across same-origin tabs, plus monotonic checkpoints.
    a='function kU(e=Zo(DU)){';z='var AU=kU();';i=c.index(a);j=c.index(z,i);part=c[i:j]
    part=part.replace('wi(async()=>{','DPP_TRACE_LOCK_331048(()=>wi(async()=>{').replace(',n})}',',n}))}').replace('AlreadyLocked(i)})}}}','AlreadyLocked(i)}))}}}')
    part=once(part,'let r=yU.decode([e],`inlineAgentTraces.upsert`)[0],i=[...(await t.readAlreadyLocked()).filter(e=>e.id!==r.id),r]','let DPPStored331048=await t.readAlreadyLocked(),r=DPP_TRACE_NEWER_331048(DPPStored331048.find(t=>t.id===e.id),yU.decode([e],`inlineAgentTraces.upsert`)[0]),i=[...DPPStored331048.filter(e=>e.id!==r.id),r]')
    part=once(part,'i=DPP_TRIM_AGENT_TRACES_333(i),await t.writeAfterReadAlreadyLocked(i)','if(DPPStored331048.includes(r))return!1;i=DPP_TRIM_AGENT_TRACES_333(i),await t.writeAfterReadAlreadyLocked(i);return!0')
    c=c[:i]+part+c[j:]
    c=once(c,'status:`running`,steps:[],initialExecutions:n.map(e=>PH(e))','status:`running`,dppWriter331048:crypto.randomUUID(),dppRevision331048:0,steps:[],initialExecutions:n.map(e=>PH(e))')
    c=once(c,'BY={...e(BY),updatedAt:Date.now()}','BY=DPP_TRACE_COUNTS_331048({...e(BY),dppRevision331048:(BY.dppRevision331048??0)+1,updatedAt:Math.max(Date.now(),BY.updatedAt+1)})')
    c=once(c,'function PH(e,t={}){return{name:e.name,','function PH(e,t={}){return{...typeof e.callId===`string`?{callId:e.callId.slice(0,240)}:{},name:e.name,')
    c=once(c,'C0(t=>T0(t,e.stepIndex,{status:`executing_tools`}),{persist:!1})','C0(t=>({...T0(t,e.stepIndex,{status:`executing_tools`}),dppPendingCalls331048:[...new Set([...(t.dppPendingCalls331048??[]),String(e.call?.id??``)].filter(Boolean))].slice(-128)}),{immediate:!0})')
    c=once(c,'return{id:e.id,status:e.status,originalTask:','return{id:e.id,status:e.status,uncertainCallIds:e.dppPendingCalls331048??[],resumeRule:`Verify uncertain tool outcomes and existing artifacts before issuing new commands; never replay a consumed call ID.`,originalTask:')
    c=once(c,'function DPP_AGENT_TOOL_COMPLETE_331010(e){if(e.loopId!==LY||!Q)return;','function DPP_AGENT_TOOL_COMPLETE_331010(e){if(e.loopId!==LY||!Q)return;C0(t=>DPP_TRACE_TOOL_331048(t,e),{immediate:!0});')
    c=once(c,'r?{immediate:!0}:{persist:!1}),DPP_AGENT_STATUS_TOUCH_331010','{immediate:!0}),DPP_AGENT_STATUS_TOUCH_331010')
    c=once(c,'async function O0(e){let t=A0(e);await qX.track(TX,`inline-agent trace write`,MU(t)),CX?.active&&KY.set(t.id,t)}','async function O0(e){let t=A0(e);DPP_TRACE_DIAG_331048(`requested`,t);try{const accepted=await qX.track(TX,`inline-agent trace write`,MU(t));DPP_TRACE_DIAG_331048(accepted===!1?`stale_rejected`:`confirmed`,t);accepted!==!1&&CX?.active&&KY.set(t.id,t)}catch(error){DPP_TRACE_DIAG_331048(`failed`,t,error);throw error}}')
    c=once(c,'function r1(DPPReason331034){FX(),o1();','function r1(DPPReason331034){FX(),o1();p1();')
    c=once(c,'DPPStopText331034=typeof DPPReason331034', 'DPPStopText331034=DPPReason331034===`pagehide`?`Page closed or navigated away; task paused. Verify in-flight tool outcomes before resuming.`:typeof DPPReason331034')
    c=once(c,'status:`stopping`,error:DPPStopText331034','status:`stopping`,dppStopReason331048:DPPReason331034===`pagehide`?`pagehide`:typeof DPPReason331034===`string`&&DPPReason331034?`superseded_or_explicit`:`user_stop`,error:DPPStopText331034')
    c=once(c,'window.addEventListener(`pagehide`,()=>{t1()&&r1()})','window.addEventListener(`pagehide`,()=>{t1()&&r1(`pagehide`)})')
    # Honest UI: retrying/closing does not clear server history; no automatic new conversation or task replay.
    c=once(c,'heading.textContent=info.title;detail.textContent=info.detail;','heading.textContent=info.title;detail.textContent=info.detail+(JSON.stringify(diag?.controlTrail??[]).includes(`generation_err`)?(String(nX||``).toLowerCase().startsWith(`zh`)?` 反复失败时请用简短任务交接摘要新建对话。关闭重开不会清除服务端历史；精简恢复也不保证生成成功。`:` If failures repeat, start a new conversation with a short task handoff. Reopening does not clear server history; compact recovery cannot guarantee generation.`):``);')
    # Recovery persists only branch IDs in bounded TTL storage, never model content or tool authorization.
    anchor='DPP_GENERATION_ERR_STREAK_TTL_MS_331026=12e4;'
    mw=once(mw,anchor,anchor+'DPP_GENERATION_ERR_RECOVERY_331020=DPP_RECOVERY_STORE_331048();\n'+(HERE/'dspp-recovery-v48.js').read_text('utf-8'))
    mw=once(mw,'e?.parentMessageId!==n.expectedParentMessageId)return null','e?.parentMessageId!==n.expectedParentMessageId&&!DPP_RECOVERY_BRANCH_331048(e,n))return null')
    needle='expectedParentMessageId:t.assistantMessageId,expiresAt:'
    if mw.count(needle)!=3:raise ValueError('Expected three recovery records')
    mw=mw.replace(needle,'expectedParentMessageId:t.assistantMessageId,expectedUserMessageId:t.dppRequestMessageId331048??null,expiresAt:')
    mw=once(mw,'parentMessageId:c(r.parent_message_id),promptOptions:','parentMessageId:c(r.parent_message_id),targetMessageId331048:c(r.message_id??r.child_message_id),requestRoute331048:t.requestRoute331048??null,promptOptions:')
    mw=once(mw,'DPPInitialRequest331018=ja(n.body);','DPPInitialRequest331018=ja(n.body,{requestRoute331048:a});')
    mw=once(mw,'DPPInitialRequest331018=ja(e);','DPPInitialRequest331018=ja(e,{requestRoute331048:r});')
    mw=once(mw,'assistantMessageId:n.responseMessageId,promptOptions:e.promptOptions','assistantMessageId:n.responseMessageId,dppRequestMessageId331048:n.requestMessageId,promptOptions:e.promptOptions')
    values['content-scripts/content.js']=c.encode();values['content-scripts/main-world.js']=mw.encode();values['background.js']=bg.encode()
    m=json.loads(values['manifest.json']);m['version']=VERSION;m['version_name']=NAME;values['manifest.json']=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode()
    for lang in ['en','zh_CN']:
        n=f'_locales/{lang}/messages.json'
        if n in values:values[n]=once(values[n].decode(),'DeepSeek++ ShunCode MCP Fix 3.3.10.47','DeepSeek++ ShunCode MCP Fix 3.3.10.48').encode()
    for n in list(values):
        if '/' not in n and 'selftest' in n and n.endswith('.js'):
            s=values[n].decode().replace('1.14.0.52',VERSION).replace('1.14.0 ShunCode MCP Fix 3.3.10.47',NAME).replace('|46|47)$','|46|47|48)$')
            if n=='dspp-bare-tool-tag-v41-selftest.js':s=s.replace('22e7687c843bea404d53457cf5a44533dd29e9c062bb33f991b1480e97d9a74d',sha(values['background.js'])).replace('background.js is the .42 build (only exposure literals changed; authorization gate intact)','background.js matches .48 approved initialization-only delta').replace('50ea860665adf7710e645d9708ac9b08fc59d27059ebae3e78165068677df7fe',sha(values['content-scripts/main-world.js']))
            if n=='fix33107-agent-lifecycle-mcp503-selftest.js':
                s=once(s,"retryable}});","retryable,details:{externalOutcome:'not_dispatched',retrySafe:true}}});")
            if n in ['fix331034-run-command-status-selftest.js','fix33108-lifecycle-selftest.js']:
                s=s.replace('t1()&&r1()','t1()&&r1(`pagehide`)').replace('pagehide path still plain r1()','pagehide path records explicit reason')
            if n=='fix333-agent-stability-selftest.js':
                s=s.replace("content.includes('status:`executing_tools`}),{persist:!1})')","content.includes('dppPendingCalls331048:[...new Set(')").replace('tool detected is memory-only','tool dispatch is checkpointed as uncertain in .48')
                s=s.replace('// Stress model: 19 results','// Historical .33 cadence fixture only (not a .48 write-frequency claim): 19 results')
                s=s.replace("content.includes('r?{immediate:!0}:{persist:!1}')","content.includes('{immediate:!0}),DPP_AGENT_STATUS_TOUCH_331010')").replace('completed steps checkpoint only on cadence','completed steps checkpoint immediately in .48')
            if n=='fix334-tool-storm-selftest.js':
                s=s.replace('async read(){return wi(async()=>{','async read(){return DPP_TRACE_LOCK_331048(()=>wi(async()=>{').replace('writeAfterReadAlreadyLocked(n),n})}','writeAfterReadAlreadyLocked(n),n}))}')
            values[n]=s.encode()
    for n in ['dspp-reliability-v48-selftest.js']:
        if (HERE/n).exists():values[n]=(HERE/n).read_bytes()
    return values

def build(base,out):
    base=Path(base).resolve();out=Path(out).resolve()
    locks=json.loads((HERE/'fix331048-source-sha256.json').read_text('utf-8'))
    for n,d in locks.items():
        if sha((HERE/n).read_bytes())!=d:raise ValueError('Source hash mismatch: '+n)
    if out.exists() or out==base or base in out.parents:raise ValueError('Output must be new and outside baseline')
    stage=out.with_name(out.name+'.stage47')
    if stage.exists():raise ValueError('Staging exists')
    spec=importlib.util.spec_from_file_location('b47',HERE/'apply-fix331047.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    values=transform(b.build(base,stage))
    for n in ['background.js','content-scripts/content.js','content-scripts/main-world.js','fix3-policy.js']:
        r=subprocess.run(['node','--check','--input-type=module'],input=values[n],capture_output=True)
        if r.returncode:raise ValueError('Syntax: '+n+' '+r.stderr.decode(errors='replace'))
    out.mkdir(parents=True)
    for n,raw in values.items():p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    shutil.rmtree(stage);print(json.dumps({'version':VERSION,'files':len(values)}),flush=True);return values
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',nargs=2,required=True);a=p.parse_args()
    try:build(*a.build)
    except (ValueError,OSError) as e:raise SystemExit('FAIL-CLOSED: '+str(e))
