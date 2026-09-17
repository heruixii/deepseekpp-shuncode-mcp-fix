#!/usr/bin/env python3
"""Offline .42 release gate; never modifies live installs or uploads images.
python tools/validate-fix331042.py --root CANDIDATE --baseline BASE_36 --output NEW_EXTERNAL_DIR
.42 = .41 + exposure drift fix (fix3-policy.js, background.js, content.js whitelist).
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
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--tools',type=Path,default=None);a=ap.parse_args()
    root=a.root.resolve();base=a.baseline.resolve();out=a.output.resolve();tools=(a.tools or (base/'tools')).resolve()
    if out.exists() or out==root or root in out.parents:raise ValueError('Use new output directory outside candidate')
    out.mkdir(parents=True);logs=out/'logs';logs.mkdir();checks=[];tests=[]
    def check(name,cond):
        checks.append({'name':name,'passed':bool(cond)});print(('PASS ' if cond else 'FAIL ')+name,flush=True)
    def run(name,cmd,cwd=root):
        r=subprocess.run(cmd,cwd=cwd,capture_output=True,timeout=300,env={**os.environ,'DPP_ROOT':str(root)})
        (logs/(name+'.log')).write_bytes(r.stdout+b'\n'+r.stderr);tests.append({'name':name,'passed':r.returncode==0,'exit_code':r.returncode});print(('PASS ' if r.returncode==0 else 'FAIL ')+name,flush=True)
    spec=importlib.util.spec_from_file_location('builder42',tools/'apply-fix331042.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    rebuilt=builder.build(base,out/'rebuilt')
    inventory=json.loads((tools/'fix331037-baseline-sha256.json').read_text(encoding='utf-8'))
    allowed={'background.js','content-scripts/content.js','content-scripts/main-world.js','fix3-policy.js','manifest.json','_locales/en/messages.json','_locales/zh_CN/messages.json'}
    changed={n for n in inventory if (root/n).exists() and (root/n).read_bytes()!=(base/n).read_bytes()}
    selftest_changes={n for n in changed if '/' not in n and 'selftest' in n}
    check('runtime_changes_exactly_allowed',(changed-selftest_changes)==allowed)
    check('independently_rebuilt_all_files',all((root/n).read_bytes()==rebuilt[n] for n in inventory))
    extras=['dspp-bare-tool-tag-v41-selftest.js','dspp-exposure-drift-v42-selftest.js']
    check('no_extra_files',sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file())==sorted(list(inventory)+extras))
    bg=(root/'background.js').read_text(encoding='utf-8');old=(base/'background.js').read_text(encoding='utf-8')
    def seg(s,a,b): i=s.index(a);j=s.index(b,i);return s[i:j].replace('\r\n','\n')
    check('gate_functions_unchanged',all(seg(bg,x,y)==seg(old,x,y) for x,y in [('function wN(','function TN('),('function TN(','function EN('),('function EN(','function DN('),('function DN(','function ON('),('async function aI(','async function oI('),('async function DPP_ASSERT_CURRENT_UPLOAD_V7(','async function DPP_DISPATCH_UPLOAD_V7(')]))
    check('allowlist_unchanged',seg(bg,'xN=new Set(`','`.split')==seg(old,'xN=new Set(`','`.split'))
    # .42 background: exactly three literal edits relative to .41 background
    bg41=rebuilt41=None
    spec41=importlib.util.spec_from_file_location('builder41',tools/'apply-fix331041.py');b41=importlib.util.module_from_spec(spec41);spec41.loader.exec_module(b41)
    v41=b41.build(base,out/'rebuilt41')
    e=lambda s:s.encode('utf-8')
    bg41=v41['background.js']
    exp=bg41.replace(e(builder.OLD_DEFAULTS),e(builder.NEW_DEFAULTS),1).replace(e(builder.OLD_CEILING),e(builder.NEW_CEILING),1).replace(e(builder.OLD_FLOOR),e(builder.NEW_FLOOR),1)
    check('background_is_41_plus_three_literals',exp==(root/'background.js').read_bytes())
    pol=(root/'fix3-policy.js').read_text(encoding='utf-8');pol41=v41['fix3-policy.js']
    check('policy_is_41_plus_two_literals',pol41.replace(e(builder.OLD_TRIGGER),e(builder.NEW_TRIGGER),1).replace(e(builder.OLD_MODE),e(builder.NEW_MODE),1)==(root/'fix3-policy.js').read_bytes())
    cjs=(root/'content-scripts/content.js').read_text(encoding='utf-8');c41=v41['content-scripts/content.js']
    check('content_is_41_plus_whitelist_literal',c41.replace(e(builder.OLD_DIAG_ROW),e(builder.NEW_DIAG_ROW),1)==(root/'content-scripts/content.js').read_bytes())
    check('v41_suite_repointed_not_dropped',(root/'dspp-bare-tool-tag-v41-selftest.js').read_bytes()==builder.gates(v41['dspp-bare-tool-tag-v41-selftest.js'].decode('utf-8')).encode('utf-8').replace(e(builder.OLD_41_BG_ASSERT),e(builder.NEW_41_BG_ASSERT%sha((root/'background.js').read_bytes())),1))
    check('mw_identical_to_41',(root/'content-scripts/main-world.js').read_bytes()==v41['content-scripts/main-world.js'])
    check('v41_block_still_present',cjs.count('DPP_BARE_TOOL_TAG_V41_BEGIN')==1)
    check('resolution_in_whitelist','resolution:typeof t.resolution==`string`?t.resolution.slice(0,40):null' in cjs)
    check('no_auth_keywords_in_policy_diff',all(k not in builder.NEW_MODE+builder.NEW_TRIGGER for k in ['Authorization','token','runtime_message_unauthorized']))
    original=json.loads((base/'manifest.json').read_text(encoding='utf-8'));mf=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    check('version',mf['version']=='1.14.0.47' and mf['version_name']=='1.14.0 ShunCode MCP Fix 3.3.10.42')
    check('manifest_only_version_changed',{k:v for k,v in mf.items() if k not in ('version','version_name')}=={k:v for k,v in original.items() if k not in ('version','version_name')})
    check('no_new_runtime_permissions',mf['permissions']==original['permissions'] and mf['host_permissions']==original['host_permissions'])
    for lang in ['en','zh_CN']:
        d=json.loads((root/f'_locales/{lang}/messages.json').read_text(encoding='utf-8'));check('locale:'+lang,d['extension_name']['message']=='DeepSeek++ ShunCode MCP Fix 3.3.10.42')
    suites=sorted(root.glob('*selftest*.js'));check('57_suites',len(suites)==57)
    for n in ['apply-fix331041.py','apply-fix331042.py','validate-fix331042.py']:
        ast.parse((tools/n).read_text(encoding='utf-8'));check('python_ast:'+n,True)
    for n in ['content-scripts/content.js','background.js','fix3-policy.js','content-scripts/main-world.js']:
        run('syntax-'+Path(n).name,['node','--check',str(root/n)])
    run('skill-popup-observe',['node',str(tools/'dspp-skill-popup-observe-selftest.js'),str(root),str(base)])
    run('mw-bridge-diag-v10',['node',str(tools/'dspp-mw-bridge-diag-v10-selftest.js'),str(root),str(base)])
    run('upload-gate-v10',['node',str(tools/'dspp-upload-gate-v10-selftest.js'),str(root),str(base)])
    run('visual-workflow-v8',['node',str(tools/'dspp-visual-workflow-v8-selftest.js'),str(root)])
    run('image-runtime-v7',['node',str(tools/'dspp-readimage-v7-selftest.js'),str(root/'content-scripts/content.js')])
    run('image-boundary-v7',['node',str(tools/'dspp-readimage-v7-boundary-selftest.js'),str(root)])
    run('bare-tool-tag-v41',['node',str(root/'dspp-bare-tool-tag-v41-selftest.js')])
    run('exposure-drift-v42',['node',str(root/'dspp-exposure-drift-v42-selftest.js'),str(root)])
    for p in suites:run(p.stem,['node',str(p)])
    hashes={n:sha((root/n).read_bytes()) for n in sorted(allowed)}
    report={'release':'v1.14.0-fix3.3.10.42','passed':all(x['passed'] for x in checks+tests),'checks':checks,'tests':tests,'runtime_sha256':hashes,'browser_model_acceptance':'pending: reload extension, close old DeepSeek tabs, new session; web_response_diag.descriptorNames must list all 15 ShunCode tools on every turn'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':report['passed'],'checks':len(checks),'test_processes':len(tests),'suites':len(suites)},indent=2));return 0 if report['passed'] else 1

if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError) as e:raise SystemExit('FAIL-CLOSED: '+str(e))
