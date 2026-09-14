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
    "content-scripts/content.js": "594159BFC2CE13022AC3FB4A403CAAB2EDE30604EAAB247E39F088F1B7D66108",
    "manifest.json": "AB59E8B689931CB904DD604B733FD863A561927102D9D2171D3346E150BD7C1A",
    "_locales/en/messages.json": "302F18B58FEE84D852B4F819984B3C722023FA05CD824720DC98EFB3AA9B9D04",
    "_locales/zh_CN/messages.json": "2CCB2C18BAD04C2CBDF0235171C6053A2447D2A3A098D25775ACEDABD0B29D05",
}
output_expected = {
    "content-scripts/content.js": "6A3F72E316265ED33A1CEA974E6048A79DBD7F124D135128F1934557827C5ECB",
    "manifest.json": "7CAE4EEC1486D6E8FDEEB9152A5AD954B082C25320661AA5CF867EA105451C79",
    "_locales/en/messages.json": "0C9166A9E59386011B19DD971AECC0EDE28ABF6F55E4CD1EFDA5A1B81416B6EF",
    "_locales/zh_CN/messages.json": "68C1CC5AD159851BBA7B807A7929613A409BABFBBD6553579B1DCB809BC49249",
}

legacy_claim_helpers = "function DPP_STAT_CLAIM_MISMATCH_33109(e,t){let n=t.map(DPP_VERIFIED_FACTS_33109).map(e=>e.verifiedFacts).filter(Boolean);if(!n.length)return null;let r=new Set;for(let e of n)for(let t of [`returnedEntries`,`directoryEntries`,`fileEntries`])Number.isInteger(e?.[t])&&r.add(e[t]);let i=[/(\\d+)\\s*(?:个|项|条)?\\s*(?:目录|文件|条目)/gi,/(?:目录|文件|条目|总计|合计|共计|返回(?:了)?)[^\\d\\n]{0,12}(\\d+)\\s*(?:个|项|条)?/gi,/\\b(\\d+)\\s+(?:directories|folders|files|entries|items)\\b/gi,/(?:total|returned)[^\\d\\n]{0,12}\\b(\\d+)\\b/gi,/(?:实际|一共|共)[^\\d\\n]{0,6}(\\d+)\\s*(?:个|项|条)(?:目录|文件|条目|工具)?/gi];for(let t of i)for(let n of e.matchAll(t)){if(/工具/.test(n[0]))continue;let e=n.slice(1).find(e=>/^\\d+$/.test(e??``)),t=Number(e);if(Number.isInteger(t)&&!r.has(t))return`A numeric directory/file/entry claim (${t}) conflicts with verifiedFacts. Rewrite the answer using only these verified totals: ${[...r].sort((e,t)=>e-t).join(`, `)}.`}return null}"
claim_helpers = "function DPP_STAT_CLAIM_MISMATCH_33109(e,t){let n=t.map(DPP_VERIFIED_FACTS_33109).map(e=>e.verifiedFacts).filter(Boolean);if(!n.length)return null;let r=new Set;for(let e of n)for(let t of [`returnedEntries`,`directoryEntries`,`fileEntries`])Number.isInteger(e?.[t])&&r.add(e[t]);let i=[/(\\d+)\\s*(?:个|项|条)?\\s*(?:目录|文件|条目)/gi,/(?:目录|文件|条目|返回(?:了)?)[^\\d\\n]{0,12}(\\d+)\\s*(?:个|项|条)?/gi,/\\b(\\d+)\\s+(?:directories|folders|files|entries|items)\\b/gi,/(?:total|returned)[^\\d\\n]{0,12}\\b(\\d+)\\s+(?:directories|folders|files|entries|items)\\b/gi,/(?:total|returned)\\s+(?:directories|folders|files|entries|items)[^\\d\\n]{0,12}\\b(\\d+)\\b/gi,/(?:实际|一共|共)[^\\d\\n]{0,6}(\\d+)\\s*(?:个|项|条)(?:目录|文件|条目|工具)?/gi];for(let t of i)for(let n of e.matchAll(t)){if(/工具/.test(n[0]))continue;let e=n.slice(1).find(e=>/^\\d+$/.test(e??``)),t=Number(e);if(Number.isInteger(t)&&!r.has(t))return`A numeric directory/file/entry claim (${t}) conflicts with verifiedFacts. Rewrite the answer using only these verified totals: ${[...r].sort((e,t)=>e-t).join(`, `)}.`}return null}"
claim_hook_old = "if(r)return!1;let i=Sz(n);"
claim_hook_new = "if(r)return!1;let h=DPP_STAT_CLAIM_MISMATCH_33109(n,g);if(h){if(y.completionReason=h,y.currentTurnIsNudge&&y.count>=Ce.maxNudges)return ae=DPP_NUDGE_LIMIT_31(d,y.count),!0;return!1}let i=Sz(n);"
cleanup_guard_old = "let t=P0(e,n),s=i instanceof Set&&i.has(e.id),c=e.status===`running`&&!s&&(t||i instanceof Set&&DPP_TRACE_EXPIRED_33109(e,o)),l=DPP_TRACE_NEEDS_REPAIR_33109(e)"
cleanup_guard_new = "let t=P0(e,n),s=i instanceof Set&&i.has(e.id),c=e.status===`running`&&i instanceof Set&&!s&&(t||DPP_TRACE_EXPIRED_33109(e,o)),l=DPP_TRACE_NEEDS_REPAIR_33109(e)"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


manifest_path = root / "manifest.json"
try:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
except Exception as exc:
    raise SystemExit(f"APPLY_FIX33109_FAIL: manifest unreadable: {exc}")

content_path = root / "content-scripts/content.js"
if (
    manifest.get("version") == "1.14.0.14"
    and manifest.get("version_name") == "1.14.0 ShunCode MCP Fix 3.3.10.9"
    and content_path.exists()
    and "DPP_ACTIVE_TRACE_IDS_33109" in content_path.read_text(encoding="utf-8-sig")
):
    current = content_path.read_text(encoding="utf-8-sig")
    refined = False
    if "function DPP_STAT_CLAIM_MISMATCH_33109" not in current:
        if current.count("function Iz(e){") != 1:
            raise SystemExit("APPLY_FIX33109_FAIL: claim helper refine anchor mismatch")
        if current.count(claim_hook_old) != 1:
            raise SystemExit("APPLY_FIX33109_FAIL: claim guard refine anchor mismatch")
        current = current.replace("function Iz(e){", claim_helpers + "function Iz(e){", 1)
        current = current.replace(claim_hook_old, claim_hook_new, 1)
        refined = True
    elif legacy_claim_helpers in current:
        current = current.replace(legacy_claim_helpers, claim_helpers, 1)
        refined = True
    if cleanup_guard_old in current:
        current = current.replace(cleanup_guard_old, cleanup_guard_new, 1)
        refined = True
    if refined:
        generated = {relative: (root / relative).read_bytes() for relative in targets}
        generated["content-scripts/content.js"] = current.encode("utf-8")
        mismatch = []
        for relative, data in generated.items():
            actual = hashlib.sha256(data).hexdigest().upper()
            if actual != output_expected[relative]:
                mismatch.append(f"{relative}={actual}")
        if mismatch:
            raise SystemExit("APPLY_FIX33109_GENERATED_HASHES: " + " ".join(mismatch))
        content_path.write_bytes(generated["content-scripts/content.js"])
        print("APPLY_FIX33109_REFINED")
        raise SystemExit(0)
    for relative, wanted in output_expected.items():
        actual = sha(root / relative)
        if actual != wanted:
            raise SystemExit(
                f"APPLY_FIX33109_FAIL: installed output mismatch {relative} "
                f"expected={wanted} got={actual}"
            )
    print("APPLY_FIX33109_ALREADY_APPLIED")
    raise SystemExit(0)

for relative in targets:
    path = root / relative
    if not path.is_file():
        raise SystemExit(f"APPLY_FIX33109_FAIL: missing {relative}")
    actual = sha(path)
    if actual != expected[relative]:
        raise SystemExit(
            f"APPLY_FIX33109_FAIL: hash mismatch {relative} "
            f"expected={expected[relative]} got={actual}"
        )

s = content_path.read_text(encoding="utf-8-sig")


def replace_once(old: str, new: str, label: str) -> None:
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"APPLY_FIX33109_FAIL: {label} anchor count={count}")
    s = s.replace(old, new, 1)


replace_once(
    "`,`[Fix 3.3.3 targeted discovery]",
    "`,`[Fix 3.3.10.9 verified statistics] Never invent, estimate, or mentally count numeric totals from verbose tool output. State an aggregate only when it is present in verifiedFacts or explicitly reported by a successful tool result. If the user needs a total and no verified aggregate exists, use a tool that computes it; otherwise say it was not computed. When sources disagree, report the mismatch instead of choosing a number.`,`[Fix 3.3.3 targeted discovery]",
    "verified statistics prompt contract",
)

replace_once(
    "function Iz(e){",
    "function DPP_FACT_TEXT_33109(e){let t=[],n=new Set,r=new Set,i=(e,a=0)=>{if(e==null||a>4)return;if(typeof e==`string`){let n=e.trim();if(n&&a<4&&(/^[\\[{]/.test(n)))try{i(JSON.parse(n),a+1);return}catch{}r.has(e)||(r.add(e),t.push(e));return}if(Array.isArray(e)){for(let t of e)i(t,a+1);return}if(typeof e==`object`&&!n.has(e)){n.add(e);for(let t of [`text`,`content`,`detail`,`output`])Object.prototype.hasOwnProperty.call(e,t)&&i(e[t],a+1)}};return i(e?.result?.detail),i(e?.result?.output),t.join(`\\n`)}function DPP_VERIFIED_FACTS_33109(e){if(DPP_TOOL_NAME_33(e?.name)!==`list_directory`||e?.result?.ok!==!0)return{};let t=DPP_FACT_TEXT_33109(e),n=/returned_entries:\\s*(\\d+)\\b/i.exec(t);if(!n)return{};let r=Number(n[1]),i=(t.match(/(?:^|\\n)\\[DIR\\](?:[ \\t]|$)/g)||[]).length,a=(t.match(/(?:^|\\n)\\[FILE\\](?:[ \\t]|$)/g)||[]).length,o=/truncated:\\s*(true|false)\\b/i.exec(t),s={source:`tool_result`,returnedEntries:r,...o?{truncated:o[1].toLowerCase()===`true`}:{}};return i+a===r&&(s.directoryEntries=i,s.fileEntries=a),{verifiedFacts:s}}function Iz(e){",
    "verified fact extraction helpers",
)

replace_once(
    "function Iz(e){",
    claim_helpers + "function Iz(e){",
    "verified statistics final-answer guard",
)

replace_once(
    "...DPP_RESULT_HINT_33(e),...t?{capabilityCatalog:!0}:{}",
    "...DPP_RESULT_HINT_33(e),...DPP_VERIFIED_FACTS_33109(e),...t?{capabilityCatalog:!0}:{}",
    "full result verified facts",
)

replace_once(
    "...DPP_RESULT_HINT_33(e),...t?{capabilityWindow:t}:{}",
    "...DPP_RESULT_HINT_33(e),...DPP_VERIFIED_FACTS_33109(e),...t?{capabilityWindow:t}:{}",
    "windowed result verified facts",
)

old_restore = "async function M0(e,t){let n=g0(),r=await k0();if(!XX(e,t))return;let i=!1;for(let e of r)if(P0(e,n)&&!KY.has(e.id)){let t=N0(e);KY.set(t.id,t),e.status===`running`&&await O0(t),qY.add(t.id),i=!0}i&&U2()}function N0(e){let t=e.status===`running`,n=typeof e.finalText==`string`?e.finalText:``;return{...e,status:t?`stopping`:e.status,error:t?$(`content.agent.stopped`):e.error,finalText:a0(n,eJ)??``,steps:e.steps.map(e=>({...e,status:t&&e.status===`streaming`?`error`:e.status,collapsed:!0,text:a0(e.text,$q)??``,toolExecutions:e.toolExecutions.map(e=>FH(e))}))}}"
new_restore = "var DPP_TRACE_EXPIRY_33109=3e5,DPP_TRACE_PROBE_WINDOW_33109=320,DPP_AGENT_LIFECYCLE_CHANNEL_33109=null;function DPP_TRACE_EXPIRED_33109(e,t=Date.now()){let n=Number(e?.updatedAt??e?.createdAt??0);return Number.isFinite(n)&&n>0&&t-n>=DPP_TRACE_EXPIRY_33109}function DPP_TRACE_NEEDS_REPAIR_33109(e){return e?.status!==`running`&&Array.isArray(e?.steps)&&e.steps.some(e=>e?.status===`streaming`)}function DPP_INIT_AGENT_LIFECYCLE_CHANNEL_33109(){if(DPP_AGENT_LIFECYCLE_CHANNEL_33109!==null)return DPP_AGENT_LIFECYCLE_CHANNEL_33109;try{let e=new BroadcastChannel(`dpp-inline-agent:${chrome.runtime.id}`);return e.addEventListener(`message`,t=>{let n=t?.data;n?.type===`probe`&&n.nonce&&t1()&&BY?.id&&e.postMessage({type:`active`,nonce:n.nonce,traceId:BY.id})}),DPP_AGENT_LIFECYCLE_CHANNEL_33109=e,e}catch{return null}}function DPP_ACTIVE_TRACE_IDS_33109(e=DPP_TRACE_PROBE_WINDOW_33109){let t=DPP_INIT_AGENT_LIFECYCLE_CHANNEL_33109();if(!t)return Promise.resolve(null);return new Promise(n=>{let r=`${Date.now()}:${Math.random()}`,i=new Set,a=t=>{let n=t?.data;n?.type===`active`&&n.nonce===r&&typeof n.traceId==`string`&&i.add(n.traceId)},o=null,s=()=>{o!==null&&clearTimeout(o),t.removeEventListener(`message`,a),n(i)};t.addEventListener(`message`,a),t1()&&BY?.id&&i.add(BY.id);try{t.postMessage({type:`probe`,nonce:r}),o=setTimeout(()=>{try{t.postMessage({type:`probe`,nonce:r})}catch{}},Math.floor(e/3)),setTimeout(s,e)}catch{t.removeEventListener(`message`,a),n(null)}})}DPP_INIT_AGENT_LIFECYCLE_CHANNEL_33109();async function M0(e,t){let n=g0(),r=await k0(),i=await DPP_ACTIVE_TRACE_IDS_33109();if(!XX(e,t))return;let a=!1,o=Date.now();for(let e of r){let t=P0(e,n),s=i instanceof Set&&i.has(e.id),c=e.status===`running`&&i instanceof Set&&!s&&(t||DPP_TRACE_EXPIRED_33109(e,o)),l=DPP_TRACE_NEEDS_REPAIR_33109(e),u=c||l?N0(e):e;(c||l)&&await O0(u),t&&!KY.has(e.id)&&(KY.set(u.id,u),qY.add(u.id),a=!0)}a&&U2()}function N0(e){let t=e.status===`running`,n=typeof e.finalText==`string`?e.finalText:``;return{...e,status:t?`stopping`:e.status,error:t?$(`content.agent.stopped`):e.error,finalText:a0(n,eJ)??``,steps:e.steps.map(e=>({...e,status:e.status===`streaming`?`error`:e.status,collapsed:!0,text:a0(e.text,$q)??``,toolExecutions:e.toolExecutions.map(e=>FH(e))}))}}"
replace_once(old_restore, new_restore, "global stale trace cleanup")

replace_once(claim_hook_old, claim_hook_new, "final-answer statistics gate")

manifest["version"] = "1.14.0.14"
manifest["version_name"] = "1.14.0 ShunCode MCP Fix 3.3.10.9"

updates = {
    "content-scripts/content.js": s.encode("utf-8"),
    "manifest.json": (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).replace("\n", "\r\n").encode("utf-8"),
}

for relative in ["_locales/en/messages.json", "_locales/zh_CN/messages.json"]:
    data = json.loads((root / relative).read_text(encoding="utf-8-sig"))
    data["extension_name"]["message"] = "DeepSeek++ ShunCode MCP Fix 3.3.10.9"
    updates[relative] = (
        json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    ).replace("\n", "\r\n").encode("utf-8")

generated_mismatch = []
for relative, data in updates.items():
    actual = hashlib.sha256(data).hexdigest().upper()
    if actual != output_expected[relative]:
        generated_mismatch.append(f"{relative}={actual}")
if generated_mismatch:
    raise SystemExit("APPLY_FIX33109_GENERATED_HASHES: " + " ".join(generated_mismatch))

for relative, data in updates.items():
    (root / relative).write_bytes(data)

print("APPLY_FIX33109_PASS")
