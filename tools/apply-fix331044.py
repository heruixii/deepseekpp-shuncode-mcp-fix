#!/usr/bin/env python3
"""Hash-locked .36 -> .44 builder (chains .43). Only --build BASE_36 NEW_OUTPUT.

Field evidence: docs/mcp-deepseekpp-fix43-first-run-20260918.md (.43 first run, 2026-09-17 22:45-23:52).
A  fix3-policy.js  promptExposureSettings counted EVERY enabled descriptor -- the 9 built-in
   local tools (memory/web/artifact/skill/import, ~17.3 KB) as well as the MCP tools -- against
   the 64,000-byte auto-degrade trigger. ShunCode alone is 49,240 B, but 49,240 + 17,319 = 66,559
   > 64,000, so the agent path (background sz()) still rewrote the single ShunCode server from
   `direct` to `adaptive` (8 slots): descriptorCount 20 instead of 24, find_files & co. missing.
   The manual-chat path (vz()) never applies the policy, which is why descriptorCount 24 rows
   coexist with 20 rows in the same log. Built-in tools are injected regardless of the MCP
   exposure mode, so they must not count toward a budget whose only remedy is compacting MCP
   servers. .44 counts MCP descriptors only.
B  content.js      DeepSeek answered 23:42:50 / 23:43:07 / 23:51:07 with an empty stream whose only
   marker was finish_reason=rate_limit_reached. The agent could not see that marker: HR() treated
   the empty stream as a transient empty EOF and replayed the request (burning quota), and the run
   then died with an unrelated "JSON instead of SSE / invalid message id" text. .44 surfaces
   finish_reason in the stream diag frames and provider_terminal rows, and an empty attempt whose
   stream said rate_limit_reached stops the run immediately with an explicit rate-limit message.
No authorization check is touched. background.js and main-world.js are byte-identical to .43.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
VERSION = '1.14.0.49'
NAME = '1.14.0 ShunCode MCP Fix 3.3.10.44'

spec = importlib.util.spec_from_file_location('builder43', HERE / 'apply-fix331043.py')
B43 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B43)
sha, once = B43.sha, B43.once

# ---- A: fix3-policy.js -- only MCP descriptors count toward the auto-degrade trigger --------
OLD_TOTAL = ('let enabled=descriptors.filter(d=>d?.execution?.enabled!==false),'
             'total=enabled.reduce((sum,d)=>sum+promptDescriptorCost(d),0),')
NEW_TOTAL = ('let enabled=descriptors.filter(d=>d?.execution?.enabled!==false&&d?.provider?.kind===`mcp`&&!!d.provider.id),'
             'total=enabled.reduce((sum,d)=>sum+promptDescriptorCost(d),0),')

# ---- B: content.js -- finish_reason visibility + explicit rate-limit stop -----------------
# B1 stream diag frames carry `finish` (fixed enum, /^[a-z_]{1,40}$/) when a parsed SSE frame
#    carries finish_reason; two pure helpers are added next to the frame builder.
OLD_FRAME = 't.length&&(n.batch=t)}return n}function DPP_STREAM_DIAG_PUSH_33('
NEW_FRAME = ('t.length&&(n.batch=t)}let DPPFinish331044=typeof DPP_FINISH_REASON_331044==`function`?DPP_FINISH_REASON_331044(e):null;'
             'DPPFinish331044&&(n.finish=DPPFinish331044);return n}'
             'function DPP_FINISH_REASON_331044(e,t=0){if(t>3||e==null||typeof e!=`object`)return null;'
             'if(Array.isArray(e)){for(let n of e.slice(0,16)){let r=DPP_FINISH_REASON_331044(n,t+1);if(r)return r}return null}'
             'if(typeof e.finish_reason==`string`&&/^[a-z_]{1,40}$/i.test(e.finish_reason))return e.finish_reason.toLowerCase();'
             'return DPP_FINISH_REASON_331044(e.v,t+1)||DPP_FINISH_REASON_331044(e.error,t+1)}'
             'function DPP_LAST_FINISH_REASON_331044(e){if(!Array.isArray(e))return null;'
             'for(let t=e.length-1;t>=0;t--){let n=e[t]?.finish;if(typeof n==`string`&&n)return n}return null}'
             'function DPP_STREAM_DIAG_PUSH_33(')
# B2 HR(): an empty attempt whose stream said finish_reason=rate_limit_reached is not replayed
#    (the .33 empty-EOF retry) -- it throws a clear, non-retryable rate-limit error at once.
OLD_HR = ('s.dppAttempt=n,s.dppFreshPow=n>1&&typeof r==`function`;'
          'let c=!s.finished&&!a&&s.responseMessageId==null&&s.requestMessageId==null&&n<zR;')
NEW_HR = ('s.dppAttempt=n,s.dppFreshPow=n>1&&typeof r==`function`;'
          'if(!a&&typeof DPP_LAST_FINISH_REASON_331044==`function`&&DPP_LAST_FINISH_REASON_331044(s.dppStreamEvents)===`rate_limit_reached`){'
          'let DPPRateErr331044=Error(DPP_RATE_LIMIT_STOP_331044(typeof navigator==`object`&&navigator?navigator.language:``));'
          'DPPRateErr331044.dppNoRetry337=!0,DPPRateErr331044.dppRateLimited331044=!0;throw DPPRateErr331044}'
          'let c=!s.finished&&!a&&s.responseMessageId==null&&s.requestMessageId==null&&n<zR;')
# B3 provider_terminal diag rows record finishReason (whitelisted string, <=40 chars).
OLD_TERMINAL = 'e.onAgentStreamTerminal?.({finished:ie?.finished===!0,responseMessageId:ie?.responseMessageId??null,'
NEW_TERMINAL = ('e.onAgentStreamTerminal?.({finished:ie?.finished===!0,'
                'finishReason:typeof DPP_LAST_FINISH_REASON_331044==`function`?DPP_LAST_FINISH_REASON_331044(ie?.streamEvents):null,'
                'responseMessageId:ie?.responseMessageId??null,')
OLD_WHITELIST = 'resolution:typeof t.resolution==`string`?t.resolution.slice(0,40):null,finished:'
NEW_WHITELIST = ('resolution:typeof t.resolution==`string`?t.resolution.slice(0,40):null,'
                 'finishReason:typeof t.finishReason==`string`?t.finishReason.slice(0,40):null,finished:')
# B4 user-facing message (zh/en), placed next to the .25 generic-limit message.
OLD_MESSAGE = 'function DPP_GENERIC_NUDGE_LIMIT_331025(e,t){'
NEW_MESSAGE = ('function DPP_RATE_LIMIT_STOP_331044(e){return String(e??``).toLowerCase().startsWith(`zh`)?'
               '`DeepSeek 返回 finish_reason=rate_limit_reached（当前账号/会话已被限流），DeepSeek++ 已安全停止本轮，避免继续消耗配额；请等待几分钟后发送“继续”从 checkpoint 续跑。`:'
               '`DeepSeek returned finish_reason=rate_limit_reached (the account or session is rate limited). DeepSeek++ stopped this run safely instead of burning more quota; wait a few minutes, then send "continue" to resume from the checkpoint.`}'
               'function DPP_GENERIC_NUDGE_LIMIT_331025(e,t){')
CONTENT_EDITS = [(OLD_FRAME, NEW_FRAME), (OLD_HR, NEW_HR), (OLD_TERMINAL, NEW_TERMINAL),
                 (OLD_WHITELIST, NEW_WHITELIST), (OLD_MESSAGE, NEW_MESSAGE)]

def gates(text):
    return (text.replace('1.14.0.48', VERSION)
            .replace('1.14.0 ShunCode MCP Fix 3.3.10.43', NAME)
            .replace('manifest version_name is Fix 3.3.10.43', 'manifest version_name is Fix 3.3.10.44')
            .replace('|36|37|38|39|40|41|42|43)$', '|36|37|38|39|40|41|42|43|44)$'))


def build(base, output):
    base = Path(base).resolve()
    output = Path(output).resolve()
    if output.exists() or output == base or base in output.parents:
        raise ValueError('Output must be new and outside baseline')
    staging = output.parent / (output.name + '.stage43')
    if staging.exists():
        raise ValueError('Staging path already exists: ' + str(staging))
    locks = json.loads((HERE / 'fix331044-source-sha256.json').read_text(encoding='utf-8'))
    for n in ['apply-fix331043.py', 'dspp-exposure-builtin-v44-selftest.js']:
        if sha((HERE / n).read_bytes()) != locks[n]:
            raise ValueError('Source hash mismatch: ' + n)
    values = B43.build(str(base), str(staging))
    enc = lambda s: s.encode('utf-8') if isinstance(s, str) else s
    pol = values['fix3-policy.js']
    if b'd?.provider?.kind===`mcp`&&!!d.provider.id' in pol:
        raise ValueError('v44 policy change already present')
    values['fix3-policy.js'] = once(pol, enc(OLD_TOTAL), enc(NEW_TOTAL))
    c = values['content-scripts/content.js']
    if b'331044' in c:
        raise ValueError('v44 content change already present')
    for o, n in CONTENT_EDITS:
        c = once(c, enc(o), enc(n))
    values['content-scripts/content.js'] = c
    for n in ['background.js', 'content-scripts/content.js', 'content-scripts/main-world.js']:
        result = subprocess.run(['node', '--check', '--input-type=module'], input=values[n], capture_output=True)
        if result.returncode:
            raise ValueError('Node syntax failure: ' + n + ' ' + result.stderr.decode('utf-8', 'replace')[:800])
    result = subprocess.run(['node', '--check'], input=values['fix3-policy.js'], capture_output=True)
    if result.returncode:
        raise ValueError('Node syntax failure: fix3-policy.js ' + result.stderr.decode('utf-8', 'replace')[:800])
    mf = once(values['manifest.json'], '"version": "1.14.0.48"', '"version": "' + VERSION + '"')
    values['manifest.json'] = once(mf, '1.14.0 ShunCode MCP Fix 3.3.10.43', NAME)
    for lang in ['en', 'zh_CN']:
        n = '_locales/' + lang + '/messages.json'
        values[n] = once(values[n], 'DeepSeek++ ShunCode MCP Fix 3.3.10.43', 'DeepSeek++ ShunCode MCP Fix 3.3.10.44')
    for n in list(values):
        if '/' not in n and 'selftest' in n and n.endswith('.js'):
            values[n] = gates(values[n].decode('utf-8')).encode('utf-8')
    # .41 suite pins the background hash; background.js is unchanged in .44, so the pin must already match.
    v41 = values['dspp-bare-tool-tag-v41-selftest.js']
    m = re.search(rb"bgSha === '([0-9a-f]{64})'", v41)
    if not m or m.group(1).decode() != sha(values['background.js']):
        raise ValueError('v41 suite background pin does not match the (unchanged) .43 background.js')
    values['dspp-exposure-builtin-v44-selftest.js'] = (HERE / 'dspp-exposure-builtin-v44-selftest.js').read_bytes()
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
