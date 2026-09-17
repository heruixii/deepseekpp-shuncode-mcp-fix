#!/usr/bin/env python3
"""Offline .43 release gate; never modifies live installs or uploads images.
python tools/validate-fix331043.py --root CANDIDATE --baseline BASE_36 --output NEW_EXTERNAL_DIR
.43 = .42 + trigger 64k, Zo() keeps MCP image blocks, v7 note + visual rules name include_data_uri.
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
    spec=importlib.util.spec_from_file_location('builder43',tools/'apply-fix331043.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    rebuilt=builder.build(base,out/'rebuilt')
    inventory=json.loads((tools/'fix331037-baseline-sha256.json').read_text(encoding='utf-8'))
    allowed={'background.js','content-scripts/content.js','content-scripts/main-world.js','fix3-policy.js','manifest.json','_locales/en/messages.json','_locales/zh_CN/messages.json'}
    changed={n for n in inventory if (root/n).exists() and (root/n).read_bytes()!=(base/n).read_bytes()}
    selftest_changes={n for n in changed if '/' not in n and 'selftest' in n}
    check('runtime_changes_exactly_allowed',(changed-selftest_changes)==allowed)
    check('independently_rebuilt_all_files',all((root/n).read_bytes()==rebuilt[n] for n in inventory))
    extras=['dspp-bare-tool-tag-v41-selftest.js','dspp-exposure-drift-v42-selftest.js','dspp-image-block-v43-selftest.js']
    check('no_extra_files',sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file())==sorted(list(inventory)+extras))
    bg=(root/'background.js').read_text(encoding='utf-8');old=(base/'background.js').read_text(encoding='utf-8')
    def seg(s,a,b): i=s.index(a);j=s.index(b,i);return s[i:j].replace('\r\n','\n')
    check('gate_functions_unchanged',all(seg(bg,x,y)==seg(old,x,y) for x,y in [('function wN(','function TN('),('function TN(','function EN('),('function EN(','function DN('),('function DN(','function ON('),('async function aI(','async function oI('),('async function DPP_ASSERT_CURRENT_UPLOAD_V7(','async function DPP_DISPATCH_UPLOAD_V7(')]))
    check('allowlist_unchanged',seg(bg,'xN=new Set(`','`.split')==seg(old,'xN=new Set(`','`.split'))
    # .43: exact literal diffs relative to an independent .42 rebuild
    spec42=importlib.util.spec_from_file_location('builder42',tools/'apply-fix331042.py');b42=importlib.util.module_from_spec(spec42);spec42.loader.exec_module(b42)
    v42=b42.build(base,out/'rebuilt42')
    e=lambda s:s.encode('utf-8')
    check('background_is_42_plus_Zo_literal',v42['background.js'].replace(e(builder.OLD_ZO),e(builder.NEW_ZO),1)==(root/'background.js').read_bytes())
    check('policy_is_42_plus_trigger_literal',v42['fix3-policy.js'].replace(e(builder.OLD_TRIGGER),e(builder.NEW_TRIGGER),1)==(root/'fix3-policy.js').read_bytes())
    c42=v42['content-scripts/content.js']
    for o,n in [(builder.OLD_NOTE,builder.NEW_NOTE),(builder.OLD_RULES_ZH,builder.NEW_RULES_ZH),(builder.OLD_RULES_EN,builder.NEW_RULES_EN)]:c42=c42.replace(e(o),e(n),1)
    check('content_is_42_plus_three_literals',c42==(root/'content-scripts/content.js').read_bytes())
    check('mw_identical_to_42',(root/'content-scripts/main-world.js').read_bytes()==v42['content-scripts/main-world.js'])
    cjs=(root/'content-scripts/content.js').read_text(encoding='utf-8')
    zo=bg[bg.index('function Zo('):bg.index('function Qo(')]
    check('Zo_only_copies_type_mimeType_data','({type:`image`,mimeType:e.mimeType,data:e.data})' in zo and 'text' not in zo.replace('structuredContent',''))
    check('Zo_never_clobbers_own_content','t.content===void 0&&(t.content=n)' in zo)
    check('Zo_capped_four','.slice(0,4)' in zo)
    check('v7_collect_walker_unchanged','for (const key of [\'result\', \'details\', \'output\', \'structuredContent\', \'content\']) walk(o[key], depth + 1);' in cjs)
    check('v7_redact_unchanged',"['data_uri', 'dataUri', 'dataURL'].includes(key) || (value.type === 'image' && key === 'data') ? '[image bytes omitted]'" in cjs)
    check('no_auth_keywords_in_diff',all(k not in builder.NEW_ZO+builder.NEW_NOTE+builder.NEW_RULES_EN for k in ['Authorization','token','runtime_message_unauthorized','DPP_REQUIRE_UPLOAD_CONTEXT_V7']))
    check('v41_block_still_present',cjs.count('DPP_BARE_TOOL_TAG_V41_BEGIN')==1)
    check('v41_suite_pinned_to_43_bg',sha((root/'background.js').read_bytes()) in (root/'dspp-bare-tool-tag-v41-selftest.js').read_text(encoding='utf-8'))
    check('resolution_in_whitelist','resolution:typeof t.resolution==`string`?t.resolution.slice(0,40):null' in cjs)
    original=json.loads((base/'manifest.json').read_text(encoding='utf-8'));mf=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    check('version',mf['version']=='1.14.0.48' and mf['version_name']=='1.14.0 ShunCode MCP Fix 3.3.10.43')
    check('manifest_only_version_changed',{k:v for k,v in mf.items() if k not in ('version','version_name')}=={k:v for k,v in original.items() if k not in ('version','version_name')})
    check('no_new_runtime_permissions',mf['permissions']==original['permissions'] and mf['host_permissions']==original['host_permissions'])
    for lang in ['en','zh_CN']:
        d=json.loads((root/f'_locales/{lang}/messages.json').read_text(encoding='utf-8'));check('locale:'+lang,d['extension_name']['message']=='DeepSeek++ ShunCode MCP Fix 3.3.10.43')
    suites=sorted(root.glob('*selftest*.js'));check('58_suites',len(suites)==58)
    for n in ['apply-fix331041.py','apply-fix331042.py','apply-fix331043.py','validate-fix331043.py']:
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
    run('image-block-v43',['node',str(root/'dspp-image-block-v43-selftest.js'),str(root)])
    for p in suites:run(p.stem,['node',str(p)])
    hashes={n:sha((root/n).read_bytes()) for n in sorted(allowed)}
    report={'release':'v1.14.0-fix3.3.10.43','passed':all(x['passed'] for x in checks+tests),'checks':checks,'tests':tests,'runtime_sha256':hashes,'browser_model_acceptance':'pending: reload extension, close old DeepSeek tabs, new session; web_response_diag.read_image with include_data_uri:false must now show capture/upload_ok in dpp_read_image_diag_v7; descriptorCount 24 (single ShunCode server stays direct)'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':report['passed'],'checks':len(checks),'test_processes':len(tests),'suites':len(suites)},indent=2));return 0 if report['passed'] else 1

if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError) as e:raise SystemExit('FAIL-CLOSED: '+str(e))
