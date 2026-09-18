async function Sc(e,t){
  const refreshIds=new Set;
  const result=await _c.run(async()=>{
    const state=await kc();
    const invalidated=new Set;
    let updated=null;
    const servers=state.servers.map(server=>{
      if(server.id!==e)return server;
      const patch=t.secrets?{...t,secrets:Lc(server.secrets,t.secrets)}:t;
      const next=jc({...server,...patch,updatedAt:Date.now(),status:Mc(server,patch)});
      if(Bc(server,next)){
        invalidated.add(server.id);
        if(next.enabled)refreshIds.add(server.id);
        updated={...next,status:next.enabled?`unknown`:`disabled`,lastConnectedAt:null,lastError:null};
      }else updated=next;
      return updated;
    });
    if(!updated)return null;
    await Ac({...state,servers,toolCaches:state.toolCaches.filter(cache=>!invalidated.has(cache.serverId))});
    return Dc(updated);
  });
  await Promise.all([...refreshIds].map(id=>ju(id).catch(()=>{})));
  return result;
}
