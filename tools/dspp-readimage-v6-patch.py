#!/usr/bin/env python3
"""Hash-locked read_image v5 -> v6 overlay. Default: inspect only; never run v4/v5 patchers.
All candidate validation precedes mutation. Apply/rollback write documentation receipts too.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

EXT = Path('D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3')
WORKSPACE = Path('D:/learn/Athena计划')
V5 = '6ba876bd3b2cfa3f6328c328621d43d259a83f5298bb3f68d50ea21f9fe5c54b'
ORIGINAL = '6657748d6d644b32e288aa7264283122402950c920450d652293c3b9720b5962'
BACKGROUND = 'ed5751c7dfa819e51bb8df24beea990c505db7eb6f7c3654fa58217177844f32'
RUNTIME_SHA = 'c40d2a5cc594c570e13e023aadbc51e4de3dec1d27492671a559cdd26642f73e'
CANDIDATE_SHA = '251db07b3d1fc1aad31c492594b74bb11adac9143bde8032f120ce34d87d14d9'
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(data, old, new):
    if isinstance(old, str):
        old = old.encode('utf-8')
    if isinstance(new, str):
        new = new.encode('utf-8')
    if data.count(old) != 1:
        raise ValueError('Anchor missing or ambiguous: ' + repr(old[:100]))
    return data.replace(old, new, 1)


def build(original, runtime):
    if sha(original) != ORIGINAL:
        raise ValueError('Original .34 baseline hash mismatch')
    if sha(runtime) != RUNTIME_SHA:
        raise ValueError('Runtime source hash mismatch')
    if runtime.count(b'DPP_READIMAGE_V6_BEGIN') != 1 or runtime.count(b'DPP_READIMAGE_V6_END') != 1:
        raise ValueError('Runtime markers missing or ambiguous')
    data = replace_once(original, 'async function Jz(e){', runtime + b'\nasync function Jz(e){')
    data = replace_once(data, 'g=[...t.toolExecutions],_=[],v=new Map',
                        'g=[...t.toolExecutions],DPPVisionV6=DPP_CREATE_READIMAGE_V6({backend:p,signal:i,chatSessionId:s,loopId:a}),_=[],v=new Map')
    data = replace_once(data, 'submitTurn:BR({powWasmUrl:u}),session:f,serializePrompt:',
                        'submitTurn:DPPVisionV6.wrapSubmit(BR({powWasmUrl:u})),session:f,serializePrompt:')
    data = replace_once(data, '_.push(DPPExecution),(()=>{try{if(String(e.toolName',
                        'DPPExecution=await DPPVisionV6.capture(DPPExecution);_.push(DPPExecution),(()=>{try{if(String(e.toolName')
    data = replace_once(data, 'try{await UN([{role:`user`,content:t.originalPrompt,',
                        'try{for(let DPPImageIndexV6=0;DPPImageIndexV6<g.length;DPPImageIndexV6++)g[DPPImageIndexV6]=await DPPVisionV6.capture(g[DPPImageIndexV6]);await UN([{role:`user`,content:t.originalPrompt,')
    data = replace_once(data, 'error:e instanceof Error?e.message:String(e)})}}function Yz(e)',
                        'error:e instanceof Error?e.message:String(e)})}finally{DPPVisionV6.close()}}function Yz(e)')
    if b'DPP_RIF' in data or b'DPP_READIMAGE_V5' in data:
        raise ValueError('Legacy image queue unexpectedly remains')
    if sha(data) != CANDIDATE_SHA:
        raise ValueError('Candidate output hash mismatch')
    return data


def syntax(data):
    with tempfile.TemporaryDirectory(prefix='dspp-v6-check-') as directory:
        path = Path(directory) / 'content.js'
        path.write_bytes(data)
        result = subprocess.run(['node', '--check', str(path)], capture_output=True, text=True)
        if result.returncode:
            raise ValueError('JavaScript syntax check failed: ' + result.stderr[:2000])


def atomic_batch(changes, expected):
    """Preflight every source, stage images, commit and best-effort rollback on an I/O failure.
    This is rollback-capable, not a cross-filesystem/crash-atomic transaction.
    """
    old = {path: path.read_bytes() if path.exists() else None for path in changes}
    for path, digest in expected.items():
        current = path.read_bytes() if path.exists() else None
        if (sha(current) if current is not None else None) != digest:
            raise ValueError('STALE_FILE: ' + str(path))
    staged, committed = {}, []
    try:
        for path, data in changes.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix=path.name + '.v6-stage-', dir=path.parent)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            staged[path] = Path(name)
        for path, digest in expected.items():
            current = path.read_bytes() if path.exists() else None
            if (sha(current) if current is not None else None) != digest:
                raise ValueError('STALE_FILE before commit: ' + str(path))
        for path in changes:
            os.replace(staged[path], path)
            committed.append(path)
    except Exception:
        for path in reversed(committed):
            if old[path] is None:
                path.unlink(missing_ok=True)
            else:
                fd, name = tempfile.mkstemp(prefix=path.name + '.v6-restore-', dir=path.parent)
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(old[path])
                os.replace(name, path)
        raise
    finally:
        for path in staged.values():
            path.unlink(missing_ok=True)


def receipts(workspace, action, old_sha, new_sha, size, backup):
    now = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    text = (f'\n\n### {now} · read_image v6 {action}\n\n'
            f'- content.js: `{old_sha}` → `{new_sha}`，{size} B。\n'
            f'- 回退备份：`{backup.as_posix()}`；background.js 保持 `{BACKGROUND}`。\n'
            '- 本操作通过 Node 语法预检；离线行为测试见 v6 专项文档。\n'
            '- 未自动重载扩展、未执行真实图片上传、未发布 GitHub/ZIP；浏览器端到端验收仍待进行。\n')
    changes, expected = {}, {}
    for relative in ['docs/mcp-deepseekpp-readimage-v6.md',
                     'docs/DeepSeekPP-read_image-自动读图-交接排查文档.md',
                     'docs/DeepSeekPP-Fix3-项目交接文档.md']:
        path = workspace / relative
        raw = path.read_bytes()
        expected[path] = sha(raw)
        previous = raw.decode('utf-8').replace('\r\n', '\n')
        prefix = '> 部署状态（脚本维护）：'
        state = 'v6 已写入磁盘，待重载及浏览器验收' if action == '应用' else '已回滚到历史失败版 v5，待重载'
        lines = [line for line in previous.splitlines() if not line.startswith(prefix)]
        lines.insert(1, f'{prefix}{state}；SHA `{new_sha}`；{now}。')
        changes[path] = ('\n'.join(lines).rstrip() + text + '\n').encode('utf-8')
    path = workspace / 'AGENT_HANDOVER.md'
    raw = path.read_bytes()
    expected[path] = sha(raw)
    previous = raw.decode('utf-8').replace('\r\n', '\n')
    anchor = '## 12. 变更日志（Change Log）\n'
    if previous.count(anchor) != 1:
        raise ValueError('Project change-log anchor mismatch')
    entry = f'- {now} | DeepSeekPP read_image v6 {action}: content.js SHA `{new_sha}`; no Athena runtime/DB/service changes; browser verification pending. | docs/mcp-deepseekpp-readimage-v6.md\n'
    changes[path] = previous.replace(anchor, anchor + entry, 1).encode('utf-8')
    return changes, expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ext', type=Path, default=EXT)
    parser.add_argument('--workspace', type=Path, default=WORKSPACE)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--check', action='store_true')
    action.add_argument('--build', type=Path, help='Write an isolated candidate content.js (must not exist)')
    action.add_argument('--apply', action='store_true')
    action.add_argument('--rollback', action='store_true')
    args = parser.parse_args()
    target = args.ext / 'content-scripts/content.js'
    original_path = args.ext / 'content-scripts/content.js.v5_bak'
    backup = args.ext / 'content-scripts/content.js.v6_bak'
    original = original_path.read_bytes()
    runtime = (HERE / 'dspp-readimage-v6-runtime.js').read_bytes()
    candidate = build(original, runtime)
    candidate_sha = sha(candidate)
    current = target.read_bytes()
    if sha((args.ext / 'background.js').read_bytes()) != BACKGROUND:
        raise ValueError('Background baseline mismatch; stop')
    if json.loads((args.ext / 'manifest.json').read_text(encoding='utf-8-sig'))['version'] != '1.14.0.39':
        raise ValueError('Manifest baseline mismatch; stop')
    if sha(current) not in (V5, candidate_sha):
        raise ValueError('Unknown content.js hash; stop without writing')
    syntax(candidate)
    print(json.dumps({'current_sha256': sha(current), 'candidate_sha256': candidate_sha,
                      'candidate_bytes': len(candidate), 'syntax': 'passed',
                      'status': 'already_v6' if current == candidate else 'v5_ready'}, indent=2))
    if args.build:
        dest = args.build.resolve()
        if dest == target.resolve() or dest.exists() or args.ext.resolve() in dest.parents:
            raise ValueError('Build destination must be new and outside the live extension')
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as stream:
            stream.write(candidate)
        return
    if not args.apply and not args.rollback:
        return
    if args.apply and current == candidate:
        print('Already exactly v6; no changes.')
        return
    if args.rollback:
        if current != candidate or not backup.is_file() or sha(backup.read_bytes()) != V5:
            raise ValueError('Rollback requires exact v6 target and exact v5 archive')
        next_data, operation = backup.read_bytes(), '回滚到 v5（仍为历史失败版）'
    else:
        if backup.exists() and sha(backup.read_bytes()) != V5:
            raise ValueError('Existing v6 backup is not the expected v5 source')
        next_data, operation = candidate, '应用'
    syntax(next_data)
    changes, expected = receipts(args.workspace, operation, sha(current), sha(next_data), len(next_data), backup)
    if args.apply and not backup.exists():
        changes[backup] = current
    # Runtime file last: documentation and backup stage before live replacement.
    changes[target] = next_data
    expected[backup] = V5 if backup.exists() else None
    expected[HERE / 'dspp-readimage-v6-runtime.js'] = RUNTIME_SHA
    expected[target] = sha(current)
    expected[original_path] = ORIGINAL
    expected[args.ext / 'background.js'] = BACKGROUND
    atomic_batch(changes, expected)
    print('Applied with documentation receipts. Browser reload/real upload not performed.')


if __name__ == '__main__':
    main()
