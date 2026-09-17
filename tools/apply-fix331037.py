#!/usr/bin/env python3
"""Hash-locked .36 -> .37 builder. Only --build BASE_36 NEW_OUTPUT; no live install writes.
.37 adds fixed-enum upload-gate rejection diagnostics (background + content). No gate is relaxed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
VERSION = '1.14.0.42'
NAME = '1.14.0 ShunCode MCP Fix 3.3.10.37'

def sha(raw): return hashlib.sha256(raw).hexdigest()

def once(raw, old, new):
    if isinstance(old, str): old = old.encode('utf-8')
    if isinstance(new, str): new = new.encode('utf-8')
    if raw.count(old) != 1:
        alt = old.replace(b'\n', b'\r\n')
        if alt != old and raw.count(alt) == 1:
            return raw.replace(alt, new.replace(b'\n', b'\r\n'), 1)
        raise ValueError('Missing/ambiguous anchor: ' + repr(old[:90]))
    return raw.replace(old, new, 1)

def gates(text):
    return (text.replace('1.14.0.41', VERSION)
            .replace('1.14.0 ShunCode MCP Fix 3.3.10.36', NAME)
            .replace('manifest version_name is Fix 3.3.10.36', 'manifest version_name is Fix 3.3.10.37')
            .replace('|32|33|34|35|36)$', '|32|33|34|35|36|37)$'))

def transform_background(bg, helper):
    nl = b'\r\n' if bg.count(b'\r\n') > bg.count(b'\n') // 2 else b'\n'
    helper = helper.replace(b'\r\n', b'\n').replace(b'\n', nl)
    bg = once(bg, '/* DPP_READIMAGE_V7_BACKGROUND_BEGIN */', helper.rstrip(nl) + nl + b'/* DPP_READIMAGE_V7_BACKGROUND_BEGIN */')
    # Synchronous listener rejections (CN/wN/EN incl. DPP_REQUIRE_UPLOAD_CONTEXT_V7): sender t, context i.
    bg = once(bg, 'catch(e){return n(DN(e,r)),!1}', 'catch(e){return n(DPP_GATE_DIAG_V9(e,r,t,DN(e,r),i)),!1}')
    # Asynchronous rejections (aI/TN after tabs.get).
    bg = once(bg, '.catch(e=>n(e instanceof SN?DN(e,r):gN(r,e,', '.catch(e=>n(e instanceof SN?DPP_GATE_DIAG_V9(e,r,t,DN(e,r),i):gN(r,e,')
    # Dispatch-level SN (assertCurrent before/after upload): attach reason with the normalized context.
    bg = once(bg, "      trusted.stage === 'pow' ? 'pow_failed' : 'upload_failed';\n    return {ok: false, error: code, code};",
              "      trusted.stage === 'pow' ? 'pow_failed' : 'upload_failed';\n    return error instanceof SN ? DPP_GATE_DIAG_V9(error, {type: 'UPLOAD_DEEPSEEK_IMAGE'}, null, {ok: false, error: code, code}, context) : {ok: false, error: code, code};")
    return bg

def transform_content(content):
    # Surface the fixed reason enum + boolean probe into the existing bounded v7 diagnostics; nothing else changes.
    content = once(content,
        "            return finish(new Error(safe.has(code) ? code : 'upload_failed'));",
        "            if (code === 'runtime_message_unauthorized') gateReason(response);\n"
        "            return finish(new Error(safe.has(code) ? code : 'upload_failed'));")
    content = once(content,
        "  function upload(image, timeout) {",
        "  // .37: fixed-enum gate reason from the background; whitelisted keys, booleans/short enums only.\n"
        "  function gateReason(response) {\n"
        "    try {\n"
        "      const reason = typeof response?.reason === 'string' && /^[a-z_]{1,48}$/.test(response.reason) ? response.reason : 'unknown';\n"
        "      const probe = response?.probe && typeof response.probe === 'object' ? response.probe : {};\n"
        "      const fields = {reason};\n"
        "      for (const key of ['frame', 'lifecycle']) if (typeof probe[key] === 'string' && /^[a-z_]{1,24}$/.test(probe[key])) fields[key] = probe[key];\n"
        "      for (const key of ['documentId', 'tab', 'tabUrl', 'senderSession', 'tabSession', 'sameSession', 'ctxSenderSession', 'ctxTabSession', 'ctxSameSession']) if (typeof probe[key] === 'boolean') fields[key] = probe[key];\n"
        "      diag('gate_reason', fields);\n"
        "      if (notes.length < 8) notes.push(`read_image visual attachment: upload authorization rejected (${reason}). This is not retryable within the current page document; report the blocker instead of retrying or shrinking the image.`);\n"
        "    } catch {}\n"
        "  }\n"
        "  function upload(image, timeout) {")
    return content

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
    helper = (HERE / 'dspp-upload-gate-diag-v9.js').read_bytes()
    locks = json.loads((HERE / 'fix331037-source-sha256.json').read_text(encoding='utf-8'))
    if sha(helper) != locks['dspp-upload-gate-diag-v9.js']: raise ValueError('Helper hash mismatch: dspp-upload-gate-diag-v9.js')
    values['background.js'] = transform_background(values['background.js'], helper)
    values['content-scripts/content.js'] = transform_content(values['content-scripts/content.js'])
    for n in ['background.js', 'content-scripts/content.js']:
        result = subprocess.run(['node', '--check', '--input-type=module'], input=values[n], capture_output=True)
        if result.returncode: raise ValueError('Node syntax failure: ' + n + ' ' + result.stderr.decode('utf-8', 'replace')[:800])
    mf = once(values['manifest.json'], '"version": "1.14.0.41"', '"version": "' + VERSION + '"')
    values['manifest.json'] = once(mf, '1.14.0 ShunCode MCP Fix 3.3.10.36', NAME)
    for lang in ['en', 'zh_CN']:
        n = '_locales/' + lang + '/messages.json'
        values[n] = once(values[n], 'DeepSeek++ ShunCode MCP Fix 3.3.10.36', 'DeepSeek++ ShunCode MCP Fix 3.3.10.37')
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
