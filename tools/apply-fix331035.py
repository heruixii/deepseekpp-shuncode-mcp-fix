#!/usr/bin/env python3
"""Rebuild Fix 3.3.10.35 runtime from a hash-locked .34 archive, into a NEW directory.
Copies only files in the committed baseline inventory; no local browser/native data.
Run: python tools/apply-fix331035.py BASE_34 NEW_OUTPUT
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TARGET = {'content-scripts/content.js': '76c02e472300316dd537af587dc3630d13a45ef3bde0b03aca189f7d640586d4', 'background.js': '4f89a4d8b8d92a0e8c8661fdc5fc3a1745f39e2de2fc3306e0b3d9e7c87e3abc'}
SOURCES = {'dspp-readimage-v6-runtime.js': 'c40d2a5cc594c570e13e023aadbc51e4de3dec1d27492671a559cdd26642f73e', 'dspp-readimage-v7-runtime.js': '07ebf98fc03912c4546dd09f976a6f465ded64ffb9a786c4515d710d47253e17', 'dspp-readimage-v7-background.js': '90e2f9c119bd03ab41511a73f72a9ab691a368c57105275b56f9b061ce9ae9c7'}

def sha(raw): return hashlib.sha256(raw).hexdigest()

def version_gates(text):
    """Only release metadata gates change in the 55 existing behavior suites."""
    return (text.replace('1.14.0.39', '1.14.0.40')
            .replace('1.14.0 ShunCode MCP Fix 3.3.10.34', '1.14.0 ShunCode MCP Fix 3.3.10.35')
            .replace('manifest version_name is Fix 3.3.10.34', 'manifest version_name is Fix 3.3.10.35')
            .replace('|30|31|32|33|34)$', '|30|31|32|33|34|35)$'))

def build(base, output):
    base, output = Path(base).resolve(), Path(output).resolve()
    if output.exists() or base == output or base in output.parents: raise ValueError('Output must be new and outside baseline')
    inventory = json.loads((HERE / 'fix331035-baseline-sha256.json').read_text(encoding='utf-8'))
    values = {}
    for relative, digest in inventory.items():
        p = base / relative
        if Path(relative).is_absolute() or '..' in Path(relative).parts or p.is_symlink() or base not in p.resolve().parents: raise ValueError('Unsafe baseline path')
        raw = p.read_bytes()
        if sha(raw) != digest: raise ValueError('Baseline hash mismatch: ' + relative)
        values[relative] = raw
    sources = {name: (HERE / name).read_bytes() for name in SOURCES}
    for name, digest in SOURCES.items():
        if sha(sources[name]) != digest: raise ValueError('Build-source hash mismatch: ' + name)
    spec = importlib.util.spec_from_file_location('readimage_build_core', HERE / 'readimage-build-core.py')
    core = importlib.util.module_from_spec(spec); spec.loader.exec_module(core)
    # The public .34 Git archive stores these two JS files with LF. Historical
    # Windows deployment/build locks used CRLF; reconstruct that representation
    # explicitly before applying the already-validated transformations.
    windows = lambda raw: raw.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    v6 = core.build_v6(windows(values['content-scripts/content.js']), sources['dspp-readimage-v6-runtime.js'])
    c, b = core.build_v7(v6, windows(values['background.js']), sources['dspp-readimage-v7-runtime.js'], sources['dspp-readimage-v7-background.js'])
    values.update({'content-scripts/content.js': c, 'background.js': b})
    for name, digest in TARGET.items():
        if sha(values[name]) != digest: raise ValueError('Built runtime hash mismatch: ' + name)
        result = subprocess.run(['node', '--check', '--input-type=module'], input=values[name], capture_output=True)
        if result.returncode: raise ValueError('Node syntax check failed: ' + name)
    manifest = values['manifest.json']
    for old, new in [(b'"version": "1.14.0.39"', b'"version": "1.14.0.40"'), (b'1.14.0 ShunCode MCP Fix 3.3.10.34', b'1.14.0 ShunCode MCP Fix 3.3.10.35')]:
        if manifest.count(old) != 1: raise ValueError('Manifest version anchor mismatch')
        manifest = manifest.replace(old, new, 1)
    values['manifest.json'] = manifest
    for language in ('en', 'zh_CN'):
        name = '_locales/' + language + '/messages.json'; old = b'DeepSeek++ ShunCode MCP Fix 3.3.10.34'
        if values[name].count(old) != 1: raise ValueError('Locale version anchor mismatch: ' + language)
        values[name] = values[name].replace(old, b'DeepSeek++ ShunCode MCP Fix 3.3.10.35', 1)
    output.mkdir(parents=True)
    for name, raw in values.items():
        p = output / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)
    print(json.dumps({'version': '1.14.0.40', 'runtime_files': len(values), 'hashes': {n: sha(values[n]) for n in TARGET}}, indent=2))
    return values

if __name__ == '__main__':
    if len(sys.argv) != 3: raise SystemExit(__doc__)
    try: build(sys.argv[1], sys.argv[2])
    except (ValueError, OSError) as error: raise SystemExit('FAIL-CLOSED: ' + str(error))
