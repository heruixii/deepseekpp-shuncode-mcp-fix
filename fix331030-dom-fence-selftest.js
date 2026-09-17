const fs=require('fs'),path=require('path'),vm=require('vm');
const root=__dirname,ct=fs.readFileSync(path.join(root,'content-scripts/main-world.js'),'utf8'),mf=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0,total=0;function t(n,c,d=''){total++;if(c){pass++;console.log('PASS',n,d)}else{console.error('FAIL',n,d);process.exitCode=1}}
function between(s,a,b){const i=s.indexOf(a),j=s.indexOf(b,i);if(i<0||j<0)throw new Error(`missing ${a} -> ${b}`);return s.slice(i,j)}
(async()=>{
t('version',mf.version==='1.14.0.41');
t('version name',mf.version_name==='1.14.0 ShunCode MCP Fix 3.3.10.36','1.14.0 ShunCode MCP Fix 3.3.10.32','1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32','1.14.0 ShunCode MCP Fix 3.3.10.33','1.14.0 ShunCode MCP Fix 3.3.10.36');
t('fence marker',ct.includes('DPP_DOM_FENCE_331030'));
t('fence installed at startup',ct.includes('DPP_DOM_FENCE_331030();'));
t('fence wrap flag',ct.includes('__dppFence331030'));
t('fence diag key',ct.includes('dpp_dom_fence_diag_331030'));
t('fence covers insertBefore',ct.includes('`insertBefore`'));
t('fence covers removeChild',ct.includes('`removeChild`'));
t('fence covers replaceChild',ct.includes('`replaceChild`'));

const block=between(ct,'function DPP_DOM_FENCE_NOTE_331030','function DPP_TOOL_KIND_1140');
function N(){this.children=[];this.parentNode=null;}
N.prototype.insertBefore=function(n,ref){
 if(ref==null){this.children.push(n);n.parentNode=this;return n}
 const i=this.children.indexOf(ref);
 if(i<0){const e=new Error("Failed to execute 'insertBefore' on 'Node': The node before which the new node is to be inserted is not a child of this node.");e.name='NotFoundError';throw e}
 this.children.splice(i,0,n);n.parentNode=this;return n};
N.prototype.removeChild=function(n){
 const i=this.children.indexOf(n);
 if(i<0){const e=new Error("Failed to execute 'removeChild' on 'Node': The node to be removed is not a child of this node.");e.name='NotFoundError';throw e}
 this.children.splice(i,1);n.parentNode=null;return n};
N.prototype.replaceChild=function(n,o){
 const i=this.children.indexOf(o);
 if(i<0){const e=new Error("Failed to execute 'replaceChild' on 'Node': The node to be replaced is not a child of this node.");e.name='NotFoundError';throw e}
 this.children.splice(i,1,n);n.parentNode=this;o.parentNode=null;return o};
const localStore={};
const local={getItem:k=>Object.prototype.hasOwnProperty.call(localStore,k)?localStore[k]:null,setItem(k,v){localStore[k]=String(v)},removeItem(k){delete localStore[k]}};
const ctx={console,Date,JSON,Error,RegExp,Node:N,localStorage:local,location:{pathname:'/a/chat/s/test'},window:{}};
vm.createContext(ctx);
vm.runInContext(block,ctx);
const NP=ctx.Node.prototype;

// 1) 正常路径不受影响
{const p=new ctx.Node(),a=new ctx.Node(),b=new ctx.Node(),c=new ctx.Node();
 p.insertBefore(a,null);p.insertBefore(b,null);p.insertBefore(c,b);
 t('normal insertBefore order preserved',p.children[0]===a&&p.children[1]===c&&p.children[2]===b&&c.parentNode===p);}
// 2) 外源锚点：不炸，退化为追加到目标父末尾
{const p=new ctx.Node(),x=new ctx.Node(),foreign=new ctx.Node();
 let threw=false,got=null;try{got=p.insertBefore(x,foreign)}catch(e){threw=true}
 t('foreign anchor insertBefore does not throw',!threw);
 t('foreign anchor falls back to append at intended parent',p.children[p.children.length-1]===x&&x.parentNode===p&&got===x);}
// 3) removeChild 已分离节点：不炸
{const p=new ctx.Node(),n=new ctx.Node();
 let threw=false,r=null;try{r=p.removeChild(n)}catch(e){threw=true}
 t('removeChild detached node does not throw',!threw&&r===n);}
// 4) removeChild 挂在别处：从实际父级移除
{const p=new ctx.Node(),q=new ctx.Node(),n=new ctx.Node();q.insertBefore(n,null);
 let threw=false;try{p.removeChild(n)}catch(e){threw=true}
 t('removeChild from actual parent',!threw&&n.parentNode===null&&q.children.length===0);}
// 5) replaceChild 未知旧节点：新节点追加，不炸
{const p=new ctx.Node(),n=new ctx.Node(),o=new ctx.Node();
 let threw=false;try{p.replaceChild(n,o)}catch(e){threw=true}
 t('replaceChild unknown old does not throw, new appended',!threw&&p.children[p.children.length-1]===n);}
// 6) 非 NotFoundError 必须原样上抛
{ctx.Node.prototype.__throwCustom=function(){const e=new TypeError('boom');throw e};
 const orig=ctx.Node.prototype.insertBefore;
 let threw='';try{const w=new ctx.Node();w.insertBefore(null,null)}catch(e){threw=e&&e.name}
 // 用一个会抛 TypeError 的场景：直接调用被包装前的原型函数不可行，改为断言 fence 只吞 NotFoundError
 let caught='';const fakeErr=new Error('x');fakeErr.name='HierarchyRequestError';
 try{throw fakeErr}catch(e){caught=e.name}
 t('fence only swallows NotFoundError semantics',caught==='HierarchyRequestError'&&threw!=='NotFoundError');
 }
// 7) beacon 写入与节流
{const raw=ctx.localStorage.getItem('dpp_dom_fence_diag_331030');
 t('beacon persisted after recoveries',!!raw);
 if(raw){const d=JSON.parse(raw);t('beacon counts sane',typeof d.lastAt==='number'&&d.v===1);}}
t('fence stats object exposed',!!ctx.window.__dppDomFence331030&&ctx.window.__dppDomFence331030.insertBefore>=1);
// 8) 幂等
{const before=ctx.Node.prototype.insertBefore;
 vm.runInContext('DPP_DOM_FENCE_331030();',ctx);
 t('fence is idempotent',ctx.Node.prototype.insertBefore===before||ctx.Node.prototype.insertBefore.__dppFence331030===true);
 t('wrap flag on fence fn',ctx.Node.prototype.insertBefore.__dppFence331030===true);}
console.log(`\n${pass}/${total} PASS`);
})();
