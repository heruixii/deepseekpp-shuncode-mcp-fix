#!/usr/bin/env python3
"""Hash-locked .36 -> .43 builder (chains .42). Only --build BASE_36 NEW_OUTPUT.

Field evidence: docs/mcp-deepseekpp-fix42-first-run-20260917.md (loop 806d5ac7).
A  fix3-policy.js  auto-degrade trigger 48000 -> 64000. Real ShunCode 15-tool cost is
   49,240 B (gd=1024 per tool), so the .42 line was still crossed.
B  background.js   Zo(): when structuredContent exists, MCP `content[]` image blocks
   are no longer dropped -- they are appended as output.content (type/mimeType/data only,
   whitelisted; only when structuredContent has no own `content`). That key is one
   the v7 collect() walker already visits, so content.js needs no walker change. This is what lets read_image with include_data_uri:false
   still reach the v7 visual channel. Nothing else in Zo() changes.
C  content.js      v7 note text names the two real causes (include_data_uri:false,
   Max Result Bytes) so the model stops concluding "the tool has no vision".
D  content.js      .36 visual rules tell the model to keep include_data_uri at its
   default true and to downsample before reading large originals.
No authorization check is touched.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
VERSION = '1.14.0.48'
NAME = '1.14.0 ShunCode MCP Fix 3.3.10.43'

spec = importlib.util.spec_from_file_location('builder42', HERE / 'apply-fix331042.py')
B42 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B42)
sha, once = B42.sha, B42.once

OLD_TRIGGER = 'triggerBudget=Math.max(48000,adaptiveBudget*2);if(total<=triggerBudget)return settings;'
NEW_TRIGGER = 'triggerBudget=Math.max(64000,adaptiveBudget*2);if(total<=triggerBudget)return settings;'

OLD_ZO = 'function Zo(e){return e.structuredContent===void 0?Array.isArray(e.content)?e.content.map(e=>as(Qo(e))):null:as(e.structuredContent)}'
NEW_ZO = ('function Zo(e){if(e.structuredContent===void 0)return Array.isArray(e.content)?e.content.map(e=>as(Qo(e))):null;'
          'let t=as(e.structuredContent);'
          'if(Array.isArray(e.content)&&t&&typeof t==`object`&&!Array.isArray(t)){'
          'let n=e.content.filter(e=>e&&typeof e==`object`&&e.type===`image`&&typeof e.data==`string`&&typeof e.mimeType==`string`).slice(0,4).map(e=>({type:`image`,mimeType:e.mimeType,data:e.data}));'
          'n.length>0&&t.content===void 0&&(t.content=n)}return t}')

OLD_NOTE = "if (notes.length < 8) notes.push(`read_image visual attachment: ${code} (${count}). Do not claim to have seen an image unless its visual content is actually available.`);"
NEW_NOTE = ("if (notes.length < 8) notes.push(`read_image visual attachment: ${code} (${count}). Do not claim to have seen an image unless its visual content is actually available.`"
            " + (code === 'no_image_data' ? ' Likely cause: include_data_uri was set to false; call read_image again with include_data_uri true (the default).' : '')"
            " + (code === 'tool_failed_or_truncated' ? ' If the error mentions a byte limit, the file exceeds the MCP server Max Result Bytes setting; downsample the image with run_command first (about 600px wide is enough), then read the copy.' : ''));")

OLD_RULES_ZH = '保留真实格式、分辨率和上传限制，不沿用未经证实的128KB通用上限。\';'
NEW_RULES_ZH = ('保留真实格式、分辨率和上传限制，不沿用未经证实的128KB通用上限。调用 read_image 时保持 include_data_uri 为默认 true（传 false 会只剩元数据、看不到画面）；'
                '若返回超出字节上限，先用 run_command 把图缩到约 600px 宽再读缩略副本。\';')
OLD_RULES_EN = "Do not assume an obsolete universal 128KB limit.';"
NEW_RULES_EN = ("Do not assume an obsolete universal 128KB limit. Keep include_data_uri at its default true when calling read_image (false returns metadata only); "
                "if a byte-limit error is returned, downsample with run_command to about 600px wide first and read that copy.';")

OLD_42_TRIGGER_ASSERT = "ok('trigger literal is 48000', polSrc.includes('triggerBudget=Math.max(48000,adaptiveBudget*2)'));"
NEW_42_TRIGGER_ASSERT = "ok('trigger literal is 64000 (Fix 3.3.10.43)', polSrc.includes('triggerBudget=Math.max(64000,adaptiveBudget*2)'));"
OLD_42_BAND_ASSERT = "ok('fixture cost is in the real ShunCode band (30-48 KB)', total > 30000 && total < 48000, String(total));"
NEW_42_BAND_ASSERT = "ok('fixture cost is below the .43 trigger (64 KB)', total > 30000 && total < 64000, String(total));"


def gates(text):
    return (text.replace('1.14.0.47', VERSION)
            .replace('1.14.0 ShunCode MCP Fix 3.3.10.42', NAME)
            .replace('manifest version_name is Fix 3.3.10.42', 'manifest version_name is Fix 3.3.10.43')
            .replace('|36|37|38|39|40|41|42)$', '|36|37|38|39|40|41|42|43)$'))


def build(base, output):
    base = Path(base).resolve()
    output = Path(output).resolve()
    if output.exists() or output == base or base in output.parents:
        raise ValueError('Output must be new and outside baseline')
    staging = output.parent / (output.name + '.stage42')
    if staging.exists():
        raise ValueError('Staging path already exists: ' + str(staging))
    locks = json.loads((HERE / 'fix331043-source-sha256.json').read_text(encoding='utf-8'))
    for n in ['apply-fix331042.py', 'dspp-image-block-v43-selftest.js']:
        if sha((HERE / n).read_bytes()) != locks[n]:
            raise ValueError('Source hash mismatch: ' + n)
    values = B42.build(str(base), str(staging))
    enc = lambda s: s.encode('utf-8') if isinstance(s, str) else s
    pol = values['fix3-policy.js']
    if b'64000' in pol:
        raise ValueError('v43 policy change already present')
    values['fix3-policy.js'] = once(pol, enc(OLD_TRIGGER), enc(NEW_TRIGGER))
    bg = values['background.js']
    if b't.content===void 0&&(t.content=n)' in bg:
        raise ValueError('v43 background change already present')
    values['background.js'] = once(bg, enc(OLD_ZO), enc(NEW_ZO))
    c = values['content-scripts/content.js']
    c = once(c, enc(OLD_NOTE), enc(NEW_NOTE))
    c = once(c, enc(OLD_RULES_ZH), enc(NEW_RULES_ZH))
    c = once(c, enc(OLD_RULES_EN), enc(NEW_RULES_EN))
    values['content-scripts/content.js'] = c
    t = values['dspp-exposure-drift-v42-selftest.js']
    t = once(t, enc(OLD_42_TRIGGER_ASSERT), enc(NEW_42_TRIGGER_ASSERT))
    t = once(t, enc(OLD_42_BAND_ASSERT), enc(NEW_42_BAND_ASSERT))
    values['dspp-exposure-drift-v42-selftest.js'] = t
    for n in ['background.js', 'content-scripts/content.js', 'content-scripts/main-world.js']:
        result = subprocess.run(['node', '--check', '--input-type=module'], input=values[n], capture_output=True)
        if result.returncode:
            raise ValueError('Node syntax failure: ' + n + ' ' + result.stderr.decode('utf-8', 'replace')[:800])
    result = subprocess.run(['node', '--check'], input=values['fix3-policy.js'], capture_output=True)
    if result.returncode:
        raise ValueError('Node syntax failure: fix3-policy.js ' + result.stderr.decode('utf-8', 'replace')[:800])
    mf = once(values['manifest.json'], '"version": "1.14.0.47"', '"version": "' + VERSION + '"')
    values['manifest.json'] = once(mf, '1.14.0 ShunCode MCP Fix 3.3.10.42', NAME)
    for lang in ['en', 'zh_CN']:
        n = '_locales/' + lang + '/messages.json'
        values[n] = once(values[n], 'DeepSeek++ ShunCode MCP Fix 3.3.10.42', 'DeepSeek++ ShunCode MCP Fix 3.3.10.43')
    for n in list(values):
        if '/' not in n and 'selftest' in n and n.endswith('.js'):
            values[n] = gates(values[n].decode('utf-8')).encode('utf-8')
    # .41 suite pins the background hash; re-point from the .42 hash to the .43 hash.
    v41 = values['dspp-bare-tool-tag-v41-selftest.js']
    import re
    m = re.search(rb"bgSha === '([0-9a-f]{64})'", v41)
    if not m:
        raise ValueError('v41 suite background pin not found')
    values['dspp-bare-tool-tag-v41-selftest.js'] = once(v41, m.group(0), b"bgSha === '" + sha(values['background.js']).encode() + b"'")
    values['dspp-image-block-v43-selftest.js'] = (HERE / 'dspp-image-block-v43-selftest.js').read_bytes()
    output.mkdir(parents=True)
    for n, raw in values.items():
        p = output / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
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
