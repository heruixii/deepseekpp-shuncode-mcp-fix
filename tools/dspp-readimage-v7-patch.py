#!/usr/bin/env python3
"""Exact two-file v6 -> v7 overlay. Default read-only; apply/rollback synchronize documents.
No browser restart, settings mutation, real upload or publication is performed.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import hashlib

def sha(data):
    return hashlib.sha256(data).hexdigest()

BASE_CONTENT = '251db07b3d1fc1aad31c492594b74bb11adac9143bde8032f120ce34d87d14d9'
BASE_BACKGROUND = 'ed5751c7dfa819e51bb8df24beea990c505db7eb6f7c3654fa58217177844f32'
MANIFEST_SHA = 'b86a6f88793f96de6104bd0a8b2f64de97aef8e3c2722172e75ea9080fe4498f'


def once(data, old, new):
    if isinstance(old, str): old = old.encode('utf-8')
    if isinstance(new, str): new = new.encode('utf-8')
    if data.count(old) != 1: raise ValueError('Unique anchor mismatch: ' + repr(old[:90]))
    return data.replace(old, new, 1)


def build(content, background, runtime, helper):
    if sha(content) != BASE_CONTENT or sha(background) != BASE_BACKGROUND:
        raise ValueError('Exact v6 input hashes required')
    start = content.index(b'/* DPP_READIMAGE_V6_BEGIN')
    endmarker = b'/* DPP_READIMAGE_V6_END */'
    end = content.index(endmarker, start) + len(endmarker)
    c = content[:start] + runtime.rstrip(b'\n') + content[end:]
    c = once(c, 'DPP_CREATE_READIMAGE_V6({backend:p,signal:i,chatSessionId:s,loopId:a})',
                'DPP_CREATE_READIMAGE_V7({backend:p,signal:i,chatSessionId:s,loopId:a})')
    # The existing local variable name DPPVisionV6 is retained to minimize owning-loop changes.
    b = once(background, 'SET_PENDING_PROJECT_CONTEXT.TOUCH_MEMORIES`.split(`.`)),SN=class',
              'SET_PENDING_PROJECT_CONTEXT.TOUCH_MEMORIES.UPLOAD_DEEPSEEK_IMAGE`.split(`.`)),SN=class')
    b = once(b, 'var LN=new Set([`CREATE_TOOL_AUTHORIZATION`,`CLOSE_TOOL_AUTHORIZATION`,`APPEND_EXTERNAL_TOOL_PAYLOAD_CHUNK`,`EXECUTE_TOOL_CALL`]);',
              'var LN=new Set([`CREATE_TOOL_AUTHORIZATION`,`CLOSE_TOOL_AUTHORIZATION`,`APPEND_EXTERNAL_TOOL_PAYLOAD_CHUNK`,`EXECUTE_TOOL_CALL`,`UPLOAD_DEEPSEEK_IMAGE`]);')
    b = once(b, 'function EN(e,t){t.surface!==`extension_context`&&(xN.has(e.type)||B(`Runtime command ${e.type} is not authorized for DeepSeek content.`))}',
              'function EN(e,t){t.surface!==`extension_context`&&(xN.has(e.type)||B(`Runtime command ${e.type} is not authorized for DeepSeek content.`));if(e.type===`UPLOAD_DEEPSEEK_IMAGE`)DPP_REQUIRE_UPLOAD_CONTEXT_V7(t)}')
    b = once(b, 'function UF(e){', helper + b'\nfunction UF(e){')
    b = once(b, '_F(`UPLOAD_DEEPSEEK_IMAGE`,(t,n)=>e.service.uploadImage(t,n.tabId))',
              '_F(`UPLOAD_DEEPSEEK_IMAGE`,(t,n)=>DPP_DISPATCH_UPLOAD_V7(e.service,t,n))')
    b = once(b, 're=async(t,n,r)=>{let i=await e.getChatEnabled();if(HF(n.signal),!i)return{ok:!1,error:`chat_disabled`};let a=bP(t);HF(n.signal);let o=await e.loadClientHeaders(r);if(HF(n.signal),!o)return{ok:!1,error:e.missingAuthMessage()};let s=await e.createUploadPowHeaders(o,n.signal);HF(n.signal);let c=await e.uploadFile({file:a.file,filename:a.name,modelType:`vision`,clientHeaders:o,powHeaders:s},n.signal);return HF(n.signal),{ok:!0,file:c}},ie=async(e,t)=>',
              're=async(t,n,r,DPPUploadV7)=>{await DPPUploadV7?.assertCurrent?.();let i=DPPUploadV7?.content===!0||await e.getChatEnabled();if(HF(n.signal),!i)return{ok:!1,error:`chat_disabled`};if(DPPUploadV7)DPPUploadV7.stage=`payload`;let a=bP(t);HF(n.signal);await DPPUploadV7?.assertCurrent?.();if(DPPUploadV7)DPPUploadV7.stage=`auth`;let o=await e.loadClientHeaders(r);if(HF(n.signal),!o)return{ok:!1,error:e.missingAuthMessage(),...DPPUploadV7?{code:`auth_missing`}:{}};await DPPUploadV7?.assertCurrent?.();if(DPPUploadV7)DPPUploadV7.stage=`pow`;let s=await e.createUploadPowHeaders(o,n.signal);HF(n.signal);await DPPUploadV7?.assertCurrent?.();if(DPPUploadV7)DPPUploadV7.stage=`upload`;let c=await e.uploadFile({file:a.file,filename:a.name,modelType:`vision`,clientHeaders:o,powHeaders:s},n.signal);return HF(n.signal),{ok:!0,file:c}},ie=async(e,t,DPPUploadV7)=>')
    b = once(b, 'let r=re(e,n.controller,t);n.settled=r.then(()=>void 0,()=>void 0);',
              'let r=re(e,n.controller,t,DPPUploadV7);n.settled=r.then(()=>void 0,()=>void 0);')
    return c, b

RUNTIME_SHA = '07ebf98fc03912c4546dd09f976a6f465ded64ffb9a786c4515d710d47253e17'
HELPER_SHA = '90e2f9c119bd03ab41511a73f72a9ab691a368c57105275b56f9b061ce9ae9c7'
TARGET_CONTENT = '76c02e472300316dd537af587dc3630d13a45ef3bde0b03aca189f7d640586d4'
TARGET_BACKGROUND = '4f89a4d8b8d92a0e8c8661fdc5fc3a1745f39e2de2fc3306e0b3d9e7c87e3abc'

HERE = Path(__file__).resolve().parent
EXT = Path('D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3')
WORKSPACE = Path('D:/learn/Athena计划')
NAMES = ('content-scripts/content.js', 'background.js')
BASE = (BASE_CONTENT, BASE_BACKGROUND)
TARGET = (TARGET_CONTENT, TARGET_BACKGROUND)


def candidates(sources):
    runtime = (HERE / 'dspp-readimage-v7-runtime.js').read_bytes()
    helper = (HERE / 'dspp-readimage-v7-background.js').read_bytes()
    if sha(runtime) != RUNTIME_SHA or sha(helper) != HELPER_SHA:
        raise ValueError('Build source hash mismatch')
    values = build(*sources, runtime, helper)
    if tuple(map(sha, values)) != TARGET:
        raise ValueError('Candidate output hash mismatch')
    return values


def syntax(values):
    with tempfile.TemporaryDirectory(prefix='dspp-v7-syntax-') as directory:
        for number, data in enumerate(values):
            p = Path(directory) / ('file%d.js' % number)
            p.write_bytes(data)
            r = subprocess.run(['node', '--check', str(p)], capture_output=True, text=True)
            if r.returncode:
                raise ValueError('Candidate syntax failure: ' + r.stderr[:2000])


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
            fd, name = tempfile.mkstemp(prefix=path.name + '.v7-stage-', dir=path.parent)
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
                fd, name = tempfile.mkstemp(prefix=path.name + '.v7-restore-', dir=path.parent)
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(old[path])
                os.replace(name, path)
        raise
    finally:
        for path in staged.values():
            path.unlink(missing_ok=True)



def docs_receipt(workspace, action, values):
    now = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    changes, expected = {}, {}
    state = 'v7 已写入磁盘，待重载与真实上传验收' if action == 'apply' else '已回滚到 v6（已知上传权限阻断），待重载'
    hashes = tuple(map(sha, values))
    entry = (f'\n\n### {now} · read_image v7 {action}\n\n'
             f'- content.js: {len(values[0])} B, SHA `{hashes[0]}`。\n'
             f'- background.js: {len(values[1])} B, SHA `{hashes[1]}`。\n'
             '- 两文件备份为各自 `.v7_bak`（v6）；本操作含双文件语法校验和文档回执。\n'
             '- 未修改侧栏开关、未重载浏览器、未进行真实图片上传；端到端验收仍待进行。\n')
    for name in ['docs/mcp-deepseekpp-readimage-v7.md', 'docs/mcp-deepseekpp-readimage-v6.md',
                 'docs/mcp-deepseekpp-readimage-upload-boundary.md',
                 'docs/DeepSeekPP-read_image-自动读图-交接排查文档.md',
                 'docs/DeepSeekPP-Fix3-项目交接文档.md']:
        path = workspace / name
        raw = path.read_bytes(); expected[path] = sha(raw)
        lines = [line.rstrip() for line in raw.decode('utf-8').splitlines() if not line.startswith('> 部署状态（脚本维护）：')]
        lines.insert(1, f'> 部署状态（脚本维护）：{state}；{now}。')
        changes[path] = ('\n'.join(lines).rstrip() + entry + '\n').encode('utf-8')
    path = workspace / 'AGENT_HANDOVER.md'
    raw = path.read_bytes(); expected[path] = sha(raw)
    text = raw.decode('utf-8').replace('\r\n', '\n')
    anchor = '## 12. 变更日志（Change Log）\n'
    if text.count(anchor) != 1: raise ValueError('Project handoff anchor mismatch')
    line = f'- {now} | DeepSeekPP read_image v7 {action}, content={hashes[0]}, background={hashes[1]}; documents synchronized, browser/live upload pending; Athena/settings unchanged. | docs/mcp-deepseekpp-readimage-v7.md\n'
    changes[path] = text.replace(anchor, anchor + line, 1).encode('utf-8')
    return changes, expected


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ext', type=Path, default=EXT)
    ap.add_argument('--workspace', type=Path, default=WORKSPACE)
    group = ap.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true')
    group.add_argument('--build', type=Path, help='New isolated full extension tree; never a live directory')
    group.add_argument('--apply', action='store_true')
    group.add_argument('--rollback', action='store_true')
    args = ap.parse_args()
    paths = tuple(args.ext / name for name in NAMES)
    backups = tuple(Path(str(p) + '.v7_bak') for p in paths)
    current = tuple(p.read_bytes() for p in paths)
    current_hashes = tuple(map(sha, current))
    if sha((args.ext / 'manifest.json').read_bytes()) != MANIFEST_SHA:
        raise ValueError('Exact .34 manifest required')
    if current_hashes not in (BASE, TARGET):
        raise ValueError('Unknown or mixed version pair; fail closed without mutation')
    sources = current if current_hashes == BASE else tuple(p.read_bytes() for p in backups)
    if tuple(map(sha, sources)) != BASE: raise ValueError('Exact v6 backups required')
    values = candidates(sources)
    syntax(values)
    print(json.dumps({'state': 'v6_ready' if current_hashes == BASE else 'already_v7',
                      'target': [{'file': n, 'bytes': len(v), 'sha256': sha(v)} for n, v in zip(NAMES, values)]}, indent=2))
    if args.build:
        destination = args.build.resolve()
        if destination.exists() or destination == args.ext.resolve() or args.ext.resolve() in destination.parents:
            raise ValueError('Build destination must be new and outside live extension')
        shutil.copytree(args.ext, destination)
        for name, data in zip(NAMES, values):
            (destination / name).write_bytes(data)
        return
    if not args.apply and not args.rollback: return
    if args.apply and current_hashes == TARGET:
        print('Already exact v7: no changes.'); return
    if args.rollback:
        if current_hashes != TARGET: raise ValueError('Rollback requires exact v7 pair')
        values = sources
    syntax(values)
    action = 'rollback' if args.rollback else 'apply'
    changes, expected = docs_receipt(args.workspace, action, values)
    for backup, source, base in zip(backups, sources, BASE):
        if backup.exists() and sha(backup.read_bytes()) != base: raise ValueError('Backup hash mismatch')
        expected[backup] = base if backup.exists() else None
        if not backup.exists(): changes[backup] = source
    expected[args.ext / 'manifest.json'] = MANIFEST_SHA
    expected[HERE / 'dspp-readimage-v7-runtime.js'] = RUNTIME_SHA
    expected[HERE / 'dspp-readimage-v7-background.js'] = HELPER_SHA
    for p, data, digest in zip(paths, values, current_hashes):
        changes[p] = data; expected[p] = digest
    atomic_batch(changes, expected)
    print('Two-file operation committed with backups and documentation. Browser untouched.')


if __name__ == '__main__':
    main()
