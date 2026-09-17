#!/usr/bin/env python3
"""Offline release gate. Logs/report go to a NEW output folder outside the repository.
Usage: python tools/validate-fix331035.py --root . --baseline BASE_34 --output NEW_REPORT_DIR
Never reloads browsers, uploads an image, modifies native installs or publishes.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def sha(raw): return hashlib.sha256(raw).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    ap.add_argument('--baseline',type=Path)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); root=a.root.resolve(); output=a.output.resolve()
    if output.exists() or output==root or root in output.parents: raise ValueError('Use a new report directory outside repository')
    output.mkdir(parents=True); logs=output/'logs'; logs.mkdir()
    tests=[]; checks=[]
    def check(name, condition):
        checks.append({'name':name,'passed':bool(condition)})
        print(('PASS ' if condition else 'FAIL ')+name,flush=True)
    def run(name,command):
        try:
            r=subprocess.run(command,cwd=root,capture_output=True,timeout=180)
            (logs/(name+'.log')).write_bytes(r.stdout+b'\n'+r.stderr)
            passed=r.returncode==0; code=r.returncode
        except subprocess.TimeoutExpired:
            passed=False; code='timeout'; (logs/(name+'.log')).write_text('Timed out after 180 seconds')
        tests.append({'name':name,'passed':passed,'exit_code':code})
        print(('PASS ' if passed else 'FAIL ')+name,flush=True)
    tools=root/'tools'
    spec=importlib.util.spec_from_file_location('release_builder',tools/'apply-fix331035.py'); builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
    for n,h in builder.TARGET.items(): check('runtime_hash:'+n,sha((root/n).read_bytes())==h)
    for n,h in builder.SOURCES.items(): check('source_hash:'+n,sha((tools/n).read_bytes())==h)
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    check('manifest_version',manifest['version']=='1.14.0.40')
    check('manifest_version_name',manifest['version_name']=='1.14.0 ShunCode MCP Fix 3.3.10.35')
    for lang in ('en','zh_CN'):
        locale=json.loads((root/f'_locales/{lang}/messages.json').read_text(encoding='utf-8'))
        check('locale:'+lang,locale['extension_name']['message']=='DeepSeek++ ShunCode MCP Fix 3.3.10.35')
    check('historical_background_fixture',sha((tools/'fixtures/readimage-v6-background.txt').read_bytes())=='ed5751c7dfa819e51bb8df24beea990c505db7eb6f7c3654fa58217177844f32')
    suites=sorted(root.glob('*selftest*.js')); check('legacy_suite_count',len(suites)==55)
    for n in ['apply-fix331035.py','readimage-build-core.py','validate-fix331035.py','shuncode-read-image-patch.py','shuncode-read-image-selftest.py']:
        try: ast.parse((tools/n).read_text(encoding='utf-8')); good=True
        except SyntaxError: good=False
        check('python_ast:'+n,good)
    for relative in ('content-scripts/content.js','background.js','tools/dspp-readimage-v7-runtime.js','tools/dspp-readimage-v7-background.js','tools/dspp-readimage-v7-selftest.js','tools/dspp-readimage-v7-boundary-selftest.js'):
        run('syntax-'+Path(relative).name,['node','--check',str(root/relative)])
    run('readimage-runtime-22',['node',str(tools/'dspp-readimage-v7-selftest.js'),str(root/'content-scripts/content.js')])
    run('readimage-real-boundary-16',['node',str(tools/'dspp-readimage-v7-boundary-selftest.js'),str(root)])
    run('native-maintenance-22',[sys.executable,str(tools/'shuncode-read-image-selftest.py')])
    for suite in suites: run(suite.stem,['node',str(suite),str(root)])
    if a.baseline:
        baseline=a.baseline.resolve()
        rebuilt=builder.build(baseline,output/'rebuilt-runtime')
        check('reproduced_runtime_tree',all((root/n).read_bytes()==raw for n,raw in rebuilt.items()))
        original_manifest=json.loads((baseline/'manifest.json').read_text(encoding='utf-8'))
        check('only_version_fields_changed_in_manifest',{k:v for k,v in manifest.items() if k not in ('version','version_name')}=={k:v for k,v in original_manifest.items() if k not in ('version','version_name')})
        check('legacy_changes_only_version_gates',all(s.read_text(encoding='utf-8')==builder.version_gates((baseline/s.name).read_text(encoding='utf-8')) for s in suites))
        changed=[n for n in rebuilt if (baseline/n).read_bytes()!=rebuilt[n]]
        check('exact_five_runtime_changes',set(changed)=={'content-scripts/content.js','background.js','manifest.json','_locales/en/messages.json','_locales/zh_CN/messages.json'})
    report={'release':'v1.14.0-fix3.3.10.35','passed':all(c['passed'] for c in checks+tests),'checks':checks,'tests':tests,'reproducible_build':'passed' if a.baseline and all(c['passed'] for c in checks) else 'not_passed_or_not_requested','browser_http_test':'not performed by this offline validator'}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'checks':len(checks),'test_processes':len(tests),'legacy_suites':len(suites)},indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,OSError) as error: raise SystemExit('FAIL-CLOSED: '+str(error))
