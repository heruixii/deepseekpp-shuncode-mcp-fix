#!/usr/bin/env python3
"""Offline .45 release gate; never modifies live installs or uploads images.
python tools/validate-fix331045.py --root CANDIDATE --baseline BASE_36 --output NEW_EXTERNAL_DIR
.45 = .44 + (A) Vc excludes limits/timeouts, Sc auto ju, Nu self-heal, UPDATE refresh
(B) visual missing guarded by tool presence, plus visual_tool_absent final
(C) manifest host_permissions adds ngrok URL
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
    if not (tools/'apply-fix331044.py').exists():
        tools=Path(__file__).resolve().parent
    if out.exists() or out==root or root in out.parents:raise ValueError('Use new output directory outside candidate')
    out.mkdir(parents=True);logs=out/'logs';logs.mkdir();checks=[];tests=[]
    def check(name,cond):
        checks.append({'name':name,'passed':bool(cond)});print(('PASS ' if cond else 'FAIL ')+name,flush=True)
    def run(name,cmd,cwd=root):
        r=subprocess.run(cmd,cwd=cwd,capture_output=True,timeout=300,env={**os.environ,'DPP_ROOT':str(root)})
        (logs/(name+'.log')).write_bytes(r.stdout+b'\n'+r.stderr);tests.append({'name':name,'passed':r.returncode==0,'exit_code':r.returncode});print(('PASS ' if r.returncode==0 else 'FAIL ')+name,flush=True)
    spec=importlib.util.spec_from_file_location('builder45',tools/'apply-fix331045.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    rebuilt=builder.build(base,out/'rebuilt')
    inventory=json.loads((tools/'fix331037-baseline-sha256.json').read_text(encoding='utf-8'))
    allowed={'background.js','content-scripts/content.js','content-scripts/main-world.js','fix3-policy.js','manifest.json','_locales/en/messages.json','_locales/zh_CN/messages.json'}
    changed={n for n in inventory if (root/n).exists() and (root/n).read_bytes()!=(base/n).read_bytes()}
    selftest_changes={n for n in changed if '/' not in n and 'selftest' in n}
    check('runtime_changes_exactly_allowed',(changed-selftest_changes)==allowed)
    check('independently_rebuilt_all_files',all((root/n).read_bytes()==rebuilt[n] for n in inventory))
    extras=['dspp-bare-tool-tag-v41-selftest.js','dspp-exposure-drift-v42-selftest.js','dspp-image-block-v43-selftest.js','dspp-exposure-builtin-v44-selftest.js','dspp-mcp-cache-v45-selftest.js','dspp-visual-absent-v45-selftest.js']
    check('no_extra_files',sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file())==sorted(list(inventory)+extras))
    bg=(root/'background.js').read_text(encoding='utf-8');old=(base/'background.js').read_text(encoding='utf-8')
    def seg(s,a,b): i=s.index(a);j=s.index(b,i);return s[i:j].replace('\r\n','\n')
    check('gate_functions_unchanged',all(seg(bg,x,y)==seg(old,x,y) for x,y in [('function wN(','function TN('),('function TN(','function EN('),('function EN(','function DN('),('function DN(','function ON('),('async function aI(','async function oI('),('async function DPP_ASSERT_CURRENT_UPLOAD_V7(','async function DPP_DISPATCH_UPLOAD_V7(')]))
    check('allowlist_unchanged',seg(bg,'xN=new Set(`','`.split')==seg(old,'xN=new Set(`','`.split'))
    spec44=importlib.util.spec_from_file_location('builder44',tools/'apply-fix331044.py');b44=importlib.util.module_from_spec(spec44);spec44.loader.exec_module(b44)
    v44=b44.build(base,out/'rebuilt44')
    e=lambda s:s.encode('utf-8')
    b44_bg=v44['background.js']
    for o,n in builder.BG_EDITS:
        b44_bg=b44_bg.replace(e(o),e(n),1)
    check('background_is_44_plus_4_edits',b44_bg==(root/'background.js').read_bytes())
    check('mw_identical_to_44',v44['content-scripts/main-world.js']==(root/'content-scripts/main-world.js').read_bytes())
    check('policy_identical_to_44',v44['fix3-policy.js']==(root/'fix3-policy.js').read_bytes())
    c44=v44['content-scripts/content.js']
    for o,n in builder.CONTENT_EDITS:
        c44=c44.replace(e(o),e(n),1)
    check('content_is_44_plus_4_edits',c44==(root/'content-scripts/content.js').read_bytes())
    cbytes=(root/'content-scripts/content.js').read_bytes()
    check('each_content_literal_applied_once',all(cbytes.count(e(n))==1 and cbytes.count(e(o))==(1 if o in n else 0) for o,n in builder.CONTENT_EDITS))
    check('each_bg_literal_applied_once',all((root/'background.js').read_bytes().count(e(n))==1 and (root/'background.js').read_bytes().count(e(o))==(1 if o in n else 0) for o,n in builder.BG_EDITS))
    pol=(root/'fix3-policy.js').read_text(encoding='utf-8');cjs=(root/'content-scripts/content.js').read_text(encoding='utf-8')
    check('policy_mcp_only_literal','let enabled=descriptors.filter(d=>d?.execution?.enabled!==false&&d?.provider?.kind===`mcp`&&!!d.provider.id),total=' in pol)
    check('vc_excludes_limits_timeouts','timeouts:e.timeouts,limits:e.limits' not in bg and 'function Vc(e){return JSON.stringify({transport:' in bg)
    check('sc_auto_ju','ju(e).catch' in bg and 'async function Sc(e,t){let n=new Set' in bg)
    check('nu_self_heal','o=new Set' in bg and 'expiresAt<=r' in bg and 'async function Nu(e)' in bg)
    check('update_refresh','refreshMcpServerDiscovery' in bg and 'UPDATE_MCP_SERVER' in bg)
    check('visual_missing_guard','!!DPP_VISUAL_TOOL_NAME_V41(v)' in cjs)
    check('visual_absent_present','DPP_VISUAL_TOOL_ABSENT_331045' in cjs and 'visual_tool_absent_331045' in cjs)
    check('no_auth_keywords_in_diff',all(k not in ''.join(n for _,n in builder.BG_EDITS)+''.join(n for _,n in builder.CONTENT_EDITS) for k in ['Authorization','token','runtime_message_unauthorized','DPP_REQUIRE_UPLOAD_CONTEXT_V7','chrome.runtime','fetch(']))
    check('v43_Zo_still_present','t.content===void 0&&(t.content=n)' in bg)
    check('v41_block_still_present',cjs.count('DPP_BARE_TOOL_TAG_V41_BEGIN')==1)
    check('v41_suite_pinned_to_45_bg',sha((root/'background.js').read_bytes()) in (root/'dspp-bare-tool-tag-v41-selftest.js').read_text(encoding='utf-8'))
    check('manifest_version',json.loads((root/'manifest.json').read_text(encoding='utf-8'))['version']=='1.14.0.50')
    mf=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    check('manifest_host_permissions', 'https://unlimited-underline-lunchroom.ngrok-free.dev/*' in mf.get('host_permissions',[]))
    check('no_new_runtime_permissions',set(mf['permissions'])==set(json.loads((base/'manifest.json').read_text(encoding='utf-8'))['permissions']))
    for lang in ['en','zh_CN']:
        d=json.loads((root/f'_locales/{lang}/messages.json').read_text(encoding='utf-8'));check('locale:'+lang,d['extension_name']['message']=='DeepSeek++ ShunCode MCP Fix 3.3.10.45')
    suites=sorted(root.glob('*selftest*.js'));check('61_suites',len(suites)==61)
    for n in ['apply-fix331044.py','apply-fix331045.py','validate-fix331045.py']:
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
    run('exposure-builtin-v44',['node',str(root/'dspp-exposure-builtin-v44-selftest.js'),str(root)])
    run('mcp-cache-v45',['node',str(root/'dspp-mcp-cache-v45-selftest.js'),str(root)])
    run('visual-absent-v45',['node',str(root/'dspp-visual-absent-v45-selftest.js'),str(root)])
    for p in suites:run(p.stem,['node',str(p)])
    hashes={n:sha((root/n).read_bytes()) for n in sorted(allowed)}
    report={'release':'v1.14.0-fix3.3.10.45','passed':all(x['passed'] for x in checks+tests),'checks':checks,'tests':tests,'runtime_sha256':hashes}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':report['passed'],'checks':len(checks),'test_processes':len(tests),'suites':len(suites)},indent=2));return 0 if report['passed'] else 1

if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError) as e:raise SystemExit('FAIL-CLOSED: '+str(e))
