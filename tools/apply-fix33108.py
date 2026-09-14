from pathlib import Path
import hashlib
import json
import sys


root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
targets = [
    "content-scripts/content.js",
    "manifest.json",
    "_locales/en/messages.json",
    "_locales/zh_CN/messages.json",
]
expected = {
    "content-scripts/content.js": "7A2DB7A62D041CD9C31433C9F4D419E7FBE95AEF12B37C78FE375EC8AF73A7CF",
    "manifest.json": "BEBFA1F53942AFE394BE3861A84754A0CAE9E2344BB7E1596D4C8C757A749AA5",
    "_locales/en/messages.json": "541076A6B7B717DA0507AF6A90F1865FF510809D4249044D6CEF9BDBEB271CCB",
    "_locales/zh_CN/messages.json": "93D7F7C3DC28429FE8AAB33BDCDE9594647496E4B35702E1304AB4EAD70963C2",
}
output_expected = {
    "content-scripts/content.js": "594159BFC2CE13022AC3FB4A403CAAB2EDE30604EAAB247E39F088F1B7D66108",
    "manifest.json": "AB59E8B689931CB904DD604B733FD863A561927102D9D2171D3346E150BD7C1A",
    "_locales/en/messages.json": "302F18B58FEE84D852B4F819984B3C722023FA05CD824720DC98EFB3AA9B9D04",
    "_locales/zh_CN/messages.json": "2CCB2C18BAD04C2CBDF0235171C6053A2447D2A3A098D25775ACEDABD0B29D05",
}
old_result_pattern = r"r=/status:\s*failed\b/i.test(n),i=/exit_code:\s*(-?\d+)\b/i.exec(n)"
new_result_pattern = r'''r=/["']?status["']?\s*[:=]\s*["']?failed\b/i.test(n),i=/["']?exit[_-]?code["']?\s*[:=]\s*["']?(-?\d+)\b/i.exec(n)'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


manifest_path = root / "manifest.json"
try:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
except Exception as exc:
    raise SystemExit(f"APPLY_FIX33108_FAIL: manifest unreadable: {exc}")

content_path = root / "content-scripts/content.js"
if (
    manifest.get("version") == "1.14.0.13"
    and manifest.get("version_name") == "1.14.0 ShunCode MCP Fix 3.3.10.8"
    and content_path.exists()
    and "DPP_AGENT_IDLE_WATCHDOG_33108" in content_path.read_text(encoding="utf-8-sig")
):
    current = content_path.read_text(encoding="utf-8-sig")
    refined = False
    if old_result_pattern in current:
        current = current.replace(old_result_pattern, new_result_pattern, 1)
        refined = True
    stale_restore = "e.status===`running`&&JX(O0(t))"
    durable_restore = "e.status===`running`&&await O0(t)"
    if stale_restore in current:
        current = current.replace(stale_restore, durable_restore, 1)
        refined = True
    if refined:
        content_path.write_text(current, encoding="utf-8", newline="")
        print("APPLY_FIX33108_REFINED")
        raise SystemExit(0)
    for relative, wanted in output_expected.items():
        actual = sha(root / relative)
        if actual != wanted:
            raise SystemExit(
                f"APPLY_FIX33108_FAIL: installed output mismatch {relative} "
                f"expected={wanted} got={actual}"
            )
    print("APPLY_FIX33108_ALREADY_APPLIED")
    raise SystemExit(0)

for relative in targets:
    path = root / relative
    if not path.is_file():
        raise SystemExit(f"APPLY_FIX33108_FAIL: missing {relative}")
    actual = sha(path)
    if actual != expected[relative]:
        raise SystemExit(
            f"APPLY_FIX33108_FAIL: hash mismatch {relative} "
            f"expected={expected[relative]} got={actual}"
        )

s = content_path.read_text(encoding="utf-8-sig")


def replace_once(old: str, new: str, label: str) -> None:
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"APPLY_FIX33108_FAIL: {label} anchor count={count}")
    s = s.replace(old, new, 1)


replace_once(
    "function DPP_PTY_EMPTY_33(e){",
    "function DPP_RUN_COMMAND_TEXT_33108(e){try{return[e?.summary??``,typeof e?.detail===`string`?e.detail:JSON.stringify(e?.detail??``),JSON.stringify(e?.output??``)].join(`\\n`)}catch{return`${e?.summary??``}\\n${e?.detail??``}`}}function DPP_NORMALIZE_RUN_COMMAND_RESULT_33108(e,t){if(DPP_TOOL_NAME_33(e)!==`run_command`||t?.ok!==!0)return t;let n=DPP_RUN_COMMAND_TEXT_33108(t),r=/status:\\s*failed\\b/i.test(n),i=/exit_code:\\s*(-?\\d+)\\b/i.exec(n),a=i?Number(i[1]):null;if(!r&&(a===null||a===0))return t;let o=a===null?`ShunCode command reported status=failed.`:`ShunCode command exited with code ${a}.`;return{...t,ok:!1,summary:`Command failed`,error:{code:`run_command_failed`,message:o,retryable:!1,details:{externalOutcome:`confirmed`,...a===null?{}:{exitCode:a}}}}}function DPP_DESCRIPTOR_PROPERTY_33108(e,t){return!!e?.inputSchema?.properties&&Object.prototype.hasOwnProperty.call(e.inputSchema.properties,t)}function DPP_PTY_EMPTY_33(e){",
    "run_command result helpers",
)
if s.count(old_result_pattern) != 1:
    raise SystemExit(
        f"APPLY_FIX33108_FAIL: command result pattern count={s.count(old_result_pattern)}"
    )
s = s.replace(old_result_pattern, new_result_pattern, 1)

replace_once(
    "if(DPP_SHOULD_DIRECT_RETRY_33(e.invocationName,c,f?.result)){let i={...c,execution:`direct`}",
    "if(DPP_DESCRIPTOR_PROPERTY_33108(e,`execution`)&&DPP_SHOULD_DIRECT_RETRY_33(e.invocationName,c,f?.result)){let i={...c,execution:`direct`}",
    "schema-aware direct retry",
)

replace_once(
    "let a=await o2(i,r),o=s2(a);",
    "let a=await o2(i,r),o=DPP_NORMALIZE_RUN_COMMAND_RESULT_33108(i,s2(a));",
    "primary result normalization",
)

retry_old = "let e=s2(await o2(i,r));if(e)return e"
retry_new = "let e=DPP_NORMALIZE_RUN_COMMAND_RESULT_33108(i,s2(await o2(i,r)));if(e)return e"
if s.count(retry_old) != 2:
    raise SystemExit(
        f"APPLY_FIX33108_FAIL: retry result normalization anchor count={s.count(retry_old)}"
    )
s = s.replace(retry_old, retry_new)

replace_once(
    "`[Fix 3.3 stdout] For non-interactive read/check commands where stdout is needed, prefer run_command execution=direct; do not retry mutating commands merely because PTY stdout is empty.`",
    "`[Fix 3.3.10.8 shell contract] ShunCode run_command executes native Bash. Send Bash source and /c/... drive paths. Never add an execution field unless that field exists in the current run_command tool schema. Invoke powershell.exe explicitly only for Windows-only facilities. Never replay a command merely because PTY stdout is empty.`",
    "current Bash tool contract",
)

replace_once(
    "async function M0(e,t){let n=g0(),r=await k0();if(!XX(e,t))return;let i=!1;for(let e of r)!P0(e,n)||KY.has(e.id)||(KY.set(e.id,N0(e)),qY.add(e.id),i=!0);i&&U2()}",
    "async function M0(e,t){let n=g0(),r=await k0();if(!XX(e,t))return;let i=!1;for(let e of r)if(P0(e,n)&&!KY.has(e.id)){let t=N0(e);KY.set(t.id,t),e.status===`running`&&await O0(t),qY.add(t.id),i=!0}i&&U2()}",
    "persist restored terminal state",
)

replace_once(
    "function Y$(e){let t=i1(e).catch(e=>{console.error(`[DeepSeek++] inline agent loop failed`,e)});",
    "var DPP_AGENT_IDLE_TIMEOUT_33108=NR+15e3;function DPP_AGENT_ERROR_TEXT_33108(e,t){return e instanceof Error&&e.message?e.message:typeof e==`string`&&e?e:t}function DPP_AGENT_FAIL_ACTIVE_33108(e,t){if(LY!==e||!BY)return!1;return b1({loopId:e,stepIndex:BY.totalSteps,totalTools:BY.totalTools,error:t}),!0}function DPP_AGENT_IDLE_WATCHDOG_33108(e,t,n=DPP_AGENT_IDLE_TIMEOUT_33108){let r=null,i=!1,a=()=>{r!==null&&(clearTimeout(r),r=null)},o=()=>{if(i||e?.aborted)return;a(),r=setTimeout(()=>{if(i||e?.aborted)return;i=!0,r=null,t()},n)};return o(),{kick:o,clear(){i=!0,a()}}}function Y$(e){let t=i1(e).catch(t=>{let n=DPP_AGENT_ERROR_TEXT_33108(t,`Inline agent loop failed.`);DPP_AGENT_FAIL_ACTIVE_33108(e.loopId,n),console.error(`[DeepSeek++] inline agent loop failed`,t)});",
    "agent lifecycle helpers",
)

replace_once(
    "function r1(){FX(),o1();let e=Q;if(C0(e=>({...e,status:`stopping`,error:$(`content.agent.stopped`)}),{immediate:!0}),p1(),WY.clear(),LY=null,Q=null,IY=null,BY=null,GY=null,RY?.disconnect(),RY=null,sX?.abort(),sX=null,e){let t=ZB(e);t&&IV(t),RX(e,`paused`,0,0,$(`content.agent.stopped`))}}async function i1(e){e.modelBackend||=await o()?`official-api`:`web`,sX&&(sX.abort(),n1());",
    "function r1(){FX(),o1();let e=Q;if(C0(e=>({...e,status:`stopping`,error:$(`content.agent.stopped`)}),{immediate:!0}),p1(),WY.clear(),LY=null,Q=null,IY=null,BY=null,GY=null,RY?.disconnect(),RY=null,sX?.abort(),sX=null,e){let t=ZB(e);t&&IV(t),RX(e,`paused`,0,0,$(`content.agent.stopped`))}}var DPP_AGENT_PAGEHIDE_BOUND_33108=!1;function DPP_BIND_AGENT_PAGEHIDE_33108(){DPP_AGENT_PAGEHIDE_BOUND_33108||(DPP_AGENT_PAGEHIDE_BOUND_33108=!0,window.addEventListener(`pagehide`,()=>{t1()&&r1()}))}DPP_BIND_AGENT_PAGEHIDE_33108();async function i1(e){e.modelBackend||=await o()?`official-api`:`web`,sX&&r1();",
    "pagehide and overlapping agent cleanup",
)

replace_once(
    "let s=[],c=(e,n)=>{let r=a1(e,n,GY??t);r&&s.push(r)},l=async t=>{let n=await i2(S1({...t,source:{trigger:`agent_run`,requestId:i,chatSessionId:e.chatSessionId,runId:e.loopId}}),a.id);return{name:n.name??t.name,result:{ok:n.ok,name:n.name,provider:n.provider,descriptorId:n.descriptorId,summary:n.summary,detail:n.detail,output:n.output,error:n.error,truncated:n.truncated},provider:n.provider??t.provider,descriptorId:n.descriptorId??t.descriptorId}},u=!1;try{await eB({...e,toolDescriptors:[...xt(a.descriptors,e.promptOptions.searchEnabled)]},{post:c,executeTool:l,signal:n.signal}),s.length>0&&(u=(await Promise.all(s)).some(Boolean))}finally{await MZ(r),sX===n&&(sX=null,GY=null)}u&&_1()}",
    "let s=[],d=null,c=(e,n)=>{d?.kick();let r=a1(e,n,GY??t);r&&s.push(r)},l=async t=>{let n=await i2(S1({...t,source:{trigger:`agent_run`,requestId:i,chatSessionId:e.chatSessionId,runId:e.loopId}}),a.id);return{name:n.name??t.name,result:{ok:n.ok,name:n.name,provider:n.provider,descriptorId:n.descriptorId,summary:n.summary,detail:n.detail,output:n.output,error:n.error,truncated:n.truncated},provider:n.provider??t.provider,descriptorId:n.descriptorId??t.descriptorId}},u=!1;d=DPP_AGENT_IDLE_WATCHDOG_33108(n.signal,()=>{let t=`Agent loop produced no activity for ${DPP_AGENT_IDLE_TIMEOUT_33108} ms.`;n.abort(new DOMException(t,`TimeoutError`)),DPP_AGENT_FAIL_ACTIVE_33108(e.loopId,t)});try{await eB({...e,toolDescriptors:[...xt(a.descriptors,e.promptOptions.searchEnabled)]},{post:c,executeTool:l,signal:n.signal}),s.length>0&&(u=(await Promise.all(s)).some(Boolean)),DPP_AGENT_FAIL_ACTIVE_33108(e.loopId,`Agent loop ended without a terminal event.`)}catch(t){if(!n.signal.aborted){let r=DPP_AGENT_ERROR_TEXT_33108(t,`Inline agent loop failed.`);DPP_AGENT_FAIL_ACTIVE_33108(e.loopId,r)||console.error(`[DeepSeek++] inline agent loop escaped after state cleanup`,t)}}finally{d.clear(),await MZ(r),sX===n&&(sX=null,GY=null)}u&&_1()}",
    "watchdog and terminal fallback wiring",
)

manifest["version"] = "1.14.0.13"
manifest["version_name"] = "1.14.0 ShunCode MCP Fix 3.3.10.8"

updates = {
    "content-scripts/content.js": s.encode("utf-8"),
    "manifest.json": (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).replace("\n", "\r\n").encode("utf-8"),
}

for relative in ["_locales/en/messages.json", "_locales/zh_CN/messages.json"]:
    data = json.loads((root / relative).read_text(encoding="utf-8-sig"))
    data["extension_name"]["message"] = "DeepSeek++ ShunCode MCP Fix 3.3.10.8"
    updates[relative] = (
        json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    ).replace("\n", "\r\n").encode("utf-8")

for relative, data in updates.items():
    actual = hashlib.sha256(data).hexdigest().upper()
    if actual != output_expected[relative]:
        raise SystemExit(
            f"APPLY_FIX33108_FAIL: generated output mismatch {relative} "
            f"expected={output_expected[relative]} got={actual}"
        )
    (root / relative).write_bytes(data)

print("APPLY_FIX33108_PASS")
