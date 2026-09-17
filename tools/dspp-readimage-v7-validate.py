#!/usr/bin/env python3
"""Offline-only v7 validation: actual message boundary, runtime, legacy extension tests and paired rollback."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('v7patch', HERE / 'dspp-readimage-v7-patch.py')
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ext', type=Path, default=patch.EXT)
    ap.add_argument('--baseline', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    out = args.output.resolve()
    if out.exists() or out == args.ext.resolve() or args.ext.resolve() in out.parents:
        raise ValueError('New isolated output required')
    out.mkdir(parents=True); logs = out / 'logs'; logs.mkdir()
    sources = tuple((args.ext / n).read_bytes() for n in patch.NAMES)
    if tuple(map(patch.sha, sources)) != patch.BASE: raise ValueError('Validate before deployment, against exact live v6')
    checks, suites = [], []

    def ok(name, value):
        checks.append({'name': name, 'passed': bool(value)})
        print(('PASS ' if value else 'FAIL ') + name, flush=True)
        if not value: raise AssertionError(name)

    def run(name, cmd, fail=False, cwd=None):
        r = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120,
                           env={**os.environ, 'DPP_ROOT': str(out / 'candidate')})
        (logs / (name + '.log')).write_bytes(r.stdout)
        ok(name, r.returncode != 0 if fail else r.returncode == 0)
        return r

    values = patch.candidates(sources); patch.syntax(values)
    independent = patch.candidates(tuple((args.baseline / n).read_bytes() for n in patch.NAMES))
    ok('independent_pair_rebuild', independent == values)
    tree = out / 'candidate'
    run('candidate_build', [sys.executable, str(HERE / 'dspp-readimage-v7-patch.py'), '--ext', str(args.ext), '--build', str(tree)])
    differences = sorted(p.relative_to(args.ext).as_posix() for p in args.ext.rglob('*')
                         if p.is_file() and p.read_bytes() != (tree / p.relative_to(args.ext)).read_bytes())
    ok('only_two_runtime_files_differ', differences == sorted(patch.NAMES))
    run('runtime_22_groups', ['node', str(HERE / 'dspp-readimage-v7-selftest.js'), str(tree / patch.NAMES[0])])
    run('real_boundary_16_groups', ['node', str(HERE / 'dspp-readimage-v7-boundary-selftest.js'), str(tree), str(args.baseline)])
    old_tests = sorted(tree.glob('*-selftest.js')); ok('existing_55_suites', len(old_tests) == 55)
    for test in old_tests:
        r = subprocess.run(['node', str(test), str(tree)], cwd=tree, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=120, env={**os.environ, 'DPP_ROOT': str(tree)})
        (logs / (test.stem + '.log')).write_bytes(r.stdout)
        suites.append({'name': test.name, 'code': r.returncode})
        print(('PASS ' if r.returncode == 0 else 'FAIL ') + test.name, flush=True)
    (out / 'legacy.json').write_text(json.dumps(suites, indent=2), encoding='utf-8')
    ok('legacy_55_passed', all(s['code'] == 0 for s in suites))

    fake, ws = out / 'fake-extension', out / 'fake-workspace'
    (fake / 'content-scripts').mkdir(parents=True); (ws / 'docs').mkdir(parents=True)
    for name in (*patch.NAMES, 'manifest.json'):
        shutil.copy2(args.ext / name, fake / name)
    for name in ['mcp-deepseekpp-readimage-v7.md', 'mcp-deepseekpp-readimage-v6.md', 'mcp-deepseekpp-readimage-upload-boundary.md',
                 'DeepSeekPP-read_image-自动读图-交接排查文档.md', 'DeepSeekPP-Fix3-项目交接文档.md']:
        (ws / 'docs' / name).write_text('# Offline fixture\n', encoding='utf-8')
    (ws / 'AGENT_HANDOVER.md').write_text('# Offline fixture\n## 12. 变更日志（Change Log）\n', encoding='utf-8')
    cmd = [sys.executable, str(HERE / 'dspp-readimage-v7-patch.py'), '--ext', str(fake), '--workspace', str(ws)]
    def snap(): return {str(p): patch.sha(p.read_bytes()) for r in [fake, ws] for p in r.rglob('*') if p.is_file()}
    def rejected(name, command):
        before = snap(); run(name, command, fail=True); ok(name + '_no_writes', snap() == before)
    before = snap(); run('default_check', cmd); ok('default_no_writes', snap() == before)
    run('apply_pair', cmd + ['--apply'])
    ok('exact_live_candidate_pair', tuple((fake / n).read_bytes() for n in patch.NAMES) == values)
    ok('exact_v6_backup_pair', tuple(Path(str(fake / n) + '.v7_bak').read_bytes() for n in patch.NAMES) == sources)
    ok('apply_docs_current_header', all('v7 已写入磁盘' in p.read_text(encoding='utf-8') for p in (ws / 'docs').glob('*.md')))
    before = snap(); run('repeat_apply', cmd + ['--apply']); ok('repeat_no_writes', before == snap())
    backup = Path(str(fake / patch.NAMES[1]) + '.v7_bak'); backup_bytes = backup.read_bytes(); backup.write_bytes(b'corrupted')
    rejected('corrupt_rollback_backup', cmd + ['--rollback']); backup.write_bytes(backup_bytes)
    run('rollback_pair', cmd + ['--rollback'])
    ok('rollback_exact_v6_pair', tuple((fake / n).read_bytes() for n in patch.NAMES) == sources)
    ok('rollback_docs_current_header', all('已回滚到 v6' in p.read_text(encoding='utf-8') for p in (ws / 'docs').glob('*.md')))
    rejected('repeat_rollback_rejected', cmd + ['--rollback'])
    for name in (*patch.NAMES, 'manifest.json'):
        p = fake / name; before = p.read_bytes(); p.write_bytes(before + b'\n/*tamper*/')
        rejected('tamper_' + p.name, cmd + ['--apply']); p.write_bytes(before)
    p = fake / patch.NAMES[0]; p.write_bytes(values[0]); rejected('mixed_version_pair', cmd + ['--apply']); p.write_bytes(sources[0])
    rejected('build_into_live_rejected', cmd + ['--build', str(fake / 'new-tree')])
    # Source corruption in an isolated copy must also fail closed.
    toolcopy = out / 'tampered-tools'; toolcopy.mkdir()
    for name in ['dspp-readimage-v7-patch.py', 'dspp-readimage-v7-runtime.js', 'dspp-readimage-v7-background.js']:
        shutil.copy2(HERE / name, toolcopy / name)
    with (toolcopy / 'dspp-readimage-v7-background.js').open('ab') as f: f.write(b'\n/*tamper*/')
    rejected('tampered_build_helper', [sys.executable, str(toolcopy / 'dspp-readimage-v7-patch.py'), '--ext', str(fake), '--workspace', str(ws), '--apply'])
    try:
        patch.syntax((b'function { syntax error', values[1])); ok('syntax_reject', False)
    except ValueError: ok('syntax_reject', True)
    tx = out / 'transaction'; tx.mkdir()
    doc, first, second = [tx / x for x in ['doc.md', 'content.js', 'background.js']]
    for p in [doc, first, second]: p.write_bytes(b'old')
    expected = {p: patch.sha(b'old') for p in [doc, first, second]}
    try:
        patch.atomic_batch({first: b'new'}, {first: 'stale'}); ok('stale_reject', False)
    except ValueError: ok('stale_reject', first.read_bytes() == b'old')
    replace = patch.os.replace
    def fail_background(src, dst):
        if Path(dst) == second and '.v7-stage-' in str(src): raise OSError('simulated second-file failure')
        return replace(src, dst)
    patch.os.replace = fail_background
    try:
        try:
            patch.atomic_batch({doc: b'new-doc', first: b'new-content', second: b'new-bg'}, expected); ok('paired_io_rollback', False)
        except OSError: ok('paired_io_rollback', all(p.read_bytes() == b'old' for p in [doc, first, second]))
    finally: patch.os.replace = replace
    ok('live_runtime_untouched', tuple((args.ext / n).read_bytes() for n in patch.NAMES) == sources)
    report = {'status': 'passed', 'targets': dict(zip(patch.NAMES, patch.TARGET)), 'checks': checks, 'legacy': suites,
              'runtime_groups': 22, 'boundary_groups': 16, 'scope': 'offline only; real HTTP/browser acceptance pending'}
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('VALIDATION PASSED ' + str(out / 'report.json'), flush=True)


if __name__ == '__main__': main()
