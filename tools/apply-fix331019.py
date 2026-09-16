from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path


EXPECTED_331018 = {
    "content-scripts/content.js": "DFAE734C0A6D277FCA11CB671E5D28AADE69E77D1A155CED19B5AA3E4AFAF410",
    "content-scripts/main-world.js": "D2C47A42FE0229A406ECD674C9409F893ABD3B95D2B7D691B103059529BA0C2F",
    "background.js": "809DB9658729E70744BA48D44698F531562C2E5BCB9A89D01162F1E3CC1FCA5B",
    "manifest.json": "467092B1F878C8F4A7B690960C1D5A509B59827FE5997721D6B885FD85ED1E34",
    "_locales/en/messages.json": "6A9091365FB35EEC12D21CB18ACB3B53DFAC864897BF46ACDA5B1AA1F577F277",
    "_locales/zh_CN/messages.json": "9812C39828D51FCC5362BF7A87336AF10B48D807BAD29CFD4CBF62F477906AC0",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def replace_exact(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(f"{label}: expected {count} marker(s), found {actual}")
    return text.replace(old, new, count)


def write_crlf(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\r\n")


def transform_content(path: Path) -> None:
    s = path.read_text("utf-8-sig")

    # Capability aliases are parser conveniences only. Every alias delegates to the
    # already-authorized mcp_invoke tool with the exact single-use handle returned by
    # the latest mcp_discover result; the background lease resolver remains the final
    # owner/TTL/replay/schema authority.
    marker = "function DPP_TOOL_NAME_33(e){"
    helper = (
        "function DPP_CAP_ALIAS_NAME_331019(e){return typeof e==`string`&&/^[A-Za-z_][A-Za-z0-9_.:-]*$/.test(e)}"
        "function DPP_CAP_ALIAS_HANDLE_331019(e){return typeof e==`string`&&/^mcp_cap_[A-Za-z0-9-]{16,}$/.test(e)}"
        "function DPP_CAP_ALIAS_ARGS_331019(e){return e&&typeof e==`object`&&!Array.isArray(e)?e:null}"
    )
    s = replace_exact(s, marker, helper + marker, "capability alias helpers")

    old = "g=[...t.toolExecutions],_=[],v=new Map(c.map(e=>[e.invocationName,e])),DPPToolMeta=new Map,y={"
    new = (
        "g=[...t.toolExecutions],_=[],v=new Map(c.map(e=>[e.invocationName,e])),"
        "DPPBaseToolNames331019=new Set(c.flatMap(e=>[e.invocationName,e.name].filter(e=>typeof e==`string`&&e))),"
        "DPPAliases331019=new Map,DPPToolMeta=new Map,y={"
    )
    s = replace_exact(s, old, new, "agent capability alias state")

    old = (
        "Se=Bz({descriptors:c,executeTool:r,callSource:{requestId:t.capabilityScopeRequestId??`agent:${a}`,chatSessionId:s}}),"
        "Ce=Hz(t.originalPrompt),we={"
    )
    new = (
        "Se=Bz({descriptors:c,executeTool:r,callSource:{requestId:t.capabilityScopeRequestId??`agent:${a}`,chatSessionId:s}}),"
        "DPPInvokeDescriptor331019=c.find(e=>e.invocationName===`mcp_invoke`||e.name===`mcp_invoke`),"
        "DPPInvokeTool331019=DPPInvokeDescriptor331019?Se.find(e=>e.name===DPPInvokeDescriptor331019.invocationName):null,"
        "DPPRemoveAlias331019=(e,t)=>{let n=DPPAliases331019.get(e);if(!n||t&&n.capability!==t)return!1;"
        "DPPAliases331019.delete(e);let r=c.indexOf(n.descriptor);r>=0&&c.splice(r,1);let i=Se.indexOf(n.tool);"
        "return i>=0&&Se.splice(i,1),st.delete(c),!0},"
        "DPPInstallAliases331019=e=>{let t=DPP_CAPABILITY_WINDOW_32(e);if(!t||!DPPInvokeDescriptor331019||!DPPInvokeTool331019)return 0;"
        "for(let e of[...DPPAliases331019.keys()])DPPRemoveAlias331019(e);let n=new Map;for(let e of t.candidates??[]){let t=e?.name;"
        "DPP_CAP_ALIAS_NAME_331019(t)&&n.set(t,(n.get(t)??0)+1)}let r=Date.now(),i=0;"
        "for(let a of t.candidates??[]){let t=a?.name,o=a?.capability;if(!DPP_CAP_ALIAS_NAME_331019(t)||!DPP_CAP_ALIAS_HANDLE_331019(o)||"
        "n.get(t)!==1||DPPBaseToolNames331019.has(t))continue;if(!Number.isFinite(a?.expiresAt)||a.expiresAt<=r+1e3)continue;"
        "let s={id:`dpp331019-capability:${o}`,provider:DPPInvokeDescriptor331019.provider,name:t,invocationName:t,title:t,"
        "description:`Temporary alias for a discovered MCP capability. Execution is still authorized and consumed through mcp_invoke.`,"
        "inputSchema:{type:`object`,properties:{},additionalProperties:!0},execution:{mode:`auto`,enabled:!0,risk:DPPInvokeDescriptor331019.execution?.risk??`low`}},"
        "l={name:t,label:t,description:s.description,parameters:s.inputSchema,prepareArguments:e=>e,execute:async(e,n,r,i)=>{"
        "let a=DPP_CAP_ALIAS_ARGS_331019(n);if(!a)return DPP_BLOCK_RESULT_33(`dpp_capability_alias_arguments_invalid`,`Capability arguments invalid`,"
        "`The discovered capability alias requires a JSON object. Re-emit the call with a structured argument object.`,`reemit_tool_call`);"
        "try{return await DPPInvokeTool331019.execute(`${e}:dpp331019`,{capability:o,arguments:a},r,i)}finally{DPPRemoveAlias331019(t,o)}}};"
        "c.push(s),Se.push(l),v.set(t,s),DPPAliases331019.set(t,{capability:o,descriptor:s,tool:l}),i+=1}return st.delete(c),i},"
        "DPPInitialAliasCount331019=g.length?DPPInstallAliases331019(g[g.length-1]):0,Ce=Hz(t.originalPrompt),we={"
    )
    s = replace_exact(s, old, new, "capability alias installer")

    old = "_.push(DPPExecution),n(`AGENT_TOOL_COMPLETE`,{loopId:a,stepIndex:b,execution:DPPExecution});break"
    new = "_.push(DPPExecution),DPPInstallAliases331019(DPPExecution),n(`AGENT_TOOL_COMPLETE`,{loopId:a,stepIndex:b,execution:DPPExecution});break"
    s = replace_exact(s, old, new, "install aliases after discovery")

    # Resume reliability: tool summaries are checkpoint facts, not raw outputs/args.
    marker = "function DPP_RESUME_LIGHT_PROMPT_331011(e,t){"
    helper = (
        "function DPP_RESUME_TOOL_FACTS_331019(e){let t=[],n=new Set,r=e=>{if(!e||typeof e!=`object`)return;"
        "let r=String(e.name??e.invocationName??``).trim();if(!r)return;let i=e.result&&typeof e.result==`object`?e.result:{},"
        "a=i.ok===!0?`ok`:`failed`,o=typeof i.error?.code==`string`?i.error.code:``,s=DPP_RESUME_CLEAN_TEXT_331011(i.summary??i.detail??``,180),"
        "c=`${r}: ${a}${o?` (${o})`:``}${s?` - ${s}`:``}`;n.has(c)||(n.add(c),t.push(c))};"
        "for(let t of Array.isArray(e)?e:[]){for(let e of t?.initialExecutions??[])r(e);for(let e of t?.steps??[])for(let t of e?.toolExecutions??[])r(t)}"
        "return t.slice(-12)}"
    )
    s = replace_exact(s, marker, helper + marker, "resume tool facts helper")

    old = "let o=a.slice(-7),s=[`[Fix 3.3.10.11 safe resume] This is a resume, not a new task.`,`Merge duplicate attempts"
    new = "let o=a.slice(-7),DPPResumeTools331019=DPP_RESUME_TOOL_FACTS_331019(n),s=[`[Fix 3.3.10.11 safe resume] [Fix 3.3.10.19 durable resume] This is a resume, not a new task.`,`Merge duplicate attempts"
    s = replace_exact(s, old, new, "resume prompt version/tool facts")

    old = "o.length?`Verified progress:\\n${o.map(e=>`- ${e}`).join(`\\n`)}`:``,`Last interruption: ${DPP_RESUME_CLEAN_TEXT_331011(i?.error,240)}`"
    new = "o.length?`Verified progress:\\n${o.map(e=>`- ${e}`).join(`\\n`)}`:``,DPPResumeTools331019.length?`Verified tool results:\\n${DPPResumeTools331019.map(e=>`- ${e}`).join(`\\n`)}`:``,`Last interruption: ${DPP_RESUME_CLEAN_TEXT_331011(i?.error,240)}`"
    s = replace_exact(s, old, new, "resume tool facts prompt")
    s = replace_exact(s, "return s.length>2400?`${s.slice(0,2380)}...[truncated]`:s", "return s.length>3600?`${s.slice(0,3580)}...[truncated]`:s", "resume prompt bound")

    # Explicit “continue” can resume a durable checkpoint even when the manual
    # DeepSeek response itself contains no fresh tool calls.
    old = (
        "async function J$(e,t){if(X$(e))return;if(t1()){S$($(`content.agent.concurrencyGuard`),`warning`);return}"
        "let n=aB(t);if(n.length===0||!e.chatSessionId||e.assistantMessageId==null)return;let DPPResume=null;"
        "try{DPPResume=DPP_AGENT_RESUME_PREPARE_331012(e,await k0())}catch(e){console.error(`[DeepSeek++] failed to prepare interrupted Agent checkpoint`,e)}"
        "let DPPAgentPrompt=DPPResume?.prompt??e.agentTaskPrompt??e.originalPrompt"
    )
    new = (
        "async function J$(e,t){let n=aB(t);if(!e.chatSessionId||e.assistantMessageId==null)return;let DPPResume=null;"
        "try{DPPResume=DPP_AGENT_RESUME_PREPARE_331012(e,await k0())}catch(e){console.error(`[DeepSeek++] failed to prepare interrupted Agent checkpoint`,e)}"
        "if(X$(e)&&!DPPResume)return;if(t1()){S$($(`content.agent.concurrencyGuard`),`warning`);return}if(n.length===0&&!DPPResume)return;"
        "let DPPAgentPrompt=DPPResume?.prompt??e.agentTaskPrompt??e.originalPrompt"
    )
    s = replace_exact(s, old, new, "zero-tool durable resume gateway")

    old = "let a={loopId:r,capabilityScopeRequestId:e.requestId,chatSessionId:e.chatSessionId,parentMessageId:e.assistantMessageId,originalPrompt:DPPAgentPrompt"
    new = "let a={loopId:r,capabilityScopeRequestId:e.requestId,chatSessionId:e.chatSessionId,parentMessageId:e.assistantMessageId,resumeSourceTraceIds:DPPResume?.sourceTraceIds??[],originalPrompt:DPPAgentPrompt"
    s = replace_exact(s, old, new, "resume source ids in agent payload")

    old = "let o=XB(r1,NX());o.setAttribute(`data-dpp-agent-loop-id`,r);let s=y0(e)"
    new = "let o=XB(r1,NX());o.setAttribute(`data-dpp-agent-loop-id`,r),o.setAttribute(`data-dpp-resume-count`,String(DPPResume?.sourceTraceIds?.length??0)),DPPResume&&QB(o,{phase:`starting`,stepNumber:0,toolCount:0,totalSteps:0,totalTools:n.length,elapsedSeconds:0},NX());let s=y0(e)"
    s = replace_exact(s, old, new, "resume status marker")

    # Preserve the old cadence for regressions, but add an immediate first-step
    # checkpoint and immediate checkpoint after a successful mutation.
    marker = "function DPP_AGENT_CHECKPOINT_333(e){return(e+1)%4===0}"
    new = marker + "function DPP_AGENT_CHECKPOINT_331019(e,t){return e===0||Array.isArray(t)&&t.some(e=>(e?.dppEffect??DPP_TOOL_EFFECT_31(e?.name))===`mutation`)}"
    s = replace_exact(s, marker, new, "durable checkpoint helper")
    old = "let n=x0(IY),r=DPP_AGENT_CHECKPOINT_333(e.stepIndex);C0("
    new = "let n=x0(IY),r=DPP_AGENT_CHECKPOINT_333(e.stepIndex)||DPP_AGENT_CHECKPOINT_331019(e.stepIndex,e.toolExecutions);C0("
    s = replace_exact(s, old, new, "durable checkpoint cadence")

    # Codex-like compact page UI. Internal reasoning and intermediate narration
    # remain in the trace for recovery but are not shown by default (or in details).
    marker = "var DPP_AGENT_STATUS_331010={maxSteps:0,activity:`starting`,toolName:``,lastActivityAt:0};"
    compact = r'''var DPP_AGENT_COMPACT_CSS_ID_331019=`dpp-agent-compact-ui-331019`;function DPP_AGENT_COMPACT_STYLE_331019(){if(document.getElementById(DPP_AGENT_COMPACT_CSS_ID_331019))return;let e=document.createElement(`style`);e.id=DPP_AGENT_COMPACT_CSS_ID_331019,e.textContent=`
    .dpp-agent-container { padding: 7px 0 !important; }
    .dpp-agent-container .dpp-agent-status-line { gap: 7px !important; min-height: 28px; }
    .dpp-agent-container .dpp-agent-status-detail { display: none !important; }
    .dpp-agent-container .dpp-agent-progress-track { margin-top: 1px !important; margin-bottom: 3px !important; }
    .dpp-agent-container .dpp-agent-stream { display: none !important; margin-top: 4px; }
    .dpp-agent-container[data-details-open="true"] .dpp-agent-stream { display: block !important; }
    .dpp-agent-container .dpp-agent-reasoning-note,
    .dpp-agent-container .dpp-agent-step,
    .dpp-agent-container .dpp-agent-starting { display: none !important; }
    .dpp-agent-details-btn { margin-left: auto; border: 0; background: transparent; color: var(--dpp-ui-text-muted); font: inherit; font-size: 11px; cursor: pointer; padding: 2px 5px; border-radius: 5px; }
    .dpp-agent-details-btn:hover { background: var(--dpp-ui-surface-hover); }
    .dpp-agent-final-answer { margin-top: 7px; color: var(--dpp-ui-text); font-size: 13px; line-height: 1.6; overflow-wrap: anywhere; }
    .dpp-agent-final-answer:empty { display: none; }
    .dpp-agent-final-answer > :first-child { margin-top: 0; }
    .dpp-agent-final-answer > :last-child { margin-bottom: 0; }
  `,document.head.appendChild(e)}function DPP_AGENT_COMPACT_COPY_331019(){let e=String(nX??``).toLowerCase().startsWith(`zh`);return e?{badge:{starting:`准备`,running:`运行中`,complete:`完成`,paused:`暂停`,error:`未完成`},resume:`续跑中`,preparing:`正在准备`,waiting:`等待模型`,thinking:`正在规划下一步`,responding:`正在整理结果`,tool:`执行`,continuing:`继续下一步`,details:`详情`,hide:`收起`,tools:`工具`,recover:`发送“继续”恢复`}:{badge:{starting:`Preparing`,running:`Running`,complete:`Done`,paused:`Paused`,error:`Incomplete`},resume:`Resuming`,preparing:`Preparing`,waiting:`Waiting for model`,thinking:`Planning next step`,responding:`Preparing result`,tool:`Running`,continuing:`Continuing`,details:`Details`,hide:`Hide`,tools:`tools`,recover:`Send “continue” to resume`}}function DPP_AGENT_COMPACT_BADGE_331019(e,t,n){let r=DPP_AGENT_COMPACT_COPY_331019(),i=Number(e.getAttribute(`data-dpp-resume-count`)??0)>0;return(t===`starting`||t===`running`)&&i?r.resume:r.badge[t]??n.badge[t]??t}function DPP_AGENT_COMPACT_TEXT_331019(e,t){let n=DPP_AGENT_COMPACT_COPY_331019(),r=Number(e.getAttribute(`data-dpp-resume-count`)??0)>0,i=t.activity??DPP_AGENT_STATUS_331010.activity,a=t.activityTool||DPP_AGENT_STATUS_331010.toolName,o=t.completedTools??0,s=t.pendingTools??0,c=Math.max(0,Number(t.elapsedSeconds??0));if(t.phase===`complete`)return`${n.badge.complete} · ${t.totalTools??o} ${n.tools} · ${c}s`;if(t.phase===`paused`||t.phase===`error`)return n.recover;if(t.phase===`starting`)return r?n.resume:n.preparing;let l=i===`tool`?`${n.tool}${a?` ${a}`:``}`:i===`thinking`?n.thinking:i===`responding`?n.responding:i===`continuing`?n.continuing:n.waiting;return`${r?n.resume:l} · ${o}${s?` +${s}`:``} ${n.tools} · ${c}s`}function DPP_AGENT_FINAL_331019(e,t){let n=e?.querySelector?.(`.dpp-agent-final-answer`),r=String(t??``).trim();n&&(n.setAttribute(`data-dpp-raw-text`,r),n.innerHTML=r?bV(r):``)}''' + marker
    s = replace_exact(s, marker, compact, "compact agent UI helpers")

    s = replace_exact(s, "function XB(e,t){let n=document.createElement(`div`);", "function XB(e,t){DPP_AGENT_COMPACT_STYLE_331019();let n=document.createElement(`div`);n.setAttribute(`data-details-open`,`false`);", "compact UI init")

    old = "let u=document.createElement(`div`);return u.className=`dpp-agent-stream`,n.appendChild(r),n.appendChild(s),n.appendChild(c),n.appendChild(u),QB(n,{phase:`starting`,stepNumber:0,toolCount:0,totalSteps:0,totalTools:0,elapsedSeconds:0},t),n}"
    new = "let u=document.createElement(`div`);u.className=`dpp-agent-stream`;let d=document.createElement(`div`);d.className=`dpp-agent-final-answer`;let f=document.createElement(`button`),p=DPP_AGENT_COMPACT_COPY_331019();return f.type=`button`,f.className=`dpp-agent-details-btn`,f.textContent=p.details,f.setAttribute(`aria-expanded`,`false`),f.addEventListener(`click`,()=>{let e=n.getAttribute(`data-details-open`)===`true`;n.setAttribute(`data-details-open`,e?`false`:`true`),f.setAttribute(`aria-expanded`,e?`false`:`true`),f.textContent=e?p.details:p.hide}),r.appendChild(f),n.appendChild(r),n.appendChild(s),n.appendChild(c),n.appendChild(d),n.appendChild(u),QB(n,{phase:`starting`,stepNumber:0,toolCount:0,totalSteps:0,totalTools:0,elapsedSeconds:0},t),n}"
    s = replace_exact(s, old, new, "compact UI container")

    old = "let i=DPP_AGENT_STATUS_COPY_331010(),a=e.querySelector(`.dpp-agent-status-badge`);a&&(a.textContent=i.badge[r.phase]??r.phase);let o=e.querySelector(`.dpp-agent-status-text`);o&&(o.textContent=$B(r,n));let s=e.querySelector(`.dpp-agent-status-detail`);s&&(s.textContent=DPP_AGENT_STATUS_DETAIL_331010(r),s.title=i.dynamic);"
    new = "let i=DPP_AGENT_STATUS_COPY_331010(),a=e.querySelector(`.dpp-agent-status-badge`);a&&(a.textContent=DPP_AGENT_COMPACT_BADGE_331019(e,r.phase,i));let o=e.querySelector(`.dpp-agent-status-text`);o&&(o.textContent=DPP_AGENT_COMPACT_TEXT_331019(e,r));let s=e.querySelector(`.dpp-agent-status-detail`);s&&(s.textContent=``,s.title=``);"
    s = replace_exact(s, old, new, "compact status rendering")

    old = "DPP_AGENT_STATUS_TOUCH_331010(`tool`,`${e.call?.provider?.displayName?`${e.call.provider.displayName} / `:``}${e.call?.name??``}`),cX+=1"
    new = "DPP_AGENT_STATUS_TOUCH_331010(`tool`,DPP_TOOL_NAME_33(e.call?.name??e.call?.invocationName??``)),cX+=1"
    s = replace_exact(s, old, new, "compact current tool name")

    old = "u&&y1(Q,u,e.loopId),RX(Q,a?`paused`:`complete`,e.totalSteps,e.totalTools);"
    new = "u&&y1(Q,u,e.loopId),!a&&u&&DPP_AGENT_FINAL_331019(Q,u),RX(Q,a?`paused`:`complete`,e.totalSteps,e.totalTools);"
    s = replace_exact(s, old, new, "separate final answer")

    write_crlf(path, s)


def transform_tree(root: Path) -> None:
    for rel, expected in EXPECTED_331018.items():
        p = root / rel
        if not p.exists():
            raise RuntimeError(f"missing required file: {rel}")
        got = sha256(p)
        if got != expected:
            raise RuntimeError(f"input hash mismatch for {rel}: {got} != {expected}")

    transform_content(root / "content-scripts/content.js")

    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8-sig"))
    if manifest.get("version") != "1.14.0.23" or manifest.get("version_name") != "1.14.0 ShunCode MCP Fix 3.3.10.18":
        raise RuntimeError("manifest is not the expected Fix 3.3.10.18 input")
    manifest["version"] = "1.14.0.24"
    manifest["version_name"] = "1.14.0 ShunCode MCP Fix 3.3.10.19"
    write_crlf(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    for rel in ("_locales/en/messages.json", "_locales/zh_CN/messages.json"):
        p = root / rel
        text = p.read_text("utf-8-sig")
        if "Fix 3.3.10.18" not in text:
            raise RuntimeError(f"{rel}: expected Fix 3.3.10.18 locale marker")
        write_crlf(p, text.replace("Fix 3.3.10.18", "Fix 3.3.10.19"))



OUTPUT_EXPECTED_331019 = {
    "content-scripts/content.js": "5161896C3E85A29EF50343FEEFD807AB464C01F46A2E7C180234EE6C6AE55856",
    "content-scripts/main-world.js": "D2C47A42FE0229A406ECD674C9409F893ABD3B95D2B7D691B103059529BA0C2F",
    "background.js": "809DB9658729E70744BA48D44698F531562C2E5BCB9A89D01162F1E3CC1FCA5B",
    "manifest.json": "4DF630AAD42AFDB1CF493AA8E0DA2F8BC08AAFDCD57814C77F10E2EDCF516D9C",
    "_locales/en/messages.json": "895A2E0A423A6253952AFCA17FAF5D842A47EB49B11372DEDC197BB1D8956111",
    "_locales/zh_CN/messages.json": "33BABFE7D8A76DEBE5E44DDDCBD0BF57D0E7E2A7FCC068390357C5F54F268238",
}
OLD_VERSION_331019 = "1.14.0 ShunCode MCP Fix 3.3.10.18"
NEW_VERSION_331019 = "1.14.0 ShunCode MCP Fix 3.3.10.19"
OLD_MANIFEST_VERSION_331019 = "1.14.0.23"
NEW_MANIFEST_VERSION_331019 = "1.14.0.24"
RELS_331019 = list(EXPECTED_331018)


def apply(root_arg: str) -> None:
    root = Path(root_arg).resolve()
    paths = {rel: root / rel for rel in RELS_331019}
    manifest = json.loads(paths["manifest.json"].read_text("utf-8-sig"))
    if manifest.get("version") == NEW_MANIFEST_VERSION_331019 and manifest.get("version_name") == NEW_VERSION_331019:
        for rel, expected in OUTPUT_EXPECTED_331019.items():
            got = sha256(paths[rel])
            if got != expected:
                raise RuntimeError(f"already-applied hash mismatch for {rel}: {got} != {expected}")
        print("APPLY_FIX331019_OK already-applied")
        return
    if manifest.get("version") != OLD_MANIFEST_VERSION_331019 or manifest.get("version_name") != OLD_VERSION_331019:
        raise RuntimeError(f"expected {OLD_VERSION_331019}, got {manifest.get('version_name')!r}")
    for rel, expected in EXPECTED_331018.items():
        got = sha256(paths[rel])
        if got != expected:
            raise RuntimeError(f"input hash mismatch for {rel}: {got} != {expected}")
    stage = Path(tempfile.mkdtemp(prefix=".fix331019-stage-", dir=root))
    try:
        for rel in RELS_331019:
            dst = stage / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(paths[rel], dst)
        transform_tree(stage)
        for rel, expected in OUTPUT_EXPECTED_331019.items():
            got = sha256(stage / rel)
            if got != expected:
                raise RuntimeError(f"staged output hash mismatch for {rel}: {got} != {expected}")
        for rel in RELS_331019:
            os.replace(stage / rel, paths[rel])
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    print("APPLY_FIX331019_OK")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply-fix331019.py <extension-root>")
    apply(sys.argv[1])
