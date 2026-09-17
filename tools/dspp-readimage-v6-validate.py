#!/usr/bin/env python3
"""Offline v6 validation. Writes ONLY to a new isolated output tree; never applies to live.
Runs the extension's existing selftests, NOT Athena's production test suite.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('v6patch', HERE / 'dspp-readimage-v6-patch.py')
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ext', type=Path, default=patch.EXT)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    out = args.output.resolve()
    if out.exists() or args.ext.resolve() == out or args.ext.resolve() in out.parents:
        raise ValueError('Validation output must be new and outside the live extension')
    out.mkdir(parents=True)
    logdir = out / 'logs'
    logdir.mkdir()
    original = (args.ext / 'content-scripts/content.js.v5_bak').read_bytes()
    v5 = (args.ext / 'content-scripts/content.js').read_bytes()
    if patch.sha(v5) != patch.V5:
        raise ValueError('Validate before live apply: expected exact v5 source')
    runtime = (HERE / 'dspp-readimage-v6-runtime.js').read_bytes()
    candidate = patch.build(original, runtime)
    patch.syntax(candidate)
    results = []

    def record(name, ok):
        results.append({'name': name, 'passed': bool(ok)})
        print(('PASS ' if ok else 'FAIL ') + name, flush=True)
        if not ok:
            raise AssertionError(name)

    def run(name, command, cwd=None, expected_code=0, env=None):
        result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        (logdir / (name + '.log')).write_bytes(result.stdout)
        record(name, (result.returncode == 0) if expected_code == 0 else result.returncode != 0)
        return result

    tree = out / 'candidate-tree'
    shutil.copytree(args.ext, tree)
    (tree / 'content-scripts/content.js').write_bytes(candidate)
    record('independent_rebuild', candidate == patch.build((args.ext / 'content-scripts/content.js.v4_bak').read_bytes(), runtime))
    diffs = []
    for source in args.ext.rglob('*'):
        if source.is_file():
            dest = tree / source.relative_to(args.ext)
            if source.read_bytes() != dest.read_bytes():
                diffs.append(source.relative_to(args.ext).as_posix())
    record('only_content_js_differs', diffs == ['content-scripts/content.js'])
    run('vision_runtime_and_real_Jz', ['node', str(HERE / 'dspp-readimage-v6-selftest.js'), str(tree / 'content-scripts/content.js')])
    suites = sorted(tree.glob('*-selftest.js'))
    record('existing_suite_count_55', len(suites) == 55)
    env = {**os.environ, 'DPP_ROOT': str(tree)}
    regression = []
    for suite in suites:
        result = subprocess.run(['node', str(suite), str(tree)], cwd=tree, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        (logdir / (suite.stem + '.log')).write_bytes(result.stdout)
        regression.append({'name': suite.name, 'code': result.returncode})
        print(('PASS ' if result.returncode == 0 else 'FAIL ') + suite.name, flush=True)
    (out / 'regression.json').write_text(json.dumps(regression, indent=2), encoding='utf-8')
    record('extension_regression_55', all(x['code'] == 0 for x in regression))

    # Minimal fake extension + fake docs exercise CLI apply/rollback without touching live.
    fake = out / 'patcher-fixture'
    (fake / 'content-scripts').mkdir(parents=True)
    for name in ['manifest.json', 'background.js']:
        shutil.copy2(args.ext / name, fake / name)
    (fake / 'content-scripts/content.js').write_bytes(v5)
    (fake / 'content-scripts/content.js.v5_bak').write_bytes(original)
    ws = out / 'fake-workspace'
    (ws / 'docs').mkdir(parents=True)
    for name in ['mcp-deepseekpp-readimage-v6.md', 'DeepSeekPP-read_image-自动读图-交接排查文档.md', 'DeepSeekPP-Fix3-项目交接文档.md']:
        (ws / 'docs' / name).write_text('# Offline fixture\n', encoding='utf-8')
    (ws / 'AGENT_HANDOVER.md').write_text('# Offline fixture\n\n## 12. 变更日志（Change Log）\n', encoding='utf-8')
    base = [sys.executable, str(HERE / 'dspp-readimage-v6-patch.py'), '--ext', str(fake), '--workspace', str(ws)]
    def snapshots():
        return {str(p): patch.sha(p.read_bytes()) for root in [fake, ws] for p in root.rglob('*') if p.is_file()}
    snap = snapshots()
    run('default_check', base)
    record('default_no_writes', snap == snapshots())
    run('cli_apply', base + ['--apply'])
    record('applied_exact_candidate', (fake / 'content-scripts/content.js').read_bytes() == candidate)
    record('apply_status_header', all(p.read_text(encoding='utf-8').count('> 部署状态（脚本维护）：v6 已写入磁盘') == 1 for p in (ws / 'docs').glob('*.md')))
    record('exact_v5_backup', (fake / 'content-scripts/content.js.v6_bak').read_bytes() == v5)
    record('documentation_receipts', all(patch.CANDIDATE_SHA in p.read_text(encoding='utf-8') for p in ws.rglob('*.md')))
    snap = snapshots()
    run('duplicate_apply', base + ['--apply'])
    record('duplicate_no_writes', snap == snapshots())
    run('cli_rollback', base + ['--rollback'])
    record('rollback_status_header', all(p.read_text(encoding='utf-8').count('> 部署状态（脚本维护）：已回滚到历史失败版 v5') == 1 for p in (ws / 'docs').glob('*.md')))
    record('rollback_exact_v5', (fake / 'content-scripts/content.js').read_bytes() == v5)
    for label, relative in [('tampered_content', 'content-scripts/content.js'), ('tampered_original', 'content-scripts/content.js.v5_bak'), ('tampered_background', 'background.js')]:
        p = fake / relative
        data = p.read_bytes()
        p.write_bytes(data + b'\n/*fixture tamper*/')
        snap = snapshots()
        run(label, base + ['--apply'], expected_code=1)
        record(label + '_no_writes', snapshots() == snap)
        p.write_bytes(data)
    snap = snapshots()
    run('reject_live_build_destination', base + ['--build', str(fake / 'new-content.js')], expected_code=1)
    record('reject_live_build_no_writes', snap == snapshots())
    try:
        patch.build(original, runtime + b'\n')
        record('reject_runtime_tamper', False)
    except ValueError:
        record('reject_runtime_tamper', True)
    try:
        patch.syntax(b'function { invalid JavaScript')
        record('reject_bad_syntax', False)
    except ValueError:
        record('reject_bad_syntax', True)
    first, second = out / 'transaction-a.txt', out / 'transaction-b.txt'
    first.write_bytes(b'old-a'); second.write_bytes(b'old-b')
    expected = {first: patch.sha(b'old-a'), second: patch.sha(b'old-b')}
    try:
        patch.atomic_batch({first: b'new-a'}, {first: 'wrong-hash'})
        record('stale_file_rejected', False)
    except ValueError:
        record('stale_file_rejected', first.read_bytes() == b'old-a')
    real_replace = patch.os.replace
    def fail_second(src, dst):
        if Path(dst) == second and '.v6-stage-' in str(src):
            raise OSError('simulated commit failure')
        return real_replace(src, dst)
    patch.os.replace = fail_second
    try:
        try:
            patch.atomic_batch({first: b'new-a', second: b'new-b'}, expected)
            record('io_failure_rollback', False)
        except OSError:
            record('io_failure_rollback', first.read_bytes() == b'old-a' and second.read_bytes() == b'old-b')
    finally:
        patch.os.replace = real_replace
    record('live_still_v5', (args.ext / 'content-scripts/content.js').read_bytes() == v5)
    report = {'status': 'passed', 'candidate_sha256': patch.sha(candidate), 'candidate_bytes': len(candidate),
              'vision_groups': 22, 'existing_suites': 55, 'checks': results, 'regression': regression,
              'scope': 'offline only; no browser reload, upload, model call, or live apply'}
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('VALIDATION PASSED ' + str(out / 'report.json'), flush=True)


if __name__ == '__main__':
    main()
