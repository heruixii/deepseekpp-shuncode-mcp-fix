#!/usr/bin/env python3
"""Hash-locked .36 -> .39 builder (= .38 runtime + MAIN-world bridge diagnostics in content-scripts/main-world.js).
Only --build BASE_36 NEW_OUTPUT. No gate is touched; main-world changes are diagnostics only (localStorage ring buffer,
fixed enums / booleans / counts). Purpose: explain why a fresh 'new chat' document sends the first message without tools.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
VERSION = '1.14.0.44'
NAME = '1.14.0 ShunCode MCP Fix 3.3.10.39'

spec = importlib.util.spec_from_file_location('builder38', HERE / 'apply-fix331038.py')
B38 = importlib.util.module_from_spec(spec); spec.loader.exec_module(B38)
sha, once = B38.sha, B38.once

MW_PATCHES = [
    ('var U=xa();', None),  # helper inserted here (handled specially)
    ('function DPP_PREFLIGHT_331018(e){try{U.onRequestPreflight(e)}catch{}}',
     'function DPP_PREFLIGHT_331018(e){try{e&&e.stage===`mw_send_hook_seen`&&DPP_MW_DIAG_V10(`send_hook`,{route:e.route,session:typeof e.chatSessionId==`string`&&e.chatSessionId.length>0,tools:Array.isArray(U.toolDescriptors)?U.toolDescriptors.length:-1}),U.onRequestPreflight(e)}catch{}}'),
    ('baseUrl:document.baseURI}):null;if(a===`history`)return io(e.call(this,t,n));if(!s(a)||typeof n?.body!=`string`)return e.call(this,t,n);',
     'baseUrl:document.baseURI}):null;if(a===`history`)return io(e.call(this,t,n));a!==null&&DPP_MW_DIAG_V10(`fetch_route`,{route:a,body:typeof n?.body==`string`,known:s(a)});if(!s(a)||typeof n?.body!=`string`)return e.call(this,t,n);'),
    ('requestAugmentedBody:(e,t,a,o)=>{if(!r?.active||!i)return Promise.resolve(null);',
     'requestAugmentedBody:(e,t,a,o)=>{DPP_MW_DIAG_V10(`augment`,{active:!!r?.active,bridge:!!i});if(!r?.active||!i)return Promise.resolve(null);'),
    ('m=t=>{if(!r?.active||!i)return!1;try{return i.postMessage({source:us,...t}),!0}',
     'm=t=>{if(!r?.active||!i)return DPP_MW_DIAG_V10(`post_drop`,{active:!!r?.active,bridge:!!i,kind:t&&t.type}),!1;try{return i.postMessage({source:us,...t}),!0}'),
    ('i.start(),d(),h({type:Ro}),h({type:`NAVIGATION_CHANGED`}))',
     'i.start(),d(),h({type:Ro}),h({type:`NAVIGATION_CHANGED`}),DPP_MW_DIAG_V10(`bridge_open`,{}))'),
    ('f=async()=>{let t=i,n=a,c=o;i=null,a=null,o=null,',
     'f=async()=>{DPP_MW_DIAG_V10(`bridge_close`,{bridge:!!i});let t=i,n=a,c=o;i=null,a=null,o=null,'),
    ('t=Ts({onNavigate(){e.post({type:`NAVIGATION_CHANGED`})}})',
     't=Ts({onNavigate(){DPP_MW_DIAG_V10(`navigate`,{session:/\\/chat\\/s\\//.test(location.pathname)}),e.post({type:`NAVIGATION_CHANGED`})}})'),
    ('function Sa(e){U={...U,...e},Object.prototype.hasOwnProperty.call(e,`toolDescriptors`)&&ka()}',
     'function Sa(e){U={...U,...e},Object.prototype.hasOwnProperty.call(e,`toolDescriptors`)&&(DPP_MW_DIAG_V10(`sync_state`,{tools:Array.isArray(e.toolDescriptors)?e.toolDescriptors.length:-1,body:!!document.body}),ka())}'),
    ('onError(e){console.error(`[DeepSeek++] MAIN content lifecycle failed`,e)}',
     'onError(e){DPP_MW_DIAG_V10(`lifecycle_error`,{}),console.error(`[DeepSeek++] MAIN content lifecycle failed`,e)}'),
    ('Ds.error(`The content script "main-world" crashed on startup!`,e),e',
     'DPP_MW_DIAG_V10(`main_crash`,{}),Ds.error(`The content script "main-world" crashed on startup!`,e),e'),
]

def gates(text):
    return (text.replace('1.14.0.41', VERSION)
            .replace('1.14.0 ShunCode MCP Fix 3.3.10.36', NAME)
            .replace('manifest version_name is Fix 3.3.10.36', 'manifest version_name is Fix 3.3.10.39')
            .replace('|32|33|34|35|36)$', '|32|33|34|35|36|37|38|39)$'))

def transform_main_world(mw, helper):
    nl = b'\r\n' if mw.count(b'\r\n') > mw.count(b'\n') // 2 else b'\n'
    helper = helper.replace(b'\r\n', b'\n').replace(b'\n', nl)
    mw = once(mw, 'var U=xa();', helper.rstrip(nl) + nl + b'var U=xa();')
    for old, new in MW_PATCHES[1:]:
        mw = once(mw, old, new)
    return mw

def build(base, output):
    base = Path(base).resolve(); output = Path(output).resolve()
    if output.exists() or output == base or base in output.parents: raise ValueError('Output must be new and outside baseline')
    inventory = json.loads((HERE / 'fix331037-baseline-sha256.json').read_text(encoding='utf-8'))
    values = {}
    for n, h in inventory.items():
        p = base / n
        if Path(n).is_absolute() or '..' in Path(n).parts or p.is_symlink() or base not in p.resolve().parents: raise ValueError('Unsafe source path')
        raw = p.read_bytes()
        if sha(raw) != h: raise ValueError('Baseline hash mismatch: ' + n)
        values[n] = raw
    locks = json.loads((HERE / 'fix331039-source-sha256.json').read_text(encoding='utf-8'))
    for n in ['dspp-upload-gate-diag-v9.js', 'apply-fix331037.py', 'apply-fix331038.py', 'dspp-mw-bridge-diag-v10.js']:
        if sha((HERE / n).read_bytes()) != locks[n]: raise ValueError('Source hash mismatch: ' + n)
    helper9 = (HERE / 'dspp-upload-gate-diag-v9.js').read_bytes()
    values['background.js'] = B38.transform_background(values['background.js'], helper9)
    values['content-scripts/content.js'] = B38.B37.transform_content(values['content-scripts/content.js'])
    values['content-scripts/main-world.js'] = transform_main_world(values['content-scripts/main-world.js'], (HERE / 'dspp-mw-bridge-diag-v10.js').read_bytes())
    for n in ['background.js', 'content-scripts/content.js', 'content-scripts/main-world.js']:
        result = subprocess.run(['node', '--check', '--input-type=module'], input=values[n], capture_output=True)
        if result.returncode: raise ValueError('Node syntax failure: ' + n + ' ' + result.stderr.decode('utf-8', 'replace')[:800])
    mf = once(values['manifest.json'], '"version": "1.14.0.41"', '"version": "' + VERSION + '"')
    values['manifest.json'] = once(mf, '1.14.0 ShunCode MCP Fix 3.3.10.36', NAME)
    for lang in ['en', 'zh_CN']:
        n = '_locales/' + lang + '/messages.json'
        values[n] = once(values[n], 'DeepSeek++ ShunCode MCP Fix 3.3.10.36', 'DeepSeek++ ShunCode MCP Fix 3.3.10.39')
    for n in values:
        if '/' not in n and 'selftest' in n and n.endswith('.js'): values[n] = gates(values[n].decode('utf-8')).encode('utf-8')
    output.mkdir(parents=True)
    for n, raw in values.items():
        p = output / n; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)
    print(json.dumps({'version': VERSION, 'files': len(values), 'background_sha256': sha(values['background.js']),
                      'content_sha256': sha(values['content-scripts/content.js']), 'main_world_sha256': sha(values['content-scripts/main-world.js'])}, indent=2))
    return values

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--build', nargs=2, metavar=('BASE_36', 'NEW_OUTPUT'), required=True); args = ap.parse_args()
    try: build(*args.build)
    except (ValueError, OSError) as e: raise SystemExit('FAIL-CLOSED: ' + str(e))
