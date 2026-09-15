from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


OLD_VERSION = "1.14.0 ShunCode MCP Fix 3.3.10.10"
NEW_VERSION = "1.14.0 ShunCode MCP Fix 3.3.10.11"
OLD_MANIFEST_VERSION = "1.14.0.15"
NEW_MANIFEST_VERSION = "1.14.0.16"
MARKER = "DPP_RESUME_LIGHT_PROMPT_331011"

EXPECTED = {
    "content-scripts/content.js": "27B177F9CFCD75295E4B23B670E226091EF320DBB5AFF968356CBFE425BD6A6B",
    "manifest.json": "F3D4AA1874514FF792DFAB720C1B7281F17186C5911C42A3F396EDC347AFA66F",
    "_locales/en/messages.json": "C2AC07E4D1BCE5AC829E52239927A9B4FD49EB2AE5FE756DDA693739AEE1BB1E",
    "_locales/zh_CN/messages.json": "BEAFDC1783D3402E2FF44A8DDE7D379BCEC2848E540E7161BE60E799AC0C93CC",
}

OUTPUT_EXPECTED = {
    "content-scripts/content.js": "5A91E6EECAD2BF6A7C3266EA43E89BEC22392F7DDCAE691C6185F04B7437FAA2",
    "manifest.json": "8BE4F258F1BAD887A691044C2329DD980E4907E5B89CAD4D9633110E5956BFF7",
    "_locales/en/messages.json": "992006EEBB484A6C9B86EF2AE939C4D6978C750C2F64D07873B5B4B53D3A6E04",
    "_locales/zh_CN/messages.json": "40F3A637B86F8BA3C8D760573DB8F9FDE521BDFC1EC572148142A518DE838BDD",
}

BROKEN_OUTPUT_EXPECTED = {
    "content-scripts/content.js": "523489208FB41914F7F606F04786FEF7E9818D919DB4C82A4B58C9F92449826D",
    "manifest.json": "8BE4F258F1BAD887A691044C2329DD980E4907E5B89CAD4D9633110E5956BFF7",
    "_locales/en/messages.json": "992006EEBB484A6C9B86EF2AE939C4D6978C750C2F64D07873B5B4B53D3A6E04",
    "_locales/zh_CN/messages.json": "40F3A637B86F8BA3C8D760573DB8F9FDE521BDFC1EC572148142A518DE838BDD",
}

SHADOW_OUTPUT_EXPECTED = {
    "content-scripts/content.js": "18E0B6D5F5815F2C5A0C267587DE6B5B9DF394F37D0586C7C51C017DB1296E6E",
    "manifest.json": "8BE4F258F1BAD887A691044C2329DD980E4907E5B89CAD4D9633110E5956BFF7",
    "_locales/en/messages.json": "992006EEBB484A6C9B86EF2AE939C4D6978C750C2F64D07873B5B4B53D3A6E04",
    "_locales/zh_CN/messages.json": "40F3A637B86F8BA3C8D760573DB8F9FDE521BDFC1EC572148142A518DE838BDD",
}

SPACED_OUTPUT_EXPECTED = {
    "content-scripts/content.js": "1FAB9169F78D2D2B2E10126F0A9B1134AD1BEC7B5CD3D096B9C3BEDD02788F43",
    "manifest.json": "8BE4F258F1BAD887A691044C2329DD980E4907E5B89CAD4D9633110E5956BFF7",
    "_locales/en/messages.json": "992006EEBB484A6C9B86EF2AE939C4D6978C750C2F64D07873B5B4B53D3A6E04",
    "_locales/zh_CN/messages.json": "40F3A637B86F8BA3C8D760573DB8F9FDE521BDFC1EC572148142A518DE838BDD",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def replace_one(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def stage_write(path: Path, data: bytes) -> Path:
    tmp = path.with_name(path.name + ".fix331011.tmp")
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
        broken = "let n=[...DPP_RESUME_EXECUTIONS_331010(e),...Array.isArray(t)?t:[]]"
        if broken in content:
            for rel, expected in BROKEN_OUTPUT_EXPECTED.items():
                actual = sha256((root / rel).read_bytes())
                if actual != expected:
                    raise RuntimeError(f"broken-build migration hash mismatch for {rel}: {actual}")
            content = replace_one(
                content,
                broken,
                "let n=[...DPP_RESUME_EXECUTIONS_331010(e),...(Array.isArray(t)?t:[])]",
                "resume execution spread precedence",
            )
            tmp = stage_write(paths["content-scripts/content.js"], content.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
            os.replace(tmp, paths["content-scripts/content.js"])
        shadowed = "let n=DPP_RESUME_EXECUTION_KEY_331011(t);if(i.has(n))continue;let o;try{o=JSON.stringify(t)}catch{continue}if(o.length>8192||a+o.length>24576)continue;i.add(n),a+=o.length,r.unshift(t)"
        if shadowed in content:
            for rel, expected in SHADOW_OUTPUT_EXPECTED.items():
                actual = sha256((root / rel).read_bytes())
                if actual != expected:
                    raise RuntimeError(f"shadowed-build migration hash mismatch for {rel}: {actual}")
            content = replace_one(
                content,
                shadowed,
                "let o=DPP_RESUME_EXECUTION_KEY_331011(t);if(i.has(o))continue;let s;try{s=JSON.stringify(t)}catch{continue}if(s.length>8192||a+s.length>24576)continue;i.add(o),a+=s.length,r.unshift(t)",
                "resume execution key shadowing",
            )
            tmp = stage_write(paths["content-scripts/content.js"], content.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
            os.replace(tmp, paths["content-scripts/content.js"])
        spaced = "function DPP_RESUME_EXECUTION_KEY_331011(e){return[ String("
        if spaced in content:
            for rel, expected in SPACED_OUTPUT_EXPECTED.items():
                actual = sha256((root / rel).read_bytes())
                if actual != expected:
                    raise RuntimeError(f"spaced-build migration hash mismatch for {rel}: {actual}")
            content = replace_one(
                content,
                spaced,
                "function DPP_RESUME_EXECUTION_KEY_331011(e){return[String(",
                "canonical resume helper bytes",
            )
            tmp = stage_write(paths["content-scripts/content.js"], content.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
            os.replace(tmp, paths["content-scripts/content.js"])
        if OUTPUT_EXPECTED:
            for rel, expected in OUTPUT_EXPECTED.items():
                actual = sha256((root / rel).read_bytes())
                if actual != expected:
                    raise RuntimeError(f"already-patched hash mismatch for {rel}: {actual}")
        print("APPLY_FIX331011_OK already-applied")
        return

    if manifest.get("version") != OLD_MANIFEST_VERSION or manifest.get("version_name") != OLD_VERSION:
        raise RuntimeError(f"expected {OLD_VERSION}, got {manifest.get('version_name')!r}")
    for rel, expected in EXPECTED.items():
        actual = sha256(paths[rel].read_bytes())
        if actual != expected:
            raise RuntimeError(f"input hash mismatch for {rel}: {actual}")

    helpers = r'''function DPP_RESUME_CLEAN_TEXT_331011(e,t){let n=String(e??``).replace(/<[^>\n]{0,240}(?:DSML|invoke|parameter|calls|tool_call)[^>\n]{0,240}>/gi,``).replace(/\s+/g,` `).trim();return n.length>t?`${n.slice(0,Math.max(0,t-16))}...[truncated]`:n}function DPP_RESUME_LIGHT_PROMPT_331011(e,t){try{let n=DPP_RESUME_TRACE_CHAIN_331010(e,t);if(n.length===0)return null;let r=n.find(e=>!DPP_RESUME_INTENT_331010(e?.originalPrompt))??n[0],i=n[n.length-1],a=[];for(let e of n)for(let t of e?.steps??[]){if(t?.status===`streaming`)continue;let e=DPP_RESUME_CLEAN_TEXT_331011(t?.text||t?.reasoning,220);e&&!a.includes(e)&&a.push(e)}let o=a.slice(-7),s=[`[Fix 3.3.10.11 safe resume] This is a resume, not a new task.`,`Merge duplicate attempts and keep the furthest verified result. Do not repeat confirmed discovery, installation, build, write, or test work. Read existing ShunCode todos first and never reset completed todos. Verify ambiguous mutations read-only before retrying.`,`Current request: ${DPP_RESUME_CLEAN_TEXT_331011(e?.originalPrompt,120)}`,`Original task: ${DPP_RESUME_CLEAN_TEXT_331011(r?.originalPrompt,360)}`,o.length?`Verified progress:\n${o.map(e=>`- ${e}`).join(`\n`)}`:``,`Last interruption: ${DPP_RESUME_CLEAN_TEXT_331011(i?.error,240)}`].filter(Boolean).join(`\n`);return s.length>2400?`${s.slice(0,2380)}...[truncated]`:s}catch(e){return console.error(`[DeepSeek++] safe resume prompt failed open`,e),null}}function DPP_RESUME_EXECUTION_KEY_331011(e){return[String(e?.callId??e?.id??``),String(e?.name??e?.invocationName??``),String(e?.result?.summary??``).slice(0,240),String(e?.result?.error?.code??``)].join(`|`)}function DPP_RESUME_EXECUTIONS_BOUNDED_331011(e,t){let n=[...DPP_RESUME_EXECUTIONS_331010(e),...(Array.isArray(t)?t:[])],r=[],i=new Set,a=0;for(let e=n.length-1;e>=0&&r.length<12;e--){let t=n[e];if(!t||typeof t!=`object`)continue;let o=DPP_RESUME_EXECUTION_KEY_331011(t);if(i.has(o))continue;let s;try{s=JSON.stringify(t)}catch{continue}if(s.length>8192||a+s.length>24576)continue;i.add(o),a+=s.length,r.unshift(t)}return r}function DPP_AGENT_RESUME_PREPARE_331011(e,t,n){try{let r=DPP_RESUME_TRACE_CHAIN_331010(e,n);if(r.length===0)return null;let i=DPP_RESUME_LIGHT_PROMPT_331011(e,r);if(!i)return null;return{prompt:i,toolExecutions:DPP_RESUME_EXECUTIONS_BOUNDED_331011(r,t),sourceTraceIds:r.map(e=>e.id)}}catch(e){return console.error(`[DeepSeek++] resume preparation failed open`,e),null}}function DPP_MANUAL_RESUME_PROMPT_SAFE_331011(e,t){if(!t)return null;try{return DPP_RESUME_LIGHT_PROMPT_331011({originalPrompt:e,chatSessionId:t},[...KY.values()])}catch(e){return console.error(`[DeepSeek++] manual resume gateway failed open`,e),null}}'''
    content = replace_one(
        content,
        "var DPP_AGENT_SYNTHETIC_REF_FILES_337=[];",
        helpers + "var DPP_AGENT_SYNTHETIC_REF_FILES_337=[];",
        "safe bounded resume helpers",
    )
    content = replace_one(
        content,
        "DPPManualResume331010=DPP_MANUAL_RESUME_PROMPT_331010(r,t.chatSessionId)",
        "DPPManualResume331010=DPP_MANUAL_RESUME_PROMPT_SAFE_331011(r,t.chatSessionId)",
        "fail-open manual resume gateway",
    )
    content = replace_one(
        content,
        "DPPResume=DPP_AGENT_RESUME_PREPARE_331010(e,n,await k0())",
        "DPPResume=DPP_AGENT_RESUME_PREPARE_331011(e,n,await k0())",
        "bounded agent resume preparation",
    )

    manifest["version"] = NEW_MANIFEST_VERSION
    manifest["version_name"] = NEW_VERSION
    outputs = {
        "content-scripts/content.js": content.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"),
        "manifest.json": (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8"),
    }
    for rel in ("_locales/en/messages.json", "_locales/zh_CN/messages.json"):
        text = paths[rel].read_text(encoding="utf-8-sig")
        outputs[rel] = text.replace("Fix 3.3.10.10", "Fix 3.3.10.11").replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")

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

    print("APPLY_FIX331011_OK")
    for rel in outputs:
        print(f"{rel} {sha256(paths[rel].read_bytes())}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply-fix331011.py <extension-root>")
    main(sys.argv[1])
