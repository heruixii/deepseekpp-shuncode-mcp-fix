/* DPP_STARTUP_UI_V47_BEGIN: owned DOM only; no request replay or authorization changes. */
function DPP_STARTUP_STATUS_331047(diag,locale){
  if(!diag||typeof diag!==`object`)return null;
  const finish=(Array.isArray(diag.controlTrail)?diag.controlTrail:[]).find(row=>row?.path===`finish_reason`)?.value;
  const zh=String(locale||``).toLowerCase().startsWith(`zh`);
  if(finish===`generation_err`)return {
    code:`generation_err`,title:zh?`DeepSeek 生成中断`:`DeepSeek generation interrupted`,
    detail:zh?`服务端未完成本次回复，不等于 MCP 断连。请稍后在同一会话发送“继续”；匹配失败回复的续接请求将使用精简上下文恢复。不要在 Agent 仍运行时发送新消息。`:`The server did not finish this reply; this is not evidence of an MCP disconnect. Wait, then send “continue” in this conversation. A continuation matching the failed reply uses compact context. Do not send a new message while the Agent is running.`};
  if(finish===`rate_limit_reached`)return {code:`rate_limit_reached`,title:zh?`DeepSeek 请求限流`:`DeepSeek rate limited`,detail:zh?`请等待几分钟后重试。扩展不会自动重放请求消耗配额。`:`Wait a few minutes before retrying. The extension will not automatically replay this request.`};
  return null;
}
function DPP_STARTUP_NOTICE_331047(payload){
  try{
    const diag=payload?.diag331015,current=EQ();
    if(!current||diag?.chatSessionId!==current)return;
    const id=`dpp-startup-notice-331047`,old=document.getElementById(id);
    const info=DPP_STARTUP_STATUS_331047(diag,nX);
    if(!info){if(diag?.streamFinished===true)old?.remove();return;}
    if(!document.body)return;
    DPP_AGENT_COMPACT_STYLE_331019();
    const box=old||document.createElement(`aside`);box.id=id;box.className=`dpp-startup-notice-331047`;
    box.setAttribute(`role`,`status`);box.setAttribute(`aria-live`,`polite`);
    const heading=document.createElement(`strong`),detail=document.createElement(`p`),close=document.createElement(`button`);
    heading.textContent=info.title;detail.textContent=info.detail;close.type=`button`;
    close.textContent=String(nX||``).toLowerCase().startsWith(`zh`)?`知道了`:`Dismiss`;
    close.addEventListener(`click`,()=>box.remove());box.replaceChildren(heading,detail,close);
    if(!old)document.body.appendChild(box);
  }catch{}
}
function DPP_TASK_OVERVIEW_331047(container,fields){
  if(!container?.querySelector)return;
  const detail=container.querySelector(`.dpp-agent-status-detail`);if(!detail)return;
  const zh=String(nX||``).toLowerCase().startsWith(`zh`),counts=DPP_AGENT_STATUS_COUNTS_331010(container);
  const success=Math.max(0,counts.done-counts.failed);
  const parts=zh?[`成功 ${success}`,`运行中 ${counts.pending}`,`失败 ${counts.failed}`]:[`${success} succeeded`,`${counts.pending} running`,`${counts.failed} failed`];
  if(counts.interrupted)parts.push(zh?`中断 ${counts.interrupted}`:`${counts.interrupted} interrupted`);
  if(fields.phase===`error`||fields.phase===`paused`)parts.push(zh?`任务未完成 · 查看详情后重试`:`Incomplete · inspect details before retrying`);
  const reason=(fields.phase===`error`||fields.phase===`paused`)?String(fields.labelOverride??``).trim().slice(0,600):``;
  detail.textContent=parts.join(` · `)+(reason?`\n`+reason:``);detail.title=``;
}
/* DPP_STARTUP_UI_V47_END */
