'use strict';
// Offline only: executes runtime extracted from the candidate and the real Jz event handler.
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert/strict');
const {webcrypto} = require('crypto');
const candidatePath = process.argv[2];
const full = candidatePath ? fs.readFileSync(candidatePath, 'utf8') : '';
const source = full ? full.slice(full.indexOf('/* DPP_READIMAGE_V6_BEGIN'), full.indexOf('/* DPP_READIMAGE_V6_END */') + '/* DPP_READIMAGE_V6_END */'.length) : fs.readFileSync(path.join(__dirname, 'dspp-readimage-v6-runtime.js'), 'utf8');
const PNG = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=';
const URI = 'data:image/png;base64,' + PNG;
const image = () => ({type: 'image', mimeType: 'image/png', data: PNG});
const execution = (name = 'read_image', output = {structuredContent: {status: 'success', data_uri: URI}}) => ({name, result: {ok: true, name, summary: 'image read', output}});
let passed = 0;
function setup(send, fastTimeout = false) {
  const sent = [], rows = [], stored = new Map();
  const controller = new AbortController();
  const box = {console, crypto: webcrypto, Uint8Array, DOMException, AbortController, atob, btoa,
    setTimeout: (fn, ms) => setTimeout(fn, fastTimeout ? 5 : ms), clearTimeout,
    localStorage: {getItem: k => stored.get(k), setItem: (k, v) => stored.set(k, v)},
    chrome: {runtime: {lastError: null, sendMessage(message, callback) { sent.push(message); return send ? send(message, callback, box) : setTimeout(() => callback({ok: true, file: {id: 'file-' + sent.length}}), 1); }}}};
  vm.createContext(box); vm.runInContext(source, box);
  const state = box.DPP_CREATE_READIMAGE_V6({backend: 'web', signal: controller.signal, chatSessionId: 'session-a', onDiagnostic: row => rows.push(row)});
  return {box, state, sent, rows, stored, controller};
}
const req = (refs = []) => ({chatSessionId: 'session-a', prompt: 'answer', refFileIds: refs});
async function request(state, fn = async value => ({finished: true, value}), input = req()) {
  return state.wrapSubmit(fn)(input, {}, new AbortController().signal);
}
async function test(name, fn) { await fn(); passed++; console.log('PASS ' + name); }
(async () => {
  await test('nested structuredContent, exact sizeBytes, wait then inject', async () => {
    const x = setup(); const original = execution(); const before = JSON.stringify(original);
    const clean = await x.state.capture(original);
    assert.equal(x.sent.length, 1); assert.equal(x.sent[0].payload.sizeBytes, Buffer.from(PNG, 'base64').length);
    assert.equal(x.sent[0].payload.mimeType, 'image/png'); assert(!JSON.stringify(clean).includes(PNG));
    assert.equal(JSON.stringify(original), before);
    assert.deepEqual(Array.from((await request(x.state)).value.refFileIds), ['file-1']);
    assert.deepEqual(Array.from((await request(x.state)).value.refFileIds), []);
  });
  await test('native content image block and nested details wrappers', async () => {
    const x = setup(); await x.state.capture(execution('mcp_invoke', {result: {details: {content: [image()]}}}));
    assert.equal(x.sent.length, 1);
  });
  await test('MCP text block JSON and structured result aliases', async () => {
    for (const key of ['data_uri', 'dataUri', 'dataURL']) {
      const x = setup(); await x.state.capture(execution('mcp_t_abc_read_image', {content: [{type: 'text', text: JSON.stringify({[key]: URI})}]}));
      assert.equal(x.sent.length, 1);
    }
  });
  await test('stringified output and hash dedup across calls', async () => {
    const x = setup(); const e = execution('mcp_invoke', JSON.stringify({structuredContent: {data_uri: URI}}));
    await x.state.capture(e); await x.state.capture(e); assert.equal(x.sent.length, 1);
    await request(x.state); await x.state.capture(e); assert.equal(x.sent.length, 1);
    assert.deepEqual(Array.from((await request(x.state)).value.refFileIds), ['file-1']);
  });
  await test('ordinary text tools never auto-upload image literals', async () => {
    const x = setup(); const e = execution('read_files'); assert.equal(await x.state.capture(e), e);
    assert.equal(x.sent.length, 0);
  });
  await test('API backend unchanged and no upload', async () => {
    const x = setup(); const api = x.box.DPP_CREATE_READIMAGE_V6({backend: 'official-api'}); const e = execution();
    assert.equal(await api.capture(e), e); assert.equal(x.sent.length, 0);
    const r = req(); assert.equal((await request(api, async value => ({value}), r)).value, r);
  });
  await test('tool failure and truncated result cannot upload', async () => {
    for (const field of ['ok', 'truncated', 'isError']) {
      const x = setup(); const e = execution(); e.result[field] = field === 'ok' ? false : true;
      await x.state.capture(e); assert.equal(x.sent.length, 0);
    }
  });
  await test('invalid, unsupported, MIME mismatch and empty payload rejected', async () => {
    for (const uri of ['data:image/png;base64,', 'data:image/png;base64,@@@', 'data:image/png;base64,A', 'data:image/jpeg;base64,' + PNG, 'data:image/svg+xml;base64,PHN2Zy8+']) {
      const x = setup(); await x.state.capture(execution('read_image', {data_uri: uri})); assert.equal(x.sent.length, 0);
      assert((await request(x.state)).value.prompt.includes('Do not claim'));
    }
  });
  await test('over 8MiB does not upload', async () => {
    const x = setup(); await x.state.capture(execution('read_image', {data_uri: 'data:image/png;base64,' + PNG + 'A'.repeat(12 * 1024 * 1024)}));
    assert.equal(x.sent.length, 0);
  });
  await test('dedup same image represented in three fields', async () => {
    const x = setup(); await x.state.capture(execution('read_image', {data_uri: URI, structuredContent: {data_uri: URI}, content: [image()]}));
    assert.equal(x.sent.length, 1);
  });
  await test('cyclic wrappers bounded', async () => {
    const x = setup(); const out = {data_uri: URI}; out.output = out;
    await x.state.capture(execution('read_image', out)); assert.equal(x.sent.length, 1);
  });
  await test('existing user refs preserved and no in-place mutation', async () => {
    const x = setup(); await x.state.capture(execution()); const r = req(['user-file', 'file-1']);
    const next = (await request(x.state, async value => ({finished: true, value}), r)).value;
    assert.deepEqual(Array.from(next.refFileIds), ['user-file', 'file-1']); assert.equal(r.prompt, 'answer');
  });
  await test('failed request retains references for retry', async () => {
    const x = setup(); await x.state.capture(execution());
    await assert.rejects(request(x.state, async () => { throw new Error('network'); }));
    assert.deepEqual(Array.from((await request(x.state)).value.refFileIds), ['file-1']);
  });
  await test('unfinished stream retains references', async () => {
    const x = setup(); await x.state.capture(execution());
    await request(x.state, async value => ({finished: false, value}));
    assert.deepEqual(Array.from((await request(x.state)).value.refFileIds), ['file-1']);
  });
  await test('server failure, invalid ID and runtime.lastError reported', async () => {
    for (const response of [{ok: false, error: 'secret-token'}, {ok: true, file: {}}, {ok: true, file: {id: 7}}]) {
      const x = setup((m, cb) => cb(response)); await x.state.capture(execution());
      const r = (await request(x.state)).value; assert.equal(r.refFileIds.length, 0); assert(r.prompt.includes('upload_failed'));
      assert(!JSON.stringify(x.rows).includes('secret-token'));
    }
    const x = setup((m, cb, box) => { box.chrome.runtime.lastError = {message: 'secret'}; cb({ok: true, file: {id: 'bad'}}); });
    await x.state.capture(execution()); assert.equal((await request(x.state)).value.refFileIds.length, 0);
  });
  await test('timeout ignores late callback', async () => {
    let callback; const x = setup((m, cb) => { callback = cb; }, true);
    await x.state.capture(execution()); callback({ok: true, file: {id: 'late'}});
    const r = (await request(x.state)).value; assert.equal(r.refFileIds.length, 0); assert(r.prompt.includes('upload_timeout'));
  });
  await test('abort during upload does not leak into another run', async () => {
    let callback; const x = setup((m, cb) => { callback = cb; });
    const p = x.state.capture(execution());
    while (!callback) await new Promise(r => setTimeout(r, 1));
    x.controller.abort(); await assert.rejects(p, e => e.name === 'AbortError'); callback({ok: true, file: {id: 'late'}});
    await assert.rejects(request(x.state), e => e.name === 'AbortError');
    const y = setup(); assert.equal((await request(y.state)).value.refFileIds.length, 0);
  });
  await test('wrong session fails before network', async () => {
    const x = setup(); await x.state.capture(execution()); let calls = 0;
    await assert.rejects(request(x.state, async () => { calls++; }, {...req(), chatSessionId: 'session-b'})); assert.equal(calls, 0);
  });
  await test('request signal abort and close prevent stale reuse', async () => {
    const x = setup(); await x.state.capture(execution()); const ac = new AbortController(); ac.abort();
    await assert.rejects(x.state.wrapSubmit(async () => {})(req(), {}, ac.signal));
    x.state.close(); await assert.rejects(request(x.state));
  });
  await test('diagnostic ring <=64, no pixels, full path, auth or file IDs', async () => {
    const x = setup(); for (let i = 0; i < 40; i++) { await x.state.capture(execution()); await request(x.state); }
    const text = x.stored.get('dpp_read_image_diag_v6'); assert(JSON.parse(text).length <= 64);
    for (const secret of [PNG, URI, 'file-1', 'session-a', 'secret-token']) assert(!text.includes(secret));
  });
  if (full) {
    await test('candidate has no v5 global queue; native forwarding preserved', async () => {
      assert(!full.includes('DPP_RIF')); assert(!full.includes('DPP_READIMAGE_V5'));
      assert(full.includes('refFileIds:o.refFileIds,thinkingEnabled:o.thinkingEnabled'));
      assert(full.includes('ref_file_ids:e.refFileIds'));
      assert(full.includes('finally{DPPVisionV6.close()}'));
    });
    await test('real Jz seeds + real tool_execution_end + actual upload wrapper', async () => {
      const x = setup(); const requests = [], events = []; let opts;
      Object.assign(x.box, {
        Kz: 12000, qz: '[truncated]', NR: 120000,
        JR: o => { opts = o; return {getModels: () => [{}]}; }, YR: () => () => {},
        BR: () => async r => { requests.push(r); return {finished: true}; }, Bz: () => [],
        Hz: () => ({maxSteps: 88, maxNudges: 8}),
        DPP_CAPABILITY_WINDOW_32: () => null, DPP_RECORD_AGENT_TOOL_SHAPE_331018: () => {},
        DPP_RECORD_AGENT_TURN_DIAG_331021: () => {}, DPP_TOOL_EFFECT_31: () => 'neutral',
        UN: async (messages, context, config, event, signal) => {
          await opts.submitTurn(req(), {}, signal);
          await event({type: 'tool_execution_start', toolCallId: 'call-2', toolName: 'mcp_invoke', args: {capability: 'fixture'}});
          await event({type: 'tool_execution_end', toolCallId: 'call-2', toolName: 'mcp_invoke', isError: false,
            result: {content: [{type: 'text', text: 'image'}], details: execution('mcp_invoke', {content: [image()]}).result}});
          await opts.submitTurn(req(), {}, signal);
        }
      });
      const start = full.indexOf('async function Jz(e){'), end = full.indexOf('function Yz(e)', start);
      vm.runInContext('function Xz(e){return (e?.content||[]).filter(x=>x.type==="text").map(x=>x.text).join("")}'+
        'function Vz(e,t){return {name:e.toolName,provider:e.provider,result:e.message.details,dppEffect:"neutral"}}'+full.slice(start, end), x.box);
      await x.box.Jz({payload: {loopId: 'loop-fixture', chatSessionId: 'session-a', parentMessageId: 1, toolDescriptors: [],
        promptOptions: {}, originalPrompt: 'read fixture', toolExecutions: [execution()]}, post: (name, e) => events.push({name, e}), executeTool: async () => {}, signal: x.controller.signal});
      assert.equal(requests.length, 2, JSON.stringify(events));
      assert.equal(x.sent.length, 1); // The second read reuses a same-run file ID, not a global queue.
      assert.deepEqual(requests.map(x => Array.from(x.refFileIds)), [['file-1'], ['file-1']]);
      const completed = events.find(x => x.name === 'AGENT_TOOL_COMPLETE'); assert(completed);
      assert(!JSON.stringify(completed).includes(PNG));
    });
  }
  console.log(`RESULT ${passed}/${passed} groups passed; offline only; no network/browser upload.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
