'use strict';
// .39 MAIN-world bridge diagnostics selftest: helper behaviour (bounded, sanitized, dedupe) and patch-site presence.
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert/strict');
const root = process.argv[2], baselineRoot = process.argv[3];
if (!root || !baselineRoot) throw Error('Usage: node dspp-mw-bridge-diag-v10-selftest.js candidate-root baseline-36-root');
const mw = fs.readFileSync(path.join(root, 'content-scripts/main-world.js'), 'utf8');
const old = fs.readFileSync(path.join(baselineRoot, 'content-scripts/main-world.js'), 'utf8');
function slice(s, a, b) { const i = s.indexOf(a), j = s.indexOf(b, i); assert(i >= 0 && j > i, 'extract ' + a); return s.slice(i, j + b.length); }
let groups = 0; async function test(n, f) { await f(); groups++; console.log('PASS ' + n); }
(async () => {
  await test('helper present once, baseline untouched elsewhere', () => {
    assert.equal((mw.match(/DPP_MW_BRIDGE_DIAG_V10_BEGIN/g) || []).length, 1);
    assert.equal((old.match(/DPP_MW_DIAG_V10/g) || []).length, 0);
    const helper = slice(mw, '/* DPP_MW_BRIDGE_DIAG_V10_BEGIN', '/* DPP_MW_BRIDGE_DIAG_V10_END */');
    const stripped = mw.replace(helper + (mw[mw.indexOf(helper) + helper.length] === '\r' ? '\r\n' : '\n'), '');
    const calls = (stripped.match(/DPP_MW_DIAG_V10\(`/g) || []).length;
    assert.equal(calls, 10, 'exactly ten instrumentation sites');
    for (const stage of ['send_hook', 'fetch_route', 'augment', 'post_drop', 'bridge_open', 'bridge_close', 'navigate', 'sync_state', 'lifecycle_error', 'main_crash']) assert(stripped.includes('DPP_MW_DIAG_V10(`' + stage + '`'), stage);
    // no gate / bridge logic changed: reverse-applying the builder's exact patch list must give back the .36 text
    const py = fs.readFileSync(path.join(path.dirname(process.argv[1]), 'apply-fix331039.py'), 'utf8');
    const block = py.slice(py.indexOf('MW_PATCHES = ['), py.indexOf('\n]\n', py.indexOf('MW_PATCHES = [')));
    const pairs = [...block.matchAll(/\(\'((?:[^'\\]|\\.)*)\',\n?\s*\'((?:[^'\\]|\\.)*)\'\)/g)].map(m => [m[1], m[2]].map(x => x.replace(/\\\\/g, '\\').replace(/\\'/g, "'")));
    assert.equal(pairs.length, 10);
    let back = stripped.replace(/\r\n/g, '\n');
    for (const [o, n] of pairs) { assert.equal(back.split(n).length, 2, 'patched once: ' + o.slice(0, 40)); back = back.replace(n, o); }
    assert.equal(back, old.replace(/\r\n/g, '\n'), 'only diagnostic calls were inserted');
  });
  await test('helper: sanitized, bounded to 64, dedupes bursts, never stores URLs/ids', () => {
    const store = new Map();
    const box = {localStorage: {getItem: k => store.has(k) ? store.get(k) : null, setItem: (k, v) => store.set(k, v)}, location: {pathname: '/a/chat/s/abc'}, document: {body: null}, Date, JSON, Math, Number, Array, Object, Set, RegExp};
    vm.createContext(box); vm.runInContext(slice(mw, '/* DPP_MW_BRIDGE_DIAG_V10_BEGIN', '/* DPP_MW_BRIDGE_DIAG_V10_END */'), box);
    let rows = JSON.parse(store.get('dpp_mw_bridge_diag_v10')); assert.equal(rows[0].stage, 'boot'); assert.equal(rows[0].session, true); assert.equal(rows[0].body, false);
    vm.runInContext('DPP_MW_DIAG_V10("send_hook",{route:"completion",session:true,tools:3,url:"https://evil.example/x",id:"abc-123",chatSessionId:"f41cba92"})', box);
    rows = JSON.parse(store.get('dpp_mw_bridge_diag_v10')); const r = rows[rows.length - 1];
    assert.deepEqual(Object.keys(r).sort(), ['route', 'session', 'stage', 'time', 'tools', 'version']);
    assert(!store.get('dpp_mw_bridge_diag_v10').includes('evil') && !store.get('dpp_mw_bridge_diag_v10').includes('f41cba92'));
    vm.runInContext('DPP_MW_DIAG_V10("not_a_stage",{a:true})', box); assert.equal(JSON.parse(store.get('dpp_mw_bridge_diag_v10')).length, rows.length);
    for (let i = 0; i < 30; i++) vm.runInContext('DPP_MW_DIAG_V10("post_drop",{active:true,bridge:false,kind:"RESPONSE_TOKEN_SPEED"})', box);
    rows = JSON.parse(store.get('dpp_mw_bridge_diag_v10')); assert.equal(rows[rows.length - 1].n, 30); assert.equal(rows.length, 3);
    for (let i = 0; i < 100; i++) vm.runInContext('DPP_MW_DIAG_V10("sync_state",{tools:' + i + '})', box);
    rows = JSON.parse(store.get('dpp_mw_bridge_diag_v10')); assert.equal(rows.length, 64); assert.equal(rows[63].tools, 99);
  });
  console.log(`RESULT ${groups}/${groups} .39 main-world diagnostics groups passed.`);
})().catch(e => { console.error(e); process.exitCode = 1; });
