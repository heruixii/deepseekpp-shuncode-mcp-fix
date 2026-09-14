const fs=require('fs'),path=require('path'),vm=require('vm');
const src=fs.readFileSync(path.join(__dirname,'content-scripts','content.js'),'utf8');
let pass=0,fail=0;function ok(c,n,d=''){console.log(c?'PASS':'FAIL',n,d);c?pass++:fail++}
function slice(a,b){let i=src.indexOf(a),j=src.indexOf(b,i);if(i<0||j<0)throw Error(`slice ${a}`);return src.slice(i,j)}
const ctx={console,JSON,Set,Map};ctx.ct=(e)=>({invocationNames:e.map(x=>x.invocationName||x.name)});vm.createContext(ctx);
vm.runInContext(slice('function DPP_CONTROL_NOISE_LINE_3310','function kR'),ctx);
const desc=[{name:'run_command',invocationName:'run_command'},{name:'apply_patch',invocationName:'apply_patch'}];
let f=ctx.DPP_CONTROL_NOISE_FILTER_3310(desc);
let raw='修好了。跑测试。\n\n';for(let i=0;i<80;i++)raw+=(i%3===0?'</｜｜DSML｜｜ parameter>\n':i%3===1?'</invoke>\n':'</parameter>\n');
let out='';for(let i=0;i<raw.length;i+=7)out=f.append(raw.slice(i,i+7));out=f.flush();
ok(out.trim()==='修好了。跑测试。','observed step10 noise removed',JSON.stringify(out.slice(0,80)));
ok(f.isStorm()===true,'observed 80-tag storm trips breaker',String(f.noiseCount));
f=ctx.DPP_CONTROL_NOISE_FILTER_3310(desc);for(let i=0;i<23;i++)f.append('</invoke>\n');ok(!f.isStorm(),'23 tags below threshold');f.append('</invoke>\n');ok(f.isStorm(),'24th tag trips threshold');
f=ctx.DPP_CONTROL_NOISE_FILTER_3310(desc);out=f.append('before\n</run_command>\nafter\n');out=f.flush();ok(out==='before\nafter\n','known orphan tool close removed',JSON.stringify(out));
f=ctx.DPP_CONTROL_NOISE_FILTER_3310(desc);out=f.append('```xml\n</invoke>\n</run_command>\n```\n');out=f.flush();ok(out.includes('</invoke>')&&out.includes('</run_command>'),'fenced examples preserved');ok(!f.isStorm(),'fenced examples do not count as storm');
f=ctx.DPP_CONTROL_NOISE_FILTER_3310(desc);out=f.append('literal </invoke> in prose\n');out=f.flush();ok(out.includes('</invoke>'),'inline prose tag preserved');
f=ctx.DPP_CONTROL_NOISE_FILTER_3310(desc);f.append('</｜｜DS');f.append('ML｜｜ parameter>\n');out=f.flush();ok(out===''&&f.noiseCount===1,'split DSML close removed');
const a={invocationName:'run_command',payload:{background:false,command:'dir'}},b={invocationName:'run_command',payload:{command:'dir',background:false}};ok(ctx.DPP_TOOL_SIGNATURE_3310(a)===ctx.DPP_TOOL_SIGNATURE_3310(b),'signature stable across key order');
const sig=ctx.DPP_TOOL_SIGNATURE_3310(a),seen=new Set([sig]);ok(seen.has(ctx.DPP_TOOL_SIGNATURE_3310(b)),'cross-format duplicate signature matches');
ok(src.includes('t===`fallback-legacy`&&DPPStreamSigs.has(n)'), 'production fallback dedupe guard wired');
ok(src.includes('t=e?Oa(x,ct(a)):b===0&&x.includes(`<`)?Da(x,ct(a)):[]'), 'DSML fallback parses legacy only');
ok(!src.includes('for(let e of Ea(x,{descriptors:a}))te('),'old double-parse fallback removed');
ok(src.includes('DPPNoise.isStorm()'),'storm detector remains wired in live stream');
console.log(`FIX3310_DSML_STORM_PASS ${pass}/${pass+fail}`);if(fail)process.exit(1);