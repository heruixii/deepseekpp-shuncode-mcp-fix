#!/usr/bin/env python3
"""Offline .41 release gate; never modifies live installs or uploads images.
python tools/validate-fix331041.py --root CANDIDATE --baseline BASE_36 --output NEW_EXTERNAL_DIR
.41 = .40 + bare ShunCode tool tag resolved to its real registered name (content.js only).
Every .41 edit is inlined on purpose: the v8 suite extracts and evaluates
DPP_VISUAL_RULES/RETRY_331036, vo() and shouldStopAfterTurn standalone, so any
external helper reference would throw ReferenceError there.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
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
    spec=importlib.util.spec_from_file_location('builder41',tools/'apply-fix331041.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    rebuilt=builder.build(base,out/'rebuilt')
    inventory=json.loads((tools/'fix331037-baseline-sha256.json').read_text(encoding='utf-8'))
    allowed={'background.js','content-scripts/content.js','content-scripts/main-world.js','manifest.json','_locales/en/messages.json','_locales/zh_CN/messages.json'}
    changed={n for n in inventory if (root/n).exists() and (root/n).read_bytes()!=(base/n).read_bytes()}
    selftest_changes={n for n in changed if '/' not in n and 'selftest' in n}
    check('runtime_changes_exactly_allowed',(changed-selftest_changes)==allowed)
    check('independently_rebuilt_all_files',all((root/n).read_bytes()==rebuilt[n] for n in inventory))
    check('no_extra_files',sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file())==sorted(list(inventory)+['dspp-bare-tool-tag-v41-selftest.js']))
    check('policy_unchanged',(root/'fix3-policy.js').read_bytes()==(base/'fix3-policy.js').read_bytes())
    bg=(root/'background.js').read_text(encoding='utf-8');old=(base/'background.js').read_text(encoding='utf-8')
    def seg(s,a,b): i=s.index(a);j=s.index(b,i);return s[i:j].replace('\r\n','\n')
    check('gate_functions_unchanged',all(seg(bg,x,y)==seg(old,x,y) for x,y in [('function wN(','function TN('),('function TN(','function EN('),('function EN(','function DN('),('function DN(','function ON('),('async function aI(','async function oI('),('async function DPP_ASSERT_CURRENT_UPLOAD_V7(','async function DPP_DISPATCH_UPLOAD_V7(')]))
    req=seg(bg,'function DPP_REQUIRE_UPLOAD_CONTEXT_V7(','async function DPP_ASSERT_CURRENT_UPLOAD_V7(')
    check('require_drops_stale_sender_url_comparison','vN(context.senderUrl)' not in req)
    check('require_keeps_all_other_conditions',all(k in req for k in ["context.frameId !== 0","context.documentLifecycle !== 'active'","typeof context.documentId !== 'string' || !context.documentId","typeof context.chatSessionId !== 'string' || !context.chatSessionId","typeof context.senderUrl !== 'string' || !context.senderUrl","typeof context.tabUrl !== 'string' || !context.tabUrl","context.dppListenerChatSessionId !== context.chatSessionId"]))
    check('require_is_the_only_gate_body_change',seg(bg,'/* DPP_READIMAGE_V7_BACKGROUND_BEGIN */','async function DPP_ASSERT_CURRENT_UPLOAD_V7(').replace(req,'')==seg(old,'/* DPP_READIMAGE_V7_BACKGROUND_BEGIN */','async function DPP_ASSERT_CURRENT_UPLOAD_V7(').replace(seg(old,'function DPP_REQUIRE_UPLOAD_CONTEXT_V7(','async function DPP_ASSERT_CURRENT_UPLOAD_V7('),''))
    check('allowlist_unchanged',seg(bg,'xN=new Set(`','`.split')==seg(old,'xN=new Set(`','`.split'))
    check('diag_call_sites_exactly_three',bg.count('DPP_GATE_DIAG_V9(')==4)
    check('no_url_or_token_fields_in_diag_helper',not any(k in seg(bg,'/* DPP_UPLOAD_GATE_DIAG_V9_BEGIN','/* DPP_UPLOAD_GATE_DIAG_V9_END */') for k in ['Authorization','senderUrl:','documentId:','url:','href']))
    original=json.loads((base/'manifest.json').read_text(encoding='utf-8'));mf=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    check('version',mf['version']=='1.14.0.46' and mf['version_name']=='1.14.0 ShunCode MCP Fix 3.3.10.41')
    check('manifest_only_version_changed',{k:v for k,v in mf.items() if k not in ('version','version_name')}=={k:v for k,v in original.items() if k not in ('version','version_name')})
    check('no_new_runtime_permissions',mf['permissions']==original['permissions'] and mf['host_permissions']==original['host_permissions'])
    for lang in ['en','zh_CN']:
        d=json.loads((root/f'_locales/{lang}/messages.json').read_text(encoding='utf-8'));check('locale:'+lang,d['extension_name']['message']=='DeepSeek++ ShunCode MCP Fix 3.3.10.41')
    suites=sorted(root.glob('*selftest*.js'));check('56_legacy_suites',len(suites)==56)
    for n in ['apply-fix331037.py','apply-fix331038.py','apply-fix331039.py','apply-fix331040.py','apply-fix331041.py','validate-fix331041.py']:
        ast.parse((tools/n).read_text(encoding='utf-8'));check('python_ast:'+n,True)
    for n in ['content-scripts/content.js','background.js','fix3-policy.js']:
        run('syntax-'+Path(n).name,['node','--check',str(root/n)])
    run('syntax-gate-diag-v9',['node','--check',str(tools/'dspp-upload-gate-diag-v9.js')])
    run('skill-popup-observe',['node',str(tools/'dspp-skill-popup-observe-selftest.js'),str(root),str(base)])
    run('mw-bridge-diag-v10',['node',str(tools/'dspp-mw-bridge-diag-v10-selftest.js'),str(root),str(base)])
    run('syntax-main-world',['node','--check',str(root/'content-scripts/main-world.js')])
    run('upload-gate-v10',['node',str(tools/'dspp-upload-gate-v10-selftest.js'),str(root),str(base)])
    run('visual-workflow-v8',['node',str(tools/'dspp-visual-workflow-v8-selftest.js'),str(root)])
    run('image-runtime-v7',['node',str(tools/'dspp-readimage-v7-selftest.js'),str(root/'content-scripts/content.js')])
    run('image-boundary-v7',['node',str(tools/'dspp-readimage-v7-boundary-selftest.js'),str(root)])
    run('native-maintenance',[sys.executable,str(tools/'shuncode-read-image-selftest.py')])
    # ---- .41 specific ----
    cjs=(root/'content-scripts/content.js').read_text(encoding='utf-8')
    bjs=(root/'background.js').read_bytes();mwjs=(root/'content-scripts/main-world.js').read_bytes()
    check('bg_identical_to_40',sha(bjs)=='76df1046a8bd3247484dc96092785b876b7b7985cbfe31c5cd31947212a536f5')
    check('mw_identical_to_40',sha(mwjs)=='e63b16762734e524af680e9f4e40fc18e92990f2f26afecca60f98bf3a199d92')
    check('v41_block_present',cjs.count('DPP_BARE_TOOL_TAG_V41_BEGIN')==1)
    check('steering_takes_registry',"DPP_UNREGISTERED_TAG_STEERING_331033(d,y.unregisteredTag,v)" in cjs)
    check('resolution_enum_recorded',"stage:`unregistered_tool_tag_331033`,resolution:" in cjs)
    check('no_external_v41_ref_in_eval_regions',
          'DPP_RESOLVE_REGISTERED_TAG_V41(' not in cjs.split('/* DPP_BARE_TOOL_TAG_V41_END */')[-1]
          and 'DPP_VISUAL_TOOL_NAME_V41(' not in cjs.split('/* DPP_BARE_TOOL_TAG_V41_END */')[-1]
          and 'DPP_VISUAL_NAME_PHRASE_V41(' not in cjs.split('/* DPP_BARE_TOOL_TAG_V41_END */')[-1])
    check('only_three_enum_values',sorted(set(re.findall(r'`(exact_hint|discover_hint|ambiguous)`',cjs)))==['ambiguous','discover_hint','exact_hint'])
    check('no_identifiers_in_diag_enum','errorMessage:DPPUnregTag331033' in cjs)
    run('bare-tool-tag-v41',['node',str(root/'dspp-bare-tool-tag-v41-selftest.js')])
    for p in suites:run(p.stem,['node',str(p)])
    hashes={n:sha((root/n).read_bytes()) for n in sorted(allowed|{'fix3-policy.js'})}
    report={'release':'v1.14.0-fix3.3.10.41','passed':all(x['passed'] for x in checks+tests),'checks':checks,'tests':tests,'runtime_sha256':hashes,'browser_model_acceptance':'pending: reload + F5, extension error panel must stay free of main-world.js observe errors; slash-command skill popup still opens'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':report['passed'],'checks':len(checks),'test_processes':len(tests),'legacy_suites':len(suites)},indent=2));return 0 if report['passed'] else 1

if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError) as e:raise SystemExit('FAIL-CLOSED: '+str(e))
