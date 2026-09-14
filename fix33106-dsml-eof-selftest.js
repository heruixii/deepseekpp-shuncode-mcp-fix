const fs=require('fs'),vm=require('vm'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'content-scripts','main-world.js'),'utf8');
function slice(a,b){const i=src.indexOf(a),j=src.indexOf(b,i+a.length);if(i<0||j<0)throw Error('range missing '+a+' -> '+b);return src.slice(i,j)}
const code=slice('function DPP_DSML_PRESENT_33106','function cr(');
const descriptors=[{id:'find',name:'find_files',invocationName:'find_files',provider:{kind:'mcp',id:'srv'},inputSchema:{type:'object',required:['patterns'],properties:{patterns:{type:'array'},root:{type:'string'}}}},{id:'read',name:'read_files',invocationName:'read_files',provider:{kind:'mcp',id:'srv'},inputSchema:{type:'object',required:['paths'],properties:{paths:{type:'array'}}}}];
function P(ds){const n=new Map(),r=new Map();for(const d of ds||[]){n.set(d.invocationName,d);r.set(d.name,d)}return{descriptorByInvocationName:n,descriptorByName:r,invocationNames:[...n.keys()]}}
function F(name,payload,raw,catalog){const d=catalog.descriptorByInvocationName.get(name)||catalog.descriptorByName.get(name);return{name:d?.name??name,invocationName:d?.invocationName??name,payload,raw,descriptorId:d?.id,provider:d?.provider}}
const er='<｜DSML｜tool_calls>',tr='</｜DSML｜tool_calls>';
const ctx={P,F,er,tr,JSON,Object,Array,Number,String,RegExp,console};vm.createContext(ctx);vm.runInContext(code+';Object.assign(globalThis,{DPP_DSML_PRESENT_33106,DPP_DSML_SCHEMA_SAFE_33106,DPP_DSML_EOF_SALVAGE_33106,DPP_SHOULD_SYNTH_FINISH_33106,DPP_FINISH_FRAME_33106});',ctx);
let pass=0,fail=0;function t(n,c,d=''){console.log(`${c?'PASS':'FAIL'} ${n}${d?' '+d:''}`);c?pass++:fail++}
const wrap=x=>ctx.DPP_DSML_EOF_SALVAGE_33106(x,{descriptors});
let s='<｜DSML｜tool_calls>\n<｜DSML｜invoke name="find_files">\n<｜DSML｜parameter name="patterns" string="false">["**/*奇思妙想*"]</｜DSML｜parameter>';
let r=wrap(s);t('canonical eof outer+invoke salvage',r.length===1&&r[0].payload.patterns?.[0]==='**/*奇思妙想*',JSON.stringify(r));
s='<｜｜DSML｜｜ calls>\n<｜｜DSML｜｜ invoke name="find_files">\n<｜｜DSML｜｜ parameter name="patterns" string="false">["**/*奇思妙想*"]</｜｜DSML｜｜ parameter>';
r=wrap(s);t('observed double-bar calls salvage',r.length===1&&r[0].name==='find_files',JSON.stringify(r));
s='<｜｜DSML｜｜ calls>\n<｜｜DSML｜｜ invoke name="find_files">\n<｜｜DSML｜｜ parameter name="patterns" string="false">["**/*奇思妙想*"]';t('half parameter rejected',wrap(s).length===0);
s='<｜DSML｜tool_calls>\n<｜DSML｜invoke name=\"find_files\">\n<｜DSML｜parameter name=\"patterns\" string=\"true\">oops<｜DSML｜parameter name=\"root\" string=\"true\">C:/x</｜DSML｜parameter></｜DSML｜parameter>';t('nested parameter markup rejected',wrap(s).length===0);
s='<｜DSML｜tool_calls>\n<｜DSML｜invoke name="find_files">\n</｜DSML｜invoke>';t('missing required rejected',wrap(s).length===0);
s='<｜DSML｜tool_calls>\n<｜DSML｜invoke name="find_files">\n<｜DSML｜parameter name="evil" string="true">x</｜DSML｜parameter>';t('unknown parameter rejected',wrap(s).length===0);
s='<｜DSML｜tool_calls>\n<｜DSML｜invoke name="find_files">\n<｜DSML｜parameter name="patterns" string="true">not-an-array</｜DSML｜parameter>';t('schema type rejected',wrap(s).length===0);
s='<｜DSML｜tool_calls>\n<｜DSML｜invoke name="unknown_tool">\n<｜DSML｜parameter name="patterns" string="false">[]</｜DSML｜parameter>';t('unknown tool rejected',wrap(s).length===0);
s='<｜DSML｜tool_calls>\n<｜DSML｜invoke name="find_files">\n<｜DSML｜parameter name="patterns" string="false">[]</｜DSML｜parameter>\n</｜DSML｜invoke>\n</｜DSML｜tool_calls>';t('canonical complete skipped to avoid duplicate',wrap(s).length===0);
s='<｜｜DSML｜｜ calls>\n<｜｜DSML｜｜ invoke name="find_files">\n<｜｜DSML｜｜ parameter name="patterns" string="false">[]</｜｜DSML｜｜ parameter>\n</｜｜DSML｜｜ invoke>\n</｜｜DSML｜｜ calls>';t('noncanonical complete recovered',wrap(s).length===1);
s='<｜DSML｜tool_calls>\n<｜DSML｜invoke name="find_files">\n<｜DSML｜parameter name="patterns" string="false">[]</｜DSML｜parameter>\n<｜DSML｜parameter name="root" string="true">C:/Notes</｜DSML｜parameter>';r=wrap(s);t('multiple complete parameters',r.length===1&&r[0].payload.root==='C:/Notes');
t('dsml present canonical',ctx.DPP_DSML_PRESENT_33106('<｜DSML｜tool_calls>'));
t('dsml present doublebar calls',ctx.DPP_DSML_PRESENT_33106('<｜｜DSML｜｜ calls>'));
t('ordinary xml not dsml',!ctx.DPP_DSML_PRESENT_33106('<find_files>{}</find_files>'));
t('synth needs recovery',!ctx.DPP_SHOULD_SYNTH_FINISH_33106(false,0,12));
t('synth needs response id',!ctx.DPP_SHOULD_SYNTH_FINISH_33106(false,1,null));
t('already finished no synth',!ctx.DPP_SHOULD_SYNTH_FINISH_33106(true,1,12));
t('safe recovery synths',ctx.DPP_SHOULD_SYNTH_FINISH_33106(false,1,12));
const frame=ctx.DPP_FINISH_FRAME_33106();const parsed=JSON.parse(frame.trim().replace(/^data:\s*/,''));t('finish frame shape',parsed.p==='response/status'&&parsed.v==='FINISHED',JSON.stringify(frame));
t('Fa recovery wiring',src.includes('recoveredDsml33106:t')&&src.includes('DPP_DSML_EOF_SALVAGE_33106(o,{descriptors:e})'));
t('eo conditional finish wiring',src.includes('DPP_SHOULD_SYNTH_FINISH_33106(n.finished,DPPRecoveredDsml,n.responseMessageId)'));
if(fail){console.error(`FIX33106_FAIL pass=${pass} fail=${fail}`);process.exit(1)}console.log(`FIX33106_PASS ${pass}/${pass+fail}`);