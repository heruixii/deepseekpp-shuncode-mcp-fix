from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


OLD_VERSION = "1.14.0 ShunCode MCP Fix 3.3.10.11"
NEW_VERSION = "1.14.0 ShunCode MCP Fix 3.3.10.12"
OLD_MANIFEST_VERSION = "1.14.0.16"
NEW_MANIFEST_VERSION = "1.14.0.17"
MARKER = "DPP_AGENT_RESUME_PREPARE_331012"

EXPECTED = {
    "content-scripts/content.js": "5A91E6EECAD2BF6A7C3266EA43E89BEC22392F7DDCAE691C6185F04B7437FAA2",
    "manifest.json": "8BE4F258F1BAD887A691044C2329DD980E4907E5B89CAD4D9633110E5956BFF7",
    "_locales/en/messages.json": "992006EEBB484A6C9B86EF2AE939C4D6978C750C2F64D07873B5B4B53D3A6E04",
    "_locales/zh_CN/messages.json": "40F3A637B86F8BA3C8D760573DB8F9FDE521BDFC1EC572148142A518DE838BDD",
}

OUTPUT_EXPECTED = {
    "content-scripts/content.js": "3AFE6900CD11DCDF66471DB0F8D7F63DEA0D4A58942F5C725F69A22A4A6B9BD8",
    "manifest.json": "B2F3F42E8082C59755369875A80D6E2B4DEBD2ACC826F6DDBD3C57AE9067C598",
    "_locales/en/messages.json": "D4291E91AA309946870CAFE8ED8BED6D60E3FB4C4ED2F6ADBD176D2F6183882E",
    "_locales/zh_CN/messages.json": "1F0FA4295D6F80DE15CB958FA193F63ABEB676BC087C66EBE8C78020DD0D5068",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def replace_one(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def stage_write(path: Path, data: bytes) -> Path:
    tmp = path.with_name(path.name + ".fix331012.tmp")
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
        for rel, expected in OUTPUT_EXPECTED.items():
            actual = sha256(paths[rel].read_bytes())
            if actual != expected:
                raise RuntimeError(f"already-patched hash mismatch for {rel}: {actual}")
        print("APPLY_FIX331012_OK already-applied")
        for rel in EXPECTED:
            print(f"{rel} {sha256(paths[rel].read_bytes())}")
        return

    if manifest.get("version") != OLD_MANIFEST_VERSION or manifest.get("version_name") != OLD_VERSION:
        raise RuntimeError(f"expected {OLD_VERSION}, got {manifest.get('version_name')!r}")
    for rel, expected in EXPECTED.items():
        actual = sha256(paths[rel].read_bytes())
        if actual != expected:
            raise RuntimeError(f"input hash mismatch for {rel}: {actual}")

    helper = (
        "function DPP_AGENT_RESUME_PREPARE_331012(e,t){try{let n=DPP_RESUME_TRACE_CHAIN_331010(e,t);"
        "if(n.length===0)return null;let r=DPP_RESUME_LIGHT_PROMPT_331011(e,n);"
        "return r?{prompt:r,sourceTraceIds:n.map(e=>e.id)}:null}catch(e){return console.error("
        "`[DeepSeek++] isolated resume preparation failed open`,e),null}}"
    )
    content = replace_one(
        content,
        "var DPP_AGENT_SYNTHETIC_REF_FILES_337=[];",
        helper + "var DPP_AGENT_SYNTHETIC_REF_FILES_337=[];",
        "isolated Agent resume helper",
    )
    content = replace_one(
        content,
        "function Zc(e,t){let n={...e},r=n.prompt,DPPOriginalPrompt331010=r,DPPManualResume331010=DPP_MANUAL_RESUME_PROMPT_SAFE_331011(r,t.chatSessionId);DPPManualResume331010&&(r=DPPManualResume331010,n.prompt=r);let i=",
        "function Zc(e,t){let n={...e},r=n.prompt,DPPOriginalPrompt331010=r;let i=",
        "manual request isolation",
    )
    content = replace_one(
        content,
        "let DPPResume=null;try{DPPResume=DPP_AGENT_RESUME_PREPARE_331011(e,n,await k0())}catch(e){console.error(`[DeepSeek++] failed to prepare interrupted Agent checkpoint`,e)}let DPPAgentRequest=DPPResume?{...e,originalPrompt:DPPResume.prompt,agentTaskPrompt:DPPResume.prompt}:e,r=crypto.randomUUID()",
        "let DPPResume=null;try{DPPResume=DPP_AGENT_RESUME_PREPARE_331012(e,await k0())}catch(e){console.error(`[DeepSeek++] failed to prepare interrupted Agent checkpoint`,e)}let DPPAgentPrompt=DPPResume?.prompt??e.agentTaskPrompt??e.originalPrompt,r=crypto.randomUUID()",
        "Agent resume preparation",
    )
    content = replace_one(
        content,
        "originalPrompt:DPPAgentRequest.agentTaskPrompt||DPPAgentRequest.originalPrompt,agentTaskPrompt:DPPAgentRequest.agentTaskPrompt||DPPAgentRequest.originalPrompt,toolExecutions:DPPResume?.toolExecutions??n,",
        "originalPrompt:DPPAgentPrompt,agentTaskPrompt:DPPAgentPrompt,toolExecutions:n,",
        "resume context isolation",
    )
    content = replace_one(
        content,
        "LY=r,BY=b0(DPPAgentRequest,r,t,p,s),JX(O0(BY))",
        "LY=r,BY=b0(e,r,t,p,s),JX(O0(BY))",
        "raw trace prompt preservation",
    )

    manifest["version"] = NEW_MANIFEST_VERSION
    manifest["version_name"] = NEW_VERSION
    outputs = {
        "content-scripts/content.js": content.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"),
        "manifest.json": (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8"),
    }
    for rel in ("_locales/en/messages.json", "_locales/zh_CN/messages.json"):
        text = paths[rel].read_text(encoding="utf-8-sig")
        outputs[rel] = text.replace("Fix 3.3.10.11", "Fix 3.3.10.12").replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")

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

    print("APPLY_FIX331012_OK")
    for rel in outputs:
        print(f"{rel} {sha256(paths[rel].read_bytes())}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply-fix331012.py <extension-root>")
    main(sys.argv[1])
