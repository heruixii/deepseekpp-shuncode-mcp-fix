const fs=require('fs'),path=require('path'),vm=require('vm');
const root=__dirname, src=fs.readFileSync(path.join(root,'content-scripts','content.js'),'utf8');
let pass=0,fail=0;const ok=(c,n,d='')=>{console.log(c?'PASS':'FAIL',n,d);c?pass++:fail++};
function slice(a,b){const i=src.indexOf(a),j=src.indexOf(b,i);if(i<0||j<0)throw Error(a);return src.slice(i,j)}
const ctx={console,JSON,Set,Map};ctx.ct=e=>({invocationNames:e.map(x=>x.invocationName||x.name)});vm.createContext(ctx);vm.runInContext(slice('function DPP_CONTROL_NOISE_LINE_3310','function kR'),ctx);
const desc=[{name:'run_command',invocationName:'run_command'}];let f=ctx.DPP_CONTROL_NOISE_FILTER_3310(desc);
let raw='修好了。跑测试。\n\n';for(let i=0;i<80;i++)raw+=(i%2?'</invoke>\n':'</parameter>\n');for(let i=0;i<raw.length;i+=5)f.append(raw.slice(i,i+5));let vis=f.flush();
ok(vis.trim()==='修好了。跑测试。','valid prefix preserved',JSON.stringify(vis));ok(f.isStorm(),'noise threshold detected',String(f.noiseCount));
ok(src.includes('DPPControlQuarantine=!1'),'quarantine state declared');
ok(src.includes('if(DPPControlQuarantine)return;'),'post-threshold chunks ignored by UI/tool layer');
ok(src.includes('if(DPPNoise.isStorm())DPPControlQuarantine=!0,S=!0,x=``'),'storm switches to quarantine without throw');
ok(!src.includes('if(DPPNoise.isStorm())throw Error(`DeepSeek emitted repeated malformed tool-control markup; stopped this turn to prevent a continuation loop.`)'),'old fatal throw removed');
ok(src.includes('n.setParentMessageId(ie.responseMessageId)'),'parent message update retained after stream completion');
ok(src.includes('!DPPControlQuarantine&&!S&&x'),'fallback disabled for quarantined turn');
ok(src.includes('re(h.flush())'),'already-started tool parser still flushes safely');
ok(src.includes('f.stopReason=f.content.some(e=>e.type===`toolCall`)?`toolUse`:`stop`'),'normal done path retained');
console.log(`FIX33101_QUARANTINE_PASS ${pass}/${pass+fail}`);if(fail)process.exit(1);