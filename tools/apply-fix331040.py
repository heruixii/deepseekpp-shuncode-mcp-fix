#!/usr/bin/env python3
"""Hash-locked .36 -> .40 builder (= .39 runtime + one MAIN-world startup-race fix). Only --build BASE_36 NEW_OUTPUT.
Fix: skill-popup `go()` called `Y.observe(document.body, ...)` while document.body was still null
(main-world runs at document_start; SYNC_HOOK_STATE can arrive before <body>) ->
'Failed to execute observe on MutationObserver: parameter 1 is not of type Node'. Now observes immediately when body
exists, otherwise defers to DOMContentLoaded (once) and re-runs the textarea lookup. No gate/bridge/tool logic touched.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
VERSION = '1.14.0.45'
NAME = '1.14.0 ShunCode MCP Fix 3.3.10.40'

spec = importlib.util.spec_from_file_location('builder39', HERE / 'apply-fix331039.py')
B39 = importlib.util.module_from_spec(spec); spec.loader.exec_module(B39)
sha, once = B39.sha, B39.once

OLD_OBSERVE = 'Y.observe(document.body,{childList:!0,subtree:!0})'
NEW_OBSERVE = ('document.body?Y.observe(document.body,{childList:!0,subtree:!0}):'
               'document.addEventListener(`DOMContentLoaded`,()=>{Y&&document.body&&Y.observe(document.body,{childList:!0,subtree:!0}),_o()},{once:!0})')

def gates(text):
    return (text.replace('1.14.0.41', VERSION)
            .replace('1.14.0 ShunCode MCP Fix 3.3.10.36', NAME)
            .replace('manifest version_name is Fix 3.3.10.36', 'manifest version_name is Fix 3.3.10.40')
            .replace('|32|33|34|35|36)$', '|32|33|34|35|36|37|38|39|40)$'))

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
    locks = json.loads((HERE / 'fix331040-source-sha256.json').read_text(encoding='utf-8'))
    for n in ['dspp-upload-gate-diag-v9.js', 'apply-fix331037.py', 'apply-fix331038.py', 'apply-fix331039.py', 'dspp-mw-bridge-diag-v10.js']:
        if sha((HERE / n).read_bytes()) != locks[n]: raise ValueError('Source hash mismatch: ' + n)
    values['background.js'] = B39.B38.transform_background(values['background.js'], (HERE / 'dspp-upload-gate-diag-v9.js').read_bytes())
    values['content-scripts/content.js'] = B39.B38.B37.transform_content(values['content-scripts/content.js'])
    mw = B39.transform_main_world(values['content-scripts/main-world.js'], (HERE / 'dspp-mw-bridge-diag-v10.js').read_bytes())
    values['content-scripts/main-world.js'] = once(mw, OLD_OBSERVE, NEW_OBSERVE)
    for n in ['background.js', 'content-scripts/content.js', 'content-scripts/main-world.js']:
        result = subprocess.run(['node', '--check', '--input-type=module'], input=values[n], capture_output=True)
        if result.returncode: raise ValueError('Node syntax failure: ' + n + ' ' + result.stderr.decode('utf-8', 'replace')[:800])
    mf = once(values['manifest.json'], '"version": "1.14.0.41"', '"version": "' + VERSION + '"')
    values['manifest.json'] = once(mf, '1.14.0 ShunCode MCP Fix 3.3.10.36', NAME)
    for lang in ['en', 'zh_CN']:
        n = '_locales/' + lang + '/messages.json'
        values[n] = once(values[n], 'DeepSeek++ ShunCode MCP Fix 3.3.10.36', 'DeepSeek++ ShunCode MCP Fix 3.3.10.40')
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
