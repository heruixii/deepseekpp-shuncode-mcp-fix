// Recovery hints contain only bounded branch IDs and expiry; never prompts, grants or tool payloads.
function DPP_RECOVERY_STORE_331048(){
  class Store extends Map {
    key(k){return `dpp-recovery-331048:${String(k)}`}
    valid(v){return v && [`compact`,`passthrough`].includes(v.mode) && Number.isInteger(v.expectedParentMessageId) && v.expectedParentMessageId>=0 && Number.isFinite(v.expiresAt) && v.expiresAt>Date.now() && v.expiresAt<=Date.now()+600000 && Number.isInteger(v.failures) && v.failures>=1 && v.failures<=99}
    get(k){try{const raw=localStorage.getItem(this.key(k));if(raw){const v=JSON.parse(raw);if(this.valid(v)){super.set(k,v);return v}this.delete(k);return undefined}super.delete(k)}catch{}return super.get(k)}
    set(k,v){const safe={mode:v.mode,expectedParentMessageId:v.expectedParentMessageId,expectedUserMessageId:Number.isInteger(v.expectedUserMessageId)?v.expectedUserMessageId:null,failures:v.failures,expiresAt:v.expiresAt};super.set(k,safe);try{localStorage.setItem(this.key(k),JSON.stringify(safe));const keys=[];for(let i=0;i<localStorage.length;i++){const x=localStorage.key(i);if(x?.startsWith(`dpp-recovery-331048:`))keys.push(x)}for(const x of keys){try{if(!this.valid(JSON.parse(localStorage.getItem(x))))localStorage.removeItem(x)}catch{localStorage.removeItem(x)}}for(const x of keys.slice(0,Math.max(0,keys.length-32)))if(x!==this.key(k))localStorage.removeItem(x)}catch{}return this}
    delete(k){try{localStorage.removeItem(this.key(k))}catch{}return super.delete(k)}
  }
  return new Store;
}
function DPP_RECOVERY_BRANCH_331048(e,n){
  const id=e?.targetMessageId331048;
  if(!Number.isInteger(id)||id<0)return false;
  return e?.requestRoute331048===`editMessage`?Number.isInteger(n.expectedUserMessageId)&&id===n.expectedUserMessageId:e?.requestRoute331048===`regenerate`&&id===n.expectedParentMessageId;
}
