'use strict';
// .38 upload-gate selftest (supersedes v9 for .38): actual extracted listener/gates/service from the candidate background.js.
// Adds: stale sender.url after same-document navigation is ACCEPTED and bound to the tab conversation; every other
// rejection (origin, frame, lifecycle, documentId, tab id, tab origin, navigation during upload) still rejects.
// Asserts (1) every rejection still rejects exactly as before, (2) a fixed reason enum is attached,
// (3) no URL/token/documentId/sender object leaks, (4) success path and other commands are unchanged.
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert/strict');
const {webcrypto} = require('crypto');
const root = process.argv[2], baselineRoot = process.argv[3];
if (!root || !baselineRoot) throw Error('Usage: node dspp-upload-gate-v10-selftest.js candidate-root baseline-36-root');
const bg = fs.readFileSync(path.join(root, 'background.js'), 'utf8');
const old = fs.readFileSync(path.join(baselineRoot, 'background.js'), 'utf8');
const content = fs.readFileSync(path.join(root, 'content-scripts/content.js'), 'utf8');
const ID = 'kdmpkkahkhdmdhfkdihkopikgcocbpbf', URL_A = 'https://chat.deepseek.com/a/chat/s/session-a', URL_B = 'https://chat.deepseek.com/a/chat/s/session-b';
const PNG = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=';
const payload = () => ({dataUrl: 'data:image/png;base64,' + PNG, mimeType: 'image/png', name: 'fixture.png', sizeBytes: Buffer.from(PNG, 'base64').length});
const sender = () => ({id: ID, url: URL_A, origin: 'https://chat.deepseek.com', frameId: 0, documentLifecycle: 'active', documentId: 'browser-doc-a', tab: {id: 7, url: URL_A}});
const SECRETS = ['browser-doc-a', 'session-a', 'session-b', 'PRIVATE', PNG, 'chat.deepseek.com', 'evil.example'];
function slice(s, a, b) { const i = s.indexOf(a), j = s.indexOf(b, i); assert(i >= 0 && j > i, 'extract ' + a); return s.slice(i, j); }
let groups = 0;
function harness(source = bg, behavior = {}) {
  const counts = {auth: 0, pow: 0, upload: 0, tabs: 0}, state = {tab: {id: 7, url: URL_A}}, storage = new Map();
  const box = {URL, Blob, Uint8Array, ArrayBuffer, DOMException, AbortController, atob, btoa, crypto: webcrypto, console,
    setTimeout, clearTimeout, Jk: 8388608, QL: 'https://chat.deepseek.com/',
    fR: {ensureReady: async () => {}}, Z: () => 'background failed',
    chrome: {tabs: {get: async () => { counts.tabs++; if (behavior.tabGone) throw Error('missing tab'); return state.tab; }},
      storage: {local: {get: async k => ({[k]: storage.get(k)}), set: async o => { for (const [k, v] of Object.entries(o)) storage.set(k, v); }}},
      runtime: {id: ID, getURL: p => 'chrome-extension://' + ID + (p.startsWith('/') ? p : '/' + p), lastError: null}},
    network: {
      getChatEnabled: async () => behavior.chatEnabled === true,
      reconcileInterruptedChatLoop: async () => false,
      loadClientHeaders: async () => { counts.auth++; if (behavior.navigateAfterAuth) state.tab.url = URL_B; return {Authorization: 'Bearer PRIVATE-FIXTURE-TOKEN'}; },
      createUploadPowHeaders: async () => { counts.pow++; return {'X-DS-PoW-Response': 'PRIVATE-POW'}; },
      uploadFile: async () => { counts.upload++; if (behavior.navigateAfterUpload) state.tab.url = URL_B; return {id: 'fixture-file-id', mimeType: 'image/png'}; },
      missingAuthMessage: () => 'PRIVATE-LOCALIZED-AUTH-MESSAGE', interruptedMessage: () => 'interrupted', broadcastChunk: () => {}
    }};
  vm.createContext(box);
  const policy = slice(source, 'function gN(', 'function zN(');
  const decoder = slice(source, 'function bP(', 'var TP=');
  const service = slice(source, 'function zF(', 'function BF(');
  const guards = slice(source, 'function VF(', 'function UF(');
  const factory = slice(source, 'function UF(', 'function WF(');
  const typed = slice(source, 'function GN(', 'function H(') + slice(source, 'function H(', 'function KN(') + slice(source, 'function _F(', 'function J(');
  const tabs = slice(source, 'async function aI(', 'async function oI(');
  const listener = slice(source, 'chrome.runtime.onMessage.addListener(', '),chrome.storage.onChanged.addListener').slice('chrome.runtime.onMessage.addListener('.length);
  vm.runInContext(policy + decoder + service + guards + typed + tabs +
    'function yP(type, raw){ if(type === "UPLOAD_DEEPSEEK_IMAGE") return xP(raw); throw Error("Unexpected test command"); }' +
    factory + '\nvar service = zF(network); var registry = new Map(UF({service}).map(h=>[h.type,h]));\n' +
    'async function MR(message, ctx){return registry.get(message.type).handle(message,ctx)}\nvar listener=' + listener + ';', box);
  async function dispatch(message, from = sender()) {
    box.inputJSON = JSON.stringify(message); box.senderJSON = JSON.stringify(from);
    const m = vm.runInContext('JSON.parse(inputJSON)', box), s = vm.runInContext('JSON.parse(senderJSON)', box);
    return await new Promise(resolve => box.listener(m, s, resolve));
  }
  return {box, counts, state, storage, dispatch};
}
async function test(name, fn) { await fn(); groups++; console.log('PASS ' + name); }
function denied(result, reason) {
  assert.equal(result.ok, false); assert.equal(result.error, 'runtime_message_unauthorized');
  assert.equal(result.reason, reason, 'reason enum'); assert.match(result.reason, /^[a-z_]{1,48}$/);
  const text = JSON.stringify(result);
  for (const secret of SECRETS) assert(!text.includes(secret), 'leak: ' + secret);
  assert(!('senderUrl' in result) && !('sender' in result) && !('context' in result) && !('documentId' in result));
  if (result.probe) for (const v of Object.values(result.probe)) assert(typeof v === 'boolean' || /^[a-z_]{1,24}$/.test(v));
}
async function noUploadSideEffects(h) { await new Promise(r => setTimeout(r, 5)); assert.equal(h.counts.auth + h.counts.pow + h.counts.upload, 0); }
(async () => {
  const CASES = [
    ['other extension id', {...sender(), id: 'other-extension'}, 'sender_not_this_extension'],
    ['native sender', {...sender(), nativeApplication: 'host'}, 'sender_not_this_extension'],
    ['cached lifecycle at wN', {...sender(), documentLifecycle: 'cached'}, 'sender_lifecycle_not_active'],
    ['prerender lifecycle at wN', {...sender(), documentLifecycle: 'prerender'}, 'sender_lifecycle_not_active'],
    ['missing sender url', {...sender(), url: undefined}, 'sender_url_missing'],
    ['invalid sender url', {...sender(), url: 'not a url'}, 'sender_url_invalid'],
    ['origin mismatch', {...sender(), origin: 'https://evil.example'}, 'sender_origin_mismatch'],
    ['external origin', {...sender(), url: 'https://evil.example/', origin: 'https://evil.example'}, 'sender_not_top_frame'],
    ['iframe', {...sender(), frameId: 1}, 'sender_not_top_frame'],
    ['tab not deepseek', {...sender(), tab: {id: 7, url: 'https://evil.example/'}}, 'sender_tab_not_deepseek'],
    ['no frame evidence', {...sender(), frameId: undefined, tab: {id: 7}}, 'sender_no_frame_evidence'],
    ['invalid document id type', {...sender(), documentId: 5}, 'sender_field_invalid'],
    ['lifecycle undefined -> context gate', {...sender(), documentLifecycle: undefined}, 'ctx_lifecycle_none'],
    ['document id undefined -> context gate', {...sender(), documentId: undefined}, 'ctx_document_id_missing'],
    ['no conversation in either url', {...sender(), url: 'https://chat.deepseek.com/', tab: {id: 7, url: 'https://chat.deepseek.com/'}}, 'ctx_tab_session_missing'],
    ['tab has conversation, sender url is the bare origin (new-chat document later navigated)', {...sender(), url: 'https://chat.deepseek.com/'}, null],
    ['stale sender.url after same-document navigation (field case 2026-09-17 14:54:59)', {...sender(), url: URL_B}, null],
    ['stale sender.url but external origin still rejected', {...sender(), url: 'https://evil.example/a/chat/s/session-a', origin: 'https://evil.example'}, 'sender_not_top_frame'],
    ['stale sender.url in iframe still rejected', {...sender(), url: URL_B, frameId: 1}, 'sender_not_top_frame'],
    ['stale sender.url with cached lifecycle still rejected', {...sender(), url: URL_B, documentLifecycle: 'cached'}, 'sender_lifecycle_not_active'],
    ['stale sender.url without documentId still rejected', {...sender(), url: URL_B, documentId: undefined}, 'ctx_document_id_missing'],
    ['frame undefined with deepseek tab url passes wN, still top-level', {...sender(), frameId: undefined}, null]
  ];
  await test('every synchronous rejection keeps its verdict and gains a distinct fixed reason', async () => {
    for (const [name, from, reason] of CASES) {
      const h = harness(), r = await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}, from);
      if (reason === null) { assert.equal(r.ok, true, name); assert.equal(r.reason, undefined); assert.equal(h.counts.upload, 1, name); continue; }
      denied(r, reason); await noUploadSideEffects(h);
      const o = harness(old), ro = await o.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}, from);
      assert.equal(ro.ok, false, 'baseline also denies: ' + name); assert.equal(ro.error, 'runtime_message_unauthorized'); assert.equal(ro.reason, undefined);
    }
  });
  await test('asynchronous tab rejections (aI/TN) carry reasons', async () => {
    let h = harness(bg, {tabGone: true}); denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}), 'tabs_get_failed'); await noUploadSideEffects(h);
    h = harness(); h.state.tab = {id: 8, url: URL_A}; denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}), 'tab_id_mismatch'); await noUploadSideEffects(h);
    h = harness(); h.state.tab = {id: 7, url: 'https://evil.example/'}; denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}), 'tab_not_deepseek'); await noUploadSideEffects(h);
    h = harness(); h.state.tab = {id: 7}; denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}), 'tab_url_missing'); await noUploadSideEffects(h);
    // .38: sender.url stale (A) while browser tab is on B: accepted, bound to the browser-owned tab conversation, uploaded once.
    h = harness(); h.state.tab = {id: 7, url: URL_B}; let ok = await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}, {...sender(), tab: {id: 7, url: URL_B}}); assert.equal(ok.ok, true); assert.equal(h.counts.upload, 1); assert(h.counts.tabs >= 3, 'tabs.get in TN, before and after upload');
    // listener saw tab conversation A but chrome.tabs.get already shows B (navigation in flight): still rejected before auth/PoW/upload.
    h = harness(); h.state.tab = {id: 7, url: URL_B}; denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}), 'conversation_changed'); await noUploadSideEffects(h);
    // tab navigated to a non-conversation page: still rejected (tab conversation missing).
    h = harness(); h.state.tab = {id: 7, url: 'https://chat.deepseek.com/'}; denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}), 'ctx_tab_session_missing'); await noUploadSideEffects(h);
  });
  await test('dispatch-level navigation rejections carry reasons and still block/deny', async () => {
    let h = harness(bg, {navigateAfterAuth: true}); denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}), 'conversation_changed'); assert.equal(h.counts.pow, 0);
    h = harness(bg, {navigateAfterUpload: true}); const r = await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}); denied(r, 'conversation_changed'); assert(!r.file);
  });
  await test('probe reports booleans matching the field-observed shape', async () => {
    const h = harness(), r = await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}, {...sender(), documentLifecycle: 'prerender'});
    assert.deepEqual(JSON.parse(JSON.stringify(r.probe)), {frame: 'zero', lifecycle: 'prerender', documentId: true, tab: true, tabUrl: true, senderSession: true, tabSession: true, sameSession: true});
    const r2 = await harness().dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}, {...sender(), url: URL_B, frameId: 1});
    assert.equal(r2.probe.sameSession, false); assert.equal(r2.probe.frame, 'other'); assert.equal(r2.probe.tabSession, true);
  });
  await test('bounded ring buffer in chrome.storage.local, no secrets, at most 32 rows', async () => {
    const h = harness();
    for (let i = 0; i < 40; i++) await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}, {...sender(), frameId: 1});
    await new Promise(r => setTimeout(r, 10));
    const rows = h.storage.get('dpp_upload_gate_diag_v9'); assert(Array.isArray(rows)); assert.equal(rows.length, 32);
    const text = JSON.stringify(rows); for (const secret of SECRETS) assert(!text.includes(secret));
    assert.equal(rows[0].reason, 'sender_not_top_frame'); assert.equal(rows[0].version, 9); assert.equal(typeof rows[0].time, 'number');
  });
  await test('diagnostics never fire for other commands or non-boundary failures', async () => {
    const h = harness();
    for (const type of ['CHAT_NEW_SESSION', 'GET_CONFIG', 'UNKNOWN_COMMAND']) { const r = await h.dispatch({type, payload: {}}); assert.equal(r.error, 'runtime_message_unauthorized'); assert.equal(r.reason, undefined); }
    const bad = await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: {...payload(), sizeBytes: 0}}); assert.equal(bad.code, 'invalid_image'); assert.equal(bad.reason, undefined);
    await new Promise(r => setTimeout(r, 5)); assert.equal(h.storage.get('dpp_upload_gate_diag_v9'), undefined);
  });
  await test('success path unchanged: no reason/probe on ok responses', async () => {
    const h = harness(), r = await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()});
    assert.equal(r.ok, true); assert.equal(r.file.id, 'fixture-file-id'); assert.equal(r.reason, undefined); assert.equal(r.probe, undefined);
    assert.equal(h.counts.upload, 1);
  });
  await test('gate source: wN/TN/EN/aI/ASSERT/DISPATCH identical to .36 except diag wrapping; REQUIRE changed exactly as specified', async () => {
    const req = slice(bg, 'function DPP_REQUIRE_UPLOAD_CONTEXT_V7(', 'async function DPP_ASSERT_CURRENT_UPLOAD_V7(').replace(/\r\n/g, '\n');
    assert(!req.includes('vN(context.senderUrl)'), 'stale sender.url conversation comparison removed');
    for (const must of ["context.frameId !== 0", "context.documentLifecycle !== 'active'", "typeof context.documentId !== 'string' || !context.documentId", "typeof context.chatSessionId !== 'string' || !context.chatSessionId", "typeof context.senderUrl !== 'string' || !context.senderUrl", "typeof context.tabUrl !== 'string' || !context.tabUrl", "context.dppListenerChatSessionId !== context.chatSessionId"]) assert(req.includes(must), 'REQUIRE keeps: ' + must);
    for (const [a, b] of [['function wN(', 'function TN('], ['function TN(', 'function EN('], ['function EN(', 'function DN('], ['async function aI(', 'async function oI('],
      ['async function DPP_ASSERT_CURRENT_UPLOAD_V7(', 'async function DPP_DISPATCH_UPLOAD_V7(']]) {
      assert.equal(slice(bg, a, b).replace(/\r\n/g, '\n'), slice(old, a, b).replace(/\r\n/g, '\n'), 'unchanged ' + a);
    }
    const oldAllow = slice(old, 'xN=new Set(`', '`.split'), newAllow = slice(bg, 'xN=new Set(`', '`.split'); assert.equal(oldAllow, newAllow);
    assert.equal((bg.match(/DPP_GATE_DIAG_V9\(/g) || []).length, 4); // 1 definition + 3 call sites
  });
  await test('content diag: gate_reason row with whitelisted fields, blocker note, no retry loop', async () => {
    for (const [from, reason] of [[{...sender(), documentLifecycle: 'prerender'}, 'sender_lifecycle_not_active'], [{...sender(), url: URL_B, frameId: 1}, 'sender_not_top_frame']]) {
      const h = harness(), store = new Map();
      const box = {URL, Blob, Uint8Array, DOMException, AbortController, atob, btoa, crypto: webcrypto, console, setTimeout, clearTimeout,
        localStorage: {getItem: k => store.get(k), setItem: (k, v) => store.set(k, v)},
        chrome: {runtime: {lastError: null, sendMessage: (m, cb) => { h.dispatch(m, from).then(cb); }}}};
      vm.createContext(box); vm.runInContext(slice(content, '/* DPP_READIMAGE_V7_BEGIN', '/* DPP_READIMAGE_V7_END */'), box);
      const state = box.DPP_CREATE_READIMAGE_V7({backend: 'web', signal: new AbortController().signal, chatSessionId: 'session-a'});
      await state.capture({name: 'read_image', result: {ok: true, output: {structuredContent: {data_uri: payload().dataUrl}}}});
      let request; await state.wrapSubmit(async r => { request = r; return {finished: true}; })({chatSessionId: 'session-a', prompt: 'describe', refFileIds: []}, {}, new AbortController().signal);
      assert.equal(request.refFileIds.length, 0);
      const rows = JSON.parse(store.get('dpp_read_image_diag_v7'));
      const gate = rows.find(r => r.stage === 'gate_reason'); assert(gate, 'gate_reason row'); assert.equal(gate.reason, reason);
      assert.equal(typeof gate.lifecycle, 'string'); assert.equal(typeof gate.sameSession, 'boolean');
      assert(rows.some(r => r.stage === 'runtime_message_unauthorized'));
      assert.equal(rows.filter(r => r.stage === 'upload_start').length, 1, 'exactly one attempt per image');
      const text = JSON.stringify(rows) + String(request.prompt); for (const secret of SECRETS) assert(!text.includes(secret), 'leak ' + secret);
      assert(String(request.prompt).includes('upload authorization rejected (' + reason + ')'));
    }
  });
  await test('content diag: unexpected reason shapes are sanitized to unknown', async () => {
    const store = new Map();
    const box = {URL, Blob, Uint8Array, DOMException, AbortController, atob, btoa, crypto: webcrypto, console, setTimeout, clearTimeout,
      localStorage: {getItem: k => store.get(k), setItem: (k, v) => store.set(k, v)},
      chrome: {runtime: {lastError: null, sendMessage: (m, cb) => cb({ok: false, error: 'runtime_message_unauthorized', reason: 'https://evil.example/' + 'x'.repeat(80), probe: {lifecycle: 'https://evil.example', documentId: 'yes', extra: true}})}}};
    vm.createContext(box); vm.runInContext(slice(content, '/* DPP_READIMAGE_V7_BEGIN', '/* DPP_READIMAGE_V7_END */'), box);
    const state = box.DPP_CREATE_READIMAGE_V7({backend: 'web', signal: new AbortController().signal, chatSessionId: 'session-a'});
    await state.capture({name: 'read_image', result: {ok: true, output: {structuredContent: {data_uri: payload().dataUrl}}}});
    const gate = JSON.parse(store.get('dpp_read_image_diag_v7')).find(r => r.stage === 'gate_reason');
    assert.equal(gate.reason, 'unknown'); assert.equal(gate.lifecycle, undefined); assert.equal(gate.documentId, undefined); assert.equal(gate.extra, undefined);
    assert(!JSON.stringify(gate).includes('evil'));
  });
  console.log(`RESULT ${groups}/${groups} .38 upload-gate groups passed; actual extracted code, offline dependencies only.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
