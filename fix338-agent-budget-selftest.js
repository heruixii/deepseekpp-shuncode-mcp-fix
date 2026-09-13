require('./fix3-policy.js');
const fs=require('fs'),path=require('path');
const root=__dirname,src=fs.readFileSync(path.join(root,'content-scripts','content.js'),'utf8');
let failed=0,passed=0;function ok(name,cond,detail=''){console.log(`${cond?'PASS':'FAIL'} ${name}${detail?' '+detail:''}`);if(cond)passed++;else failed++;}
ok('marker-min',src.includes('DPP_AGENT_MIN_BUDGET_338=88'));
ok('marker-project',src.includes('DPP_AGENT_PROJECT_BUDGET_338=96'));
ok('marker-completion',src.includes('DPP_AGENT_COMPLETION_BUDGET_338=128'));
ok('inline-no-legacy-12',!src.includes('?24:12;return{maxSteps:n,maxNudges:8'));
ok('nudge-cap-preserved',src.includes('maxSteps:n,maxNudges:8'));
const p=globalThis.DPP_FIX3;
ok('policy-default-88',p.stepLimit('hello')===88,String(p.stepLimit('hello')));
ok('policy-project-96',p.stepLimit('修复这个项目')===96,String(p.stepLimit('修复这个项目')));
ok('policy-continue-128',p.stepLimit('继续')===128,String(p.stepLimit('继续')));
ok('policy-until-done-128',p.stepLimit('继续直到完成')===128,String(p.stepLimit('继续直到完成')));
ok('policy-min-at-least-88',[p.stepLimit('hello'),p.stepLimit('修复这个项目'),p.stepLimit('继续')].every(n=>n>=88));
if(failed)process.exit(1);console.log(`ALL_PASS ${passed}`);
