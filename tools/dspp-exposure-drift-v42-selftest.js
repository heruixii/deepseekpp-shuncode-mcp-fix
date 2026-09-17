// Fix 3.3.10.42 -- exposure drift: explicit direct mode respected, single ShunCode server stays direct,
// adaptive floor keeps run_command + read_image together, turn_diag keeps `resolution`.
// Usage: node dspp-exposure-drift-v42-selftest.js [ROOT]   (defaults to the directory of this file)
const fs = require('fs'), path = require('path'), vm = require('vm');
const root = process.argv[2] || __dirname;
const bg = fs.readFileSync(path.join(root, 'background.js'), 'utf8');
const cjs = fs.readFileSync(path.join(root, 'content-scripts', 'content.js'), 'utf8');
const polSrc = fs.readFileSync(path.join(root, 'fix3-policy.js'), 'utf8');
let pass = 0, fail = 0;
function ok(name, cond, detail) { console.log((cond ? 'PASS ' : 'FAIL ') + name + (detail ? ' ' + detail : '')); cond ? pass++ : fail++; }
function grabFn(src, name) {
  const i = src.indexOf('function ' + name + '(');
  if (i < 0) throw new Error('missing ' + name);
  let depth = 0, j = src.indexOf('{', i);
  for (; j < src.length; j++) { if (src[j] === '{') depth++; else if (src[j] === '}' && --depth === 0) break; }
  return src.slice(i, j + 1) + '\n';
}

// [1] policy
{
  const g = {}; const ctx = { globalThis: g, console, TextEncoder, JSON, Math, Number, String, Array, Object, Date, Map, Set, RegExp };
  ctx.globalThis = ctx; vm.createContext(ctx); vm.runInContext(polSrc, ctx);
  const p = ctx.DPP_FIX3;
  ok('policy exports promptExposureSettings', typeof p.promptExposureSettings === 'function');
  function d(name, pad) { return { name, invocationName: 'mcp_t_s_' + name, title: name, description: 'x'.repeat(pad), inputSchema: { type: 'object', properties: { text: { type: 'string' } } }, provider: { kind: 'mcp', id: 'srv' }, execution: { enabled: true, mode: 'auto' } }; }
  const shuncode = ['apply_patch', 'find_files', 'read_files', 'read_image', 'search_files', 'list_directory', 'run_command', 'get_command_output', 'cancel_command', 'send_command_input', 'get_diagnostics', 'lsp', 'set_todos', 'update_plan', 'report_progress'].map(n => d(n, 1300));
  const total = shuncode.reduce((a, x) => a + p.promptDescriptorCost(x), 0);
  ok('fixture cost is in the real ShunCode band (30-48 KB)', total > 30000 && total < 48000, String(total));
  const unset = { version: 1, adaptiveMaxDirectTools: 8, adaptiveMaxPromptBytes: 24000, servers: {} };
  ok('single ShunCode server (unset mode) is NOT auto-degraded', p.promptExposureSettings(shuncode, unset, '继续') === unset);
  const explicitDirect = { ...unset, servers: { srv: { mode: 'direct', pinnedDescriptorIds: [] } } };
  const huge = Array.from({ length: 40 }, (_, i) => d('t' + i, 2400));
  ok('explicit direct is respected even above trigger', p.promptExposureSettings(huge, explicitDirect, '继续') === explicitDirect);
  const r = p.promptExposureSettings(huge, unset, '继续');
  ok('unset mode above trigger still degrades', r !== unset && r.servers.srv.mode === 'adaptive');
  ok('trigger literal is 48000', polSrc.includes('triggerBudget=Math.max(48000,adaptiveBudget*2)'));
  ok('explicit-mode guard literal present', polSrc.includes('(current&&typeof current.mode===`string`))continue;'));
}

// [2] background floor + ceiling
{
  const ctx = { globalThis: {} }; vm.createContext(ctx);
  vm.runInContext(grabFn(bg, 'DPP_CORE_TOOL_FLOOR_331033') + grabFn(bg, 'Cd') + grabFn(bg, 'Td') + grabFn(bg, 'Dd') + grabFn(bg, 'Ed'), ctx);
  ok('read_image floor is 1000', ctx.DPP_CORE_TOOL_FLOOR_331033({ name: 'read_image', invocationName: 'mcp_t_s_read_image' }) === 1000);
  ok('run_command floor still 1600', ctx.DPP_CORE_TOOL_FLOOR_331033({ name: 'run_command', invocationName: 'mcp_t_s_run_command' }) === 1600);
  const names = ['apply_patch', 'find_files', 'get_command_output', 'read_image', 'run_command', 'search_files', 'list_directory', 'read_files', 'lsp', 'get_diagnostics', 'set_todos', 'report_progress', 'send_command_input', 'cancel_command', 'update_plan'];
  const descs = names.map(n => ({ id: 'mcp:s:' + n, name: n, invocationName: 'mcp_t_s_' + n, title: n, description: 'ShunCode ' + n + ' tool' }));
  for (const intent of ['继续', '参考提供的图片，使用HTML+CSS将其精确重绘为SVG', '运行命令构建']) {
    const t = ctx.Td(intent), w = ctx.Dd(t);
    const top = descs.map((d, i) => ({ d, i, s: ctx.Cd(d, t, w, false) })).sort((a, b) => b.s - a.s || ctx.Ed(a.d.title, b.d.title) || a.i - b.i).slice(0, 8).map(x => x.d.name);
    ok('top-8 for "' + intent.slice(0, 12) + '" has run_command+read_image+read_files+apply_patch+get_command_output',
      ['run_command', 'read_image', 'read_files', 'apply_patch', 'get_command_output'].every(n => top.includes(n)), top.join(','));
  }
  ok('defaults 8/24e3', bg.includes('Vu=Object.freeze({version:1,adaptiveMaxDirectTools:8,adaptiveMaxPromptBytes:24e3,servers:{}})'));
  ok('ceiling 8/24e3', bg.includes('Math.min(e.settings.adaptiveMaxDirectTools,8),Math.min(e.settings.adaptiveMaxPromptBytes,24e3)'));
  ok('old 5/14e3 ceiling gone', !bg.includes('Math.min(e.settings.adaptiveMaxDirectTools,5)'));
  ok('upload gate untouched', bg.includes('function DPP_REQUIRE_UPLOAD_CONTEXT_V7('));
}

// [3] content turn_diag whitelist keeps resolution
{
  const fn = grabFn(cjs, 'DPP_RECORD_AGENT_TURN_DIAG_331021');
  ok('whitelist has resolution', fn.includes('resolution:typeof t.resolution==`string`?t.resolution.slice(0,40):null'));
  const ctx = { rows: [], Date, JSON, Number, String, Array, Object };
  ctx.DPP_NUM_331018 = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null);
  ctx.DPP_DIAG_BATCH_APPEND_331022 = (k, lim, row) => { ctx.rows.push(row); return Promise.resolve(); };
  ctx.DPP_AGENT_TURN_DIAG_KEY_331021 = 'k';
  vm.createContext(ctx); vm.runInContext(fn, ctx);
  ctx.DPP_RECORD_AGENT_TURN_DIAG_331021({ stage: 'unregistered_tool_tag_331033', resolution: 'exact_hint', decision: 'unregistered_tool_tag_331033', errorMessage: 'read_image' });
  ctx.DPP_RECORD_AGENT_TURN_DIAG_331021({ stage: 'turn_decision', decision: 'tool_call' });
  ok('resolution persisted', ctx.rows[0].resolution === 'exact_hint');
  ok('resolution null when absent', ctx.rows[1].resolution === null);
  ok('non-string resolution rejected', (ctx.DPP_RECORD_AGENT_TURN_DIAG_331021({ resolution: { x: 1 } }), ctx.rows[2].resolution === null));
}

const mf = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8'));
ok('manifest 1.14.0.47 / Fix 3.3.10.42', mf.version === '1.14.0.47' && mf.version_name === '1.14.0 ShunCode MCP Fix 3.3.10.42');
console.log((fail ? 'FAIL ' : 'PASS ') + pass + '/' + (pass + fail));
process.exit(fail ? 1 : 0);
