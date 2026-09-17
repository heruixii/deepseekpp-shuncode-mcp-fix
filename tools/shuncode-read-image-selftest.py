#!/usr/bin/env python3
"""Offline fixtures only; never changes a real ShunCode installation."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('native_patch', HERE / 'shuncode-read-image-patch.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
SCRIPT = str(HERE / 'shuncode-read-image-patch.py')
OLD = b'''async function run(canonicalName, normalizedArgs, context) {
  if (canonicalName === READ_IMAGE_TOOL.name) {
    const result = await readImage(parseReadImageInput(normalizedArgs), {
      workspaceRoots: context.workspaceRoots,
      signal: context.signal
    });
    const text = formatReadImageForModel(result);
    const content = [{ type: "text", text }];
    if (result.status === "error") {
      return { text, structuredContent: result, content, isError: true };
    }
    const { base64: base643, ...metadata } = result;
    return { text, structuredContent: metadata, content };
  }
  if (canonicalName === SEARCH_FILES_TOOL.name) { return {}; }
}
'''

class NativePatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='native-image-fixture-')
        self.root = Path(self.tmp.name) / 'install'
        self.backups = Path(self.tmp.name) / 'backups'
        for name in mod.TARGETS:
            p = self.root / name; p.parent.mkdir(parents=True); p.write_bytes(OLD)
    def tearDown(self): self.tmp.cleanup()
    def cli(self, *args):
        return subprocess.run([sys.executable, SCRIPT, '--dir', str(self.root), '--backup-dir', str(self.backups), *map(str, args)], capture_output=True, text=True)
    def receipt(self): return next(self.backups.glob('*/receipt.json'))
    def assert_original(self):
        for n in mod.TARGETS: self.assertEqual((self.root/n).read_bytes(), OLD)
    def test_01_detect_need(self): self.assertEqual(mod.inspect(OLD)[0], 'need')
    def test_02_aliases(self):
        for var in (b'base642', b'imageData'):
            state, out = mod.inspect(OLD.replace(b'base643', var)); self.assertEqual(state, 'need'); self.assertIn(b'data: ' + var, out)
    def test_03_default_readonly(self):
        self.assertEqual(self.cli().returncode, 1); self.assert_original(); self.assertFalse(self.backups.exists())
    def test_04_idempotent(self):
        _, out = mod.inspect(OLD); self.assertEqual(mod.inspect(out), ('already', out))
    def test_05_unrelated_image_not_already(self):
        self.assertEqual(mod.inspect(b'function other(){ content.push({ type: "image", data: "x" }); }\n'+OLD)[0], 'need')
    def test_06_duplicate_handler_refused(self):
        with self.assertRaises(ValueError): mod.inspect(OLD+OLD)
    def test_07_unknown_success_refused(self):
        with self.assertRaises(ValueError): mod.inspect(OLD.replace(b'structuredContent: metadata', b'structuredContent: someOtherData'))
    def test_08_missing_boundary_refused(self):
        with self.assertRaises(ValueError): mod.inspect(OLD.replace(b'SEARCH_FILES_TOOL', b'searchFilesTool'))
    def test_09_crlf_bom_preserved(self):
        raw=b'\xef\xbb\xbf'+OLD.replace(b'\n', b'\r\n'); _, out=mod.inspect(raw)
        self.assertTrue(out.startswith(b'\xef\xbb\xbf')); self.assertNotIn(b'\n', out.replace(b'\r\n', b''))
    def test_10_pair_preflight_refuses_partial(self):
        p=self.root/mod.TARGETS[1]; p.write_bytes(b'unknown new version')
        self.assertEqual(self.cli('--apply').returncode, 2); self.assertEqual((self.root/mod.TARGETS[0]).read_bytes(), OLD); self.assertFalse(self.backups.exists())
    def test_11_missing_file_refused(self):
        (self.root/mod.TARGETS[1]).unlink(); self.assertEqual(self.cli('--apply').returncode, 2)
    def test_12_apply_backup_check_restore(self):
        r=self.cli('--apply'); self.assertEqual(r.returncode, 0, r.stdout+r.stderr)
        receipt=self.receipt(); self.assertEqual(json.loads(receipt.read_text())['state'], 'applied')
        for name in mod.TARGETS: self.assertEqual((receipt.parent/name).read_bytes(), OLD)
        self.assertEqual(self.cli('--check').returncode, 0)
        self.assertEqual(self.cli('--apply').returncode, 0); self.assertEqual(len(list(self.backups.iterdir())), 1)
        r=self.cli('--restore', receipt); self.assertEqual(r.returncode, 0, r.stderr); self.assert_original()
    def test_13_restore_refuses_product_upgrade(self):
        self.assertEqual(self.cli('--apply').returncode, 0)
        p=self.root/mod.TARGETS[0]; newer=p.read_bytes()+b'\n// newer product\n'; p.write_bytes(newer)
        self.assertEqual(self.cli('--restore', self.receipt()).returncode, 2); self.assertEqual(p.read_bytes(), newer)
    def test_14_tampered_backup_refused(self):
        self.assertEqual(self.cli('--apply').returncode, 0)
        receipt=self.receipt(); (receipt.parent/mod.TARGETS[0]).write_bytes(b'tampered')
        self.assertEqual(self.cli('--restore', receipt).returncode, 2)
    def test_15_no_backups_inside_install(self):
        self.assertEqual(self.cli('--apply','--backup-dir',self.root/'backup').returncode, 2); self.assert_original()
    def test_16_partial_replace_failure_restores(self):
        paths=[self.root/n for n in mod.TARGETS]; real_replace=mod.os.replace; calls=[0]
        def fail_second(a,b):
            calls[0]+=1
            if calls[0]==2: raise OSError('fixture failure')
            return real_replace(a,b)
        with patch.object(mod.os, 'replace', side_effect=fail_second):
            with self.assertRaises(OSError): mod.atomic_write({p:mod.inspect(OLD)[1] for p in paths},{p:mod.sha(OLD) for p in paths})
        self.assert_original()
    def test_17_stale_hash_refused(self):
        p=self.root/mod.TARGETS[0]
        with self.assertRaises(ValueError): mod.atomic_write({p:b'new'},{p:'wrong'})
        self.assert_original()
    def test_18_unknown_image_push_refused(self):
        raw=OLD.replace(b'    return { text, structuredContent: metadata', b'    content.push({ type: "image", data: wrongVariable });\n    return { text, structuredContent: metadata')
        with self.assertRaises(ValueError): mod.inspect(raw)
    def test_19_syntax_failure_no_write(self):
        for n in mod.TARGETS: (self.root/n).write_bytes(OLD+b'\nlet = ;')
        self.assertEqual(self.cli('--apply').returncode, 2); self.assertFalse(self.backups.exists())
    def test_20_mixed_known_pair_supported(self):
        (self.root/mod.TARGETS[0]).write_bytes(mod.inspect(OLD)[1]); self.assertEqual(self.cli('--apply').returncode, 0)
        self.assertEqual(self.cli('--check').returncode, 0)
    def test_21_duplicate_native_push_refused(self):
        _, out=mod.inspect(OLD); line=b'    content.push({ type: "image", data: base643, mimeType: result.mime_type });'
        with self.assertRaises(ValueError): mod.inspect(out.replace(line,line+b'\n'+line))
    def test_22_no_alias_supported(self):
        state,out=mod.inspect(OLD.replace(b'base64: base643', b'base64')); self.assertEqual(state,'need'); self.assertIn(b'data: base64,',out)

if __name__ == '__main__': unittest.main(verbosity=2)
