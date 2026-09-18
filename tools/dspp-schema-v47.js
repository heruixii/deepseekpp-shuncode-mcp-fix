function DPP_COMPACT_SCHEMA_331020(e,t=0){
  // Remove verbose prose only. Keep every validation keyword, property and branch.
  if(e===null||typeof e!==`object`)return e;
  if(Array.isArray(e))return e.map(value=>DPP_COMPACT_SCHEMA_331020(value,t+1));
  const out={};
  for(const [key,value] of Object.entries(e)){
    if([`description`,`title`,`examples`,`$comment`].includes(key))continue;
    // properties/$defs/definitions keys are user-defined names, not schema annotations.
    if([`properties`,`patternProperties`,`$defs`,`definitions`,`dependentSchemas`].includes(key)&&value&&typeof value===`object`&&!Array.isArray(value)){
      const children={};for(const [name,schema] of Object.entries(value))Object.defineProperty(children,name,{value:DPP_COMPACT_SCHEMA_331020(schema,t+1),enumerable:true,writable:true,configurable:true});
      Object.defineProperty(out,key,{value:children,enumerable:true,writable:true,configurable:true});
    }else if([`default`,`const`,`enum`,`required`,`dependentRequired`].includes(key)){
      Object.defineProperty(out,key,{value:JSON.parse(JSON.stringify(value)),enumerable:true,writable:true,configurable:true});
    }else Object.defineProperty(out,key,{value:DPP_COMPACT_SCHEMA_331020(value,t+1),enumerable:true,writable:true,configurable:true});
  }
  return out;
}
