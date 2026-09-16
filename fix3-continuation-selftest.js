function DPP_STRICT_CONTINUATION_31(e){let t=String(e??``);return/(?:\u7ee7\u7eed(?:\u6267\u884c|\u63a8\u8fdb|\u5904\u7406|\u505a)?[^\u3002\n]{0,24}(?:\u76f4\u5230|\u5230)[^\u3002\n]{0,16}\u5b8c\u6210|\u76f4\u5230[^\u3002\n]{0,24}\u5b8c\u6210|\u505a\u5b8c\u4e3a\u6b62|\u4e00\u76f4\u505a\u5230[^\u3002\n]{0,16}\u5b8c\u6210|\u5b8c\u6210\u524d[^\u3002\n]{0,16}(?:\u4e0d\u8981|\u522b)(?:\u4e2d\u65ad|\u505c\u6b62|\u505c)|\u4e0d\u8981\u4e2d\u65ad(?:\u4efb\u52a1)?|until[^.\n]{0,40}(?:complete|done)|keep\s+(?:going|working)[^.\n]{0,40}(?:complete|done)|do\s+not\s+stop[^.\n]{0,40}(?:complete|done))/i.test(t)}function DPP_MIDSTEP_CUE_31(e){let t=String(e??``);return/(?:^|[\u3002\uff01\uff1f.!?\n;\uff1b])\s*(?:\u5148|\u63a5\u7740|\u7136\u540e|\u4e0b\u4e00\u6b65|\u63a5\u4e0b\u6765|\u968f\u540e|\u518d|\u73b0\u5728)(?:\u6765|\u8981|\u9700\u8981|\u5f97|\u5e94\u8be5|\u53ef\u4ee5|\u76f4\u63a5)?\s*(?:\u6d4b\u8bd5|\u68c0\u67e5|\u9a8c\u8bc1|\u6267\u884c|\u8fd0\u884c|\u5199\u5165|\u8bfb\u53d6|\u641c\u7d22|\u67e5\u627e|\u6253\u5f00|\u4fee\u6539|\u66f4\u65b0|\u521b\u5efa|\u4fdd\u5b58|\u5b9a\u4f4d|\u786e\u8ba4|\u770b\u770b|\u8bd5\u4e00\u4e0b|\u8bd5\u8bd5|\u5904\u7406|\u4fee\u590d|\u6784\u5efa|\u90e8\u7f72|\u63d0\u4ea4|\u4e0b\u8f7d|\u4e0a\u4f20|\u540c\u6b65|\u5bfc\u51fa|\u8f6c\u6362|\u5206\u6790|\u5bf9\u6bd4|\u7ee7\u7eed)(?:\u4e00\u4e0b|\u770b\u770b|\u5b83|\u8fd9\u4e2a|\u8fd9\u4e9b|[\u3002\uff01!]|$)/i.test(t)||/(?:\u8fd8\u9700\u8981|\u4ecd\u9700|\u9700\u8981|\u5f97|\u5fc5\u987b|\u51c6\u5907|\u6253\u7b97|\u5c06\u8981|\u8981)[^\u3002\n]{0,36}(?:\u8c03\u7528|\u6267\u884c|\u8fd0\u884c|\u5199\u5165|\u8bfb\u53d6|\u6d4b\u8bd5|\u68c0\u67e5|\u9a8c\u8bc1|\u4fee\u6539|\u66f4\u65b0|\u521b\u5efa|\u4fdd\u5b58|\u641c\u7d22|\u67e5\u627e|\u786e\u8ba4|\u5904\u7406|\u4fee\u590d|\u6784\u5efa|\u90e8\u7f72|\u63d0\u4ea4|\u4e0b\u8f7d|\u4e0a\u4f20|\u540c\u6b65|\u5bfc\u51fa|\u8f6c\u6362)/i.test(t)||/(?:^|[.!?\n;])\s*(?:(?:first|next|then|now)\s+(?:i(?:'ll| will)?\s+)?|(?:i\s+)?(?:still\s+)?need(?:s)?\s+to\s+)(?:test|check|verify|run|execute|write|read|search|open|update|create|save|inspect|fix|build|deploy|commit|download|upload|sync|export|convert)/i.test(t)}function DPP_NUDGE_LIMIT_31(e,t){return String(e??``).toLowerCase().startsWith(`zh`)?`DeepSeek++ \u5df2\u8fde\u7eed\u7ea0\u504f ${t} \u6b21\uff0c\u4f46\u6a21\u578b\u4ecd\u672a\u7ed9\u51fa\u53ef\u6267\u884c\u5de5\u5177\u8c03\u7528\u6216 <task_complete> \u5b8c\u6210\u6807\u8bb0\u3002\u5df2\u5b89\u5168\u505c\u6b62\u7ea0\u504f\u4ee5\u907f\u514d\u7a7a\u8f6c\u3002`:`DeepSeek++ corrected ${t} consecutive no-tool replies, but the model still produced neither an executable tool call nor <task_complete>. Stopped safely to avoid a no-progress loop.`}

let fail=0;function t(name,got,want){let ok=got===want;console.log((ok?'PASS':'FAIL')+' '+name+' got='+got);if(!ok)fail++;}
t('sample-midstep',DPP_MIDSTEP_CUE_31('工具恢复了，但工作区是另一个项目（Athena），Obsidian vault 在 C 盘，需要用命令写入。先测试。'),true);
t('need-command',DPP_MIDSTEP_CUE_31('Obsidian vault 在 C 盘，需要用命令写入。'),true);
t('first-test',DPP_MIDSTEP_CUE_31('先测试。'),true);
t('next-check',DPP_MIDSTEP_CUE_31('下一步检查一下。'),true);
t('english-next',DPP_MIDSTEP_CUE_31('Next I will test the command.'),true);
t('final-normal',DPP_MIDSTEP_CUE_31('任务已经完成，文件已写入并验证。'),false);
t('strict-cn',DPP_STRICT_CONTINUATION_31('继续执行直到任务完成'),true);
t('strict-cn2',DPP_STRICT_CONTINUATION_31('请一直做到全部完成'),true);
t('strict-en',DPP_STRICT_CONTINUATION_31('Keep going until done'),true);
t('non-strict',DPP_STRICT_CONTINUATION_31('请检查一下文件'),false);
t('limit-zh',DPP_NUDGE_LIMIT_31('zh-CN',8).includes('8'),true);
if(fail)process.exit(1);console.log('CONTINUATION_HELPERS_PASS 11');
const fs=require('fs'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'content-scripts','content.js'),'utf8');
function scheck(name,cond){console.log((cond?'PASS':'FAIL')+' '+name);if(!cond)process.exitCode=1;}
scheck('nudge-retry-flow',source.includes('if(y.currentTurnIsNudge){if(!o)return ie=n,q(`final_after_nudge`,!0);')&&source.includes('return q(k?`tool_intent_continue`:`continue_after_nudge`,!1)'));
scheck('nudge-hard-cap',source.includes('e.nudgeCount>=e.maxNudges')&&source.includes('y.count>=Ce.maxNudges'));
scheck('nudge-reset-on-progress',source.includes('e&&(y.count=0,y.completionReason=``)'));
scheck('completion-gate-hook',source.includes('DPP_COMPLETION_GATE_31(g)')); 
scheck('old-one-nudge-stop-removed',!source.includes('y.currentTurnIsNudge?(i?ae=$z(d,b+1):ie=n,!0)'));
scheck('max-nudges-eight',source.includes('maxNudges:8'));
if(process.exitCode)process.exit(process.exitCode);
console.log('CONTINUATION_FLOW_PASS 6');
