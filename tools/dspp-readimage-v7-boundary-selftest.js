'use strict';
// Actual extracted listener, sender gates, decoder, typed handler and zF upload service.
// Browser APIs / external HTTP dependencies alone are simulated; never performs a real upload.
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert/strict');
const {webcrypto} = require('crypto');
const root = process.argv[2], baseline = process.argv[3];
if (!root) throw Error('Usage: node boundary-selftest.js candidate-root [frozen-v6-root]');
const bg = fs.readFileSync(path.join(root, 'background.js'), 'utf8');
// Frozen .34 background is byte-identical to v6; fixture is this extension, NOT ShunCode runtime.
const old = fs.readFileSync(baseline ? path.join(baseline, 'background.js') : path.join(__dirname, 'fixtures/readimage-v6-background.txt'), 'utf8');
assert.equal(require('crypto').createHash('sha256').update(old).digest('hex'), 'ed5751c7dfa819e51bb8df24beea990c505db7eb6f7c3654fa58217177844f32', 'exact historical background required');
const content = fs.readFileSync(path.join(root, 'content-scripts/content.js'), 'utf8');
const ID = 'kdmpkkahkhdmdhfkdihkopikgcocbpbf', URL_A = 'https://chat.deepseek.com/a/chat/s/session-a';
const PNG = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=';
const payload = () => ({dataUrl: 'data:image/png;base64,' + PNG, mimeType: 'image/png', name: 'fixture.png', sizeBytes: Buffer.from(PNG, 'base64').length});
const sender = () => ({id: ID, url: URL_A, origin: 'https://chat.deepseek.com', frameId: 0, documentLifecycle: 'active', documentId: 'browser-doc-a', tab: {id: 7, url: URL_A}});
function slice(s, a, b) { const i = s.indexOf(a), j = s.indexOf(b, i); assert(i >= 0 && j > i, 'extract ' + a); return s.slice(i, j); }
let groups = 0;
function harness(source = bg, behavior = {}) {
  const counts = {auth: 0, pow: 0, upload: 0, tabs: 0}, state = {tab: {id: 7, url: URL_A}};
  const box = {URL, Blob, Uint8Array, ArrayBuffer, DOMException, AbortController, atob, btoa, crypto: webcrypto, console,
    setTimeout, clearTimeout, Jk: 8388608, QL: 'https://chat.deepseek.com/',
    fR: {ensureReady: async () => {}}, Z: () => 'background failed',
    chrome: {tabs: {get: async () => { counts.tabs++; if (behavior.tabGone) throw Error('missing tab'); return state.tab; }}, runtime: {id: ID, getURL: p => 'chrome-extension://' + ID + (p.startsWith('/') ? p : '/' + p), lastError: null}},
    network: {
      getChatEnabled: async () => behavior.chatEnabled === true,
      reconcileInterruptedChatLoop: async () => false,
      loadClientHeaders: async () => { counts.auth++; if (behavior.authThrow) throw Error('PRIVATE-AUTH-DETAIL'); if (behavior.navigateAfterAuth) state.tab.url = 'https://chat.deepseek.com/a/chat/s/other'; return behavior.noAuth ? null : {Authorization: 'Bearer PRIVATE-FIXTURE-TOKEN'}; },
      createUploadPowHeaders: async () => { counts.pow++; if (behavior.powError) { const e = new Error('PRIVATE-POW-DETAIL'); e.name = behavior.powError; throw e; } if (behavior.navigateAfterPow) state.tab.url = 'https://chat.deepseek.com/a/chat/s/other'; return {'X-DS-PoW-Response': 'PRIVATE-POW'}; },
      uploadFile: async arg => { counts.upload++; assert.equal(arg.file.size, Buffer.from(PNG, 'base64').length); assert.equal(arg.file.type, 'image/png'); if (behavior.uploadError) { const e = new Error('PRIVATE-UPLOAD-DETAIL'); e.name = behavior.uploadError; throw e; } if (behavior.navigateAfterUpload) state.tab.url = 'https://chat.deepseek.com/a/chat/s/other'; return {id: 'fixture-file-id', mimeType: 'image/png'}; },
      missingAuthMessage: () => 'PRIVATE-LOCALIZED-AUTH-MESSAGE', interruptedMessage: () => 'interrupted', broadcastChunk: () => {}
    }};
  vm.createContext(box);
  const policy = slice(source, 'function gN(', 'function zN(');
  const decoder = slice(source, 'function bP(', 'var TP=');
  const service = slice(source, 'function zF(', 'function BF(');
  const guards = slice(source, 'function VF(', 'function UF('); // includes v7 helpers in candidate
  const factory = slice(source, 'function UF(', 'function WF(');
  const typed = slice(source, 'function GN(', 'function H(') + slice(source, 'function H(', 'function KN(') + slice(source, 'function _F(', 'function J(');
  const tabs = slice(source, 'async function aI(', 'async function oI(');
  const listener = slice(source, 'chrome.runtime.onMessage.addListener(', '),chrome.storage.onChanged.addListener').slice('chrome.runtime.onMessage.addListener('.length);
  vm.runInContext(policy + decoder + service + guards + typed + tabs +
    'function yP(type, raw){ if(type === "UPLOAD_DEEPSEEK_IMAGE") return xP(raw); throw Error("Unexpected test command"); }' +
    factory + '\nvar service = zF(network); var registry = new Map(UF({service}).map(h=>[h.type,h]));\n' +
    'async function MR(message, ctx){return registry.get(message.type).handle(message,ctx)}\nvar listener=' + listener + ';', box);
  async function dispatch(message, from = sender()) {
    // Real decoder checks plain objects: construct sender and message in the background realm.
    box.inputJSON = JSON.stringify(message); box.senderJSON = JSON.stringify(from);
    const m = vm.runInContext('JSON.parse(inputJSON)', box), s = vm.runInContext('JSON.parse(senderJSON)', box);
    return await new Promise(resolve => box.listener(m, s, resolve));
  }
  return {box, counts, state, dispatch};
}
async function test(name, fn) { await fn(); groups++; console.log('PASS ' + name); }
function denied(result) { assert.equal(result.ok, false); assert.equal(result.error, 'runtime_message_unauthorized'); }
(async () => {
  await test('exact v6 listener reproduces content rejection before auth/PoW/upload', async () => {
    const h = harness(old); denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}));
    assert.equal(h.counts.auth + h.counts.pow + h.counts.upload, 0);
  });
  await test('new allowlist adds exactly one command, no global bypass', async () => {
    const get = s => slice(s, 'xN=new Set(`', '`.split(`.`))').slice('xN=new Set(`'.length).split('.');
    const before = new Set(get(old)), after = new Set(get(bg));
    assert.deepEqual([...after].filter(x => !before.has(x)), ['UPLOAD_DEEPSEEK_IMAGE']);
    assert.deepEqual([...before].filter(x => !after.has(x)), []);
  });
  await test('trusted main-page upload works with sidepanel disabled, using real zF/bP', async () => {
    const h = harness(); const r = await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()});
    assert.equal(r.ok, true); assert.equal(r.file.id, 'fixture-file-id');
    assert.equal(h.counts.auth, 1); assert.equal(h.counts.pow, 1); assert.equal(h.counts.upload, 1); assert(h.counts.tabs >= 5);
  });
  await test('sidepanel setting preserved: disabled rejects, enabled works', async () => {
    const from = {id: ID, url: 'chrome-extension://' + ID + '/sidepanel.html', origin: 'chrome-extension://' + ID};
    const off = harness(), on = harness(bg, {chatEnabled: true});
    assert.equal((await off.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}, from)).error, 'chat_disabled');
    assert.equal(off.counts.upload, 0);
    assert.equal((await on.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}, from)).ok, true);
  });
  await test('spoofed payload cannot enable sidepanel or supply trusted sender', async () => {
    const h = harness(); const from = {id: ID, url: 'chrome-extension://' + ID + '/sidepanel.html'};
    const p = {...payload(), content: true, surface: 'deepseek_content', DPPUploadV7: {content: true}, isPlainObject: true};
    assert.equal((await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: p}, from)).error, 'chat_disabled');
    assert.equal(h.counts.upload, 0);
  });
  await test('external origin, iframe, wrong extension, native sender and inactive documents denied', async () => {
    const variants = [
      {...sender(), url: 'https://evil.example/', origin: 'https://evil.example'},
      {...sender(), frameId: 1}, {...sender(), id: 'other-extension'}, {...sender(), nativeApplication: 'host'},
      {...sender(), documentLifecycle: 'cached'}, {...sender(), origin: 'https://evil.example'}
    ];
    for (const from of variants) { const h = harness(); denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}, from)); assert.equal(h.counts.upload, 0); }
  });
  await test('missing active lifecycle/document ID/conversation rejected', async () => {
    const variants = [{...sender(), documentLifecycle: undefined}, {...sender(), documentId: undefined},
      {...sender(), url: 'https://chat.deepseek.com/', tab: {id: 7, url: 'https://chat.deepseek.com/'}}];
    for (const from of variants) { const h = harness(); denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}, from)); assert.equal(h.counts.upload, 0); }
  });
  await test('live tab outside origin, other conversation, wrong ID, disappeared tab rejected', async () => {
    for (const tab of [{id: 7, url: 'https://evil.example/'}, {id: 7, url: 'https://chat.deepseek.com/a/chat/s/other'}, {id: 8, url: URL_A}]) {
      const h = harness(); h.state.tab = tab; denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()})); assert.equal(h.counts.upload, 0);
    }
    const h = harness(bg, {tabGone: true}); denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}));
  });
  await test('navigation after auth prevented before PoW', async () => {
    const h = harness(bg, {navigateAfterAuth: true}); denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()})); assert.equal(h.counts.pow, 0); assert.equal(h.counts.upload, 0);
  });
  await test('navigation after PoW prevented before upload', async () => {
    const h = harness(bg, {navigateAfterPow: true}); denied(await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()})); assert.equal(h.counts.pow, 1); assert.equal(h.counts.upload, 0);
  });
  await test('navigation during upload rejects returned ID (cannot undo remote upload)', async () => {
    const h = harness(bg, {navigateAfterUpload: true}); const r = await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}); denied(r); assert.equal(h.counts.upload, 1); assert(!r.file);
  });
  await test('real payload validator rejects empty, oversized, wrong MIME and mismatched size', async () => {
    for (const p of [{...payload(), sizeBytes: 0}, {...payload(), sizeBytes: 8388609}, {...payload(), mimeType: 'text/plain'}, {...payload(), sizeBytes: 1}]) {
      const h = harness(); const r = await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: p}); assert.equal(r.code, 'invalid_image'); assert.equal(h.counts.auth, 0); assert.equal(h.counts.upload, 0);
    }
  });
  await test('missing authentication classified without leaking localized message', async () => {
    const h = harness(bg, {noAuth: true}); const r = await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()});
    assert.equal(r.code, 'auth_missing'); assert.equal(h.counts.pow, 0); assert(!JSON.stringify(r).includes('PRIVATE'));
  });
  await test('auth/PoW/auth-rejection/upload errors produce only fixed enums', async () => {
    for (const [behavior, code] of [[{authThrow: true}, 'auth_failed'], [{powError: 'Error'}, 'pow_failed'], [{powError: 'DeepSeekAuthError'}, 'auth_rejected'], [{uploadError: 'Error'}, 'upload_failed'], [{uploadError: 'DeepSeekAuthError'}, 'auth_rejected'], [{uploadError: 'AbortError'}, 'upload_aborted']]) {
      const h = harness(bg, behavior); const r = await h.dispatch({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: payload()}); assert.equal(r.code, code); assert(!JSON.stringify(r).includes('PRIVATE'));
    }
  });
  await test('unrelated extension-only commands remain forbidden', async () => {
    const h = harness(); for (const type of ['CHAT_NEW_SESSION', 'SAVE_OFFICIAL_API_CHAT_CONFIG', 'GET_CONFIG', 'UNKNOWN_COMMAND']) denied(await h.dispatch({type, payload: {}}));
  });
  await test('full content capture -> actual listener/service -> ref IDs and safe failure diagnostics', async () => {
    for (const [source, behavior, expected] of [[bg, {}, 'upload_ok'], [old, {}, 'runtime_message_unauthorized'], [bg, {noAuth: true}, 'auth_missing'], [bg, {powError: 'Error'}, 'pow_failed']]) {
      const h = harness(source, behavior), store = new Map();
      const box = {URL, Blob, Uint8Array, DOMException, AbortController, atob, btoa, crypto: webcrypto, console, setTimeout, clearTimeout,
        localStorage: {getItem: key => store.get(key), setItem: (key, value) => store.set(key, value)},
        chrome: {runtime: {lastError: null, sendMessage: (m, cb) => { h.dispatch(m).then(cb); }}}};
      vm.createContext(box); vm.runInContext(slice(content, '/* DPP_READIMAGE_V7_BEGIN', '/* DPP_READIMAGE_V7_END */'), box);
      const state = box.DPP_CREATE_READIMAGE_V7({backend: 'web', signal: new AbortController().signal, chatSessionId: 'session-a'});
      await state.capture({name: 'read_image', result: {ok: true, output: {structuredContent: {data_uri: payload().dataUrl}}}});
      let request; await state.wrapSubmit(async r => { request = r; return {finished: true}; })({chatSessionId: 'session-a', prompt: 'describe', refFileIds: []}, {}, new AbortController().signal);
      assert.equal(request.refFileIds.length, expected === 'upload_ok' ? 1 : 0);
      const logs = store.get('dpp_read_image_diag_v7'); assert(logs.includes(expected));
      for (const secret of ['PRIVATE', PNG, 'fixture-file-id', URL_A]) assert(!logs.includes(secret));
    }
  });
  console.log(`RESULT ${groups}/${groups} boundary groups passed; actual extracted code, offline dependencies only.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
