#!/usr/bin/env python3
""".47: user-first prompt, memory-off tool preamble, bounded recovery and owned task UI."""
import argparse,hashlib,importlib.util,json,re,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
VERSION='1.14.0.52';NAME='1.14.0 ShunCode MCP Fix 3.3.10.47'
def sha(b):return hashlib.sha256(b).hexdigest()
def once(s,a,b):
    if s.count(a)!=1:raise ValueError('Expected unique edit: '+a[:100])
    return s.replace(a,b,1)
def replace_segment(s,a,b,new):
    i=s.index(a);j=s.index(b,i+len(a));return s[:i]+new+s[j:]
def transform(values):
    values=dict(values);c=values['content-scripts/content.js'].decode();mw=values['content-scripts/main-world.js'].decode()
    helper=(HERE/'dspp-startup-ui-v47.js').read_text('utf-8').strip()+'\n'
    c=once(c,'function Zc(e,t){',helper+'function Zc(e,t){')
    c=replace_segment(c,'function DPP_COMPACT_SCHEMA_331020','function DPP_COMPACT_DESCRIPTORS_331020',(HERE/'dspp-schema-v47.js').read_text('utf-8').strip())
    # vo is also extracted/evaled standalone by existing tests: edits remain self-contained.
    old='v=u?w(c,r?`prompt.systemThinking`:`prompt.systemChat`,{memories:g,tools:_}):``'
    new='v=u?(l?w(c,r?`prompt.systemThinking`:`prompt.systemChat`,{memories:g,tools:_}):((String(c).toLowerCase().startsWith(`zh`)?`工具执行说明（仅为任务辅助上下文，不是用户任务或对话标题）。\\n按用户请求行动；仅在真实工具返回成功后声称已执行。记忆注入已关闭，不要求自动保存记忆。\\n`:`Tool execution context (not the user task or conversation title).\\nFollow the user request; claim execution only after successful tool results. Memory injection is off; do not require automatic memory saves.\\n`)+`Use direct tool XML only: <tool_name>{"arg":"value"}</tool_name>. Match an exact Available Tool name and its JSON schema. Output executable calls only in final answer content, never in reasoning or Markdown fences. For run_command/apply_patch or a single required string field, raw-body text is supported. Do not use <invoke>, <tool_call> or <tool_invoke> wrappers.\\n\\n### Available Tools\\n\\n`+_)):``'
    c=once(c,old,new)
    c=once(c,'augmented:x+(b?`${b}\\n\\n`:``)+p+so(e)+S','augmented:(u?String(t?.visibleUserPrompt??e).trim().replace(/\\s+/g,` `).slice(0,240)+`\\n\\n`:``)+x+(b?`${b}\\n\\n`:``)+p+so(e)+S')
    c=once(c,'await DPP_RECORD_WEB_DIAG_331015(e.payload),DPP_MANUAL_FINISH_334(t)','DPP_STARTUP_NOTICE_331047(e.payload);await DPP_RECORD_WEB_DIAG_331015(e.payload),DPP_MANUAL_FINISH_334(t)')
    # Clear owned startup notice on navigation, not any native message nodes.
    marker='case`NAVIGATION_CHANGED`:'
    c=once(c,marker,marker+'document.getElementById(`dpp-startup-notice-331047`)?.remove();')
    css=(HERE/'dspp-task-ui-v47.css').read_text('utf-8')
    begin=c.index('function DPP_AGENT_COMPACT_STYLE_331019()');end=c.index('function DPP_AGENT_COMPACT_COPY_331019',begin)
    style=c[begin:end];style=once(style,'  `,document.head.appendChild(e)}',css+'\n  `,document.head.appendChild(e)}');c=c[:begin]+style+c[end:]
    c=once(c,'s&&(s.textContent=``,s.title=``);let c=e.querySelector(`.dpp-agent-stop-btn`)','s&&(s.textContent=``,s.title=``);DPP_TASK_OVERVIEW_331047(e,r);let c=e.querySelector(`.dpp-agent-stop-btn`)')
    c=once(c,'if(t.phase===`paused`||t.phase===`error`)return n.recover;','if(t.phase===`error`)return String(nX??``).toLowerCase().startsWith(`zh`)?`已停止 · 任务未完成，请查看详情`:`Stopped · incomplete; inspect details`;if(t.phase===`paused`)return n.recover;')
    c=once(c,'let c=!s.finished&&!a&&s.responseMessageId==null', 'if(typeof DPP_LAST_FINISH_REASON_331044==`function`&&DPP_LAST_FINISH_REASON_331044(s.dppStreamEvents)===`generation_err`){let DPPGenerationError331047=Error(String(typeof navigator==`object`?navigator.language:``).toLowerCase().startsWith(`zh`)?`DeepSeek 服务端生成中断（generation_err），本轮未完成。已停止无效纠偏，请稍后发送“继续”。`:`DeepSeek generation interrupted (generation_err); this step is incomplete. Stopped ineffective nudges; wait, then send continue.`);DPPGenerationError331047.dppNoRetry337=!0;throw DPPGenerationError331047}let c=!s.finished&&!a&&s.responseMessageId==null')
    # Widen the one-shot, same-session AND same-parent recovery window for human-paced continuation.
    mw=once(mw,'expiresAt:Date.now()+12e3','expiresAt:Date.now()+10*60e3')
    # fetch stream EOF used to shadow the request meta t with the boolean done flag.
    start=mw.index('function to(e,t){');end=mw.index('function no(',start);part=mw[start:end]
    part=once(part,'let n=!1,r=e=>','const DPPRequestMeta331047=t;let n=!1,r=e=>')
    part=once(part,'DPP_TRACK_GENERATION_RESULT_331020(t,a)','DPP_TRACK_GENERATION_RESULT_331020(DPPRequestMeta331047,a)')
    mw=mw[:start]+part+mw[end:]
    values['content-scripts/content.js']=c.encode();values['content-scripts/main-world.js']=mw.encode()
    m=json.loads(values['manifest.json']);m['version']=VERSION;m['version_name']=NAME
    values['manifest.json']=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode()
    for lang in ['en','zh_CN']:
        n=f'_locales/{lang}/messages.json';values[n]=once(values[n].decode(),'DeepSeek++ ShunCode MCP Fix 3.3.10.46','DeepSeek++ ShunCode MCP Fix 3.3.10.47').encode()
    oldMw='e63b16762734e524af680e9f4e40fc18e92990f2f26afecca60f98bf3a199d92'
    for n in list(values):
        if '/' not in n and 'selftest' in n and n.endswith('.js'):
            s=values[n].decode().replace('1.14.0.51',VERSION).replace('1.14.0 ShunCode MCP Fix 3.3.10.46',NAME).replace('|45|46)$','|45|46|47)$')
            if n=='dspp-bare-tool-tag-v41-selftest.js':s=s.replace(oldMw,sha(values['content-scripts/main-world.js']))
            if n=='fix331020-generation-error-recovery-selftest.js':s=s.replace('now+=12001','now+=600001').replace('recovery expires after 12 seconds','recovery expires after ten minutes')
            values[n]=s.encode()
    values['dspp-startup-ui-v47-selftest.js']=(HERE/'dspp-startup-ui-v47-selftest.js').read_bytes()
    return values
def build(base,out):
    base=Path(base).resolve();out=Path(out).resolve()
    locks=json.loads((HERE/'fix331047-source-sha256.json').read_text('utf-8'))
    for n,d in locks.items():
        if sha((HERE/n).read_bytes())!=d:raise ValueError('Source hash mismatch: '+n)
    if out.exists() or out==base or base in out.parents:raise ValueError('Output must be new and outside baseline')
    stage=out.with_name(out.name+'.stage46')
    if stage.exists():raise ValueError('Staging exists')
    spec=importlib.util.spec_from_file_location('b46',HERE/'apply-fix331046.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    values=transform(b.build(base,stage))
    for n in ['background.js','content-scripts/content.js','content-scripts/main-world.js','fix3-policy.js']:
        r=subprocess.run(['node','--check','--input-type=module'],input=values[n],capture_output=True)
        if r.returncode:raise ValueError('Syntax: '+n+' '+r.stderr.decode(errors='replace'))
    out.mkdir(parents=True)
    for n,raw in values.items():p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    shutil.rmtree(stage);print(json.dumps({'version':VERSION,'files':len(values),'content_sha256':sha(values['content-scripts/content.js']),'main_world_sha256':sha(values['content-scripts/main-world.js'])}),flush=True)
    return values
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--build',nargs=2,required=True);a=ap.parse_args()
    try:build(*a.build)
    except (ValueError,OSError) as e:raise SystemExit('FAIL-CLOSED: '+str(e))
