const fs = require('fs');
const vm = require('vm');
const path = require('path');

const root = process.argv[2] || __dirname;
const src = fs.readFileSync(path.join(root, 'content-scripts', 'content.js'), 'utf8');

let passed = 0;
let failed = 0;
function test(name, condition, detail = '') {
  console.log(`${condition ? 'PASS' : 'FAIL'} ${name}${detail ? ` ${detail}` : ''}`);
  condition ? passed++ : failed++;
}
function between(start, end) {
  const i = src.indexOf(start);
  const j = src.indexOf(end, i + start.length);
  if (i < 0 || j < 0) throw new Error(`range missing ${start} -> ${end}`);
  return src.slice(i, j);
}

const resultHelpers = between(
  'function DPP_RUN_COMMAND_TEXT_33108',
  'function DPP_DESCRIPTOR_PROPERTY_33108',
);
const resultContext = { JSON, Number, Object, String };
resultContext.DPP_TOOL_NAME_33 = (name) => {
  const value = String(name);
  return value === 'run_command' || value.endsWith('_run_command')
    ? 'run_command'
    : value.split(/[.:/]/).pop();
};
vm.createContext(resultContext);
vm.runInContext(
  `${resultHelpers};globalThis.normalize=DPP_NORMALIZE_RUN_COMMAND_RESULT_33108;`,
  resultContext,
);
const shellFailure = {
  ok: true,
  summary: 'MCP 工具已执行',
  detail: JSON.stringify([{ type: 'text', text: 'status: failed\nexit_code: 1' }]),
};
const normalized = resultContext.normalize(
  { name: 'run_command', invocationName: 'mcp_shuncode_run_command' },
  shellFailure,
);
test('call object is recognized as run_command', normalized.ok === false);
test('non-zero exit is a confirmed failure', normalized.error?.details?.externalOutcome === 'confirmed');
test('non-zero exit code is retained', normalized.error?.details?.exitCode === 1);
test('original command detail is retained for diagnostics', normalized.detail === shellFailure.detail);

const errorSource = between('function DPP_ERROR_CLASS_3', 'function DPP_CAPABILITY_WINDOW_32');
const errorContext = { String };
vm.createContext(errorContext);
vm.runInContext(`${errorSource};globalThis.classify=DPP_ERROR_CLASS_3;`, errorContext);
test(
  'SSE loss is classified as transport failure',
  errorContext.classify({ code: 'mcp_tool_call_failed', message: 'MCP SSE stream ended without a matching response.' }).stage === 'mcp_transport',
);
test(
  'ambiguous SSE loss requires outcome verification',
  errorContext.classify({
    code: 'mcp_tool_call_failed',
    message: 'MCP SSE stream ended without a matching response.',
    details: { externalOutcome: 'ambiguous' },
  }).action === 'verify_external_outcome_before_retry',
);
test(
  'network loss recommends reconnecting only when safe',
  errorContext.classify({ code: 'mcp_tool_call_failed', message: 'network error' }).action === 'reconnect_and_retry_if_safe',
);

const hintSource = between('function DPP_RESULT_HINT_33', 'function DPP_FACT_TEXT_33109');
const hintContext = { String };
hintContext.DPP_TOOL_NAME_33 = (name) => String(name).split(/[.:/]/).pop();
vm.createContext(hintContext);
vm.runInContext(`${hintSource};globalThis.hint=DPP_RESULT_HINT_33;`, hintContext);
const ambiguousHint = hintContext.hint({
  name: 'run_command',
  result: {
    error: {
      code: 'mcp_tool_call_failed',
      message: 'MCP SSE stream ended without a matching response.',
      details: { externalOutcome: 'ambiguous' },
    },
  },
}).recoveryHint;
test('ambiguous mutation hint forbids blind repeats', /Do not blindly repeat/.test(ambiguousHint));
test('ambiguous mutation hint requires read-only verification', /read-only command/.test(ambiguousHint));
const imageHint = hintContext.hint({
  name: 'read_image',
  result: { error: { code: 'PATH_OUTSIDE_WORKSPACE', message: 'outside' } },
}).recoveryHint;
test('out-of-workspace image hint gives copy recovery', /Copy the image into the current workspace/.test(imageHint));
const sizeHint = hintContext.hint({
  name: 'read_image',
  result: { error: { code: 'mcp_tool_call_failed', message: 'MCP response exceeded 128000 bytes before parsing completed.' } },
}).recoveryHint;
test('oversized image hint recommends reducing output', /downsample large images/.test(sizeHint));

const statusHelpers = between('var DPP_AGENT_STATUS_331010', 'function XB(e,t)');
const statusContext = {
  Date,
  Math,
  Number,
  String,
  nX: 'zh-CN',
  Hz: () => ({ maxSteps: 96 }),
};
vm.createContext(statusContext);
vm.runInContext(
  `${statusHelpers};Object.assign(globalThis,{copy:DPP_AGENT_STATUS_COPY_331010,reset:DPP_AGENT_STATUS_RESET_331010,touch:DPP_AGENT_STATUS_TOUCH_331010,fields:DPP_AGENT_STATUS_FIELDS_331010,detail:DPP_AGENT_STATUS_DETAIL_331010});`,
  statusContext,
);
const fakeContainer = {
  querySelectorAll() {
    return [
      { getAttribute: () => 'ok' },
      { getAttribute: () => 'err' },
      { getAttribute: () => 'pending' },
      { getAttribute: () => 'interrupted' },
    ];
  },
};
statusContext.reset('修改项目代码');
statusContext.touch('tool', 'ShunCode / run_command');
const fields = statusContext.fields(fakeContainer, 2);
test('status counts settled tools', fields.completedTools === 2);
test('status counts active tools', fields.pendingTools === 1);
test('status counts failed tools', fields.failedTools === 1);
test('status counts interrupted tools', fields.interruptedTools === 1);
test('status exposes remaining safety rounds', fields.budgetRemaining === 93);
const detail = statusContext.detail({ phase: 'running', ...fields });
test('Chinese status names the active tool', detail.includes('ShunCode / run_command'));
test('status labels remaining value as safety capacity', detail.includes('安全额度剩余 93 轮'));
test('status explicitly says capacity is not task remainder', detail.includes('不是任务剩余量'));
test('status explains unscheduled work is dynamic', detail.includes('由模型根据工具结果动态规划'));
test('paused status says work remains', statusContext.detail({ phase: 'paused' }).includes('仍有工作未执行'));
test('error status says task is incomplete', statusContext.detail({ phase: 'error' }).includes('任务未完成'));

const uiSource = between('function XB(e,t)', 'function eV(e)');
test('status UI has a prominent phase badge', uiSource.includes('dpp-agent-status-badge'));
test('status UI has an indeterminate progress track', uiSource.includes('dpp-agent-progress-track'));
test('status UI reports accessibility busy state', uiSource.includes('aria-busy'));
test('running status recomputes live counters', uiSource.includes('DPP_AGENT_STATUS_FIELDS_331010'));

const rowSource = between('function PV(e,t,n,r)', 'function LV(e,t,n)');
test('pending tool rows show visible running text', src.includes('r?.toolRunning??`Running`'));
test('tool rows retain call ids', rowSource.includes('data-tool-call-id'));
test('tool completion settles the matching row', rowSource.includes('DPP_AGENT_PENDING_ROW_331010'));
test('step completion skips already-settled rows', rowSource.includes('getAttribute(`data-tool-status`)!==`pending`'));
test('interrupted tools show visible text', rowSource.includes('e.textContent=NX().toolInterrupted'));

const agentLoop = between('async function Jz(e)', 'function Yz(e)');
test('tool completion is emitted immediately', agentLoop.includes('n(`AGENT_TOOL_COMPLETE`'));
test('tool completion carries the call id', agentLoop.includes('callId:e.toolCallId'));
test('empty final response fails closed', agentLoop.includes('error:DPP_EMPTY_FINAL_ERROR_331010(d)'));
test('empty final response emits loop error', agentLoop.includes('if(ae===null&&ie===null){n(`AGENT_LOOP_ERROR`'));

const dispatch = between('function a1(e,t,n)', 'function o1()');
test('tool completion event has a UI handler', dispatch.includes('case`AGENT_TOOL_COMPLETE`:DPP_AGENT_TOOL_COMPLETE_331010(t)'));
test('runtime reset derives the correct safety budget', src.includes('DPP_AGENT_STATUS_RESET_331010(e.originalPrompt)'));
test('stream activity updates visible liveness', src.includes('DPP_AGENT_STATUS_TOUCH_331010(`responding`)'));
test('reasoning activity updates visible liveness', src.includes('DPP_AGENT_STATUS_TOUCH_331010(`thinking`)'));

const resumeHelpers = between('function DPP_RESUME_INTENT_331010', 'var DPP_AGENT_SYNTHETIC_REF_FILES_337');
const resumeContext = { Date, Number, String, JSON };
resumeContext.zz = (value, limit) => value && value.length > limit ? `${value.slice(0, limit)}\n...[truncated]` : value;
resumeContext.DPP_TRACE_EXPIRED_33109 = (trace, now) => now - Number(trace.updatedAt || trace.createdAt || 0) >= 300000;
resumeContext.KY = new Map();
vm.createContext(resumeContext);
vm.runInContext(
  `${resumeHelpers};Object.assign(globalThis,{intent:DPP_RESUME_INTENT_331010,chain:DPP_RESUME_TRACE_CHAIN_331010,prepare:DPP_AGENT_RESUME_PREPARE_331010,manualPrompt:DPP_MANUAL_RESUME_PROMPT_331010});`,
  resumeContext,
);
const now = Date.now();
const prior = {
  id: 'original-run', chatSessionId: 'chat-1', status: 'error', originalPrompt: 'A',
  anchorContent: '选择 A：安装 Rust，编译并验证 Daub。', error: 'interrupted before timelapse',
  createdAt: now - 50_000, updatedAt: now - 40_000,
  initialExecutions: [{ name: 'run_command', result: { ok: true, summary: 'Rust installed' } }],
  steps: [{ index: 7, status: 'complete', text: 'Daub 编译成功，真实渲染和确定性校验通过；下一步验证 timelapse。', reasoning: '', toolExecutions: [{ name: 'run_command', result: { ok: true, summary: 'build and render passed' } }] }],
};
const restarted = {
  id: 'bad-restart', chatSessionId: 'chat-1', status: 'stopping', originalPrompt: '继续中断的任务',
  anchorContent: '重新探测环境', error: 'stopped', createdAt: now - 20_000, updatedAt: now - 10_000,
  initialExecutions: [], steps: [{ index: 0, status: 'complete', text: '重复进行了环境探测', reasoning: '', toolExecutions: [] }],
};
const complete = { ...prior, id: 'complete-run', status: 'complete', updatedAt: now - 60_000 };
const foreign = { ...prior, id: 'foreign-run', chatSessionId: 'chat-2', updatedAt: now - 1_000 };
const current = { originalPrompt: '继续中断的任务', chatSessionId: 'chat-1' };
test('Chinese interrupted-task request is recognized', resumeContext.intent(current.originalPrompt));
test('ordinary new task does not trigger resume', !resumeContext.intent('重新安装另一个项目'));
const chain = resumeContext.chain(current, [prior, restarted, complete, foreign], now);
test('resume chain follows the latest interrupted run back to its source', chain.map(x => x.id).join(',') === 'original-run,bad-restart');
const prepared = resumeContext.prepare(current, [{ name: 'set_todos', result: { ok: true, summary: 'current' } }], [prior, restarted, complete, foreign]);
test('resume prompt says this is not a new task', prepared.prompt.includes('This is a resume, not a new task'));
test('resume prompt carries verified prior progress', prepared.prompt.includes('Daub 编译成功'));
test('resume prompt retains the unfinished next action', prepared.prompt.includes('timelapse'));
test('resume rules prohibit redoing confirmed work', prepared.prompt.includes('Do not restart discovery'));
test('resume rules preserve existing ShunCode progress', prepared.prompt.includes('todo/progress state before replacing it'));
test('resume rules merge repeated attempts at the furthest progress', prepared.prompt.includes('Merge duplicate attempts') && prepared.prompt.includes('furthest verified result'));
test('resume rules never reset completed todos', prepared.prompt.includes('never reset completed todos to pending'));
test('prior tool results are injected before current results', prepared.toolExecutions.map(x => x.result.summary).join(',') === 'Rust installed,build and render passed,current');
test('complete and foreign traces are excluded', !prepared.sourceTraceIds.includes('complete-run') && !prepared.sourceTraceIds.includes('foreign-run'));
const laterComplete = { ...prior, id: 'later-complete', status: 'complete', updatedAt: now - 5_000 };
test('a newer completed task blocks resurrection of older failures', resumeContext.chain(current, [prior, restarted, laterComplete], now).length === 0);
const distantSource = { ...prior, id: 'distant-source', updatedAt: now - 8 * 60 * 60 * 1000 };
test('resume chaining does not merge distant unrelated failures', resumeContext.chain(current, [distantSource, restarted], now).map(x => x.id).join(',') === 'bad-restart');
resumeContext.KY.set(prior.id, prior);
resumeContext.KY.set(restarted.id, restarted);
test('manual DeepSeek turn receives the checkpoint before its first tool call', resumeContext.manualPrompt(current.originalPrompt, current.chatSessionId).includes('Daub 编译成功'));
test('Agent launch reads durable traces before starting', src.includes('DPP_AGENT_RESUME_PREPARE_331010(e,n,await k0())'));
test('resumed prompt is persisted into the new trace', src.includes('BY=b0(DPPAgentRequest,r,t,p,s)'));
test('resumed history is passed to the continuation loop', src.includes('toolExecutions:DPPResume?.toolExecutions??n'));
const requestAugmenter = between('function Zc(e,t)', 'function Qc(e)');
test('manual request prompt is checkpoint-aware', requestAugmenter.includes('DPP_MANUAL_RESUME_PROMPT_331010(r,t.chatSessionId)'));
test('manual request keeps the raw user continuation for Agent history injection', requestAugmenter.includes('agentTaskPrompt:DPPOriginalPrompt331010'));
test('manual request augmenter receives the active chat id', src.includes('d=Zc(l,{chatSessionId:AZ(l),memories:XY'));

if (failed) {
  console.error(`FIX331010_FAIL pass=${passed} fail=${failed}`);
  process.exit(1);
}
console.log(`FIX331010_PASS ${passed}/${passed + failed}`);
