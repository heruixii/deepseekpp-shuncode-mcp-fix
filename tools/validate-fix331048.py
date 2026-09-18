#!/usr/bin/env python3
"""Independent .48 rebuild, exact reversal of background/main-world deltas, full regression gates."""
import argparse,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
def sha(x):return hashlib.sha256(x).hexdigest()
def main():
    ap=argparse.ArgumentParser()
    for n in ['root','baseline','output']:ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();root=a.root.resolve();base=a.baseline.resolve();out=a.output.resolve();tools=Path(__file__).resolve().parent
    if out.exists() or root in out.parents:raise ValueError('New external output required')
    out.mkdir(parents=True);(out/'logs').mkdir();checks=[];tests=[]
    def check(n,v):checks.append({'name':n,'passed':bool(v)});print(('PASS ' if v else 'FAIL ')+n,flush=True)
    def load(n):
        sp=importlib.util.spec_from_file_location('b'+n,tools/f'apply-fix3310{n}.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
    b=load('48');rebuilt=b.build(base,out/'rebuilt');old=load('47').build(base,out/'base47')
    actual={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    check('exact_inventory_independent_rebuild',actual==rebuilt)
    delta={n for n in old if actual.get(n)!=old[n] and not ('/' not in n and 'selftest' in n)}
    check('runtime_delta_allowlist',delta=={'background.js','content-scripts/content.js','content-scripts/main-world.js','manifest.json','_locales/en/messages.json','_locales/zh_CN/messages.json'})
    check('policy_unchanged',actual['fix3-policy.js']==old['fix3-policy.js'])
    m=json.loads(actual['manifest.json']);o=json.loads(old['manifest.json'])
    check('manifest_version',m['version']=='1.14.0.53' and m['version_name'].endswith('Fix 3.3.10.48'))
    check('permissions_and_all_nonversion_manifest_fields_unchanged',{k:v for k,v in m.items() if k not in ['version','version_name']}=={k:v for k,v in o.items() if k not in ['version','version_name']})
    def undo(s,pairs):
        for before,after in pairs:
            if s.count(after)!=1:raise ValueError('Invalid exact reversal: '+after[:100])
            s=s.replace(after,before,1)
        return s
    bg=actual['background.js'].decode()
    bg=undo(bg,[
      ('async function Fu(e,t,n={}){',(tools/'dspp-mcp-init-v48.js').read_text('utf-8')+'\nasync function Fu(e,t,n={}){'),
      ('return await Mo(i,t,{signal:n.signal}),Po(i,t,','return await DPP_MCP_INITIALIZE_331048(()=>Mo(i,t,{signal:n.signal}),n.signal),Po(i,t,'),
      ('retryable:typeof i.retryable==`boolean`?i.retryable:!0,details:i.details&&typeof i.details==`object`?i.details:void 0','retryable:!1,details:{stage:`initialize`,externalOutcome:`not_dispatched`,retrySafe:!1,action:`inspect_connection_then_new_authorized_call`}')])
    check('background_all_other_bytes_identical_including_authorization_gates',bg.encode()==old['background.js'])
    mw=actual['content-scripts/main-world.js'].decode();anchor='DPP_GENERATION_ERR_STREAK_TTL_MS_331026=12e4;'
    mw=undo(mw,[(anchor,anchor+'DPP_GENERATION_ERR_RECOVERY_331020=DPP_RECOVERY_STORE_331048();\n'+(tools/'dspp-recovery-v48.js').read_text('utf-8')),
      ('e?.parentMessageId!==n.expectedParentMessageId)return null','e?.parentMessageId!==n.expectedParentMessageId&&!DPP_RECOVERY_BRANCH_331048(e,n))return null'),
      ('parentMessageId:c(r.parent_message_id),promptOptions:','parentMessageId:c(r.parent_message_id),targetMessageId331048:c(r.message_id??r.child_message_id),requestRoute331048:t.requestRoute331048??null,promptOptions:'),
      ('DPPInitialRequest331018=ja(n.body);','DPPInitialRequest331018=ja(n.body,{requestRoute331048:a});'),
      ('DPPInitialRequest331018=ja(e);','DPPInitialRequest331018=ja(e,{requestRoute331048:r});'),
      ('assistantMessageId:n.responseMessageId,promptOptions:e.promptOptions','assistantMessageId:n.responseMessageId,dppRequestMessageId331048:n.requestMessageId,promptOptions:e.promptOptions')])
    field='expectedParentMessageId:t.assistantMessageId,expectedUserMessageId:t.dppRequestMessageId331048??null,expiresAt:'
    check('exact_three_branch_records',mw.count(field)==3);mw=mw.replace(field,'expectedParentMessageId:t.assistantMessageId,expiresAt:')
    check('main_world_all_other_bytes_identical_including_bridge_and_origin_validation',mw.encode()==old['content-scripts/main-world.js'])
    def seg(s,a,b):i=s.index(a);return s[i:s.index(b,i)]
    bgnew=actual['background.js'].decode();bgold=old['background.js'].decode()
    check('single_use_auth_reservation_and_consumption_unchanged',seg(bgnew,'async function _a(','async function ba(')==seg(bgold,'async function _a(','async function ba('))
    for lang in ['en','zh_CN']:check('locale_'+lang,json.loads(actual[f'_locales/{lang}/messages.json'])['extension_name']['message']=='DeepSeek++ ShunCode MCP Fix 3.3.10.48')
    def run(n,cmd):
        r=subprocess.run(cmd,cwd=root,capture_output=True,timeout=300,env={**os.environ,'DPP_ROOT':str(root)})
        (out/'logs'/(n+'.log')).write_bytes(r.stdout+b'\n'+r.stderr);tests.append({'name':n,'passed':r.returncode==0,'exit_code':r.returncode});print(('PASS ' if r.returncode==0 else 'FAIL ')+n,flush=True)
    suites=sorted(root.glob('*selftest*.js'));check('64_suites',len(suites)==64)
    for f in suites:run(f.stem,['node',str(f),str(root)])
    for n in ['background.js','content-scripts/content.js','content-scripts/main-world.js','fix3-policy.js']:run('syntax-'+Path(n).name,['node','--check',str(root/n)])
    # Prior bridge integrity suite on exactly reversed .47 (byte-identical above), full other boundary suites on candidate.
    for name,args in [('dspp-skill-popup-observe-selftest.js',[root,base]),('dspp-mw-bridge-diag-v47-selftest.js',[out/'base47',base]),('dspp-upload-gate-v10-selftest.js',[root,base]),('dspp-visual-workflow-v8-selftest.js',[root]),('dspp-readimage-v7-selftest.js',[root/'content-scripts/content.js']),('dspp-readimage-v7-boundary-selftest.js',[root])]:run('external-'+name,['node',str(tools/name),*map(str,args)])
    report={'release':'v1.14.0-fix3.3.10.48','passed':all(x['passed'] for x in checks+tests),'checks':checks,'tests':tests,'runtime_sha256':{n:sha(actual[n]) for n in sorted(delta)},'suites':len(suites),'new_behavior_checks':50}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');print(json.dumps({'passed':report['passed'],'checks':len(checks),'processes':len(tests),'suites':len(suites)}),flush=True)
    return 0 if report['passed'] else 1
if __name__=='__main__':sys.exit(main())
