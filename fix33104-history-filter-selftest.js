const fs=require('fs'),path=require('path'),vm=require('vm');
const src=fs.readFileSync(path.join(__dirname,'content-scripts','main-world.js'),'utf8');let pass=0,fail=0;const ok=(c,n,d='')=>{console.log(c?'PASS':'FAIL',n,d);c?pass++:fail++};
function extract(a,b){const i=src.indexOf(a),j=src.indexOf(b,i);if(i<0||j<0)throw Error('extract '+a);return src.slice(i,j)}
const ctx={Set,Array,P:(x)=>({invocationNames:[]})};vm.createContext(ctx);vm.runInContext(extract('function DPP_PAGE_CONTROL_LINE_33102','function Xa'),ctx);vm.runInContext(extract('function DPP_HISTORY_CONTROL_FILTER_33104','function Er('),ctx);
const descriptors=[];let noisy='修好了。跑测试。\n'+('</parameter>\n</invoke>\n'.repeat(80));let clean=ctx.DPP_HISTORY_CONTROL_FILTER_33104(noisy,descriptors);
ok(clean==='修好了。跑测试。\n','80-pair history tail removed',JSON.stringify(clean));
let fenced='```xml\n</parameter>\n</invoke>\n```\n';ok(ctx.DPP_HISTORY_CONTROL_FILTER_33104(fenced,descriptors)===fenced,'history fenced example preserved');
let prose='literal </invoke> in prose';ok(ctx.DPP_HISTORY_CONTROL_FILTER_33104(prose,descriptors)===prose,'inline prose preserved');
ok(src.includes('Pr(e)&&(e.content=DPP_HISTORY_CONTROL_FILTER_33104(e.content,n))'),'content sanitizer assistant-only');
ok(src.includes('Pr(e)&&DPP_HISTORY_FRAGMENT_FILTER_33104(e.fragments,n)'),'fragment sanitizer assistant-only');
ok(src.includes('if(a===`history`)return io(e.call(this,t,n))'),'fetch history hook retained');
ok(src.includes('return r===`history`&&ao(this),a.call(this,e)'),'XHR history hook retained');
ok(src.includes('this.name===`history-message`&&co(n)'),'IDB history hook retained');
ok(src.includes('Cr(e,oo())'),'history response passes through Cr');
ok(src.includes('function Cr(e,t){')&&src.includes('Er(n,r,t.toolDescriptors)'),'Cr still routes through Er');
function sim(msg){if(msg.role==='assistant')msg.content=ctx.DPP_HISTORY_CONTROL_FILTER_33104(msg.content,descriptors);return msg.content}
ok(sim({role:'assistant',content:noisy})==='修好了。跑测试。\n','assistant history sanitized');
ok(sim({role:'user',content:'</parameter>\n</invoke>\n'})==='</parameter>\n</invoke>\n','user history untouched');
console.log(`FIX33104_HISTORY_FILTER_PASS ${pass}/${pass+fail}`);if(fail)process.exit(1);