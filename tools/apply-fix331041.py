#!/usr/bin/env python3
"""Hash-locked .36 -> .41 builder (chains .40, then applies the bare-tool-tag fix). Only --build BASE_36 NEW_OUTPUT.

Root cause (docs/mcp-deepseekpp-bare-tool-tag-fix41.md): MCP tools register as
`mcp_t_<serverId>_<base>`. The model kept emitting a bare <read_image>; the .33
detector flagged it unregistered and the steering told it to mcp_discover even
though the tool was already in the catalogue, while the .36 visual prompts also
named `read_image` bare. The instructions contradicted each other, the run burned
its 3 tool-intent nudges and stopped with unexecuted_work_limit_331036.

A  steering names the exact registered tag when a unique `mcp_t_*_<base>` exists.
B  visual rules/retry inject the real read_image invocation name.
C  unregistered_tool_tag_331033 records resolution: exact_hint|discover_hint|ambiguous.
D  (bare-tag aliasing / auto-execute) deliberately NOT done.

No authorization check is touched.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
VERSION = '1.14.0.46'
NAME = '1.14.0 ShunCode MCP Fix 3.3.10.41'

spec = importlib.util.spec_from_file_location('builder40', HERE / 'apply-fix331040.py')
B40 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B40)
sha, once = B40.sha, B40.once

# ---- A: steering signature + exact-tag branch ----------------------------
OLD_STEER = 'function DPP_UNREGISTERED_TAG_STEERING_331033(e,t){return String(e??``)'
# This function is extracted and eval'd standalone by the v8 suite too, so both
# the resolution and the exact-hint text must be fully inline here.
NEW_STEER = ('function DPP_UNREGISTERED_TAG_STEERING_331033(e,t,n){'
             'let zb=String(t??``).toLowerCase(),zs=`_`+zb,zh=[];'
             'if(zb&&n&&typeof n.forEach===`function`)n.forEach((_v,k)=>{'
             'let s2=String(k||``),l2=s2.toLowerCase();'
             'if(l2.length>zs.length&&l2.indexOf(`mcp_t_`)===0&&l2.slice(-zs.length)===zs&&zh.indexOf(s2)===-1)zh.push(s2)});'
             'if(zh.length===1){let zf=zh[0];'
             'return String(e??``).toLowerCase().startsWith(`zh`)'
             '?`[Fix 3.3.10.41 \\u5de5\\u5177\\u6807\\u7b7e\\u7ea0\\u6b63] \\u4f60\\u4e0a\\u4e00\\u8f6e\\u8f93\\u51fa\\u7684 <${t}> \\u4e0d\\u662f\\u53ef\\u7528\\u6807\\u7b7e\\uff0c\\u5df2\\u88ab\\u5ffd\\u7565\\u3001\\u672a\\u6267\\u884c\\u3002\\u8be5\\u5de5\\u5177\\u5f53\\u524d\\u5df2\\u6ce8\\u518c\\u4e3a <${zf}>\\uff0c\\u5c31\\u5728\\u5f53\\u524d\\u5de5\\u5177\\u76ee\\u5f55\\u91cc\\u3002\\u4e0b\\u4e00\\u8f6e\\u8bf7\\u76f4\\u63a5\\u7528 <${zf}> \\u8c03\\u7528\\uff08\\u53c2\\u6570\\u7ed3\\u6784\\u4e0d\\u53d8\\uff09\\uff0c\\u4e0d\\u8981\\u518d\\u7528 mcp_discover\\uff0c\\u4e5f\\u4e0d\\u8981\\u518d\\u8f93\\u51fa <${t}>\\u3002`'
             ':`[Fix 3.3.10.41 tool tag correction] Your previous turn emitted <${t}>, which is not an available tag; it was ignored and nothing executed. That tool is already registered as <${zf}> and is present in the current catalogue. In the very next turn call <${zf}> directly with the same arguments. Do not call mcp_discover, and do not emit <${t}> again.`}'
             'return String(e??``)')

OLD_STEER_CALL = 'DPP_UNREGISTERED_TAG_STEERING_331033(d,y.unregisteredTag)'
NEW_STEER_CALL = 'DPP_UNREGISTERED_TAG_STEERING_331033(d,y.unregisteredTag,v)'

# ---- C: resolution enum in the diagnostic row ----------------------------
OLD_DIAG = ('DPPUnregTag331033&&DPP_RECORD_AGENT_TURN_DIAG_331021({stage:`unregistered_tool_tag_331033`,'
            'loopId:a,chatSessionId:s,stepIndex:b,turnIndex:ue,responseMessageId:h(),')
# shouldStopAfterTurn is ALSO extracted and eval'd standalone by the v8 suite,
# so the resolution enum must be computed inline here too (no external helper).
INLINE_RESOLVE = ('(()=>{let z=String(DPPUnregTag331033||``).toLowerCase(),zs=`_`+z,zh=[];'
                  'if(z){v.forEach((_v,k)=>{let s2=String(k||``),l2=s2.toLowerCase();'
                  'if(l2.length>zs.length&&l2.indexOf(`mcp_t_`)===0&&l2.slice(-zs.length)===zs&&zh.indexOf(s2)===-1)zh.push(s2)})}'
                  'return zh.length===1?`exact_hint`:zh.length>1?`ambiguous`:`discover_hint`})()')

NEW_DIAG = ('DPPUnregTag331033&&DPP_RECORD_AGENT_TURN_DIAG_331021({stage:`unregistered_tool_tag_331033`,'
            'resolution:' + INLINE_RESOLVE + ','
            'loopId:a,chatSessionId:s,stepIndex:b,turnIndex:ue,responseMessageId:h(),')

# ---- B: visual prompts carry the real invocation name --------------------
OLD_RULES_SIG = 'function DPP_VISUAL_RULES_331036(value, locale) {\n  const intent = DPP_VISUAL_INTENT_331036(value);\n  if (!intent) return \'\';'
# NOTE: the v8 selftest extracts these two functions and evaluates them in an
# isolated context, so the phrase must be computed INLINE -- referencing
# DPP_VISUAL_NAME_PHRASE_V41 here would throw ReferenceError there.
NEW_RULES_SIG = ('function DPP_VISUAL_RULES_331036(value, locale, readImageName) {\n'
                 '  const intent = DPP_VISUAL_INTENT_331036(value);\n'
                 '  if (!intent) return \'\';\n'
                 '  const RI = String(readImageName || \'\') ? \'`\' + String(readImageName) + \'` (read_image)\' : \'read_image\';')

OLD_RETRY_SIG = 'function DPP_VISUAL_RETRY_331036(locale) {\n  return String(locale || \'\').toLowerCase().startsWith(\'zh\')'
NEW_RETRY_SIG = ('function DPP_VISUAL_RETRY_331036(locale, readImageName) {\n'
                 '  const RI = String(readImageName || \'\') ? \'`\' + String(readImageName) + \'` (read_image)\' : \'read_image\';\n'
                 '  return String(locale || \'\').toLowerCase().startsWith(\'zh\')')

# Replace the bare occurrences inside the four prompt literals with ${RI}.
RULES_ZH_OLD = '\u53c2\u8003\u56fe\u4efb\u52a1\u5148\u4f7f\u7528\u5f53\u524d\u5de5\u5177\u76ee\u5f55\u4e2d\u771f\u5b9e\u53ef\u7528\u7684 read_image \u68c0\u67e5\u6307\u5b9a\u53c2\u8003\u56fe'
RULES_ZH_NEW = '\u53c2\u8003\u56fe\u4efb\u52a1\u5148\u4f7f\u7528\u5f53\u524d\u5de5\u5177\u76ee\u5f55\u4e2d\u771f\u5b9e\u53ef\u7528\u7684 \' + RI + \' \u68c0\u67e5\u6307\u5b9a\u53c2\u8003\u56fe'
RULES_EN_OLD = 'Proactively inspect the specified reference using an available read_image tool'
RULES_EN_NEW = 'Proactively inspect the specified reference using \' + RI + \''
RETRY_ZH_OLD = '\u672c\u8f6e\u5c1a\u65e0\u6210\u529f read_image \u7ed3\u679c\uff0c\u9700\u8981\u5148\u6838\u5b9e\u672c\u4efb\u52a1\u7684\u53c2\u8003\u56fe\u3002\u5148\u6309\u771f\u5b9e schema \u8c03\u7528 read_image\uff1b'
RETRY_ZH_NEW = '\u672c\u8f6e\u5c1a\u65e0\u6210\u529f read_image \u7ed3\u679c\uff0c\u9700\u8981\u5148\u6838\u5b9e\u672c\u4efb\u52a1\u7684\u53c2\u8003\u56fe\u3002\u5148\u6309\u771f\u5b9e schema \u8c03\u7528 \' + RI + \'\uff1b'
RETRY_EN_OLD = 'Invoke read_image using its real schema'
RETRY_EN_NEW = 'Invoke \' + RI + \' using its real schema'

# Call sites: resolve the name from the descriptor map / registry.
# vo() is extracted and eval'd standalone by the v8 suite as well, so the
# read_image lookup here must be inline too (no DPP_VISUAL_TOOL_NAME_V41 ref).
INLINE_RI_FROM_DESCRIPTORS = ('(()=>{let zh=[];for(let z of(f||[])){let s2=String(z&&z.invocationName||``),l2=s2.toLowerCase();'
                              'if(l2.length>11&&l2.indexOf(`mcp_t_`)===0&&l2.slice(-11)===`_read_image`&&zh.indexOf(s2)===-1)zh.push(s2)}'
                              'return zh.length===1?zh[0]:``})()')

OLD_RULES_CALL = 'u?DPP_VISUAL_RULES_331036(t?.visibleUserPrompt??e,c):``'
NEW_RULES_CALL = ('u?DPP_VISUAL_RULES_331036(t?.visibleUserPrompt??e,c,'
                  + INLINE_RI_FROM_DESCRIPTORS + '):``')
# Same for the steering call site (inside the eval'd shouldStopAfterTurn region).
INLINE_RI_FROM_REGISTRY = ('(()=>{let zh=[];v.forEach((_v,k)=>{let s2=String(k||``),l2=s2.toLowerCase();'
                           'if(l2.length>11&&l2.indexOf(`mcp_t_`)===0&&l2.slice(-11)===`_read_image`&&zh.indexOf(s2)===-1)zh.push(s2)});'
                           'return zh.length===1?zh[0]:``})()')

OLD_RETRY_CALL = 'DPP_VISUAL_RETRY_331036(d)'
NEW_RETRY_CALL = 'DPP_VISUAL_RETRY_331036(d,' + INLINE_RI_FROM_REGISTRY + ')'


def gates(text):
    return (text.replace('1.14.0.45', VERSION)
            .replace('1.14.0 ShunCode MCP Fix 3.3.10.40', NAME)
            .replace('manifest version_name is Fix 3.3.10.40', 'manifest version_name is Fix 3.3.10.41')
            .replace('|36|37|38|39|40)$', '|36|37|38|39|40|41)$'))


def transform_content(raw, helpers):
    """All patches are applied on bytes: the shared once() helper is bytes-based."""
    marker = b'/* DPP_VISUAL_WORKFLOW_V8_END */'
    if raw.count(marker) != 1:
        raise ValueError('visual workflow marker not unique')
    if b'DPP_BARE_TOOL_TAG_V41_BEGIN' in raw:
        raise ValueError('v41 block already present')
    block = helpers.strip()
    enc = lambda s: s.encode('utf-8') if isinstance(s, str) else s
    pairs = [
        (OLD_STEER, NEW_STEER), (OLD_STEER_CALL, NEW_STEER_CALL), (OLD_DIAG, NEW_DIAG),
        (OLD_RULES_SIG, NEW_RULES_SIG), (OLD_RETRY_SIG, NEW_RETRY_SIG),
        (RULES_ZH_OLD, RULES_ZH_NEW), (RULES_EN_OLD, RULES_EN_NEW),
        (RETRY_ZH_OLD, RETRY_ZH_NEW), (RETRY_EN_OLD, RETRY_EN_NEW),
        (OLD_RULES_CALL, NEW_RULES_CALL), (OLD_RETRY_CALL, NEW_RETRY_CALL),
    ]
    for o, n in pairs:
        raw = once(raw, enc(o), enc(n))
    raw = once(raw, marker, marker + b'\n' + block + b'\n')
    return raw


def build(base, output):
    base = Path(base).resolve()
    output = Path(output).resolve()
    if output.exists() or output == base or base in output.parents:
        raise ValueError('Output must be new and outside baseline')
    staging = output.parent / (output.name + '.stage40')
    if staging.exists():
        raise ValueError('Staging path already exists: ' + str(staging))
    locks = json.loads((HERE / 'fix331041-source-sha256.json').read_text(encoding='utf-8'))
    for n in ['apply-fix331040.py', 'dspp-bare-tool-tag-v41.js', 'dspp-bare-tool-tag-v41-selftest.js']:
        if sha((HERE / n).read_bytes()) != locks[n]:
            raise ValueError('Source hash mismatch: ' + n)
    # chain: produce the .40 tree first, reusing its own hash-locked builder
    values = B40.build(str(base), str(staging))
    helpers = (HERE / 'dspp-bare-tool-tag-v41.js').read_bytes()
    values['content-scripts/content.js'] = transform_content(values['content-scripts/content.js'], helpers)
    for n in ['background.js', 'content-scripts/content.js', 'content-scripts/main-world.js']:
        result = subprocess.run(['node', '--check', '--input-type=module'], input=values[n], capture_output=True)
        if result.returncode:
            raise ValueError('Node syntax failure: ' + n + ' ' + result.stderr.decode('utf-8', 'replace')[:800])
    mf = once(values['manifest.json'], '"version": "1.14.0.45"', '"version": "' + VERSION + '"')
    values['manifest.json'] = once(mf, '1.14.0 ShunCode MCP Fix 3.3.10.40', NAME)
    for lang in ['en', 'zh_CN']:
        n = '_locales/' + lang + '/messages.json'
        values[n] = once(values[n], 'DeepSeek++ ShunCode MCP Fix 3.3.10.40', 'DeepSeek++ ShunCode MCP Fix 3.3.10.41')
    for n in list(values):
        if '/' not in n and 'selftest' in n and n.endswith('.js'):
            values[n] = gates(values[n].decode('utf-8')).encode('utf-8')
    values['dspp-bare-tool-tag-v41-selftest.js'] = (HERE / 'dspp-bare-tool-tag-v41-selftest.js').read_bytes()
    output.mkdir(parents=True)
    for n, raw in values.items():
        p = output / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    # staging tree was only an intermediate; remove it so it is never mistaken for a release
    import shutil
    shutil.rmtree(staging)
    print(json.dumps({'version': VERSION, 'files': len(values),
                      'background_sha256': sha(values['background.js']),
                      'content_sha256': sha(values['content-scripts/content.js']),
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
