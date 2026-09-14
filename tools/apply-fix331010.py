from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


OLD_VERSION = "1.14.0 ShunCode MCP Fix 3.3.10.9"
NEW_VERSION = "1.14.0 ShunCode MCP Fix 3.3.10.10"
OLD_MANIFEST_VERSION = "1.14.0.14"
NEW_MANIFEST_VERSION = "1.14.0.15"
MARKER = "DPP_AGENT_STATUS_RESET_331010"

EXPECTED = {
    "content-scripts/content.js": "6A3F72E316265ED33A1CEA974E6048A79DBD7F124D135128F1934557827C5ECB",
    "manifest.json": "7CAE4EEC1486D6E8FDEEB9152A5AD954B082C25320661AA5CF867EA105451C79",
    "_locales/en/messages.json": "0C9166A9E59386011B19DD971AECC0EDE28ABF6F55E4CD1EFDA5A1B81416B6EF",
    "_locales/zh_CN/messages.json": "68C1CC5AD159851BBA7B807A7929613A409BABFBBD6553579B1DCB809BC49249",
}

# Filled after the first audited build. Keeping these hashes in the patcher makes
# both accidental double-patching and a drifting upstream bundle fail closed.
OUTPUT_EXPECTED = {
    "content-scripts/content.js": "6AB9B93EEF0028880DAC2FE5140757AB75C5A2D3AFD03F8C1334A529C29D65A8",
    "manifest.json": "F3D4AA1874514FF792DFAB720C1B7281F17186C5911C42A3F396EDC347AFA66F",
    "_locales/en/messages.json": "C2AC07E4D1BCE5AC829E52239927A9B4FD49EB2AE5FE756DDA693739AEE1BB1E",
    "_locales/zh_CN/messages.json": "BEAFDC1783D3402E2FF44A8DDE7D379BCEC2848E540E7161BE60E799AC0C93CC",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def replace_one(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def stage_write(path: Path, data: bytes) -> Path:
    tmp = path.with_name(path.name + ".fix331010.tmp")
    tmp.write_bytes(data)
    return tmp


def main(root_arg: str) -> None:
    root = Path(root_arg).resolve()
    paths = {rel: root / rel for rel in EXPECTED}
    manifest = json.loads(paths["manifest.json"].read_text(encoding="utf-8-sig"))
    content = paths["content-scripts/content.js"].read_text(encoding="utf-8-sig")

    if (
        manifest.get("version") == NEW_MANIFEST_VERSION
        and manifest.get("version_name") == NEW_VERSION
        and MARKER in content
    ):
        if OUTPUT_EXPECTED:
            for rel, expected in OUTPUT_EXPECTED.items():
                actual = sha256((root / rel).read_bytes())
                if actual != expected:
                    raise RuntimeError(f"already-patched hash mismatch for {rel}: {actual}")
        print("APPLY_FIX331010_OK already-applied")
        return

    if manifest.get("version") != OLD_MANIFEST_VERSION or manifest.get("version_name") != OLD_VERSION:
        raise RuntimeError(f"expected {OLD_VERSION}, got {manifest.get('version_name')!r}")
    for rel, expected in EXPECTED.items():
        actual = sha256(paths[rel].read_bytes())
        if actual != expected:
            raise RuntimeError(f"input hash mismatch for {rel}: {actual}")

    # Fix a real 3.3.10.8 regression: the normalizer received the whole call
    # object but tried to classify it as a string, so exit_code=1 remained ok=true.
    content = replace_one(
        content,
        "function DPP_NORMALIZE_RUN_COMMAND_RESULT_33108(e,t){if(DPP_TOOL_NAME_33(e)!==`run_command`||t?.ok!==!0)return t;",
        "function DPP_NORMALIZE_RUN_COMMAND_RESULT_33108(e,t){if(DPP_TOOL_NAME_33(typeof e==`string`?e:e?.invocationName??e?.name)!==`run_command`||t?.ok!==!0)return t;",
        "run_command result classifier",
    )

    old_error_class = "function DPP_ERROR_CLASS_3(e){let t=String(e?.code??`unknown`);return t===`dpp_fix3_no_progress`?{stage:`loop_guard`,action:`change_tool_or_parameters`}:t===`dpp_tool_storm_blocked`?{stage:`tool_storm_guard`,action:`wait_for_next_user_turn`}:t===`dpp_tool_parameter_unsafe`?{stage:`safety_guard`,action:`reduce_tool_parameter`}:t===`dpp_tool_arguments_missing`?{stage:`format_or_schema`,action:`reemit_tool_call`}:t===`dpp_windows_text_encoding_unsafe`?{stage:`safety_guard`,action:`rewrite_command_with_explicit_utf8`}:/^mcp_capability_handle_(?:replayed|expired|invalid|descriptor_stale)/.test(t)?{stage:`mcp_capability`,action:`rediscover_capability`}:/^tool_call_/.test(t)?{stage:`format_or_schema`,action:`repair_parameters`}:t===`tool_authorization_call_limit`?{stage:`tool_storm_guard`,action:`stop_tool_calls_and_summarize`}:/^tool_authorization|authorization/.test(t)?{stage:`authorization`,action:`refresh_authorization`}:/^mcp_(http|sse|connect|initialize|transport|response)/.test(t)?{stage:`mcp_transport`,action:e?.retryable===!0?`safe_retry_if_read_only`:`inspect_connection`}:/^mcp_tool|tool_unsupported/.test(t)?{stage:`mcp_tool`,action:`refresh_tool_catalog`}:{stage:`tool_runtime`,action:e?.retryable===!0?`retry_if_safe`:`inspect_error`}}"
    new_error_class = "function DPP_ERROR_CLASS_3(e){let t=String(e?.code??`unknown`),n=String(e?.message??``);return t===`dpp_fix3_no_progress`?{stage:`loop_guard`,action:`change_tool_or_parameters`}:t===`dpp_tool_storm_blocked`?{stage:`tool_storm_guard`,action:`wait_for_next_user_turn`}:t===`dpp_tool_parameter_unsafe`?{stage:`safety_guard`,action:`reduce_tool_parameter`}:t===`dpp_tool_arguments_missing`?{stage:`format_or_schema`,action:`reemit_tool_call`}:t===`dpp_windows_text_encoding_unsafe`?{stage:`safety_guard`,action:`rewrite_command_with_explicit_utf8`}:t===`mcp_tool_call_failed`&&/(?:SSE stream ended|network error|timed? out|timeout)/i.test(n)?{stage:`mcp_transport`,action:e?.details?.externalOutcome===`ambiguous`?`verify_external_outcome_before_retry`:`reconnect_and_retry_if_safe`}:/^mcp_capability_handle_(?:replayed|expired|invalid|descriptor_stale)/.test(t)?{stage:`mcp_capability`,action:`rediscover_capability`}:/^tool_call_/.test(t)?{stage:`format_or_schema`,action:`repair_parameters`}:t===`tool_authorization_call_limit`?{stage:`tool_storm_guard`,action:`stop_tool_calls_and_summarize`}:/^tool_authorization|authorization/.test(t)?{stage:`authorization`,action:`refresh_authorization`}:/^mcp_(http|sse|connect|initialize|transport|response)/.test(t)?{stage:`mcp_transport`,action:e?.retryable===!0?`safe_retry_if_read_only`:`inspect_connection`}:/^mcp_tool|tool_unsupported/.test(t)?{stage:`mcp_tool`,action:`refresh_tool_catalog`}:{stage:`tool_runtime`,action:e?.retryable===!0?`retry_if_safe`:`inspect_error`}}"
    content = replace_one(content, old_error_class, new_error_class, "transport error classification")

    old_hint = "function DPP_RESULT_HINT_33(e){let t=String(e?.result?.error?.code??``).toUpperCase(),n=DPP_TOOL_NAME_33(e?.name);return t===`FILE_NOT_FOUND`&&/^(read_files|find_files|search_files|list_directory)$/.test(n)?{recoveryHint:`ShunCode file tools are workspace-scoped. If the intended file is outside the current ShunCode workspace, use run_command with its explicit absolute path instead of retrying a workspace-relative path.`}:{}}"
    new_hint = "function DPP_RESULT_HINT_33(e){let t=String(e?.result?.error?.code??``).toUpperCase(),n=DPP_TOOL_NAME_33(e?.name),r=String(e?.result?.error?.message??e?.result?.detail??``);if((t===`FILE_NOT_FOUND`||t===`PATH_OUTSIDE_WORKSPACE`)&&/^(read_files|find_files|search_files|list_directory|read_image)$/.test(n))return{recoveryHint:n===`read_image`?`ShunCode image reads are workspace-scoped. Copy the image into the current workspace with run_command, then call read_image on that workspace-relative copy.`:`ShunCode file tools are workspace-scoped. If the intended file is outside the current ShunCode workspace, use run_command with its explicit absolute path instead of retrying a workspace-relative path.`};if(t===`MCP_TOOL_CALL_FAILED`&&/(?:SSE stream ended|network error|timed? out|timeout)/i.test(r))return{recoveryHint:e?.result?.error?.details?.externalOutcome===`ambiguous`?`The MCP connection ended after execution may have started, so the external outcome is unknown. Do not blindly repeat a mutating command. Reconnect ShunCode and verify the intended effect with a read-only command first.`:`The ShunCode MCP transport failed before a confirmed result. Reconnect the server and retry only when the operation is safe.`};if(t===`MCP_TOOL_CALL_FAILED`&&/exceeded\\s+\\d+\\s+bytes/i.test(r))return{recoveryHint:`The MCP result exceeded the configured size limit. Request a smaller range, reduce command output, or copy/downsample large images before reading them.`};return{}}"
    content = replace_one(content, old_hint, new_hint, "actionable MCP recovery hints")

    css_marker = "    @media (prefers-reduced-motion: reduce) {\n      .dpp-agent-starting::before,"
    css_insert = """    /* Fix 3.3.10.10: make liveness and honest remaining capacity visible. */
    .dpp-agent-status-line {
      align-items: flex-start;
      flex-wrap: wrap;
      padding: 5px 0 2px;
    }
    .dpp-agent-status-badge {
      flex: none;
      padding: 1px 7px;
      border-radius: 999px;
      background: var(--dpp-ui-surface);
      border: 1px solid var(--dpp-ui-border);
      color: var(--dpp-ui-text-muted);
      font-weight: 600;
      line-height: 1.45;
    }
    .dpp-agent-container[data-console-phase="starting"] .dpp-agent-status-badge,
    .dpp-agent-container[data-console-phase="running"] .dpp-agent-status-badge {
      border-color: var(--dpp-ui-accent);
      color: var(--dpp-ui-accent);
      background: var(--dpp-ui-accent-panel);
    }
    .dpp-agent-container[data-console-phase="complete"] .dpp-agent-status-badge {
      color: var(--dpp-ui-success);
    }
    .dpp-agent-container[data-console-phase="error"] .dpp-agent-status-badge {
      border-color: var(--dpp-ui-error);
      color: var(--dpp-ui-error);
      background: var(--dpp-ui-danger-panel);
    }
    .dpp-agent-status-text {
      white-space: normal;
      overflow: visible;
      text-overflow: clip;
      overflow-wrap: anywhere;
    }
    .dpp-agent-status-detail {
      flex-basis: 100%;
      margin-left: 14px;
      color: var(--dpp-ui-text-subtle);
      font-size: 11px;
      line-height: 1.55;
      white-space: normal;
      overflow-wrap: anywhere;
    }
    .dpp-agent-progress-track {
      position: relative;
      width: calc(100% - 14px);
      height: 2px;
      margin: 2px 0 5px 14px;
      overflow: hidden;
      border-radius: 999px;
      background: var(--dpp-ui-border);
    }
    .dpp-agent-progress-bar {
      position: absolute;
      inset: 0 auto 0 0;
      width: 38%;
      border-radius: inherit;
      background: var(--dpp-ui-accent);
      transform: translateX(-110%);
    }
    .dpp-agent-container[data-console-phase="starting"] .dpp-agent-progress-bar,
    .dpp-agent-container[data-console-phase="running"] .dpp-agent-progress-bar {
      animation: dpp-agent-progress-indeterminate 1.35s ease-in-out infinite;
    }
    .dpp-agent-container[data-console-phase="complete"] .dpp-agent-progress-bar {
      width: 100%;
      transform: none;
      background: var(--dpp-ui-success);
    }
    .dpp-agent-container[data-console-phase="paused"] .dpp-agent-progress-bar {
      width: 35%;
      transform: none;
      background: var(--dpp-ui-text-subtle);
    }
    .dpp-agent-container[data-console-phase="error"] .dpp-agent-progress-bar {
      width: 100%;
      transform: none;
      background: var(--dpp-ui-error);
    }
    @keyframes dpp-agent-progress-indeterminate {
      0% { transform: translateX(-110%); }
      100% { transform: translateX(310%); }
    }
""" + css_marker
    content = replace_one(content, css_marker, css_insert, "agent status CSS")

    old_ui = "function XB(e,t){let n=document.createElement(`div`);n.className=`dpp-agent-container`,n.setAttribute(`data-dpp-agent`,`true`),n.setAttribute(`data-console-phase`,`starting`);let r=document.createElement(`div`);r.className=`dpp-agent-status-line`;let i=document.createElement(`span`);i.className=`dpp-agent-status-dot`,i.setAttribute(`aria-hidden`,`true`);let a=document.createElement(`span`);if(a.className=`dpp-agent-status-text`,a.setAttribute(`role`,`status`),a.setAttribute(`aria-live`,`polite`),a.textContent=t?.starting??`Starting\\u2026`,r.appendChild(i),r.appendChild(a),e){let n=document.createElement(`button`);n.type=`button`,n.className=`dpp-agent-stop-btn`,n.textContent=t?.stop??`Stop`,n.addEventListener(`click`,t=>{t.stopPropagation(),e()}),r.appendChild(n)}let o=document.createElement(`div`);return o.className=`dpp-agent-stream`,n.appendChild(r),n.appendChild(o),n}function ZB(e){return e.querySelector(`.dpp-agent-stream`)}function QB(e,t,n){e.setAttribute(`data-console-phase`,t.phase);let r=e.querySelector(`.dpp-agent-status-text`);r&&(r.textContent=$B(t,n));let i=e.querySelector(`.dpp-agent-stop-btn`);i&&(i.hidden=t.phase!==`starting`&&t.phase!==`running`)}function $B(e,t){if(e.labelOverride)return e.labelOverride;switch(e.phase){case`starting`:return t?.starting??`Starting\\u2026`;case`running`:return t?.running?.(e.stepNumber,e.toolCount,e.elapsedSeconds)??`Running \\u00b7 step ${e.stepNumber+1} \\u00b7 ${e.toolCount} tool calls \\u00b7 ${e.elapsedSeconds}s`;case`complete`:return t?.consoleComplete?.(e.totalSteps,e.totalTools,e.elapsedSeconds)??`Complete \\u00b7 ${e.totalSteps} steps \\u00b7 ${e.totalTools} tool calls \\u00b7 ${e.elapsedSeconds}s`;case`paused`:return t?.consolePaused?.(e.totalSteps,e.totalTools,e.elapsedSeconds)??`Paused \\u00b7 ${e.totalSteps} steps \\u00b7 ${e.totalTools} tool calls \\u00b7 ${e.elapsedSeconds}s`;case`error`:return t?.consoleError?.(e.totalSteps,e.totalTools,e.elapsedSeconds)??`Error \\u00b7 ${e.totalSteps} steps \\u00b7 ${e.totalTools} tool calls \\u00b7 ${e.elapsedSeconds}s`}}"
    new_ui = r'''var DPP_AGENT_STATUS_331010={maxSteps:0,activity:`starting`,toolName:``,lastActivityAt:0};function DPP_AGENT_STATUS_COPY_331010(){let e=String(nX??``).toLowerCase().startsWith(`zh`);return e?{badge:{starting:`准备中`,running:`运行中`,complete:`已完成`,paused:`已暂停`,error:`失败 · 未完成`},starting:`正在建立 ShunCode 会话并准备工具`,running:(e,t,n,r)=>`第 ${e} 轮 · 工具 ${t} 已完成 / ${n} 运行中 · ${r}s`,activity:{starting:`准备 ShunCode 会话`,waiting:`等待 DeepSeek 返回下一步`,thinking:`DeepSeek 正在思考`,responding:`正在生成并解析回复`,tool:`正在执行工具`,continuing:`本轮完成，正在决定下一步`},dynamic:`未运行步骤：由模型根据工具结果动态规划`,budget:e=>`自动续跑安全额度剩余 ${e} 轮（不是任务剩余量）`,idle:e=>`已等待响应 ${e}s`,complete:`运行已结束 · 未运行步骤：0`,paused:`运行已暂停 · 仍有工作未执行；发送“继续”可恢复`,error:`运行已停止 · 任务未完成，请展开错误后重试`,toolRunning:`运行中`,toolInterrupted:`已中断`}:{badge:{starting:`Preparing`,running:`Running`,complete:`Complete`,paused:`Paused`,error:`Failed · incomplete`},starting:`Preparing the ShunCode session and tools`,running:(e,t,n,r)=>`Round ${e} · tools ${t} done / ${n} running · ${r}s`,activity:{starting:`Preparing the ShunCode session`,waiting:`Waiting for DeepSeek's next response`,thinking:`DeepSeek is thinking`,responding:`Generating and parsing the response`,tool:`Running tool`,continuing:`Round complete; deciding the next action`},dynamic:`Unscheduled steps are planned dynamically from tool results`,budget:e=>`${e} automatic safety rounds remain (not an estimate of task work)`,idle:e=>`Waiting ${e}s for activity`,complete:`Run ended · no unexecuted steps`,paused:`Run paused · work remains; send "continue" to resume`,error:`Run stopped · task incomplete; expand the error and retry`,toolRunning:`Running`,toolInterrupted:`Interrupted`}}function DPP_AGENT_STATUS_RESET_331010(e){DPP_AGENT_STATUS_331010={maxSteps:Hz(e).maxSteps,activity:`starting`,toolName:``,lastActivityAt:Date.now()}}function DPP_AGENT_STATUS_TOUCH_331010(e,t=``){DPP_AGENT_STATUS_331010.activity=e,DPP_AGENT_STATUS_331010.toolName=t,DPP_AGENT_STATUS_331010.lastActivityAt=Date.now()}function DPP_AGENT_STATUS_COUNTS_331010(e){let t={done:0,pending:0,failed:0,interrupted:0};for(let n of e.querySelectorAll(`.dpp-agent-tool-item[data-tool-status]`)){let e=n.getAttribute(`data-tool-status`);e===`pending`?t.pending+=1:e===`ok`?t.done+=1:e===`err`?(t.done+=1,t.failed+=1):e===`interrupted`&&(t.interrupted+=1)}return t}function DPP_AGENT_STATUS_FIELDS_331010(e,t){let n=DPP_AGENT_STATUS_COUNTS_331010(e),r=Math.max(0,Math.floor(Number(t??0))+1),i=Math.max(0,DPP_AGENT_STATUS_331010.maxSteps-r),a=DPP_AGENT_STATUS_331010.lastActivityAt?Math.max(0,Math.floor((Date.now()-DPP_AGENT_STATUS_331010.lastActivityAt)/1e3)):0;return{completedTools:n.done,pendingTools:n.pending,failedTools:n.failed,interruptedTools:n.interrupted,budgetRemaining:i,activity:DPP_AGENT_STATUS_331010.activity,activityTool:DPP_AGENT_STATUS_331010.toolName,lastActivitySeconds:a}}function DPP_AGENT_STATUS_DETAIL_331010(e){let t=DPP_AGENT_STATUS_COPY_331010();if(e.phase===`complete`)return t.complete;if(e.phase===`paused`)return t.paused;if(e.phase===`error`)return t.error;if(e.phase===`starting`)return`${t.activity.starting} · ${t.dynamic}`;let n=t.activity[e.activity]??t.activity.waiting;e.activity===`tool`&&e.activityTool&&(n+=`: ${e.activityTool}`),e.lastActivitySeconds>=15&&(n+=` · ${t.idle(e.lastActivitySeconds)}`);return`${n} · ${t.budget(e.budgetRemaining??0)} · ${t.dynamic}`}function DPP_EMPTY_FINAL_ERROR_331010(e){return String(e??``).toLowerCase().startsWith(`zh`)?`DeepSeek Agent 未返回最终文本或新的工具活动，已停止并标记为未完成。请重试或发送“继续”。`:`DeepSeek Agent returned neither final text nor new tool activity. The run was stopped and marked incomplete; retry or send "continue".`}function XB(e,t){let n=document.createElement(`div`);n.className=`dpp-agent-container`,n.setAttribute(`data-dpp-agent`,`true`),n.setAttribute(`data-console-phase`,`starting`),n.setAttribute(`aria-busy`,`true`);let r=document.createElement(`div`);r.className=`dpp-agent-status-line`;let i=document.createElement(`span`);i.className=`dpp-agent-status-dot`,i.setAttribute(`aria-hidden`,`true`);let a=document.createElement(`span`);a.className=`dpp-agent-status-badge`;let o=document.createElement(`span`);if(o.className=`dpp-agent-status-text`,o.setAttribute(`role`,`status`),o.setAttribute(`aria-live`,`polite`),o.textContent=t?.starting??`Starting…`,r.appendChild(i),r.appendChild(a),r.appendChild(o),e){let n=document.createElement(`button`);n.type=`button`,n.className=`dpp-agent-stop-btn`,n.textContent=t?.stop??`Stop`,n.addEventListener(`click`,t=>{t.stopPropagation(),e()}),r.appendChild(n)}let s=document.createElement(`div`);s.className=`dpp-agent-status-detail`;let c=document.createElement(`div`);c.className=`dpp-agent-progress-track`,c.setAttribute(`aria-hidden`,`true`);let l=document.createElement(`span`);l.className=`dpp-agent-progress-bar`,c.appendChild(l);let u=document.createElement(`div`);return u.className=`dpp-agent-stream`,n.appendChild(r),n.appendChild(s),n.appendChild(c),n.appendChild(u),QB(n,{phase:`starting`,stepNumber:0,toolCount:0,totalSteps:0,totalTools:0,elapsedSeconds:0},t),n}function ZB(e){return e.querySelector(`.dpp-agent-stream`)}function QB(e,t,n){let r=t.phase===`running`?{...t,...DPP_AGENT_STATUS_FIELDS_331010(e,t.stepNumber)}:t;e.setAttribute(`data-console-phase`,r.phase),e.setAttribute(`aria-busy`,r.phase===`starting`||r.phase===`running`?`true`:`false`);let i=DPP_AGENT_STATUS_COPY_331010(),a=e.querySelector(`.dpp-agent-status-badge`);a&&(a.textContent=i.badge[r.phase]??r.phase);let o=e.querySelector(`.dpp-agent-status-text`);o&&(o.textContent=$B(r,n));let s=e.querySelector(`.dpp-agent-status-detail`);s&&(s.textContent=DPP_AGENT_STATUS_DETAIL_331010(r),s.title=i.dynamic);let c=e.querySelector(`.dpp-agent-stop-btn`);c&&(c.hidden=r.phase!==`starting`&&r.phase!==`running`)}function $B(e,t){if(e.labelOverride)return e.labelOverride;let n=DPP_AGENT_STATUS_COPY_331010();switch(e.phase){case`starting`:return n.starting;case`running`:return n.running(e.stepNumber+1,e.completedTools??0,e.pendingTools??0,e.elapsedSeconds);case`complete`:return t?.consoleComplete?.(e.totalSteps,e.totalTools,e.elapsedSeconds)??`Complete · ${e.totalSteps} steps · ${e.totalTools} tool calls · ${e.elapsedSeconds}s`;case`paused`:return t?.consolePaused?.(e.totalSteps,e.totalTools,e.elapsedSeconds)??`Paused · ${e.totalSteps} steps · ${e.totalTools} tool calls · ${e.elapsedSeconds}s`;case`error`:return t?.consoleError?.(e.totalSteps,e.totalTools,e.elapsedSeconds)??`Error · ${e.totalSteps} steps · ${e.totalTools} tool calls · ${e.elapsedSeconds}s`}}'''
    content = replace_one(content, old_ui, new_ui, "agent status UI")

    old_nx = "codeRunFailed:$(`content.agent.codeRunFailed`)}}"
    new_nx = "codeRunFailed:$(`content.agent.codeRunFailed`),toolRunning:DPP_AGENT_STATUS_COPY_331010().toolRunning,toolInterrupted:DPP_AGENT_STATUS_COPY_331010().toolInterrupted}}"
    content = replace_one(content, old_nx, new_nx, "agent tool status copy")

    old_rows = "function PV(e,t,n,r){let i=MV(n.name,fB(n.payload),`pending`,r);jV(NV(e,t,i),r);let a=qB(e),o=a.pendingRowsByStep.get(t)??[];return o.push(i),a.pendingRowsByStep.set(t,o),i}function FV(e,t,n,r){let i=(qB(e).pendingRowsByStep.get(t)??[]).shift();if(i&&i.parentElement){LV(i,n,r);return}let a=n.result.summary.trim(),o=MV(n.name,a||null,n.result.ok?`ok`:`err`,r);jV(NV(e,t,o),r),LV(o,n,r)}function IV(e){let t=KB.get(e);if(t){for(let e of t.pendingRowsByStep.values())for(let t of e)t.getAttribute(`data-tool-status`)===`pending`&&t.setAttribute(`data-tool-status`,`interrupted`);t.pendingRowsByStep.clear()}}"
    new_rows = "function PV(e,t,n,r){let i=MV(n.name,fB(n.payload),`pending`,r);n.id&&i.setAttribute(`data-tool-call-id`,n.id),jV(NV(e,t,i),r);let a=qB(e),o=a.pendingRowsByStep.get(t)??[];return o.push(i),a.pendingRowsByStep.set(t,o),i}function DPP_AGENT_PENDING_ROW_331010(e,t,n){let r=qB(e),i=r.pendingRowsByStep.get(t)??[],a=n?.callId?i.findIndex(e=>e.getAttribute(`data-tool-call-id`)===n.callId):i.length>0?0:-1;if(a<0)return null;let[o]=i.splice(a,1);return i.length?r.pendingRowsByStep.set(t,i):r.pendingRowsByStep.delete(t),o??null}function DPP_AGENT_RENDERED_ROW_331010(e,t){if(!t)return null;for(let n of e.querySelectorAll(`.dpp-agent-tool-item[data-tool-call-id]`))if(n.getAttribute(`data-tool-call-id`)===t)return n;return null}function FV(e,t,n,r){let i=DPP_AGENT_RENDERED_ROW_331010(e,n.callId);if(i&&i.getAttribute(`data-tool-status`)!==`pending`)return;let a=DPP_AGENT_PENDING_ROW_331010(e,t,n);if(a&&a.parentElement){LV(a,n,r);return}if(i){LV(i,n,r);return}let o=n.result.summary.trim(),s=MV(n.name,o||null,n.result.ok?`ok`:`err`,r);n.callId&&s.setAttribute(`data-tool-call-id`,n.callId),jV(NV(e,t,s),r),LV(s,n,r)}function IV(e){let t=KB.get(e);if(t){for(let e of t.pendingRowsByStep.values())for(let t of e)if(t.getAttribute(`data-tool-status`)===`pending`){t.setAttribute(`data-tool-status`,`interrupted`);let e=t.querySelector(`.dpp-agent-tool-state`);e&&(e.textContent=NX().toolInterrupted)}t.pendingRowsByStep.clear()}}"
    content = replace_one(content, old_rows, new_rows, "live tool row settlement")

    old_pending_text = "u.textContent=n===`pending`?``:n===`ok`?r?.toolOk??`OK`:r?.toolError??`Error`;"
    new_pending_text = "u.textContent=n===`pending`?r?.toolRunning??`Running`:n===`ok`?r?.toolOk??`OK`:n===`interrupted`?r?.toolInterrupted??`Interrupted`:r?.toolError??`Error`;"
    content = replace_one(content, old_pending_text, new_pending_text, "pending tool label")

    old_tool_end = "DPPToolMeta.delete(e.toolCallId),_.push(Vz({toolName:t?.name??e.toolName,provider:ge(e.toolName),message:i},r?.args));break}"
    new_tool_end = "DPPToolMeta.delete(e.toolCallId);let DPPExecution={callId:e.toolCallId,...Vz({toolName:t?.name??e.toolName,provider:ge(e.toolName),message:i},r?.args)};_.push(DPPExecution),n(`AGENT_TOOL_COMPLETE`,{loopId:a,stepIndex:b,execution:DPPExecution});break}"
    content = replace_one(content, old_tool_end, new_tool_end, "tool completion event")

    old_dispatch = "case`AGENT_TOOL_DETECTED`:c1(t);break;case`AGENT_STEP_COMPLETE`:h1(t),Q4();break;"
    new_dispatch = "case`AGENT_TOOL_DETECTED`:c1(t);break;case`AGENT_TOOL_COMPLETE`:DPP_AGENT_TOOL_COMPLETE_331010(t);break;case`AGENT_STEP_COMPLETE`:h1(t),Q4();break;"
    content = replace_one(content, old_dispatch, new_dispatch, "tool completion dispatch")

    content = replace_one(
        content,
        "sX=n,cX=e.toolExecutions.length;let r=`agent:${e.loopId}`",
        "sX=n,cX=e.toolExecutions.length,DPP_AGENT_STATUS_RESET_331010(e.originalPrompt);let r=`agent:${e.loopId}`",
        "agent status reset",
    )

    old_handlers = "function s1(e){e.loopId!==LY||!Q||(o1(),WY.delete(e.stepIndex),IY=tV(e.stepIndex),QB(Q,{phase:`running`,stepNumber:e.stepIndex,toolCount:cX,totalSteps:0,totalTools:0,elapsedSeconds:IX()},NX()),C0(t=>w0(t,{index:e.stepIndex,status:`streaming`,text:``,toolExecutions:[],responseMessageId:null,collapsed:!1}),{persist:!1}))}function c1(e){if(e.loopId!==LY||!Q)return;let t=ZB(Q);t&&IY&&PV(t,e.stepIndex,e.call,NX()),cX+=1,C0(t=>T0(t,e.stepIndex,{status:`executing_tools`}),{persist:!1})}function l1(e){e.loopId!==LY||!IY||(UY=e,HY===null&&(HY=requestAnimationFrame(()=>{HY=null;let e=UY;UY=null,e&&d1(e)})))}"
    new_handlers = "function s1(e){e.loopId!==LY||!Q||(o1(),DPP_AGENT_STATUS_TOUCH_331010(`waiting`),WY.delete(e.stepIndex),IY=tV(e.stepIndex),QB(Q,{phase:`running`,stepNumber:e.stepIndex,toolCount:cX,totalSteps:0,totalTools:0,elapsedSeconds:IX()},NX()),C0(t=>w0(t,{index:e.stepIndex,status:`streaming`,text:``,toolExecutions:[],responseMessageId:null,collapsed:!1}),{persist:!1}))}function c1(e){if(e.loopId!==LY||!Q)return;let t=ZB(Q);t&&IY&&PV(t,e.stepIndex,e.call,NX()),DPP_AGENT_STATUS_TOUCH_331010(`tool`,`${e.call?.provider?.displayName?`${e.call.provider.displayName} / `:``}${e.call?.name??``}`),cX+=1,LX(),C0(t=>T0(t,e.stepIndex,{status:`executing_tools`}),{persist:!1})}function DPP_AGENT_TOOL_COMPLETE_331010(e){if(e.loopId!==LY||!Q)return;let t=ZB(Q);t&&FV(t,e.stepIndex,e.execution,NX()),DPP_AGENT_STATUS_TOUCH_331010(`continuing`),LX()}function l1(e){e.loopId!==LY||!IY||(DPP_AGENT_STATUS_TOUCH_331010(`responding`),UY=e,HY===null&&(HY=requestAnimationFrame(()=>{HY=null;let e=UY;UY=null,e&&d1(e)})))}"
    content = replace_one(content, old_handlers, new_handlers, "agent activity handlers")

    old_reasoning = "function u1(e){e.loopId!==LY||!Q||!e.fullText||(DPP_REASONING_PENDING_336=e,"
    new_reasoning = "function u1(e){e.loopId!==LY||!Q||!e.fullText||(DPP_AGENT_STATUS_TOUCH_331010(`thinking`),DPP_REASONING_PENDING_336=e,"
    content = replace_one(content, old_reasoning, new_reasoning, "reasoning activity")

    old_step_complete = "r?{immediate:!0}:{persist:!1}),IY=null}async function g1(e,t)"
    new_step_complete = "r?{immediate:!0}:{persist:!1}),DPP_AGENT_STATUS_TOUCH_331010(`continuing`),IY=null,LX()}async function g1(e,t)"
    content = replace_one(content, old_step_complete, new_step_complete, "step completion activity")

    old_empty_terminal = "if(oe){n(`AGENT_LOOP_ERROR`,{loopId:a,stepIndex:b,totalTools:g.length,error:se});return}ae===null&&ie===null&&g.length>0&&b>=Ce.maxSteps&&(ae=$z(d,b)),x||me();let e=``;"
    new_empty_terminal = "if(oe){n(`AGENT_LOOP_ERROR`,{loopId:a,stepIndex:b,totalTools:g.length,error:se});return}ae===null&&ie===null&&g.length>0&&b>=Ce.maxSteps&&(ae=$z(d,b));if(ae===null&&ie===null){n(`AGENT_LOOP_ERROR`,{loopId:a,stepIndex:b,totalTools:g.length,error:DPP_EMPTY_FINAL_ERROR_331010(d)});return}x||me();let e=``;"
    content = replace_one(content, old_empty_terminal, new_empty_terminal, "empty final result fail-closed")

    manifest["version"] = NEW_MANIFEST_VERSION
    manifest["version_name"] = NEW_VERSION

    outputs: dict[str, bytes] = {
        "content-scripts/content.js": content.encode("utf-8"),
        "manifest.json": (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8"),
    }
    for rel in ("_locales/en/messages.json", "_locales/zh_CN/messages.json"):
        text = paths[rel].read_text(encoding="utf-8-sig")
        outputs[rel] = text.replace(OLD_VERSION.split("ShunCode MCP ", 1)[1], NEW_VERSION.split("ShunCode MCP ", 1)[1]).replace("\n", "\r\n").encode("utf-8")

    staged: list[tuple[Path, Path]] = []
    try:
        for rel, data in outputs.items():
            staged.append((stage_write(paths[rel], data), paths[rel]))
        for tmp, path in staged:
            os.replace(tmp, path)
    finally:
        for tmp, _ in staged:
            if tmp.exists():
                tmp.unlink()

    print("APPLY_FIX331010_OK")
    for rel in outputs:
        print(f"{rel} {sha256(paths[rel].read_bytes())}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply-fix331010.py <extension-root>")
    main(sys.argv[1])
