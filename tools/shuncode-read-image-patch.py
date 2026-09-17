#!/usr/bin/env python3
"""Maintain native MCP image blocks after ShunCode upgrades.
Default is read-only. Only a unique, recognized READ_IMAGE_TOOL handler may be patched.
No native install files or local backup receipts should be committed to Git.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

TARGETS = ('runtime/mcp-server.js', 'dist/extension.js')
START = re.compile(r'(?m)^([ \t]*)if\s*\(canonicalName\s*===\s*READ_IMAGE_TOOL\.name\)\s*\{')
RETURN = re.compile(r'(?m)^([ \t]*)return\s*\{\s*text,\s*structuredContent:\s*metadata,\s*content\s*\};')
DESTRUCT = re.compile(r'const\s*\{\s*base64(?:\s*:\s*([A-Za-z_$][\w$]*))?,\s*\.\.\.metadata\s*\}\s*=\s*result\s*;')


def sha(raw): return hashlib.sha256(raw).hexdigest()


def inspect(raw):
    """Return (already|need, proposed bytes); no cross-handler/global image-push test."""
    text = raw.decode('utf-8-sig')
    matches = list(START.finditer(text))
    if len(matches) != 1: raise ValueError('READ_IMAGE_TOOL handler missing or ambiguous')
    start = matches[0]
    next_handler = re.search(r'(?m)^' + re.escape(start.group(1)) + r'if\s*\(canonicalName\s*===\s*[A-Z_]+_TOOL\.name\)', text[start.end():])
    if not next_handler: raise ValueError('Next sibling handler boundary missing')
    end = start.end() + next_handler.start()
    body = text[start.start():end]
    if len(body) > 16000: raise ValueError('Unrecognized oversized read_image handler')
    if not re.search(r'const\s+result\s*=\s*await\s+readImage\(', body): raise ValueError('readImage call not recognized')
    if not re.search(r'const\s+content\s*=\s*\[\{\s*type:\s*[\"\']text[\"\'],\s*text\s*\}\];', body): raise ValueError('Text content construction not recognized')
    if 'isError: true' not in body: raise ValueError('Error branch not recognized')
    ds, rs = list(DESTRUCT.finditer(body)), list(RETURN.finditer(body))
    if len(ds) != 1 or len(rs) != 1 or ds[0].end() > rs[0].start(): raise ValueError('Success data/return anchor missing or ambiguous')
    variable = ds[0].group(1) or 'base64'
    segment = body[ds[0].end():rs[0].start()]
    push = re.compile(r'content\.push\(\s*\{\s*type:\s*[\"\']image[\"\'],\s*data:\s*' + re.escape(variable) + r',\s*mimeType:\s*result\.mime_type\s*\}\s*\);')
    if len(push.findall(segment)) == 1:
        remainder = push.sub('', segment)
        guard = r'if\s*\(!' + re.escape(variable) + r'\)\s*throw new Error\("read_image returned success without image data\."\);'
        if re.sub(guard, '', remainder).strip(): raise ValueError('Unknown statements around native image block')
        return 'already', raw
    if 'content.push' in segment or re.search(r'type:\s*[\"\']image[\"\']', body): raise ValueError('Unrecognized native image block; review instead of duplicating')
    if segment.strip(): raise ValueError('Unknown statements before successful return; manual review required')
    newline = '\r\n' if '\r\n' in text else '\n'
    indent = rs[0].group(1)
    insert = (indent + 'if (!' + variable + ') throw new Error("read_image returned success without image data.");' + newline +
              indent + 'content.push({ type: "image", data: ' + variable + ', mimeType: result.mime_type });' + newline)
    index = start.start() + rs[0].start()
    result = (text[:index] + insert + text[index:]).encode('utf-8')
    if raw.startswith(b'\xef\xbb\xbf'): result = b'\xef\xbb\xbf' + result
    return 'need', result


def syntax(values):
    for raw in values:
        result = subprocess.run(['node', '--check', '--input-type=module'], input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode: raise ValueError('Node syntax check failed: ' + result.stderr.decode('utf-8', 'replace')[:1200])


def atomic_write(changes, expected):
    before = {p: p.read_bytes() for p in changes}
    staged, installed = {}, []
    try:
        for p, raw in changes.items():
            if sha(before[p]) != expected[p]: raise ValueError('STALE_FILE before staging: ' + str(p))
            fd, name = tempfile.mkstemp(prefix=p.name + '.readimage-', suffix='.tmp', dir=p.parent)
            with os.fdopen(fd, 'wb') as f: f.write(raw); f.flush(); os.fsync(f.fileno())
            staged[p] = Path(name)
        for p in changes:
            if sha(p.read_bytes()) != expected[p]: raise ValueError('STALE_FILE before commit: ' + str(p))
        for p in changes: os.replace(staged[p], p); installed.append(p)
    except Exception:
        for p in reversed(installed):
            fd, name = tempfile.mkstemp(prefix=p.name + '.restore-', dir=p.parent)
            with os.fdopen(fd, 'wb') as f: f.write(before[p])
            os.replace(name, p)
        raise
    finally:
        for p in staged.values(): p.unlink(missing_ok=True)


def detect():
    explicit = os.environ.get('SHUNCODE_EXTENSION_DIR')
    if explicit: return Path(explicit)
    candidates = [Path('D:/shuncode/ShunCode/resources/app/extensions/shuncode')]
    if os.environ.get('LOCALAPPDATA'):
        candidates.append(Path(os.environ['LOCALAPPDATA']) / 'Programs/ShunCode/resources/app/extensions/shuncode')
    found = [p for p in candidates if p.is_dir()]
    if len(found) != 1: raise ValueError('Specify --dir: no unique supported installation found; no drive-wide scan is performed')
    return found[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dir', type=Path, help='.../resources/app/extensions/shuncode directory')
    ap.add_argument('--backup-dir', type=Path, default=Path.home() / '.deepseekpp-shuncode-backups')
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--apply', action='store_true', help='Explicitly apply after closing ShunCode; never changes settings')
    mode.add_argument('--restore', type=Path, help='Local backup receipt.json; rejects a newer/different installed version')
    args = ap.parse_args()
    root = (args.dir or detect()).resolve()
    files = {name: root / name for name in TARGETS}
    for name, p in files.items():
        if not p.is_file() or p.is_symlink() or root not in p.resolve().parents: raise ValueError('Missing/non-regular target: ' + name)
    old = {name: p.read_bytes() for name, p in files.items()}
    if args.restore:
        receipt_path = args.restore.resolve()
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        if receipt.get('schema') != 1 or Path(receipt['installation']).resolve() != root: raise ValueError('Receipt belongs to another installation')
        if receipt.get('state') != 'applied' or set(receipt.get('files', {})) != set(TARGETS): raise ValueError('Receipt is incomplete or was not applied')
        values = {}
        for name in TARGETS:
            item = receipt['files'][name]
            if sha(old[name]) != item['after']: raise ValueError('Installed file changed since patch; do not overwrite a product upgrade')
            raw = (receipt_path.parent / name).read_bytes()
            if sha(raw) != item['before']: raise ValueError('Backup checksum mismatch')
            values[files[name]] = raw
        syntax(values.values()); atomic_write(values, {files[n]: sha(old[n]) for n in TARGETS})
        receipt['state'] = 'restored'; receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        print('RESTORED. Restart ShunCode.'); return 0
    plans = {name: inspect(raw) for name, raw in old.items()}
    print(json.dumps({'installation': str(root), 'files': {n: {'state': state, 'before': sha(old[n]), 'after': sha(raw)} for n, (state, raw) in plans.items()}}, ensure_ascii=False, indent=2))
    needed = [n for n, (state, _) in plans.items() if state == 'need']
    if not needed: print('ALREADY: both read_image handlers emit image blocks; no files changed.'); return 0
    if not args.apply: print('NEED: read-only check; close ShunCode and use --apply after reviewing this result.'); return 1
    syntax(raw for _, raw in plans.values())
    backup_root = args.backup_dir.resolve()
    if backup_root == root or root in backup_root.parents: raise ValueError('Backup directory must be outside installation to survive overwrite installs')
    backup_root.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-'), dir=backup_root))
    receipt = {'schema': 1, 'state': 'prepared', 'installation': str(root), 'files': {n: {'before': sha(old[n]), 'after': sha(plans[n][1])} for n in TARGETS}}
    for n in TARGETS: (run / n).parent.mkdir(parents=True, exist_ok=True); (run / n).write_bytes(old[n])
    rp = run / 'receipt.json'; rp.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    try:
        atomic_write({files[n]: plans[n][1] for n in TARGETS}, {files[n]: sha(old[n]) for n in TARGETS})
    except Exception:
        receipt['state'] = 'failed'; rp.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8'); raise
    receipt['state'] = 'applied'; rp.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('APPLIED; local backup receipt: ' + str(rp)); print('Restart ShunCode, reconnect MCP, and test a small non-sensitive image.'); return 0


if __name__ == '__main__':
    try: sys.exit(main())
    except (ValueError, OSError, KeyError) as error: print('BLOCKED: ' + str(error), file=sys.stderr); sys.exit(2)
