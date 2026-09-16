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

const factHelpers = between('function DPP_FACT_TEXT_33109', 'function Iz(e)');
const factContext = { JSON, Number, Object, Array, Set, String };
factContext.DPP_TOOL_NAME_33 = (name) => {
  const value = String(name).toLowerCase();
  return value === 'list_directory' || value.endsWith('_list_directory')
    ? 'list_directory'
    : value.split(/[.:/]/).pop();
};
vm.createContext(factContext);
vm.runInContext(
  `${factHelpers};Object.assign(globalThis,{facts:DPP_VERIFIED_FACTS_33109,text:DPP_FACT_TEXT_33109,claimMismatch:DPP_STAT_CLAIM_MISMATCH_33109});`,
  factContext,
);

const directoryLines = [
  '=== LIST_DIRECTORY ===',
  'path: .',
  'returned_entries: 119',
  'truncated: false',
  ...Array.from({ length: 23 }, (_, i) => `[DIR] dir-${i}`),
  ...Array.from({ length: 96 }, (_, i) => `[FILE] file-${i}.txt`),
].join('\n');
const listResult = {
  name: 'mcp_shuncode_list_directory',
  result: {
    ok: true,
    detail: JSON.stringify([{ type: 'text', text: directoryLines }]),
  },
};
const listFacts = factContext.facts(listResult).verifiedFacts;
test('list total is extracted from explicit tool metadata', listFacts?.returnedEntries === 119);
test('directory count is deterministically derived', listFacts?.directoryEntries === 23);
test('file count is deterministically derived', listFacts?.fileEntries === 96);
test('truncation flag is preserved', listFacts?.truncated === false);

const mismatched = factContext.facts({
  name: 'list_directory',
  result: { ok: true, detail: 'returned_entries: 10\n[DIR] one\n[FILE] two' },
}).verifiedFacts;
test('mismatched category counts are not published',
  mismatched?.returnedEntries === 10
    && mismatched.directoryEntries === undefined
    && mismatched.fileEntries === undefined);
test('failed list has no verified facts',
  Object.keys(factContext.facts({ name: 'list_directory', result: { ok: false, detail: directoryLines } })).length === 0);
test('unrelated tools have no list statistics',
  Object.keys(factContext.facts({ name: 'read_files', result: { ok: true, detail: directoryLines } })).length === 0);
test('contradictory directory count is rejected',
  typeof factContext.claimMismatch('目录一共有 20 个。', [listResult]) === 'string');
test('contradictory generic item count is rejected',
  typeof factContext.claimMismatch('实际 24 项。', [listResult]) === 'string');
test('verified directory count is accepted',
  factContext.claimMismatch('目录 23 个，文件 96 个，共计 119 个条目。', [listResult]) === null);
test('unrelated tool-call count is ignored',
  factContext.claimMismatch('实际调用了 2 个工具，总计调用了 2 个工具。', [listResult]) === null);

test('prompt forbids invented totals', src.includes('[Fix 3.3.10.9 verified statistics] Never invent, estimate, or mentally count'));
const fullResult = between('function Iz(e)', 'function Lz(e)');
const windowedResult = between('function Lz(e)', 'function Rz(e)');
test('full tool context includes verified facts', fullResult.includes('DPP_VERIFIED_FACTS_33109(e)'));
test('windowed tool context retains verified facts', windowedResult.includes('DPP_VERIFIED_FACTS_33109(e)'));
test('agent completion path invokes statistics gate',
  src.includes('let DPPStatMismatch331023=DPP_STAT_CLAIM_MISMATCH_33109(n,g);if(DPPStatMismatch331023)'));

const traceHelpers = between('var DPP_TRACE_EXPIRY_33109', 'DPP_INIT_AGENT_LIFECYCLE_CHANNEL_33109();async function M0');
const traceContext = { Date, Number, Array, Set, Promise, Math, setTimeout, clearTimeout };
vm.createContext(traceContext);
vm.runInContext(
  `${traceHelpers};Object.assign(globalThis,{expired:DPP_TRACE_EXPIRED_33109,needsRepair:DPP_TRACE_NEEDS_REPAIR_33109});`,
  traceContext,
);
const now = Date.now();
test('five-minute-old trace is expired', traceContext.expired({ updatedAt: now - 300001 }, now) === true);
test('fresh trace is not expired', traceContext.expired({ updatedAt: now - 299999 }, now) === false);
test('invalid timestamp fails closed', traceContext.expired({ updatedAt: 0 }, now) === false);
test('terminal streaming step requires repair',
  traceContext.needsRepair({ status: 'error', steps: [{ status: 'streaming' }] }) === true);
test('running trace is not treated as terminal repair',
  traceContext.needsRepair({ status: 'running', steps: [{ status: 'streaming' }] }) === false);

const cleanupSource = between('async function M0(e,t)', 'function N0(e)');
const cleanupContext = {
  Set,
  Date,
  currentUrl: 'https://chat.deepseek.com/a',
  traces: [],
  active: new Set(),
  writes: [],
  KY: new Map(),
  qY: new Set(),
};
cleanupContext.g0 = () => cleanupContext.currentUrl;
cleanupContext.k0 = async () => cleanupContext.traces;
cleanupContext.DPP_ACTIVE_TRACE_IDS_33109 = async () => cleanupContext.active;
cleanupContext.XX = () => true;
cleanupContext.P0 = (trace, url) => trace.url === url;
cleanupContext.DPP_TRACE_EXPIRED_33109 = (trace) => trace.expired === true;
cleanupContext.DPP_TRACE_NEEDS_REPAIR_33109 = (trace) => trace.repair === true;
cleanupContext.N0 = (trace) => ({ ...trace, status: trace.status === 'running' ? 'stopping' : trace.status, normalized: true });
cleanupContext.O0 = async (trace) => { cleanupContext.writes.push(trace); };
cleanupContext.U2 = () => {};
vm.createContext(cleanupContext);
vm.runInContext(`${cleanupSource};globalThis.cleanup=M0;`, cleanupContext);

(async () => {
  cleanupContext.traces = [
    { id: 'live-foreign', url: 'https://chat.deepseek.com/b', status: 'running', expired: true },
    { id: 'stale-foreign', url: 'https://chat.deepseek.com/c', status: 'running', expired: true },
    { id: 'fresh-foreign', url: 'https://chat.deepseek.com/d', status: 'running', expired: false },
    { id: 'current-stale', url: cleanupContext.currentUrl, status: 'running', expired: false },
    { id: 'terminal-broken', url: 'https://chat.deepseek.com/e', status: 'error', repair: true },
  ];
  cleanupContext.active = new Set(['live-foreign']);
  await cleanupContext.cleanup('generation', 'chat');
  const writeIds = cleanupContext.writes.map((trace) => trace.id);
  test('active foreign trace survives global sweep', !writeIds.includes('live-foreign'));
  test('expired unclaimed foreign trace is stopped', writeIds.includes('stale-foreign'));
  test('fresh foreign trace survives global sweep', !writeIds.includes('fresh-foreign'));
  test('unclaimed current trace is stopped immediately', writeIds.includes('current-stale'));
  test('terminal trace with streaming step is repaired', writeIds.includes('terminal-broken'));

  cleanupContext.writes = [];
  cleanupContext.traces = [
    { id: 'current-probe-failed', url: cleanupContext.currentUrl, status: 'running', expired: true },
  ];
  cleanupContext.active = null;
  await cleanupContext.cleanup('generation', 'chat');
  test('probe failure leaves every running trace untouched', cleanupContext.writes.length === 0);

  test('cleanup requires a successful active-set probe for foreign sweep',
    cleanupSource.includes('e.status===`running`&&i instanceof Set&&!s'));
  test('lifecycle probe uses two announcements',
    traceHelpers.includes('Math.floor(e/3)'));
  test('probe failure returns null',
    traceHelpers.includes('t.removeEventListener(`message`,a),n(null)'));

  const normalizerSource = between('function N0(e)', 'function P0(e,t)');
  test('restored streaming steps always become error',
    normalizerSource.includes('status:e.status===`streaming`?`error`:e.status'));

  if (failed) {
    console.error(`FIX33109_FAIL pass=${passed} fail=${failed}`);
    process.exit(1);
  }
  console.log(`FIX33109_PASS ${passed}/${passed + failed}`);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
