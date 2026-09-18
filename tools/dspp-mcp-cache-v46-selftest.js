#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const root=process.env.DPP_ROOT||process.argv[2]||__dirname;
const bg=fs.readFileSync(path.join(root,'background.js'),'utf8');
function segment(a,b){const i=bg.indexOf(a),j=bg.indexOf(b,i);assert(i>=0&&j>i);return bg.slice(i,j)}
const nu=segment('async function Nu(','async function Pu(');
// Sc has nested async callbacks, but next top-level marker is stable in the source.
const scStart=bg.indexOf('async function Sc(');
function extractFunction(start){let braces=0,quote=null,escaped=false;const body=bg.indexOf('{',start);for(let i=body;i<bg.length;i++){const c=bg[i];if(quote){if(escaped)escaped=false;else if(c==='\\')escaped=true;else if(c===quote)quote=null;continue}if('"\'`'.includes(c)){quote=c;continue}if(c==='{')braces++;if(c==='}'&&!--braces)return bg.slice(start,i+1)}throw Error('unterminated')}
const sc=extractFunction(scStart);
const ho=segment('function Ho(','function Uo(');
const copy=x=>JSON.parse(JSON.stringify(x));
function server(id,extra={}){return {id,enabled:true,execution:{enabled:true,mode:'auto'},transport:{kind:'streamable_http',url:'https://example.invalid'},allowlist:{mode:'all',toolNames:[]},timeouts:{requestMs:100},limits:{maxResultBytes:7000000},...extra}}
function cache(id,name='read_files',extra={}){return {serverId:id,refreshedAt:9900,expiresAt:20000,descriptors:[{id:id+':'+name,name,invocationName:id+'_'+name,provider:{kind:'mcp',id},execution:{enabled:true,mode:'auto'}}],...extra}}
function setup(servers,caches,refresh){let state={servers:copy(servers),toolCaches:copy(caches)};let calls=[],writes=0,locked=false;
 const ctx={console,Date:{now:()=>10000},Set,Map,
 yc:async()=>copy(state.servers),Tc:async()=>copy(state.toolCaches),
 ju:async id=>{assert(!locked,'discovery must run outside transaction');calls.push(id);if(refresh)return refresh(id,state);},
 _c:{run:async fn=>{locked=true;try{return await fn()}finally{locked=false}}},kc:async()=>copy(state),Ac:async value=>{writes++;state=copy(value)},
 Lc:(a,b)=>b,jc:x=>x,Mc:(s,p)=>s.status,Dc:x=>x,
 Bc:(a,b)=>JSON.stringify(a.transport)!==JSON.stringify(b.transport)||JSON.stringify(a.secrets)!==JSON.stringify(b.secrets)};
 vm.createContext(ctx);vm.runInContext(nu+sc+ho+';this.get=Nu;this.update=Sc;',ctx);
 return {ctx,calls,state:()=>state,writes:()=>writes};}
let passed=0,failed=0;
async function test(name,fn){try{await fn();passed++;console.log('PASS '+name)}catch(e){failed++;console.error('FAIL '+name+': '+e.stack)}}
const names=a=>Array.from(a,x=>x.name);
(async()=>{
 await test('fresh cache no discovery',async()=>{const x=setup([server('a')],[cache('a')]);assert.deepEqual(names(await x.ctx.get()),['read_files']);assert.equal(x.calls.length,0)});
 await test('missing cache recovered on same call',async()=>{const x=setup([server('a')],[],(id,s)=>s.toolCaches.push(cache(id)));assert.equal((await x.ctx.get()).length,1);assert.deepEqual(x.calls,['a'])});
 await test('expired cache uses NEW descriptors no stale duplicate',async()=>{const x=setup([server('a')],[cache('a','old',{expiresAt:9000})],(id,s)=>{s.toolCaches=[cache(id,'new')]});assert.deepEqual(names(await x.ctx.get()),['new'])});
 await test('maxAge refresh uses NEW descriptors immediately',async()=>{const x=setup([server('a')],[cache('a','old',{refreshedAt:100})],(id,s)=>{s.toolCaches=[cache(id,'new')]});assert.deepEqual(names(await x.ctx.get({maxAgeMs:500})),['new'])});
 await test('failed refresh does not break healthy server',async()=>{const x=setup([server('a'),server('b')],[cache('a'),cache('b','old',{expiresAt:9000})],async()=>{throw Error('host missing')});assert.deepEqual(names(await x.ctx.get()),['read_files']);assert.deepEqual(x.calls,['b'])});
 await test('failed missing cache is isolated',async()=>{const x=setup([server('a'),server('b')],[cache('a')],async()=>{throw Error('offline')});assert.equal((await x.ctx.get()).length,1)});
 await test('execution-disabled expired Shell Local never probed by normal reads',async()=>{const x=setup([server('a'),server('shell',{execution:{enabled:false,mode:'auto'}})],[cache('a'),cache('shell','shell',{expiresAt:1})],async()=>{throw Error('host missing')});assert.equal((await x.ctx.get()).length,1);assert.equal(x.calls.length,0)});
 await test('disabled server not probed even for includeDisabled',async()=>{const x=setup([server('b',{enabled:false})],[cache('b','hidden',{expiresAt:1})]);assert.equal((await x.ctx.get()).length,0);const a=await x.ctx.get({includeDisabled:true});assert.equal(a.length,1);assert.equal(a[0].execution.enabled,false);assert.equal(x.calls.length,0)});
 await test('allowlist still enforced',async()=>{const x=setup([server('a',{allowlist:{mode:'allow',toolNames:[]}})],[cache('a')]);assert.equal((await x.ctx.get()).length,0);assert.equal((await x.ctx.get({includeDisabled:true}))[0].execution.enabled,false)});
 await test('server disabled during discovery is not exposed',async()=>{const x=setup([server('a')],[],(id,s)=>{s.servers[0].enabled=false;s.toolCaches=[cache(id)]});assert.equal((await x.ctx.get()).length,0)});
 await test('server removed during discovery is not exposed',async()=>{const x=setup([server('a')],[],(id,s)=>{s.servers=[];s.toolCaches=[cache(id)]});assert.equal((await x.ctx.get()).length,0)});
 await test('duplicate descriptors deduplicated',async()=>{const x=setup([server('a')],[cache('a'),cache('a')]);assert.equal((await x.ctx.get()).length,1)});
 await test('limits update preserves cache, no rediscovery',async()=>{const x=setup([server('a')],[cache('a')]);await x.ctx.update('a',{limits:{maxResultBytes:8000000}});assert.equal(x.state().toolCaches.length,1);assert.equal(x.calls.length,0)});
 await test('transport update invalidates only affected server and rediscovers outside lock',async()=>{const x=setup([server('a'),server('b')],[cache('a'),cache('b')]);await x.ctx.update('a',{transport:{kind:'streamable_http',url:'https://changed.invalid'}});assert.deepEqual(x.state().toolCaches.map(c=>c.serverId),['b']);assert.deepEqual(x.calls,['a'])});
 await test('secrets update does not call add on patch object',async()=>{const x=setup([server('a')],[cache('a')]);await x.ctx.update('a',{secrets:[{kind:'test',value:'synthetic'}]});assert.deepEqual(x.calls,['a']);assert.equal(x.state().toolCaches.length,0)});
 await test('disabled updated server invalidates but is not discovered',async()=>{const x=setup([server('a')],[cache('a')]);await x.ctx.update('a',{enabled:false,transport:{kind:'native_messaging'}});assert.equal(x.calls.length,0);assert.equal(x.state().toolCaches.length,0)});
 await test('missing server update is null without writes',async()=>{const x=setup([],[]);assert.equal(await x.ctx.update('missing',{}),null);assert.equal(x.writes(),0)});
 await test('discovery failure does not undo committed transport update',async()=>{const x=setup([server('a')],[cache('a')],async()=>{throw Error('offline')});const a=await x.ctx.update('a',{transport:{kind:'native_messaging'}});assert.equal(a.transport.kind,'native_messaging');assert.equal(x.writes(),1)});
 console.log(JSON.stringify({passed,failed}));process.exitCode=failed?1:0;
})();
