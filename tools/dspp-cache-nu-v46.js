async function Nu(e){
  let [servers,caches]=await Promise.all([yc({includeSecrets:!1}),Tc()]);
  const now=Date.now();
  const eligible=server=>server.enabled&&(e?.includeDisabled||server.execution.enabled&&server.execution.mode!==`disabled`);
  const stale=cache=>!cache||cache.expiresAt<=now||(e?.maxAgeMs!=null&&now-cache.refreshedAt>e.maxAgeMs);
  const refreshIds=new Set;
  for(const server of servers){
    if(eligible(server)&&stale(caches.find(cache=>cache.serverId===server.id)))refreshIds.add(server.id);
  }
  if(refreshIds.size){
    await Promise.all([...refreshIds].map(id=>ju(id).catch(()=>{})));
    [servers,caches]=await Promise.all([yc({includeSecrets:!1}),Tc()]);
  }
  const byId=new Map(servers.map(server=>[server.id,server]));
  const result=[];
  const seen=new Set;
  for(const cache of caches){
    const server=byId.get(cache.serverId);
    if(!server||(!e?.includeDisabled&&!eligible(server)))continue;
    if(server.enabled&&stale(cache))continue;
    if(e?.maxAgeMs!=null&&Date.now()-cache.refreshedAt>e.maxAgeMs)continue;
    for(const descriptor of Ho(cache.descriptors,server)){
      if(!e?.includeDisabled&&(!descriptor.execution.enabled||descriptor.execution.mode===`disabled`))continue;
      if(seen.has(descriptor.id))continue;
      seen.add(descriptor.id);result.push(descriptor);
    }
  }
  return result;
}
