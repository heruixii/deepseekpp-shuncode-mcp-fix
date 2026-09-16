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
vm.runInContext(`${helperSource};Object.assign(globalThis,{light:DPP_RESUME_LIGHT_PROMPT_331011,bounded:DPP_RESUME_EXECUTIONS_BOUNDED_331011,prepare:DPP_AGENT_RESUME_PREPARE_331011,manual:DPP_MANUAL_RESUME_PROMPT_SAFE_331011});`, context);

const now = Date.now();
const noisy = '<｜DSML｜invoke name="run_command"><｜DSML｜parameter name="command">repeat</｜DSML｜parameter>';
const trace = {
  id: 'interrupted',
  chatSessionId: 'chat',
  status: 'error',
  originalPrompt: '完成 Daub 剩余验证',
  error: '页面请求中断',
  createdAt: now - 30000,
  updatedAt: now - 10000,
  initialExecutions: [],
  steps: Array.from({ length: 20 }, (_, index) => ({
    index,
    status: 'complete',
    text: `${noisy} 已验证步骤 ${index} ${'结果'.repeat(180)}`,
    reasoning: '',
    toolExecutions: [],
  })),
};
context.KY.set(trace.id, trace);
const request = { originalPrompt: '继续任务', chatSessionId: 'chat' };
const prompt = context.light(request, [trace]);

test('version includes or supersedes crash hotfix', Number(manifest.version.split('.').at(-1)) >= 16);
test('version name includes or supersedes crash hotfix', /Fix 3\.3\.10\.(?:11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31|32|33)$/.test(manifest.version_name));
test('safe resume prompt is generated', typeof prompt === 'string' && prompt.includes('safe resume'));
test('safe resume prompt is hard capped', prompt.length <= 2400, `chars=${prompt.length}`);
test('raw DSML control markup is stripped', !prompt.includes('DSML') && !prompt.includes('<｜'));
test('original task remains visible', prompt.includes('完成 Daub 剩余验证'));
test('furthest progress remains visible', prompt.includes('已验证步骤 19'));
test('todo reset remains forbidden', prompt.includes('never reset completed todos'));
test('manual gateway uses the same bounded prompt', context.manual('继续任务', 'chat') === prompt);

const executions = Array.from({ length: 40 }, (_, index) => ({
  callId: `call-${index % 15}`,
  name: 'run_command',
  result: { ok: true, summary: `summary-${index % 15}`, detail: 'x'.repeat(4000) },
}));
const bounded = context.bounded([{ ...trace, initialExecutions: executions }], []);
const boundedBytes = bounded.reduce((sum, item) => sum + JSON.stringify(item).length, 0);
test('resume history has a call-count ceiling', bounded.length <= 12, `count=${bounded.length}`);
test('resume history has a byte ceiling', boundedBytes <= 24576, `bytes=${boundedBytes}`);
test('duplicate copied executions are removed', new Set(bounded.map(item => item.callId)).size === bounded.length);

const circular = { name: 'run_command', result: { ok: true, summary: 'circular' } };
circular.self = circular;
const prepared = context.prepare(request, [circular], [trace]);
test('circular execution cannot crash resume preparation', prepared && Array.isArray(prepared.toolExecutions));

const savedKY = context.KY;
context.KY = { values() { throw new Error('corrupt runtime map'); } };
test('manual resume failures fall open', context.manual('继续任务', 'chat') === null);
context.KY = savedKY;

const requestAugmenter = between('function Zc(e,t)', 'function Qc(e)');
const agentLauncher = between('async function J$(e,t)', 'var DPP_AGENT_IDLE_TIMEOUT_33108');
test('legacy fail-open gateway remains available for compatibility', helperSource.includes('DPP_MANUAL_RESUME_PROMPT_SAFE_331011'));
test('manual request path no longer calls unsafe gateway', !requestAugmenter.includes('DPP_MANUAL_RESUME_PROMPT_331010(r,t.chatSessionId)'));
test('Agent launch uses current isolated resume preparation', agentLauncher.includes('DPP_AGENT_RESUME_PREPARE_331012'));
test('legacy unbounded preparation is not used by Agent launch', !agentLauncher.includes('DPP_AGENT_RESUME_PREPARE_331010(e,n,await k0())'));

if (failed) {
  console.error(`FIX331011_FAIL pass=${passed} fail=${failed}`);
  process.exit(1);
}
console.log(`FIX331011_PASS ${passed}/${passed}`);
