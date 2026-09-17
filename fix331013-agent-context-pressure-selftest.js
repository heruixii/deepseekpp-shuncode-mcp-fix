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

const helperSource = between('function DPP_AGENT_RESULT_DELTA_331013', 'async function Jz(e)');
const context = { Number };
vm.createContext(context);
vm.runInContext(`${helperSource};globalThis.delta=DPP_AGENT_RESULT_DELTA_331013;`, context);

const a = { id: 'a', payload: 'A'.repeat(4096) };
const b = { id: 'b', payload: 'B'.repeat(4096) };
const c = { id: 'c', payload: 'C'.repeat(4096) };
const d = { id: 'd', payload: 'D'.repeat(4096) };
let ledger = [a, b];
let cursor = 0;
let next = context.delta(ledger, cursor);

test('version bumped for context-pressure fix', ['1.14.0.18','1.14.0.19','1.14.0.20','1.14.0.21','1.14.0.22','1.14.0.23','1.14.0.24','1.14.0.25','1.14.0.26','1.14.0.27','1.14.0.28','1.14.0.29','1.14.0.30','1.14.0.31','1.14.0.32','1.14.0.33','1.14.0.34','1.14.0.35','1.14.0.36','1.14.0.37','1.14.0.38','1.14.0.41'].includes(manifest.version));
test('version name bumped for context-pressure fix', ['1.14.0 ShunCode MCP Fix 3.3.10.13','1.14.0 ShunCode MCP Fix 3.3.10.14','1.14.0 ShunCode MCP Fix 3.3.10.15','1.14.0 ShunCode MCP Fix 3.3.10.16','1.14.0 ShunCode MCP Fix 3.3.10.17','1.14.0 ShunCode MCP Fix 3.3.10.18','1.14.0 ShunCode MCP Fix 3.3.10.19','1.14.0 ShunCode MCP Fix 3.3.10.20','1.14.0 ShunCode MCP Fix 3.3.10.21','1.14.0 ShunCode MCP Fix 3.3.10.22','1.14.0 ShunCode MCP Fix 3.3.10.23','1.14.0 ShunCode MCP Fix 3.3.10.24','1.14.0 ShunCode MCP Fix 3.3.10.25','1.14.0 ShunCode MCP Fix 3.3.10.26','1.14.0 ShunCode MCP Fix 3.3.10.27','1.14.0 ShunCode MCP Fix 3.3.10.28','1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30','1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32','1.14.0 ShunCode MCP Fix 3.3.10.33','1.14.0 ShunCode MCP Fix 3.3.10.36'].includes(manifest.version_name));
test('first web continuation receives current-turn results', next.results.length === 2 && next.results[0].id === 'a' && next.results[1].id === 'b');
test('first cursor advances to ledger end', next.cursor === 2);
cursor = next.cursor;
ledger.push(c, d);
next = context.delta(ledger, cursor);
test('second continuation receives only newly settled results', next.results.length === 2 && next.results[0].id === 'c' && next.results[1].id === 'd');
test('second cursor advances to new ledger end', next.cursor === 4);
cursor = next.cursor;
next = context.delta(ledger, cursor);
test('continuation without new tools resends no old result', next.results.length === 0 && next.cursor === 4);
test('oversized cursor fails closed to empty delta', context.delta(ledger, 99).results.length === 0);
test('invalid cursor safely restarts from available ledger', context.delta(ledger, -1).results.length === ledger.length);

let synthetic = [];
let deltaCursor = 0;
let cumulativeBytes = 0;
let deltaBytes = 0;
for (let i = 0; i < 12; i += 1) {
  synthetic.push({ id: i, detail: 'x'.repeat(5000) });
  cumulativeBytes += Buffer.byteLength(JSON.stringify(synthetic));
  const step = context.delta(synthetic, deltaCursor);
  deltaCursor = step.cursor;
  deltaBytes += Buffer.byteLength(JSON.stringify(step.results));
}
const reduction = 1 - deltaBytes / cumulativeBytes;
test('synthetic 12-turn resend amplification falls by over 80%', reduction > 0.8, `reduction=${(reduction * 100).toFixed(1)}%`);

const agent = between('async function Jz(e)', 'function Yz(e)');
const serializerStart = agent.indexOf('serializePrompt:');
const serializerEnd = agent.indexOf(',mapToolCall:', serializerStart);
const serializer = agent.slice(serializerStart, serializerEnd);
test('web serializer consumes delta cursor', serializer.includes('DPPNextResults331013()'));
test('web serializer sends delta to normal continuation', serializer.includes('Nz(t.originalPrompt,e,d)'));
test('web serializer sends delta to nudge continuation', serializer.includes('Pz(t.originalPrompt,y.lastAssistantText,e,y.count,d)'));
test('old cumulative normal serializer removed', !serializer.includes('Nz(t.originalPrompt,g,d)'));
test('old cumulative nudge serializer removed', !serializer.includes('Pz(t.originalPrompt,y.lastAssistantText,g,y.count,d)'));
test('full execution ledger still accumulates settled tools', agent.includes('g.push(..._)'));
test('completion gate still sees the full execution ledger', agent.includes('DPP_COMPLETION_GATE_31(g)'));
test('verified-statistics gate still sees the full execution ledger', agent.includes('DPP_STAT_CLAIM_MISMATCH_33109(n,g)'));
test('task-progress classifier still sees the full execution ledger', agent.includes('Az(t.originalPrompt,g,Gz(n))'));

if (failed) {
  console.error(`FIX331013_FAIL pass=${passed} fail=${failed}`);
  process.exit(1);
}
console.log(`FIX331013_PASS ${passed}/${passed + failed}`);
