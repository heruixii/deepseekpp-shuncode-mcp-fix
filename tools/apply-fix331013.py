from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

OLD_VERSION = "1.14.0 ShunCode MCP Fix 3.3.10.12"
NEW_VERSION = "1.14.0 ShunCode MCP Fix 3.3.10.13"
OLD_MANIFEST_VERSION = "1.14.0.17"
NEW_MANIFEST_VERSION = "1.14.0.18"
MARKER = "DPP_AGENT_RESULT_DELTA_331013"

EXPECTED = {
    "content-scripts/content.js": "3AFE6900CD11DCDF66471DB0F8D7F63DEA0D4A58942F5C725F69A22A4A6B9BD8",
    "manifest.json": "B2F3F42E8082C59755369875A80D6E2B4DEBD2ACC826F6DDBD3C57AE9067C598",
    "_locales/en/messages.json": "D4291E91AA309946870CAFE8ED8BED6D60E3FB4C4ED2F6ADBD176D2F6183882E",
    "_locales/zh_CN/messages.json": "1F0FA4295D6F80DE15CB958FA193F63ABEB676BC087C66EBE8C78020DD0D5068",
}

OUTPUT_EXPECTED = {
    "content-scripts/content.js": "FB3CDB5CE056B3CE8C824A2084788DD0C0F33F7A2705AC3AD80601F6C715C827",
    "manifest.json": "22AA662AE139A9D13D8B03415B49AEB5354F5EEEF6634BAF42821645070F7BC2",
    "_locales/en/messages.json": "C66C9B90EB0A201C3374DFD43EC4376AA50A7EB436689825D7859992F4212525",
    "_locales/zh_CN/messages.json": "181839DEC6AF05957AFBF5253B09902A851098B64EBA581D52DC5B443DB15654",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def replace_one(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def stage_write(path: Path, data: bytes) -> Path:
    tmp = path.with_name(path.name + ".fix331013.tmp")
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
                actual = sha256(paths[rel].read_bytes())
                if actual != expected:
                    raise RuntimeError(f"already-patched hash mismatch for {rel}: {actual}")
        print("APPLY_FIX331013_OK already-applied")
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
        "function DPP_AGENT_RESULT_DELTA_331013(e,t){"
        "let n=Number.isSafeInteger(t)&&t>=0?Math.min(t,e.length):0;"
        "return{results:e.slice(n),cursor:e.length}}"
    )
    content = replace_one(
        content,
        "async function Jz(e){",
        helper + "async function Jz(e){",
        "Agent result delta helper",
    )
    content = replace_one(
        content,
        "le=!1,ue=0,de=e=>e.length>Kz?`${e.slice(0,Kz)}${qz}`:e,",
        "le=!1,ue=0,DPPResultCursor331013=0,DPPNextResults331013=()=>{let e=DPP_AGENT_RESULT_DELTA_331013(g,DPPResultCursor331013);return DPPResultCursor331013=e.cursor,e.results},de=e=>e.length>Kz?`${e.slice(0,Kz)}${qz}`:e,",
        "Agent result cursor",
    )
    content = replace_one(
        content,
        "serializePrompt:()=>y.active?(y.active=!1,y.currentTurnIsNudge=!0,Pz(t.originalPrompt,y.lastAssistantText,g,y.count,d)):Nz(t.originalPrompt,g,d),",
        "serializePrompt:()=>{let e=DPPNextResults331013();return y.active?(y.active=!1,y.currentTurnIsNudge=!0,Pz(t.originalPrompt,y.lastAssistantText,e,y.count,d)):Nz(t.originalPrompt,e,d)},",
        "web Agent delta prompt",
    )

    manifest["version"] = NEW_MANIFEST_VERSION
    manifest["version_name"] = NEW_VERSION
    outputs = {
        "content-scripts/content.js": content.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"),
        "manifest.json": (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8"),
    }
    for rel in ("_locales/en/messages.json", "_locales/zh_CN/messages.json"):
        text = paths[rel].read_text(encoding="utf-8-sig")
        outputs[rel] = text.replace("Fix 3.3.10.12", "Fix 3.3.10.13").replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")

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

    print("APPLY_FIX331013_OK")
    for rel in outputs:
        print(f"{rel} {sha256(paths[rel].read_bytes())}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply-fix331013.py <extension-root>")
    main(sys.argv[1])
