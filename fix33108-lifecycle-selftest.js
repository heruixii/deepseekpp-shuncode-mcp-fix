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
  'function DPP_PTY_EMPTY_33',
);
const resultContext = { JSON, Number, Object, String, DPP_ANNOTATE_EMPTY_PTY_331028:(e,t)=>t };
resultContext.DPP_TOOL_NAME_33 = (name) => String(name).split(/[.:/]/).pop();
vm.createContext(resultContext);
vm.runInContext(
  `${resultHelpers};Object.assign(globalThis,{normalize:DPP_NORMALIZE_RUN_COMMAND_RESULT_33108,hasProperty:DPP_DESCRIPTOR_PROPERTY_33108});`,
  resultContext,
);

const failedStatus = resultContext.normalize('run_command', {
  ok: true,
  summary: 'MCP tool executed',
  detail: 'status: failed\nexit_code: 127',
});
test('failed command status becomes tool failure', failedStatus.ok === false);
test('failed command exposes confirmed outcome', failedStatus.error?.details?.externalOutcome === 'confirmed');
test('failed command preserves exit code', failedStatus.error?.details?.exitCode === 127);

const nonZero = resultContext.normalize('run_command', {
  ok: true,
  summary: 'MCP tool executed',
  detail: [{ type: 'text', text: 'status: completed\nexit_code: 2' }],
});
test('non-zero command exit becomes tool failure', nonZero.ok === false);

const jsonFailure = resultContext.normalize('run_command', {
  ok: true,
  summary: 'MCP tool executed',
  output: { status: 'failed', exit_code: 9 },
});
test('JSON command status becomes tool failure', jsonFailure.ok === false);
test('JSON command exit code is preserved', jsonFailure.error?.details?.exitCode === 9);

const success = { ok: true, summary: 'ok', detail: 'status: completed\nexit_code: 0' };
test('successful command remains unchanged', resultContext.normalize('run_command', success) === success);
test('non-command result remains unchanged', resultContext.normalize('read_files', success) === success);
test(
  'descriptor property detection accepts advertised execution',
  resultContext.hasProperty({ inputSchema: { properties: { execution: {} } } }, 'execution') === true,
);
test(
  'descriptor property detection rejects absent execution',
  resultContext.hasProperty({ inputSchema: { properties: { command: {} } } }, 'execution') === false,
);

const lifecycleHelpers = between(
  'var DPP_AGENT_IDLE_TIMEOUT_33108',
  'function Y$(e)',
);
const lifecycleContext = {
  NR: 120000,
  Error,
  String,
  setTimeout,
  clearTimeout,
  LY: 'loop-1',
  BY: { totalSteps: 6, totalTools: 9 },
  failure: null,
};
lifecycleContext.b1 = (value) => { lifecycleContext.failure = value; };
vm.createContext(lifecycleContext);
vm.runInContext(
  `${lifecycleHelpers};Object.assign(globalThis,{watchdog:DPP_AGENT_IDLE_WATCHDOG_33108,failActive:DPP_AGENT_FAIL_ACTIVE_33108});`,
  lifecycleContext,
);

test(
  'active failure writes current totals',
  lifecycleContext.failActive('loop-1', 'boom') === true
    && lifecycleContext.failure.stepIndex === 6
    && lifecycleContext.failure.totalTools === 9,
);
test('foreign loop cannot finalize active trace', lifecycleContext.failActive('other-loop', 'boom') === false);

(async () => {
  let fires = 0;
  const signal = new AbortController().signal;
  const watchdog = lifecycleContext.watchdog(signal, () => { fires++; }, 25);
  await new Promise((resolve) => setTimeout(resolve, 15));
  watchdog.kick();
  await new Promise((resolve) => setTimeout(resolve, 15));
  test('watchdog kick resets inactivity window', fires === 0);
  await new Promise((resolve) => setTimeout(resolve, 18));
  test('watchdog fires after renewed inactivity window', fires === 1);
  watchdog.clear();

  let abortedFires = 0;
  const controller = new AbortController();
  const abortedWatchdog = lifecycleContext.watchdog(
    controller.signal,
    () => { abortedFires++; },
    10,
  );
  controller.abort();
  await new Promise((resolve) => setTimeout(resolve, 20));
  abortedWatchdog.clear();
  test('aborted signal suppresses watchdog callback', abortedFires === 0);

  const restore = between('async function M0(e,t)', 'function N0(e)');
  test('startup durably persists normalized traces', restore.includes('(c||l)&&await O0(u)'));
  test('startup still recognizes running traces', restore.includes('e.status===`running`'));

  const runner = between('async function i1(e)', 'function a1(e,t,n)');
  test('overlap uses full stopping path', runner.includes('sX&&r1()'));
  test('runner owns inactivity watchdog', runner.includes('DPP_AGENT_IDLE_WATCHDOG_33108(n.signal'));
  test('runner resets watchdog on every event', runner.includes('d?.kick();let r=a1('));
  test('runner aborts on inactivity', runner.includes('n.abort(new DOMException(t,`TimeoutError`))'));
  test('runner detects missing terminal event', runner.includes('Agent loop ended without a terminal event.'));
  test('runner catches non-abort failures', runner.includes('if(!n.signal.aborted)'));
  test('runner always clears watchdog', runner.includes('finally{d.clear(),await MZ(r)'));

  const startWrapper = between('function Y$(e)', 'function X$(e)');
  test('detached runner catch finalizes active trace', startWrapper.includes('DPP_AGENT_FAIL_ACTIVE_33108(e.loopId,n)'));

  const stopArea = between('function r1()', 'async function i1(e)');
  test('pagehide best-effort stop is installed', stopArea.includes('window.addEventListener(`pagehide`,()=>{t1()&&r1()})'));

  const toolWrapper = between('function Uz(e,t,d)', 'var Wz=');
  test(
    'PTY direct fallback requires advertised schema field',
    toolWrapper.includes('DPP_DESCRIPTOR_PROPERTY_33108(e,`execution`)&&DPP_SHOULD_DIRECT_RETRY_33'),
  );

  const commonExecution = between('async function i2(e,t)', 'function a2(e)');
  test(
    'manual and agent tool results normalize command exit status',
    (commonExecution.match(/DPP_NORMALIZE_RUN_COMMAND_RESULT_33108/g) || []).length === 3,
  );

  test('prompt declares native Bash', src.includes('[Fix 3.3.10.8 shell contract] ShunCode run_command executes native Bash.'));
  test('prompt no longer recommends execution=direct', !src.includes('prefer run_command execution=direct'));
  test('manifest runtime marker present', src.includes('DPP_AGENT_PAGEHIDE_BOUND_33108'));

  if (failed) {
    console.error(`FIX33108_FAIL pass=${passed} fail=${failed}`);
    process.exit(1);
  }
  console.log(`FIX33108_PASS ${passed}/${passed + failed}`);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
