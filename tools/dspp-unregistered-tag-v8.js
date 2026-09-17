function DPP_UNREGISTERED_TOOL_TAG_331033(e,t){
  // Linear tag scan: no 20,000-character body window, and no silent whole-text cutoff.
  // Quoted fenced examples are not actionable attempts. This detector NEVER executes.
  let n=String(e??``).replace(/```[^\n]*\n[\s\S]*?```|~~~[^\n]*\n[\s\S]*?~~~/g,``);
  if(!n)return``;
  let r=/<(\/?)([a-z][a-z0-9_]{2,96})>/gi,i,pending=new Map,known=new Map,best=null;
  while(i=r.exec(n)){
    let name=i[2].toLowerCase();
    if(!known.has(name)){
      let base=name.replace(/^mcp_t_[a-z0-9]+(?:_[a-z0-9]+){4}_/,``);
      let registered=typeof t==`function`?t(name):t&&typeof t.has==`function`&&t.has(name);
      known.set(name,!registered&&(DPP_SHUNCODE_TOOL_TAGS_331033.has(base)||/^mcp_t_/.test(name)));
    }
    if(!known.get(name))continue;
    if(!i[1]){if(!pending.has(name))pending.set(name,i.index)}
    else if(pending.has(name)){
      let position=pending.get(name);
      if(!best||position<best.position)best={name,position};
      pending.delete(name);
    }
  }
  return best?best.name:``;
}
