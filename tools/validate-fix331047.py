#!/usr/bin/env python3
"""Independent .47 reconstruction, exact runtime delta, permissions invariance and executable suites."""
import argparse,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
def sha(x):return hashlib.sha256(x).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ['root','baseline','output']:ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();root=a.root.resolve();base=a.baseline.resolve();out=a.output.resolve();tools=Path(__file__).resolve().parent
    if out.exists() or out==root or root in out.parents:raise ValueError('New external output required')
    out.mkdir(parents=True);(out/'logs').mkdir();checks=[];tests=[]
    def check(n,v):checks.append({'name':n,'passed':bool(v)});print(('PASS ' if v else 'FAIL ')+n,flush=True)
    def load(n):
        spec=importlib.util.spec_from_file_location('b'+n,tools/f'apply-fix3310{n}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    b47=load('47');rebuilt=b47.build(base,out/'rebuilt');b46=load('46');old=b46.build(base,out/'base46')
    actual={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    check('exact_inventory_and_independent_rebuild',actual==rebuilt)
    runtime_changes={n for n in old if actual.get(n)!=old[n] and not ('/' not in n and 'selftest' in n)}
    check('runtime_delta_only_content_main_manifest_locales',runtime_changes=={'content-scripts/content.js','content-scripts/main-world.js','manifest.json','_locales/en/messages.json','_locales/zh_CN/messages.json'})
    expected=b47.transform(old)
    check('exact_approved_content_and_main_edits',all(actual[n]==expected[n] for n in ['content-scripts/content.js','content-scripts/main-world.js']))
    for n in ['background.js','fix3-policy.js']:check('unchanged:'+n,actual[n]==old[n])
    bg=actual['background.js'].decode();orig=old['background.js'].decode()
    def seg(s,x,y):i=s.index(x);return s[i:s.index(y,i)]
    boundaries=[('function wN(','function TN('),('function TN(','function EN('),('function EN(','function DN('),('function DN(','function ON('),('async function aI(','async function oI('),('async function DPP_ASSERT_CURRENT_UPLOAD_V7(','async function DPP_DISPATCH_UPLOAD_V7('),('xN=new Set(`','`.split')]
    check('authorization_gates_and_allowlist_byte_identical',all(seg(bg,x,y)==seg(orig,x,y) for x,y in boundaries))
    m=json.loads(actual['manifest.json']);o=json.loads(old['manifest.json'])
    check('manifest_version',m['version']=='1.14.0.52' and m['version_name'].endswith('Fix 3.3.10.47'))
    check('all_manifest_fields_except_version_unchanged',{k:v for k,v in m.items() if k not in ['version','version_name']}=={k:v for k,v in o.items() if k not in ['version','version_name']})
    for lang in ['en','zh_CN']:check('locale:'+lang,json.loads(actual[f'_locales/{lang}/messages.json'])['extension_name']['message']=='DeepSeek++ ShunCode MCP Fix 3.3.10.47')
    def run(n,cmd):
        r=subprocess.run(cmd,cwd=root,capture_output=True,timeout=300,env={**os.environ,'DPP_ROOT':str(root)})
        (out/'logs'/(n+'.log')).write_bytes(r.stdout+b'\n'+r.stderr);tests.append({'name':n,'passed':r.returncode==0,'exit_code':r.returncode});print(('PASS ' if r.returncode==0 else 'FAIL ')+n,flush=True)
    suites=sorted(root.glob('*selftest*.js'));check('63_suites',len(suites)==63)
    for p in suites:run(p.stem,['node',str(p),str(root)])
    for n in ['background.js','content-scripts/content.js','content-scripts/main-world.js','fix3-policy.js']:run('syntax-'+Path(n).name,['node','--check',str(root/n)])
    for name,args in [('dspp-skill-popup-observe-selftest.js',[root,base]),('dspp-mw-bridge-diag-v47-selftest.js',[root,base]),('dspp-upload-gate-v10-selftest.js',[root,base]),('dspp-visual-workflow-v8-selftest.js',[root]),('dspp-readimage-v7-selftest.js',[root/'content-scripts/content.js']),('dspp-readimage-v7-boundary-selftest.js',[root])]:run('external-'+name,['node',str(tools/name),*map(str,args)])
    report={'release':'v1.14.0-fix3.3.10.47','passed':all(x['passed'] for x in checks+tests),'checks':checks,'tests':tests,'runtime_sha256':{n:sha(actual[n]) for n in sorted(runtime_changes)},'suites':len(suites)}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');print(json.dumps({'passed':report['passed'],'checks':len(checks),'processes':len(tests),'suites':len(suites)}),flush=True)
    return 0 if report['passed'] else 1
if __name__=='__main__':sys.exit(main())
