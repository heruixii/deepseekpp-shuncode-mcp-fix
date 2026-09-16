from __future__ import annotations
import hashlib,json,os,sys
from pathlib import Path
OLD_VERSION="1.14.0 ShunCode MCP Fix 3.3.10.15"
NEW_VERSION="1.14.0 ShunCode MCP Fix 3.3.10.16"
OLD_MANIFEST_VERSION="1.14.0.20"
NEW_MANIFEST_VERSION="1.14.0.21"
OLD='l=t=>{o||(o=!0,U.onRequestTerminal({requestId:t.requestId,...t?{diag331015:t}:{}}))}'
NEW='l=e=>{o||(o=!0,U.onRequestTerminal({requestId:t.requestId,...e?{diag331015:e}:{}}))}'
EXPECTED={
"content-scripts/content.js":"7FECC173832CE58B39DCB118537CD2B42D70418418D51C0C5EC2B81EB9CB071E",
"content-scripts/main-world.js":"507E8A802E1367D08DDDDDB5CC94095CD9449D854AF0BF640C1C3202B97BC686",
"manifest.json":"9CE98F269394226CE8E72EDDCAF9EFE1B77C7B8BB9B9F997C942F38AFF569F33",
"_locales/en/messages.json":"36F957EFD2821CAD1CA6C4DB7BD6D2F7D0321207662ADF7AF01D8F695A9A48A2",
"_locales/zh_CN/messages.json":"620D15D7BA375CA3DB1477DC8A2A447E8C8D53884AA0429017A2BD07202F5D9C"}
OUTPUT_EXPECTED={
"content-scripts/content.js":"7FECC173832CE58B39DCB118537CD2B42D70418418D51C0C5EC2B81EB9CB071E",
"content-scripts/main-world.js":"E1238231B0B4C70B3C1DDC6B5821B9DF69AB684FA1829D14934DA23337D68C8C",
"manifest.json":"C22AFE084F513B9A44155CCC94D4F67EC4717B3EEEE28694F06A8E338160F4C4",
"_locales/en/messages.json":"177059BA9CA77B52235712F0A635FD02E54C13B1D8F00404D8B5AE017C70CE4F",
"_locales/zh_CN/messages.json":"5A8876A0E030E2F061A4C8EF74EB6CEC99B145BE4A2618D7EC548677DF6C2B47"}
def sha(data:bytes):return hashlib.sha256(data).hexdigest().upper()
def stage(path:Path,data:bytes):
 t=path.with_name(path.name+'.fix331016.tmp');t.write_bytes(data);return t
def main(root_arg):
 root=Path(root_arg).resolve(); paths={k:root/k for k in EXPECTED}
 manifest=json.loads(paths['manifest.json'].read_text(encoding='utf-8-sig'))
 mainw=paths['content-scripts/main-world.js'].read_text(encoding='utf-8-sig')
 if manifest.get('version')==NEW_MANIFEST_VERSION and manifest.get('version_name')==NEW_VERSION and NEW in mainw:
  for rel,want in OUTPUT_EXPECTED.items():
   got=sha(paths[rel].read_bytes())
   if got!=want:raise RuntimeError(f'already-patched hash mismatch for {rel}: {got}')
  print('APPLY_FIX331016_OK already-applied');return
 if manifest.get('version')!=OLD_MANIFEST_VERSION or manifest.get('version_name')!=OLD_VERSION:raise RuntimeError(f'expected {OLD_VERSION}, got {manifest.get("version_name")!r}')
 for rel,want in EXPECTED.items():
  got=sha(paths[rel].read_bytes())
  if got!=want:raise RuntimeError(f'input hash mismatch for {rel}: {got}')
 if mainw.count(OLD)!=1:raise RuntimeError(f'XHR terminal target count {mainw.count(OLD)}')
 mainw=mainw.replace(OLD,NEW,1)
 manifest['version']=NEW_MANIFEST_VERSION;manifest['version_name']=NEW_VERSION
 outputs={
 'content-scripts/content.js':paths['content-scripts/content.js'].read_bytes(),
 'content-scripts/main-world.js':mainw.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'),
 'manifest.json':(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf-8')}
 for rel in ('_locales/en/messages.json','_locales/zh_CN/messages.json'):
  txt=paths[rel].read_text(encoding='utf-8-sig').replace('Fix 3.3.10.15','Fix 3.3.10.16')
  outputs[rel]=txt.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8')
 for rel,data in outputs.items():
  got=sha(data);want=OUTPUT_EXPECTED[rel]
  if got!=want:raise RuntimeError(f'staged output hash mismatch for {rel}: {got} != {want}')
 staged=[]
 try:
  for rel,data in outputs.items():staged.append((stage(paths[rel],data),paths[rel]))
  for t,p in staged:os.replace(t,p)
 finally:
  for t,_ in staged:
   if t.exists():t.unlink()
 print('APPLY_FIX331016_OK')
if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('usage: apply-fix331016.py <extension-root>')
 main(sys.argv[1])
