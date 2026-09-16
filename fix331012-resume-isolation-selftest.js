const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = __dirname;
const src = fs.readFileSync(path.join(root, 'content-scripts', 'content.js'), 'utf8');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8'));
let passed = 0;
let failed = 0;

function test(name, condition, detail = '') {
  if (condition) {
    passed += 1;
    console.log(`PASS ${name}${detail ? ` ${detail}` : ''}`);
  } else {
    failed += 1;
    console.error(`FAIL ${name}${detail ? ` ${detail}` : ''}`);
  }
}

function between(start, end) {
  const a = src.indexOf(start);
  const b = src.indexOf(end, a);
  if (a < 0 || b < 0) throw new Error(`missing helper range: ${start} -> ${end}`);
  return src.slice(a, b);
}

const helperSource = between('function DPP_RESUME_INTENT_331010', 'var DPP_AGENT_SYNTHETIC_REF_FILES_337');
const context = {
  Date,
  Number,
  String,
  JSON,
  Map,
  console: { error() {} },
  zz(value, limit) {
    return value && value.length > limit ? `${value.slice(0, limit)}\n...[truncated]` : value;
  },
  DPP_TRACE_EXPIRED_33109(trace, now) {
    return now - Number(trace.updatedAt || trace.createdAt || 0) >= 300000;
  },
  KY: new Map(),
};
vm.createContext(context);
vm.runInContext(
  `${helperSource};Object.assign(globalThis,{prepare:DPP_AGENT_RESUME_PREPARE_331012});`,
  context,
);

const now = Date.now();
const trace = {
  id: 'interrupted',
  chatSessionId: 'chat',
  status: 'error',
  originalPrompt: '完成 Daub 剩余验证',
  error: '页面请求中断',
  createdAt: now - 30000,
  updatedAt: now - 10000,
  initialExecutions: [{
    callId: 'huge-history',
    name: 'run_command',
    result: { ok: true, detail: 'x'.repeat(100000) },
  }],
  steps: [{
    index: 8,
    status: 'complete',
    text: '<｜DSML｜invoke name="run_command">Daub 已编译；下一步验证 timelapse。',
    reasoning: '',
    toolExecutions: [],
  }],
};
const request = { originalPrompt: '继续任务', chatSessionId: 'chat' };
const prepared = context.prepare(request, [trace]);

test('version includes or supersedes isolated resume hotfix', Number(manifest.version.split('.').at(-1)) >= 17);
test('version name includes or supersedes isolated resume hotfix', /Fix 3\.3\.10\.(?:12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31|32)$/.test(manifest.version_name));
test('isolated checkpoint is generated', typeof prepared?.prompt === 'string');
test('checkpoint keeps verified progress', prepared.prompt.includes('timelapse'));
test('checkpoint strips DSML markup', !prepared.prompt.includes('DSML') && !prepared.prompt.includes('<｜'));
test('checkpoint remains hard capped', prepared.prompt.length <= 2400, `chars=${prepared.prompt.length}`);
test('preparation returns no historical tool objects', !Object.hasOwn(prepared, 'toolExecutions'));
test('source trace identity is retained', prepared.sourceTraceIds.join(',') === 'interrupted');

const requestAugmenter = between('function Zc(e,t)', 'function Qc(e)');
const agentLauncher = between('async function J$(e,t)', 'var DPP_AGENT_IDLE_TIMEOUT_33108');
test('manual DeepSeek request has no resume gateway', !requestAugmenter.includes('DPP_MANUAL_RESUME_PROMPT'));
test('manual DeepSeek prompt is not reassigned', !requestAugmenter.includes('n.prompt=r'));
test('Agent uses isolated resume preparation', agentLauncher.includes('DPP_AGENT_RESUME_PREPARE_331012(e,await k0())'));
test('only the internal Agent receives the checkpoint', agentLauncher.includes('originalPrompt:DPPAgentPrompt,agentTaskPrompt:DPPAgentPrompt'));
test('current-turn executions remain current-only', agentLauncher.includes('toolExecutions:n'));
test('historical execution replay is absent', !agentLauncher.includes('DPPResume?.toolExecutions'));
test('trace stores the raw user request', agentLauncher.includes('BY=b0(e,r,t,p,s)'));
test('trace does not store the synthetic checkpoint', !agentLauncher.includes('b0(DPPAgentRequest'));

if (failed) {
  console.error(`FIX331012_FAIL pass=${passed} fail=${failed}`);
  process.exit(1);
}
console.log(`FIX331012_PASS ${passed}/${passed + failed}`);
