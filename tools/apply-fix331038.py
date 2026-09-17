#!/usr/bin/env python3
"""Hash-locked .36 -> .38 builder (supersedes .37; same .36 baseline). Only --build BASE_36 NEW_OUTPUT.
.38 = .37 diagnostics + ONE gate correction in DPP_REQUIRE_UPLOAD_CONTEXT_V7:
the conversation id is taken from the browser-owned tab URL only (sender.tab.url at the listener,
then chrome.tabs.get in TN and twice more in ASSERT_CURRENT). The stale `sender.url` (frozen at document
commit, never updated by DeepSeek's same-document History navigation) is no longer required to carry
the same conversation id. sender.url is still required, still origin-checked, still top-frame checked.
Nothing else is relaxed: extension id, origin, frameId 0, active lifecycle, documentId, tab id match,
DeepSeek tab origin, conversation-unchanged before/after upload, payload never trusted.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
VERSION = '1.14.0.43'
NAME = '1.14.0 ShunCode MCP Fix 3.3.10.38'

spec = importlib.util.spec_from_file_location('builder37', HERE / 'apply-fix331037.py')
B37 = importlib.util.module_from_spec(spec); spec.loader.exec_module(B37)
sha, once = B37.sha, B37.once

OLD_REQUIRE = ("      typeof context.chatSessionId !== 'string' || !context.chatSessionId ||\n"
               "      vN(context.senderUrl) !== context.chatSessionId)\n"
               "    throw new SN(bN.unauthorizedSender, 'Image upload requires an active top-level conversation document.');")
NEW_REQUIRE = ("      typeof context.chatSessionId !== 'string' || !context.chatSessionId ||\n"
               "      typeof context.senderUrl !== 'string' || !context.senderUrl ||\n"
               "      typeof context.tabUrl !== 'string' || !context.tabUrl)\n"
               "    // .38: conversation identity comes from the browser-owned tab URL only (sender.tab.url at the listener, then\n"
               "    // chrome.tabs.get in TN and in ASSERT_CURRENT before/after upload). sender.url is frozen at document commit and goes\n"
               "    // stale after DeepSeek's same-document navigation, so it stays required and origin/top-frame checked in wN but is\n"
               "    // no longer compared by conversation id. The tab conversation seen at the listener must never change afterwards.\n"
               "    throw new SN(bN.unauthorizedSender, 'Image upload requires an active top-level conversation document.');\n"
               "  if (context.dppListenerChatSessionId === undefined) context.dppListenerChatSessionId = context.chatSessionId;\n"
               "  else if (context.dppListenerChatSessionId !== context.chatSessionId)\n"
               "    throw new SN(bN.unauthorizedSender, 'Image upload conversation changed.');")

def gates(text):
    return (text.replace('1.14.0.41', VERSION)
            .replace('1.14.0 ShunCode MCP Fix 3.3.10.36', NAME)
            .replace('manifest version_name is Fix 3.3.10.36', 'manifest version_name is Fix 3.3.10.38')
            .replace('|32|33|34|35|36)$', '|32|33|34|35|36|37|38)$'))

def transform_background(bg, helper):
    bg = B37.transform_background(bg, helper)
    return once(bg, OLD_REQUIRE, NEW_REQUIRE)

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
    locks = json.loads((HERE / 'fix331038-source-sha256.json').read_text(encoding='utf-8'))
    for n in ['dspp-upload-gate-diag-v9.js', 'apply-fix331037.py']:
        if sha((HERE / n).read_bytes()) != locks[n]: raise ValueError('Source hash mismatch: ' + n)
    helper = (HERE / 'dspp-upload-gate-diag-v9.js').read_bytes()
    values['background.js'] = transform_background(values['background.js'], helper)
    values['content-scripts/content.js'] = B37.transform_content(values['content-scripts/content.js'])
    for n in ['background.js', 'content-scripts/content.js']:
        result = subprocess.run(['node', '--check', '--input-type=module'], input=values[n], capture_output=True)
        if result.returncode: raise ValueError('Node syntax failure: ' + n + ' ' + result.stderr.decode('utf-8', 'replace')[:800])
    mf = once(values['manifest.json'], '"version": "1.14.0.41"', '"version": "' + VERSION + '"')
    values['manifest.json'] = once(mf, '1.14.0 ShunCode MCP Fix 3.3.10.36', NAME)
    for lang in ['en', 'zh_CN']:
        n = '_locales/' + lang + '/messages.json'
        values[n] = once(values[n], 'DeepSeek++ ShunCode MCP Fix 3.3.10.36', 'DeepSeek++ ShunCode MCP Fix 3.3.10.38')
    for n in values:
        if '/' not in n and 'selftest' in n and n.endswith('.js'): values[n] = gates(values[n].decode('utf-8')).encode('utf-8')
    output.mkdir(parents=True)
    for n, raw in values.items():
        p = output / n; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)
    print(json.dumps({'version': VERSION, 'files': len(values), 'background_sha256': sha(values['background.js']),
                      'content_sha256': sha(values['content-scripts/content.js'])}, indent=2))
    return values

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--build', nargs=2, metavar=('BASE_36', 'NEW_OUTPUT'), required=True); args = ap.parse_args()
    try: build(*args.build)
    except (ValueError, OSError) as e: raise SystemExit('FAIL-CLOSED: ' + str(e))
