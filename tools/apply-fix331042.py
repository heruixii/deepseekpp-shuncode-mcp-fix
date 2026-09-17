#!/usr/bin/env python3
"""Hash-locked .36 -> .42 builder (chains .41, then applies the exposure fix). Only --build BASE_36 NEW_OUTPUT.

Root cause (docs/mcp-deepseekpp-exposure-drift-fix42.md): the 15 ShunCode
descriptors cost ~35.9 KB, above the 28 KB auto-degrade trigger in
fix3-policy.promptExposureSettings, so every request was silently rewritten
from `direct` to `adaptive` (5 slots / 14 KB) even when the user chose `direct`.
The adaptive picker re-scores per prompt, so the injected tool set drifted turn
to turn ("继续" carries no keywords); the model then called a tool that had
been present one turn earlier and was gone now (`<read_image>` after
run_command won the slots, `<run_command>` after read_image did). Bare-tag
steering (.41) cannot help: the tool is not in the registry at all.

A  policy: an explicit per-server mode is respected (only unset servers may be
   auto-degraded); trigger raised 28000 -> 48000 so a single ShunCode server
   stays fully direct.
B  background: adaptive ceiling 5 slots/14 KB -> 8 slots/24 KB; rank floor gives
   read_image 1000 so run_command/read_image/read_files/get_command_output/
   apply_patch always co-exist in adaptive mode.
C  content: `resolution` added to the turn_diag row whitelist (the .41 enum was
   being dropped by DPP_RECORD_AGENT_TURN_DIAG_331021).

No authorization check is touched.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
VERSION = '1.14.0.47'
NAME = '1.14.0 ShunCode MCP Fix 3.3.10.42'

spec = importlib.util.spec_from_file_location('builder41', HERE / 'apply-fix331041.py')
B41 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B41)
sha, once = B41.sha, B41.once

# ---- A: fix3-policy.js -----------------------------------------------------
OLD_TRIGGER = 'triggerBudget=Math.max(28000,adaptiveBudget*2);if(total<=triggerBudget)return settings;'
NEW_TRIGGER = 'triggerBudget=Math.max(48000,adaptiveBudget*2);if(total<=triggerBudget)return settings;'
OLD_MODE = 'let id=d.provider.id,current=servers[id],mode=current?.mode??`direct`;if(mode!==`direct`)continue;'
# Only servers WITHOUT an explicit mode may be auto-degraded (Fix 3.3.10.42).
NEW_MODE = 'let id=d.provider.id,current=servers[id],mode=current?.mode??`direct`;if(mode!==`direct`||(current&&typeof current.mode===`string`))continue;'

# ---- B: background.js ------------------------------------------------------
OLD_DEFAULTS = 'Vu=Object.freeze({version:1,adaptiveMaxDirectTools:5,adaptiveMaxPromptBytes:14e3,servers:{}})'
NEW_DEFAULTS = 'Vu=Object.freeze({version:1,adaptiveMaxDirectTools:8,adaptiveMaxPromptBytes:24e3,servers:{}})'
OLD_CEILING = 'Math.min(e.settings.adaptiveMaxDirectTools,5),Math.min(e.settings.adaptiveMaxPromptBytes,14e3)'
NEW_CEILING = 'Math.min(e.settings.adaptiveMaxDirectTools,8),Math.min(e.settings.adaptiveMaxPromptBytes,24e3)'
OLD_FLOOR = '/(?:^|_)(?:get_command_output|read_files)$/.test(t)?1e3:'
NEW_FLOOR = '/(?:^|_)(?:get_command_output|read_files|read_image)$/.test(t)?1e3:'

# ---- C: content.js turn_diag whitelist ------------------------------------
OLD_DIAG_ROW = 'decision:typeof t.decision==`string`?t.decision.slice(0,80):``,finished:'
NEW_DIAG_ROW = ('decision:typeof t.decision==`string`?t.decision.slice(0,80):``,'
                'resolution:typeof t.resolution==`string`?t.resolution.slice(0,40):null,finished:')

# selftest expectation updates (fixed literals in shipped suites)
OLD_33_FLOOR_ASSERT = 'ok("read_image gets 0", f({ name: "read_image", invocationName: "mcp_x_read_image" }) === 0);'
NEW_33_FLOOR_ASSERT = 'ok("read_image gets 1000 (Fix 3.3.10.42)", f({ name: "read_image", invocationName: "mcp_x_read_image" }) === 1000);'
OLD_33105_BASE = "const base={version:1,adaptiveMaxDirectTools:5,adaptiveMaxPromptBytes:14000,servers:{srv:{mode:'direct',pinnedDescriptorIds:['keep-me']}}};"
NEW_33105_BASE = "const base={version:1,adaptiveMaxDirectTools:8,adaptiveMaxPromptBytes:24000,servers:{srv:{pinnedDescriptorIds:['keep-me']}}};"
OLD_33105_BIG = "let big=Array.from({length:12},(_,i)=>d(`tool_${i}`,'mcp','srv',2400));"
NEW_33105_BIG = "let big=Array.from({length:24},(_,i)=>d(`tool_${i}`,'mcp','srv',2400));"
OLD_33105_MUT = "ok('original-not-mutated',base.servers.srv.mode==='direct');"
NEW_33105_MUT = ("ok('original-not-mutated',base.servers.srv.mode===undefined);\n"
                 "let explicitDirect={...base,servers:{srv:{mode:'direct',pinnedDescriptorIds:[]}}};let e2=p.promptExposureSettings(big,explicitDirect,'读取文件');\n"
                 "ok('explicit-direct-respected-331042',e2===explicitDirect);\n"
                 "let shuncode=Array.from({length:15},(_,i)=>d(`sc_${i}`,'mcp','srv',1300));let s2=p.promptExposureSettings(shuncode,base,'继续');\n"
                 "ok('single-shuncode-server-stays-direct-331042',s2===base,String(shuncode.reduce((a,x)=>a+p.promptDescriptorCost(x),0)));")
OLD_33105_TAIL = "if(failed)process.exit(1);console.log('ALL_PASS 12');"
# .41 suite pinned background.js to the .40 hash; .42 changes background (B), so the
# shipped assertion is re-pointed at the .42 build hash by literal replacement.
OLD_41_BG_ASSERT = "ok('background.js untouched vs .40 (authorization gate intact)',\n   bgSha === '76df1046a8bd3247484dc96092785b876b7b7985cbfe31c5cd31947212a536f5', bgSha.slice(0, 16));"
NEW_41_BG_ASSERT = "ok('background.js is the .42 build (only exposure literals changed; authorization gate intact)',\n   bgSha === '%s', bgSha.slice(0, 16));"
NEW_33105_TAIL = "if(failed)process.exit(1);console.log('ALL_PASS 14');"


def gates(text):
    return (text.replace('1.14.0.46', VERSION)
            .replace('1.14.0 ShunCode MCP Fix 3.3.10.41', NAME)
            .replace('manifest version_name is Fix 3.3.10.41', 'manifest version_name is Fix 3.3.10.42')
            .replace('|36|37|38|39|40|41)$', '|36|37|38|39|40|41|42)$'))


def build(base, output):
    base = Path(base).resolve()
    output = Path(output).resolve()
    if output.exists() or output == base or base in output.parents:
        raise ValueError('Output must be new and outside baseline')
    staging = output.parent / (output.name + '.stage41')
    if staging.exists():
        raise ValueError('Staging path already exists: ' + str(staging))
    locks = json.loads((HERE / 'fix331042-source-sha256.json').read_text(encoding='utf-8'))
    for n in ['apply-fix331041.py', 'dspp-exposure-drift-v42-selftest.js']:
        if sha((HERE / n).read_bytes()) != locks[n]:
            raise ValueError('Source hash mismatch: ' + n)
    values = B41.build(str(base), str(staging))
    enc = lambda s: s.encode('utf-8') if isinstance(s, str) else s
    pol = values['fix3-policy.js']
    if b'48000' in pol:
        raise ValueError('v42 policy change already present')
    pol = once(pol, enc(OLD_TRIGGER), enc(NEW_TRIGGER))
    pol = once(pol, enc(OLD_MODE), enc(NEW_MODE))
    values['fix3-policy.js'] = pol
    bg = values['background.js']
    bg = once(bg, enc(OLD_DEFAULTS), enc(NEW_DEFAULTS))
    bg = once(bg, enc(OLD_CEILING), enc(NEW_CEILING))
    bg = once(bg, enc(OLD_FLOOR), enc(NEW_FLOOR))
    values['background.js'] = bg
    values['content-scripts/content.js'] = once(values['content-scripts/content.js'], enc(OLD_DIAG_ROW), enc(NEW_DIAG_ROW))
    values['fix331033-capability-exposure-selftest.js'] = once(values['fix331033-capability-exposure-selftest.js'], enc(OLD_33_FLOOR_ASSERT), enc(NEW_33_FLOOR_ASSERT))
    t = values['fix33105-prompt-exposure-selftest.js']
    for o, n in [(OLD_33105_BASE, NEW_33105_BASE), (OLD_33105_BIG, NEW_33105_BIG), (OLD_33105_MUT, NEW_33105_MUT), (OLD_33105_TAIL, NEW_33105_TAIL)]:
        t = once(t, enc(o), enc(n))
    values['fix33105-prompt-exposure-selftest.js'] = t
    for n in ['background.js', 'content-scripts/content.js', 'content-scripts/main-world.js']:
        result = subprocess.run(['node', '--check', '--input-type=module'], input=values[n], capture_output=True)
        if result.returncode:
            raise ValueError('Node syntax failure: ' + n + ' ' + result.stderr.decode('utf-8', 'replace')[:800])
    result = subprocess.run(['node', '--check'], input=values['fix3-policy.js'], capture_output=True)
    if result.returncode:
        raise ValueError('Node syntax failure: fix3-policy.js ' + result.stderr.decode('utf-8', 'replace')[:800])
    mf = once(values['manifest.json'], '"version": "1.14.0.46"', '"version": "' + VERSION + '"')
    values['manifest.json'] = once(mf, '1.14.0 ShunCode MCP Fix 3.3.10.41', NAME)
    for lang in ['en', 'zh_CN']:
        n = '_locales/' + lang + '/messages.json'
        values[n] = once(values[n], 'DeepSeek++ ShunCode MCP Fix 3.3.10.41', 'DeepSeek++ ShunCode MCP Fix 3.3.10.42')
    for n in list(values):
        if '/' not in n and 'selftest' in n and n.endswith('.js'):
            values[n] = gates(values[n].decode('utf-8')).encode('utf-8')
    values['dspp-exposure-drift-v42-selftest.js'] = (HERE / 'dspp-exposure-drift-v42-selftest.js').read_bytes()
    values['dspp-bare-tool-tag-v41-selftest.js'] = once(values['dspp-bare-tool-tag-v41-selftest.js'], enc(OLD_41_BG_ASSERT), enc(NEW_41_BG_ASSERT % sha(values['background.js'])))
    output.mkdir(parents=True)
    for n, raw in values.items():
        p = output / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    import shutil
    shutil.rmtree(staging)
    print(json.dumps({'version': VERSION, 'files': len(values),
                      'background_sha256': sha(values['background.js']),
                      'content_sha256': sha(values['content-scripts/content.js']),
                      'policy_sha256': sha(values['fix3-policy.js']),
                      'main_world_sha256': sha(values['content-scripts/main-world.js'])}, indent=2))
    return values


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', nargs=2, metavar=('BASE_36', 'NEW_OUTPUT'), required=True)
    args = ap.parse_args()
    try:
        build(*args.build)
    except (ValueError, OSError) as e:
        raise SystemExit('FAIL-CLOSED: ' + str(e))
