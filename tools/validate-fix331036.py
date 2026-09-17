#!/usr/bin/env python3
"""Offline .36 release gate; never modifies live installs or uploads images.
python tools/validate-fix331036.py --root . --baseline BASE_35 --output NEW_EXTERNAL_DIR
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


def sha(raw): return hashlib.sha256(raw).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    root=a.root.resolve();base=a.baseline.resolve();out=a.output.resolve()
    if out.exists() or out==root or root in out.parents:raise ValueError('Use new output directory outside repository')
    out.mkdir(parents=True);logs=out/'logs';logs.mkdir();checks=[];tests=[]
    def check(name,cond):
        checks.append({'name':name,'passed':bool(cond)});print(('PASS ' if cond else 'FAIL ')+name,flush=True)
    def run(name,cmd):
        r=subprocess.run(cmd,cwd=root,capture_output=True,timeout=180,env={**os.environ,'DPP_ROOT':str(root)})
        (logs/(name+'.log')).write_bytes(r.stdout+b'\n'+r.stderr);tests.append({'name':name,'passed':r.returncode==0,'exit_code':r.returncode});print(('PASS ' if r.returncode==0 else 'FAIL ')+name,flush=True)
    tools=root/'tools';spec=importlib.util.spec_from_file_location('builder36',tools/'apply-fix331036.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    rebuilt=builder.build(base,out/'rebuilt')
    runtime=json.loads((tools/'fix331035-baseline-sha256.json').read_text(encoding='utf-8'))
    expected_runtime_changes={'content-scripts/content.js','fix3-policy.js','manifest.json','_locales/en/messages.json','_locales/zh_CN/messages.json'}
    check('exact_five_runtime_changes',{n for n in runtime if (root/n).read_bytes()!=(base/n).read_bytes()}==expected_runtime_changes)
    check('independently_rebuilt_runtime',all((root/n).read_bytes()==rebuilt[n] for n in runtime))
    check('background_unchanged',(root/'background.js').read_bytes()==(base/'background.js').read_bytes())
    original=json.loads((base/'manifest.json').read_text(encoding='utf-8'));mf=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    check('version',mf['version']=='1.14.0.41' and mf['version_name']=='1.14.0 ShunCode MCP Fix 3.3.10.36')
    check('manifest_only_version_changed',{k:v for k,v in mf.items() if k not in ('version','version_name')}=={k:v for k,v in original.items() if k not in ('version','version_name')})
    for lang in ['en','zh_CN']:
        d=json.loads((root/f'_locales/{lang}/messages.json').read_text(encoding='utf-8'));check('locale:'+lang,d['extension_name']['message']=='DeepSeek++ ShunCode MCP Fix 3.3.10.36')
    suites=sorted(root.glob('*selftest*.js'));check('55_legacy_suites',len(suites)==55)
    check('legacy_test_changes_only_version_gates',all(p.read_bytes()==rebuilt[p.name] for p in suites))
    check('native_maintenance_unchanged',all((tools/n).read_bytes()==(base/'tools'/n).read_bytes() for n in ['shuncode-read-image-patch.py','shuncode-read-image-selftest.py']))
    check('image_transport_sources_unchanged',all((tools/n).read_bytes()==(base/'tools'/n).read_bytes() for n in ['dspp-readimage-v7-runtime.js','dspp-readimage-v7-background.js']))
    check('no_new_runtime_permissions',mf['permissions']==original['permissions'] and mf['host_permissions']==original['host_permissions'])
    for n in ['apply-fix331036.py','validate-fix331036.py']:
        ast.parse((tools/n).read_text(encoding='utf-8'));check('python_ast:'+n,True)
    for n in ['content-scripts/content.js','background.js','fix3-policy.js','tools/dspp-visual-workflow-v8.js','tools/dspp-unregistered-tag-v8.js','tools/dspp-visual-workflow-v8-selftest.js']:
        run('syntax-'+Path(n).name,['node','--check',str(root/n)])
    run('visual-workflow-v8',['node',str(tools/'dspp-visual-workflow-v8-selftest.js'),str(root)])
    run('image-runtime-v7',['node',str(tools/'dspp-readimage-v7-selftest.js'),str(root/'content-scripts/content.js')])
    run('image-boundary-v7',['node',str(tools/'dspp-readimage-v7-boundary-selftest.js'),str(root)])
    run('native-maintenance',[sys.executable,str(tools/'shuncode-read-image-selftest.py')])
    for p in suites:run(p.stem,['node',str(p)])
    hashes={n:sha((root/n).read_bytes()) for n in sorted(expected_runtime_changes|{'background.js'})}
    report={'release':'v1.14.0-fix3.3.10.36','passed':all(x['passed'] for x in checks+tests),'checks':checks,'tests':tests,'runtime_sha256':hashes,'browser_model_acceptance':'pending user reload and a fresh SVG task; not proven by offline fixtures'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':report['passed'],'checks':len(checks),'test_processes':len(tests),'legacy_suites':len(suites)},indent=2));return 0 if report['passed'] else 1

if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError) as e:raise SystemExit('FAIL-CLOSED: '+str(e))
