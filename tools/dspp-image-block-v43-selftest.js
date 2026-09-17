// Fix 3.3.10.43 -- read_image with include_data_uri:false must still reach the v7 visual channel.
// Usage: node dspp-image-block-v43-selftest.js [ROOT]
const fs = require('fs'), path = require('path'), vm = require('vm');
const root = process.argv[2] || __dirname;
const bg = fs.readFileSync(path.join(root, 'background.js'), 'utf8');
const cjs = fs.readFileSync(path.join(root, 'content-scripts', 'content.js'), 'utf8');
const pol = fs.readFileSync(path.join(root, 'fix3-policy.js'), 'utf8');
let pass = 0, fail = 0;
function ok(name, cond, detail) { console.log((cond ? 'PASS ' : 'FAIL ') + name + (detail ? ' ' + detail : '')); cond ? pass++ : fail++; }
function grabFn(src, name) {
  const i = src.indexOf('function ' + name + '(');
  if (i < 0) throw new Error('missing ' + name);
  let depth = 0, j = src.indexOf('{', i);
  for (; j < src.length; j++) { if (src[j] === '{') depth++; else if (src[j] === '}' && --depth === 0) break; }
  return src.slice(i, j + 1) + '\n';
}
// 1x1 JPEG (valid SOI header) -- enough for the v7 magic-byte check.
const JPEG_B64 = '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AVN//2Q==';

// [1] background Zo()
{
  const ctx = {}; vm.createContext(ctx);
  vm.runInContext(grabFn(bg, 'as') + grabFn(bg, 'Qo') + grabFn(bg, 'ss') + grabFn(bg, 'Zo'), ctx);
  const withSC = { content: [{ type: 'text', text: 'meta' }, { type: 'image', mimeType: 'image/jpeg', data: JPEG_B64 }], structuredContent: { status: 'success', width: 240 } };
  const out = ctx.Zo(withSC);
  ok('structuredContent fields preserved', out.status === 'success' && out.width === 240);
  ok('image block retained as output.content', Array.isArray(out.content) && out.content.length === 1 && out.content[0].data === JPEG_B64 && out.content[0].mimeType === 'image/jpeg');
  ok('only whitelisted keys in retained block', Object.keys(out.content[0]).sort().join(',') === 'data,mimeType,type');
  ok('text blocks are NOT copied', JSON.stringify(out).indexOf('"meta"') === -1);
  const noImg = ctx.Zo({ content: [{ type: 'text', text: 'x' }], structuredContent: { a: 1 } });
  ok('no image -> no content key', !('content' in noImg) && noImg.a === 1);
  const own = ctx.Zo({ content: [{ type: 'image', mimeType: 'image/png', data: 'AAAA' }], structuredContent: { content: 'keep' } });
  ok('structuredContent own content field is never clobbered', own.content === 'keep');
  const noSC = ctx.Zo({ content: [{ type: 'image', mimeType: 'image/png', data: 'AAAA' }] });
  ok('no structuredContent -> legacy content mapping unchanged', Array.isArray(noSC) && noSC[0].type === 'image' && noSC[0].data === 'AAAA');
  const arrSC = ctx.Zo({ content: [{ type: 'image', mimeType: 'image/png', data: 'AAAA' }], structuredContent: [1, 2] });
  ok('array structuredContent untouched', Array.isArray(arrSC) && arrSC.length === 2);
  const many = ctx.Zo({ content: Array.from({ length: 7 }, () => ({ type: 'image', mimeType: 'image/png', data: 'AAAA' })), structuredContent: {} });
  ok('capped at 4 images', many.content.length === 4);
  const bad = ctx.Zo({ content: [{ type: 'image', data: 'AAAA' }, { type: 'image', mimeType: 'image/png', data: 5 }], structuredContent: {} });
  ok('blocks missing mimeType or non-string data are skipped', !('content' in bad));
  ok('Zo literal is the .43 form', bg.includes('t.content===void 0&&(t.content=n)') && !bg.includes('function Zo(e){return e.structuredContent===void 0?'));
}

// [2] content v7 collect() finds the retained block (generic walk over `output`)
{
  const src = cjs.slice(cjs.indexOf('/* DPP_READIMAGE_V7_BEGIN'), cjs.indexOf('/* DPP_READIMAGE_V7_END */'));
  const { webcrypto } = require('crypto');
  const sent = [];
  const controller = new AbortController();
  const box = { console, crypto: webcrypto, Uint8Array, DOMException, AbortController, atob, btoa, setTimeout, clearTimeout,
    localStorage: { getItem: () => null, setItem: () => {} },
    chrome: { runtime: { lastError: null, sendMessage(m, cb) { sent.push(m); setTimeout(() => cb({ ok: true, file: { id: 'file-1' } }), 1); } } } };
  vm.createContext(box); vm.runInContext(src, box);
  const state = box.DPP_CREATE_READIMAGE_V7({ backend: 'web', signal: controller.signal, chatSessionId: 's' });
  const exec = { name: 'mcp_t_9a_read_image', result: { ok: true, name: 'read_image', output: { status: 'success', width: 240, content: [{ type: 'image', mimeType: 'image/jpeg', data: JPEG_B64 }] } } };
  let outcome;
  state.capture(exec).then(r => { outcome = r; }, e => { outcome = e; });
  setTimeout(() => {
    ok('v7 capture found the image (UPLOAD_DEEPSEEK_IMAGE sent, jpeg)', sent.length === 1 && sent[0].type === 'UPLOAD_DEEPSEEK_IMAGE' && sent[0].payload.mimeType === 'image/jpeg', String(sent.length));
    ok('redacted result does not carry base64', outcome && JSON.stringify(outcome).indexOf(JPEG_B64) === -1);
    // note text
    ok('no_image_data note names include_data_uri', src.includes("code === 'no_image_data' ? ' Likely cause: include_data_uri was set to false"));
    ok('tool_failed note names Max Result Bytes + downsample', src.includes('Max Result Bytes setting; downsample the image with run_command first'));
    // [3] visual rules
    ok('zh visual rules name include_data_uri', cjs.includes('保持 include_data_uri 为默认 true'));
    ok('en visual rules name include_data_uri', cjs.includes('Keep include_data_uri at its default true when calling read_image'));
    // [4] policy
    ok('trigger 64000', pol.includes('triggerBudget=Math.max(64000,adaptiveBudget*2)'));
    const mf = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8'));
    ok('manifest 1.14.0.48 / Fix 3.3.10.43', mf.version === '1.14.0.48' && mf.version_name === '1.14.0 ShunCode MCP Fix 3.3.10.43');
    console.log((fail ? 'FAIL ' : 'PASS ') + pass + '/' + (pass + fail));
    process.exit(fail ? 1 : 0);
  }, 300);
}
