from __future__ import annotations
import hashlib,json,os,sys
from pathlib import Path
OLD_VERSION="1.14.0 ShunCode MCP Fix 3.3.10.13"
NEW_VERSION="1.14.0 ShunCode MCP Fix 3.3.10.14"
OLD_MANIFEST_VERSION="1.14.0.18"
NEW_MANIFEST_VERSION="1.14.0.19"
MARKER="DPP_MUTATION_MESSAGES_331014"
EXPECTED={
"content-scripts/content.js":"FB3CDB5CE056B3CE8C824A2084788DD0C0F33F7A2705AC3AD80601F6C715C827",
"manifest.json":"22AA662AE139A9D13D8B03415B49AEB5354F5EEEF6634BAF42821645070F7BC2",
"_locales/en/messages.json":"C66C9B90EB0A201C3374DFD43EC4376AA50A7EB436689825D7859992F4212525",
"_locales/zh_CN/messages.json":"181839DEC6AF05957AFBF5253B09902A851098B64EBA581D52DC5B443DB15654"}
OUTPUT_EXPECTED={
"content-scripts/content.js":"F647EB21F644DF87898D2DF44152DBF43170C8C7A5F719497391E95E4E1FC5C5",
"manifest.json":"83D8F13274CE9C866C2D6D6A288B70C213D5A10A9BFF9ECBC2B4BE3E1A64D906",
"_locales/en/messages.json":"CF42215ED8744C145AEF411E8037CC2A855265AF78A2971EF90F03CBB4AE9F70",
"_locales/zh_CN/messages.json":"3CE14B003430E0AE064BB3B94BE869B345E5A7B2932B5973A02A321CC5CBEC9C"}
def sha256(data:bytes)->str:return hashlib.sha256(data).hexdigest().upper()
def replace_one(text,old,new,label):
 c=text.count(old)
 if c!=1:raise RuntimeError(f"{label}: expected one match, got {c}")
 return text.replace(old,new,1)
def stage_write(path,data):
 tmp=path.with_name(path.name+".fix331014.tmp");tmp.write_bytes(data);return tmp
def main(root_arg):
 root=Path(root_arg).resolve();paths={rel:root/rel for rel in EXPECTED}
 manifest=json.loads(paths["manifest.json"].read_text(encoding="utf-8-sig"));content=paths["content-scripts/content.js"].read_text(encoding="utf-8-sig")
 if manifest.get("version")==NEW_MANIFEST_VERSION and manifest.get("version_name")==NEW_VERSION and MARKER in content:
  for rel,expected in OUTPUT_EXPECTED.items():
   actual=sha256(paths[rel].read_bytes())
   if actual!=expected:raise RuntimeError(f"already-patched hash mismatch for {rel}: {actual}")
  print("APPLY_FIX331014_OK already-applied");return
 if manifest.get("version")!=OLD_MANIFEST_VERSION or manifest.get("version_name")!=OLD_VERSION:raise RuntimeError(f"expected {OLD_VERSION}, got {manifest.get('version_name')!r}")
 for rel,expected in EXPECTED.items():
  actual=sha256(paths[rel].read_bytes())
  if actual!=expected:raise RuntimeError(f"input hash mismatch for {rel}: {actual}")
 old='function g4(e,t){_4();let n=!1,r=()=>{n||OJ>0||(n=!0,zY=requestAnimationFrame(()=>{zY=null,n=!1,C4()}))};r(),e.addCleanup(`cleanup`,t.subscribe({matches:t=>bX!==e||!e.active?!1:lq(t,{hasPendingRecords:pY.size>0,restoredUiSelector:Sq}).schedulePendingRender||t.some(v4),handle(e){let t=lq(e,{hasPendingRecords:pY.size>0,restoredUiSelector:Sq});t.requeueMountedRecords&&z2(),r(),t.schedulePendingRender&&pY.size>0&&(hY=0,V2())}}))}'
 new='var DPP_DOM_MUTATION_MAX_MESSAGES_331014=4;function DPP_MUTATION_MESSAGES_331014(e){let t=new Set,n=e=>{if(t.size>=DPP_DOM_MUTATION_MAX_MESSAGES_331014)return;let r=e instanceof Element?e:e?.parentElement;if(!r||r.closest(cq))return;let i=r.matches?.(`.ds-message`)?r:r.closest?.(`.ds-message`);if(i){t.add(i);return}if(!r.querySelectorAll)return;for(let e of r.querySelectorAll(`.ds-message`)){t.add(e);if(t.size>=DPP_DOM_MUTATION_MAX_MESSAGES_331014)break}};for(let t of e)if(t.type===`characterData`)n(t.target);else for(let e of t.addedNodes)n(e);return[...t]}function DPP_SCAN_MESSAGES_331014(e){for(let t of e)D4(t),j4(t)}function g4(e,t){_4();let n=!1,r=new Set,i=e=>{e&&e.forEach(e=>r.add(e)),n||OJ>0||(n=!0,zY=requestAnimationFrame(()=>{zY=null,n=!1;let e=[...r];r.clear(),e.length?DPP_SCAN_MESSAGES_331014(e):C4()}))};i(),e.addCleanup(`cleanup`,t.subscribe({matches:t=>bX!==e||!e.active?!1:lq(t,{hasPendingRecords:pY.size>0,restoredUiSelector:Sq}).schedulePendingRender||t.some(v4),handle(e){let t=lq(e,{hasPendingRecords:pY.size>0,restoredUiSelector:Sq});t.requeueMountedRecords&&z2(),i(DPP_MUTATION_MESSAGES_331014(e)),t.schedulePendingRender&&pY.size>0&&(hY=0,V2())}}))}'
 content=replace_one(content,old,new,"targeted DOM mutation scan")
 manifest["version"]=NEW_MANIFEST_VERSION;manifest["version_name"]=NEW_VERSION
 outputs={"content-scripts/content.js":content.replace("\r\n","\n").replace("\n","\r\n").encode("utf-8"),"manifest.json":(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n").replace("\n","\r\n").encode("utf-8")}
 for rel in ("_locales/en/messages.json","_locales/zh_CN/messages.json"):
  text=paths[rel].read_text(encoding="utf-8-sig");outputs[rel]=text.replace("Fix 3.3.10.13","Fix 3.3.10.14").replace("\r\n","\n").replace("\n","\r\n").encode("utf-8")
 for rel,data in outputs.items():
  got=sha256(data);want=OUTPUT_EXPECTED[rel]
  if got!=want:raise RuntimeError(f"staged output hash mismatch for {rel}: {got} != {want}")
 staged=[]
 try:
  for rel,data in outputs.items():staged.append((stage_write(paths[rel],data),paths[rel]))
  for tmp,path in staged:os.replace(tmp,path)
 finally:
  for tmp,_ in staged:
   if tmp.exists():tmp.unlink()
 print("APPLY_FIX331014_OK")
 for rel in outputs:print(f"{rel} {sha256(paths[rel].read_bytes())}")
if __name__=="__main__":
 if len(sys.argv)!=2:raise SystemExit("usage: apply-fix331014.py <extension-root>")
 main(sys.argv[1])
