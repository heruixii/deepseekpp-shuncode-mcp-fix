const fs=require('fs'),path=require('path'),vm=require('vm');
const root=__dirname,bg=fs.readFileSync(path.join(root,'background.js'),'utf8'),ct=fs.readFileSync(path.join(root,'content-scripts/content.js'),'utf8'),mf=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0,total=0;function t(n,c,d=''){total++;if(c){pass++;console.log('PASS',n,d)}else{console.error('FAIL',n,d);process.exitCode=1}}
function between(s,a,b){const i=s.indexOf(a),j=s.indexOf(b,i);if(i<0||j<0)throw Error(`missing ${a} -> ${b}`);return s.slice(i,j)}
function clone(x){return x===undefined?undefined:JSON.parse(JSON.stringify(x))}
(async()=>{
t('version',['1.14.0.34','1.14.0.35'].includes(mf.version));t('version name',['1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30'].includes(mf.version_name));
t('v2 meta marker',bg.includes('deepseek_pp_usage_turns_v2_meta'));
t('v2 day prefix marker',bg.includes('deepseek_pp_usage_turns_v2_day_'));
t('hot batch writes v2 helper',bg.includes('return await DPP_USAGE_V2_WRITE_BATCH_331029(t),t'));
t('legacy Sm retained only compatibility',bg.includes('async function Sm(e)'));
t('tool history budget 64K',bg.includes('Math.min(Math.floor(e*O_),65536)'));
t('trace budget 64K',ct.includes('function DPP_TRIM_AGENT_TRACES_333(e,t=65536)'));
const block=between(bg,'var cm=`deepseek_pp_usage_turns_v1`','var Cm=new WeakMap');
const store={};const writes=[],removes=[];
const local={
 async get(keys){if(keys===null)return clone(store);let ks=Array.isArray(keys)?keys:[keys],o={};for(const k of ks)if(Object.prototype.hasOwnProperty.call(store,k))o[k]=clone(store[k]);return o},
 async set(obj){writes.push(clone(obj));for(const[k,v]of Object.entries(obj))store[k]=clone(v)},
 async remove(keys){let ks=Array.isArray(keys)?keys:[keys];removes.push([...ks]);for(const k of ks)delete store[k]}
};
const day=ms=>new Date(ms).toISOString().slice(0,10);
const ctx={console,Date,setTimeout,clearTimeout,Map,Set,Object,Array,Number,Promise,chrome:{storage:{local}},
 em:x=>clone(x),zp:x=>Array.isArray(x)?clone(x):[],Bp:x=>clone(x),Cp:day,xp:x=>x,Sp:(x,o)=>({records:x,range:o.rangeDays})};
vm.createContext(ctx);vm.runInContext(block+';Object.assign(globalThis,{writeBatch:DPP_USAGE_V2_WRITE_BATCH_331029,readAll:xm,clearAll:gm,mutate:mm,key:DPP_USAGE_V2_KEY_331029,metaDecode:DPP_USAGE_V2_META_DECODE_331029,trim:bm});',ctx);
const now=Date.now(),today=day(now),yday=day(now-86400000);
const legacy=[{id:'legacy-a',recordedAt:now-86400000,day:yday,source:'deepseek-web',chatSessionId:'s0',assistantMessageId:2,modelType:'default',totalTokens:100,tokenSource:'server',tps:1,speedSource:'server',elapsedMs:10,messageCount:2}];
store.deepseek_pp_usage_turns_v1=clone(legacy);writes.length=0;
const rec={id:'new-a',recordedAt:now,day:today,source:'deepseek-web',chatSessionId:'s1',assistantMessageId:4,modelType:'default',totalTokens:200,tokenSource:'server',tps:2,speedSource:'server',elapsedMs:20,messageCount:2};
await ctx.mutate([rec]);
t('hot write never rewrites legacy v1',!writes.some(w=>Object.prototype.hasOwnProperty.call(w,'deepseek_pp_usage_turns_v1')));
const shard='deepseek_pp_usage_turns_v2_day_'+today;
t('hot write creates only current day shard',Array.isArray(store[shard])&&store[shard].length===1&&store[shard][0].id==='new-a');
t('hot write creates small meta',store.deepseek_pp_usage_turns_v2_meta?.version===2&&store.deepseek_pp_usage_turns_v2_meta.days[today]===1);
t('legacy v1 remains byte/logically untouched',JSON.stringify(store.deepseek_pp_usage_turns_v1)===JSON.stringify(legacy));
const all=await ctx.readAll();t('dual read sees legacy and v2',all.some(x=>x.id==='legacy-a')&&all.some(x=>x.id==='new-a'),`len=${all.length}`);
// update same id should stay one record in day shard and prefer server/newer
const rec2={...rec,recordedAt:now+1000,totalTokens:250};await ctx.mutate([rec2]);
t('same-id update stays deduped in shard',store[shard].length===1&&store[shard][0].totalTokens===250);
t('second update still never writes legacy v1',!writes.slice(1).some(w=>Object.prototype.hasOwnProperty.call(w,'deepseek_pp_usage_turns_v1')));
// different day -> separate shard
const old={...rec,id:'new-old',recordedAt:now-2*86400000,day:day(now-2*86400000),totalTokens:50};await ctx.mutate([old]);
t('different day is independently sharded',Array.isArray(store['deepseek_pp_usage_turns_v2_day_'+old.day]));
// meta decoder rejects junk day/count
const md=ctx.metaDecode({version:2,days:{[today]:2,bad:5,'2026-01-01':-1}});t('meta decoder keeps only valid nonnegative days',md.days[today]===2&&!('bad'in md.days)&&!('2026-01-01'in md.days));
const expired={...rec,id:'expired',recordedAt:now-200*86400000,day:day(now-200*86400000)};await ctx.mutate([expired]);t('expired incoming shard is not re-added after prune',!Object.prototype.hasOwnProperty.call(store,'deepseek_pp_usage_turns_v2_day_'+expired.day)&&!Object.prototype.hasOwnProperty.call(store.deepseek_pp_usage_turns_v2_meta.days,expired.day));
await ctx.clearAll();t('clear removes legacy key',!('deepseek_pp_usage_turns_v1'in store));t('clear removes v2 meta',!('deepseek_pp_usage_turns_v2_meta'in store));t('clear removes v2 shards',!Object.keys(store).some(k=>k.startsWith('deepseek_pp_usage_turns_v2_day_')));
// static safety: hot writer doesn't call Sm / set legacy
const hot=between(bg,'async function DPP_USAGE_V2_WRITE_BATCH_331029','var fm=DPP_USAGE_BUFFER_331022');
t('v2 hot writer contains no legacy key',!hot.includes('deepseek_pp_usage_turns_v1'));
t('v2 hot writer contains no Sm full-array writer',!hot.includes('Sm('));
// retention contracts retained
t('180-day retention retained',bg.includes('um=180'));t('5000 total contract retained',bg.includes('lm=5e3'));
console.log(`FIX331029_PASS ${pass}/${total}`);if(pass!==total)process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});
