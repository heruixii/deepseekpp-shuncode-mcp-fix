from pathlib import Path
import hashlib, json, os, sys, tempfile

EXPECTED={
'hI':'e2039791f9fe4009d7da6244337722cee64a785311d073a2e6e0c066ed303742',
'CI':'08d392ae47f2cd6e65145618386d33418d6da8fcec1d92e0a5c30b55cb6b7b22',
'UI':'a70ae03210fd096c6512905572bc46df70eef6f6249855f10eb4481009c08ac4',
'HR':'1b5199f021e2a628dc039aa99b33c9316377f19dea7de32f830bc70fc7e34c5b',
'NzPz':'b4f6666ae68c8b6c637cf73077e2109c6fa20cedff5e843ce57cf1f4705e721c',
'ErrCap':'114bcfda47814c2b4d0ddba2baf0467fa13f08d84020a31f4c67d7d20b225317',
'IzLz':'a185ddc7b38a123b67448b27b20ad25164bfb7359c3218dc6d861668b6e9a861',
'Effect':'dd7def7817f699a24024130c707dfba2756ecdbdaf35b160595883ea172bdd32',
'Uz':'9f2243b8e0ca6a6a583b39461e30bbf2fb387d024fe3d1ca0aea0d07be107e4d',
'i2':'b344987fdd316bde3eccb8477d24cabb364f2a3f44412bb726b0f4126056eee1',
}
RANGES={
'hI':('function hI(){','function gI(){'),
'CI':('function CI(','function wI('),
'UI':('function UI(','function WI('),
'HR':('async function HR(','function UR('),
'NzPz':('function Nz(','function Fz('),
'ErrCap':('function DPP_ERROR_CLASS_3(','function DPP_CAPABILITY_WINDOW_32('),
'IzLz':('function Iz(','function Rz('),
'Effect':('function DPP_TOOL_EFFECT_31(','function DPP_COMPLETION_GATE_31('),
'Uz':('function Uz(','var Wz='),
'i2':('async function i2(','function a2('),
}

NEW={}
NEW['hI']="""function hI(){return{assistantText:``,assistantReasoningText:``,responseMessageId:null,requestMessageId:null,finished:!1,dppStreamEvents:[]}}"""
NEW['CI']="""function DPP_STREAM_DIAG_FRAME_33(e,t){let n={event:typeof t?.type==`string`?t.type:`message`};if(typeof e?.p==`string`&&(n.p=e.p.slice(0,96)),typeof e?.o==`string`&&(n.o=e.o.slice(0,32)),(e?.p===`response/status`||e?.p===`quasi_status`)&&(`string`==typeof e?.v||`number`==typeof e?.v||`boolean`==typeof e?.v)&&(n.v=String(e.v).slice(0,32)),Array.isArray(e?.v)){let t=e.v.slice(0,12).map(e=>{if(!e||typeof e!=`object`)return null;let t={};return typeof e.p==`string`&&(t.p=e.p.slice(0,96)),typeof e.o==`string`&&(t.o=e.o.slice(0,32)),(e.p===`response/status`||e.p===`quasi_status`)&&(`string`==typeof e.v||`number`==typeof e.v||`boolean`==typeof e.v)&&(t.v=String(e.v).slice(0,32)),Object.keys(t).length?t:null}).filter(Boolean);t.length&&(n.batch=t)}return n}function DPP_STREAM_DIAG_PUSH_33(e,t,n){if(!Array.isArray(e?.dppStreamEvents))return;let r=DPP_STREAM_DIAG_FRAME_33(t,n);e.dppStreamEvents.push(r),e.dppStreamEvents.length>8&&e.dppStreamEvents.splice(0,e.dppStreamEvents.length-8)}function CI(e,t,n,r,i){DPP_STREAM_DIAG_PUSH_33(n,e,t),ZI(e,n),r.onParsed?.(e,t);let a=RI(e,PI(n));a.text&&(i.push(a.text),r.retainAssistantText!==!1&&(n.assistantText+=a.text)),a.reasoning&&(n.assistantReasoningText+=a.reasoning,r.onReasoningChunk?.(a.reasoning,n.assistantReasoningText)),UI(e)&&(n.finished=!0)}"""
NEW['UI']="""function DPP_STREAM_FINISHED_33(e,t=0,n={count:0}){if(t>8||n.count>=128||!e||typeof e!=`object`)return!1;if(n.count+=1,!Array.isArray(e)){let t=e.p,r=e.v;if((t===`response/status`||t===`quasi_status`)&&typeof r==`string`&&r.toUpperCase()===`FINISHED`)return!0}if(Array.isArray(e)){for(let r of e)if(DPP_STREAM_FINISHED_33(r,t+1,n))return!0;return!1}for(let r of Object.values(e))if(r&&typeof r==`object`&&DPP_STREAM_FINISHED_33(r,t+1,n))return!0;return!1}function UI(e){return DPP_STREAM_FINISHED_33(e)}"""
NEW['HR']="""async function HR(e,t,n){let r=n??new AbortController().signal,i=!1;for(let n=1;n<=zR;n++){let a=IR(r);try{let o=await WL(e,{retainAssistantText:!1,onTextChunk(e,n){i=!0,t.onTextChunk(e,n)},onReasoningChunk(e,n){i=!0,t.onReasoningChunk?.(e,n)},onTokenSpeed:t.onTokenSpeed},a.signal),s=!o.finished&&!i&&o.responseMessageId==null&&o.requestMessageId==null&&n<zR;if(s){if(await LR(r),r.aborted)throw new DOMException(`DeepSeek request was aborted.`,`AbortError`);continue}return{assistantText:o.assistantText,responseMessageId:o.responseMessageId,requestMessageId:o.requestMessageId,finished:o.finished,streamEvents:Array.isArray(o.dppStreamEvents)?o.dppStreamEvents:[]}}catch(e){if(r.aborted)throw e;let t=a.timedOut();if(t&&i)throw Error(`DeepSeek agent step timed out while streaming; the response was interrupted.`);if(n>=zR)throw t?Error(`DeepSeek agent step timed out after retry.`):e;if(await LR(r),r.aborted)throw e}finally{a.clear()}}throw Error(`DeepSeek agent step failed without a completed attempt.`)}"""
NEW['NzPz']="""var DPP_AGENT_RULES_33=[`[Fix 3.3 UTF-8 safety] On Windows PowerShell 5.1, never read UTF-8 text that may lack a BOM with bare Get-Content -Raw before writing it back. Use Get-Content -Encoding UTF8 -Raw or [System.IO.File]::ReadAllText(path,[System.Text.Encoding]::UTF8).`,`[Fix 3.3 workspace] ShunCode read_files/find_files/search_files/list_directory are scoped to the current ShunCode workspace. If an explicit target is outside that workspace, use run_command with the absolute path instead of inventing a workspace-relative path.`,`[Fix 3.3 stdout] For non-interactive read/check commands where stdout is needed, prefer run_command execution=direct; do not retry mutating commands merely because PTY stdout is empty.`].join(`\\n`);function Nz(e,t,n=he){let r=t.some(e=>!e.result.ok),i=Fz(t);return[C(n,`prompt.inlineAgent.continuationIntro`),C(n,`prompt.inlineAgent.continuationEnough`),C(n,`prompt.inlineAgent.continuationNoPseudo`),C(n,`prompt.inlineAgent.nativeChartSyntax`),DPP_AGENT_RULES_33,``,`<original_task>`,zz(e,8e3),`</original_task>`,...r?[C(n,`prompt.inlineAgent.failureRecovery`)]:[],``,`<tool_results>`,JSON.stringify(i,null,2),`</tool_results>`].join(`\\n`)}function Pz(e,t,n,r,i=he){let a=Fz(n);return[C(i,`prompt.inlineAgent.nudgeNoTools`),C(i,`prompt.inlineAgent.nudgeChoice`),C(i,`prompt.inlineAgent.nudgeNextTool`),C(i,`prompt.inlineAgent.nudgeComplete`),C(i,`prompt.inlineAgent.nativeChartSyntax`),C(i,`prompt.inlineAgent.nudgeCount`,{count:r}),DPP_AGENT_RULES_33,``,`<original_task>`,zz(e,8e3),`</original_task>`,``,`<previous_assistant_text>`,zz(t,4e3),`</previous_assistant_text>`,``,`<tool_results_so_far>`,JSON.stringify(a,null,2),`</tool_results_so_far>`].join(`\\n`)}"""
NEW['ErrCap']="""function DPP_ERROR_CLASS_3(e){let t=String(e?.code??`unknown`);return t===`dpp_fix3_no_progress`?{stage:`loop_guard`,action:`change_tool_or_parameters`}:t===`dpp_tool_arguments_missing`?{stage:`format_or_schema`,action:`reemit_tool_call`}:t===`dpp_windows_text_encoding_unsafe`?{stage:`safety_guard`,action:`rewrite_command_with_explicit_utf8`}:/^mcp_capability_handle_(?:replayed|expired|invalid|descriptor_stale)/.test(t)?{stage:`mcp_capability`,action:`rediscover_capability`}:/^tool_call_/.test(t)?{stage:`format_or_schema`,action:`repair_parameters`}:/^tool_authorization|authorization/.test(t)?{stage:`authorization`,action:`refresh_authorization`}:/^mcp_(http|sse|connect|initialize|transport|response)/.test(t)?{stage:`mcp_transport`,action:e?.retryable===!0?`safe_retry_if_read_only`:`inspect_connection`}:/^mcp_tool|tool_unsupported/.test(t)?{stage:`mcp_tool`,action:`refresh_tool_catalog`}:{stage:`tool_runtime`,action:e?.retryable===!0?`retry_if_safe`:`inspect_error`}}"""
NEW['IzLz']="""function DPP_TOOL_NAME_33(e){let t=String(e??``).toLowerCase(),n=[`run_command`,`read_files`,`find_files`,`search_files`,`list_directory`,`apply_patch`,`get_command_output`,`get_diagnostics`,`lsp`];for(let e of n)if(t===e||t.endsWith(`_${e}`)||t.endsWith(`:${e}`)||t.endsWith(`.${e}`)||t.endsWith(`/${e}`))return e;return t.split(/[.:/]/).pop()??t}function DPP_RESULT_HINT_33(e){let t=String(e?.result?.error?.code??``).toUpperCase(),n=DPP_TOOL_NAME_33(e?.name);return t===`FILE_NOT_FOUND`&&/^(read_files|find_files|search_files|list_directory)$/.test(n)?{recoveryHint:`ShunCode file tools are workspace-scoped. If the intended file is outside the current ShunCode workspace, use run_command with its explicit absolute path instead of retrying a workspace-relative path.`}:{}}function Iz(e){let t=DPP_CAPABILITY_WINDOW_32(e),n=t===null?(e.result.output===void 0?void 0:JSON.stringify(e.result.output)):JSON.stringify(t),r=DPP_MODEL_RESULT_BUDGET_3(e.name);return{tool:e.name,provider:e.provider?.displayName,ok:e.result.ok,summary:e.result.summary,detail:zz(e.result.detail,3500),error:Rz(e.result.error),output:zz(n,r),...DPP_RESULT_HINT_33(e),...t?{capabilityCatalog:!0}:{},contextCompacted:typeof n==`string`&&n.length>r,truncated:e.result.truncated===!0}}function Lz(e){let t=DPP_CAPABILITY_WINDOW_32(e);return{tool:e.name,provider:e.provider?.displayName,ok:e.result.ok,summary:zz(e.result.summary,400),error:Rz(e.result.error),...DPP_RESULT_HINT_33(e),...t?{capabilityWindow:t}:{},windowed:!0,truncated:e.result.truncated===!0}}"""
NEW['Effect']="""function DPP_TOOL_EFFECT_31(e,t={}){let n=DPP_TOOL_BASE_31(e);if(/^(apply_patch|write|create|delete|remove|update|edit|patch|move|rename|install|upload|commit|push|merge|send|post|put)$/.test(n))return`mutation`;if(/^(read_files|read|find_files|find|search_files|search|grep|list_directory|list|get_diagnostics|lsp|status|health|check|stat|snapshot|inspect|preview|history)$/.test(n))return`verification`;if(/^(run_command|shell_exec|shell_session_exec|exec|run)$/.test(n)){let e=String(t?.command??t?.cmd??``).toLowerCase();if(/(?:set-content|add-content|out-file|writealltext|writealllines|writeallbytes|appendalltext|appendalllines|remove-item|move-item|copy-item|new-item|git\\s+(?:commit|push|merge|reset|checkout)|npm\\s+(?:install|i\\b)|pnpm\\s+(?:add|install)|yarn\\s+add|pip\\s+install|mkdir\\b|rmdir\\b|\\bdel\\b|\\berase\\b|\\brm\\b|\\bmv\\b|\\bcp\\b)/i.test(e))return`mutation`;if(/(?:get-content|test-path|getchilditem|get-childitem|get-child-item|select-string|git\\s+(?:status|diff|log)|pytest|\\btest\\b|npm\\s+test|pnpm\\s+test|yarn\\s+test|node\\s+--check|tsc\\b|eslint\\b|lint\\b|dotnet\\s+test|cargo\\s+test|go\\s+test|\\bdir\\b|\\bls\\b|\\bcat\\b|findstr)/i.test(e))return`verification`}return`neutral`}"""
NEW['Uz']="""function DPP_REQUIRED_ARGS_33(e,t){let n=Array.isArray(e?.inputSchema?.required)?e.inputSchema.required.filter(e=>typeof e==`string`):[],r=t&&typeof t==`object`&&!Array.isArray(t)?t:{};return n.filter(e=>!(e in r)||r[e]===void 0||typeof r[e]==`string`&&!r[e].trim())}function DPP_BLOCK_RESULT_33(e,t,n,r){return{content:[{type:`text`,text:n}],details:{ok:!1,summary:t,detail:n,error:{code:e,message:n,retryable:!1,details:{action:r}}}}}function DPP_WINDOWS_ENCODING_GUARD_33(e,t){if(DPP_TOOL_NAME_33(e)!==`run_command`)return null;let n=String(t?.command??t?.cmd??``);if(!n)return null;let r=[...n.matchAll(/\\bGet-Content\\b[^\\r\\n;|]*/gi)].some(e=>/-Raw\\b/i.test(e[0])&&!/-Encoding\\b/i.test(e[0])),i=/(?:WriteAllText|WriteAllLines|WriteAllBytes|AppendAllText|AppendAllLines|Set-Content|Add-Content|Out-File)\\b/i.test(n);return r&&i?`Blocked a Windows PowerShell 5.1 text round-trip that reads with bare Get-Content -Raw and writes text back. UTF-8 files without a BOM can be decoded using the legacy ANSI code page and permanently corrupted. Reissue the command using Get-Content -Encoding UTF8 -Raw or [System.IO.File]::ReadAllText(path,[System.Text.Encoding]::UTF8) before writing.`:null}function DPP_PTY_EMPTY_33(e){let t;try{t=[e?.summary??``,e?.detail??``,JSON.stringify(e?.output??``)].join(`\\n`)}catch{t=`${e?.summary??``}\\n${e?.detail??``}`}return /execution:\\s*pty/i.test(t)&&/status:\\s*completed/i.test(t)&&/exit_code:\\s*0/i.test(t)&&/total_output_bytes:\\s*0/i.test(t)}function DPP_SHOULD_DIRECT_RETRY_33(e,t,n){return DPP_TOOL_NAME_33(e)===`run_command`&&t?.background!==!0&&String(t?.execution??`pty`).toLowerCase()!==`direct`&&DPP_TOOL_EFFECT_31(`run_command`,t)===`verification`&&DPP_PTY_EMPTY_33(n)}function Uz(e,t,d){let{executeTool:n,callSource:r}=t;return{name:e.invocationName,label:e.title,description:e.description,parameters:e.inputSchema,prepareArguments:e=>e,execute:async(t,i,a,o)=>{let c=i??{},s=`${e.invocationName}:${DPP_STABLE_3(c)}`;d.count=d.last===s?d.count+1:1,d.last=s;if(d.count>=4){let t=`Fix3 blocked repeated identical tool call ${d.count}. Change the tool or parameters.`;return{content:[{type:`text`,text:t}],details:{ok:!1,summary:`Repeated tool loop blocked`,detail:t,error:{code:`dpp_fix3_no_progress`,message:t,retryable:!1}}}}let l=DPP_REQUIRED_ARGS_33(e,c);if(l.length){let t=`Tool call is missing required argument(s): ${l.join(`, `)}. Re-emit the same tool call with a complete structured argument object.${DPP_TOOL_NAME_33(e.invocationName)===`run_command`?` For run_command include at least command and background (true or false).`:``}`;return DPP_BLOCK_RESULT_33(`dpp_tool_arguments_missing`,`Tool arguments incomplete`,t,`reemit_tool_call`)}let u=DPP_WINDOWS_ENCODING_GUARD_33(e.invocationName,c);if(u)return DPP_BLOCK_RESULT_33(`dpp_windows_text_encoding_unsafe`,`Unsafe Windows text encoding round-trip blocked`,u,`rewrite_command_with_explicit_utf8`);let f=await n({id:t,name:e.name,invocationName:e.invocationName,payload:c,raw:``,source:{trigger:`agent_run`,requestId:r.requestId,chatSessionId:r.chatSessionId}});if(DPP_SHOULD_DIRECT_RETRY_33(e.invocationName,c,f?.result)){let i={...c,execution:`direct`},a=await n({id:`${t}:dpp33-direct`,name:e.name,invocationName:e.invocationName,payload:i,raw:``,source:{trigger:`agent_run`,requestId:r.requestId,chatSessionId:r.chatSessionId}});a?.result?.ok===!0&&(f=a)}return{content:[{type:`text`,text:f.result.summary??``}],details:f.result}}}}"""

NEW['i2']="""function DPP_COMMON_DESCRIPTOR_33(e){let t=e?.invocationName,n=e?.name,r=e?.descriptorId;return Array.isArray(iX)?iX.find(e=>t&&e?.invocationName===t||n&&e?.name===n||r&&e?.descriptorId===r):void 0}function DPP_COMMON_PREFLIGHT_RESULT_33(e,t,n,r){return{ok:!1,name:e?.name,provider:e?.provider,descriptorId:e?.descriptorId,summary:t,detail:n,error:{code:r.code,message:n,retryable:!1,details:{action:r.action}}}}function DPP_COMMON_PREFLIGHT_33(e){let t=e?.payload&&typeof e.payload==`object`&&!Array.isArray(e.payload)?e.payload:{},n=DPP_COMMON_DESCRIPTOR_33(e),r=n?DPP_REQUIRED_ARGS_33(n,t):[],i=DPP_TOOL_NAME_33(e?.invocationName??e?.name);if(!n&&i===`run_command`){typeof t.command==`string`&&t.command.trim()||r.push(`command`),typeof t.background==`boolean`||r.push(`background`)}if(r.length){r=[...new Set(r)];let t=`Tool call is missing required argument(s): ${r.join(`, `)}. Re-emit the same tool call with a complete structured argument object.${i===`run_command`?` For run_command include at least command and background (true or false).`:``}`;return DPP_COMMON_PREFLIGHT_RESULT_33(e,`Tool arguments incomplete`,t,{code:`dpp_tool_arguments_missing`,action:`reemit_tool_call`})}let a=DPP_WINDOWS_ENCODING_GUARD_33(e?.invocationName??e?.name,t);return a?DPP_COMMON_PREFLIGHT_RESULT_33(e,`Unsafe Windows text encoding round-trip blocked`,a,{code:`dpp_windows_text_encoding_unsafe`,action:`rewrite_command_with_explicit_utf8`}):null}async function i2(e,t){if(e.parseError)return await DPP_RECORD_PARSE_DIAG_1140(e),{ok:!1,summary:$(`tool.runtime.invalidFormat`),detail:e.parseError.message,error:e.parseError};let d=DPP_COMMON_PREFLIGHT_33(e);if(d)return d;let n=C1(e),r=t??n?.id,i=await gq(e,n?.chatSessionId,{readChatSessionId:EQ,signal:bX?.signal});if(!i)return a2(e);let a=await o2(i,r),o=s2(a);if(o){if(jr(i,o)){let e=i.payload?.url;if(typeof e==`string`&&await _2(e)){let e=s2(await o2(i,r));if(e)return e}}if(DPP_WEB_SAFE_RETRY_3(i,o)){await DPP_WEB_RETRY_DELAY_3();let e=s2(await o2(i,r));if(e)return e}return o}return hX?c2(i,a):{ok:!1,summary:$(`content.toolBlock.summaries.failed`),detail:$(`content.extensionReloaded`)}}"""

VR_OLD='if(!ie.finished&&!d?.aborted)throw Error(`DeepSeek response stream ended before completion (the response was interrupted).`);'
VR_NEW='if(!ie.finished&&!d?.aborted){let e=Array.isArray(ie.streamEvents)&&ie.streamEvents.length?` Last stream markers: ${JSON.stringify(ie.streamEvents).slice(0,1200)}`:``;throw Error(`DeepSeek response stream ended before completion (the response was interrupted).${e}`)}'

def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def get_range(s,a,b):
    if s.count(a)!=1 or s.count(b)<1: raise RuntimeError(f'marker count invalid {a!r} {s.count(a)} / {b!r} {s.count(b)}')
    i=s.find(a); j=s.find(b,i+len(a))
    if j<0: raise RuntimeError(f'end marker not found after {a}')
    return i,j,s[i:j]

def atomic_write(path,text):
    tmp=path.with_name(path.name+'.fix33.tmp')
    tmp.write_text(text,encoding='utf-8',newline='')
    os.replace(tmp,path)

def main(root):
    root=Path(root)
    content_path=root/'content-scripts'/'content.js'
    manifest_path=root/'manifest.json'
    en_path=root/'_locales'/'en'/'messages.json'
    zh_path=root/'_locales'/'zh_CN'/'messages.json'
    content=content_path.read_text(encoding='utf-8-sig')
    manifest=json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    en=json.loads(en_path.read_text(encoding='utf-8-sig'))
    zh=json.loads(zh_path.read_text(encoding='utf-8-sig'))
    if manifest.get('version_name')=='1.14.0 ShunCode MCP Fix 3.3' and 'DPP_STREAM_FINISHED_33' in content and 'DPP_WINDOWS_ENCODING_GUARD_33' in content:
        print('APPLY_FIX33_ALREADY_APPLIED')
        return 0
    if manifest.get('version_name')!='1.14.0 ShunCode MCP Fix 3.2':
        raise RuntimeError(f"expected Fix 3.2 manifest, got {manifest.get('version_name')!r}")
    if en.get('extension_name',{}).get('message')!='DeepSeek++ ShunCode MCP Fix 3.2': raise RuntimeError('EN extension_name is not Fix 3.2')
    if zh.get('extension_name',{}).get('message')!='DeepSeek++ ShunCode MCP Fix 3.2': raise RuntimeError('ZH extension_name is not Fix 3.2')
    validated={}
    for name,(a,b) in RANGES.items():
        i,j,old=get_range(content,a,b)
        got=sha(old)
        if got!=EXPECTED[name]: raise RuntimeError(f'{name} compatibility hash mismatch: {got} != {EXPECTED[name]}')
        validated[name]=(a,b,old)
    if content.count(VR_OLD)!=1: raise RuntimeError(f'VR incomplete-stream marker count is {content.count(VR_OLD)}, expected 1')
    # All compatibility checks have completed. Mutate only in memory from here.
    out=content
    for name,(a,b) in RANGES.items():
        i=out.find(a); j=out.find(b,i+len(a))
        if i<0 or j<0: raise RuntimeError(f'{name} marker disappeared during in-memory patch')
        out=out[:i]+NEW[name]+out[j:]
    out=out.replace(VR_OLD,VR_NEW,1)
    manifest['version_name']='1.14.0 ShunCode MCP Fix 3.3'
    en['extension_name']['message']='DeepSeek++ ShunCode MCP Fix 3.3'
    zh['extension_name']['message']='DeepSeek++ ShunCode MCP Fix 3.3'
    # Stage every file first, then replace targets.
    payloads=[
      (content_path,out),
      (manifest_path,json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'),
      (en_path,json.dumps(en,ensure_ascii=False,indent=2)+'\n'),
      (zh_path,json.dumps(zh,ensure_ascii=False,indent=2)+'\n'),
    ]
    staged=[]
    try:
        for path,text in payloads:
            tmp=path.with_name(path.name+'.fix33.tmp')
            tmp.write_text(text,encoding='utf-8',newline='')
            staged.append((tmp,path))
        for tmp,path in staged: os.replace(tmp,path)
    finally:
        for tmp,_ in staged:
            try: tmp.unlink()
            except FileNotFoundError: pass
    print('APPLY_FIX33_PASS')
    return 0

if __name__=='__main__':
    if len(sys.argv)!=2:
        print('usage: apply-fix33.py ROOT',file=sys.stderr); sys.exit(2)
    try: sys.exit(main(sys.argv[1]))
    except Exception as e:
        print(f'APPLY_FIX33_FAIL: {e}',file=sys.stderr); sys.exit(1)