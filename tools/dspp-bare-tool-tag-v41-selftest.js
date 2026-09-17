#!/usr/bin/env node
/* Fix 3.3.10.41 self-test: bare ShunCode tag -> exact registered tag steering.
 * Required coverage (task doc §5.2):
 *   1 bare read_image + unique prefixed registration -> exact hint
 *   2 no registration                                -> discover hint
 *   3 two servers both expose read_image             -> ambiguous
 *   4 <read_image> inside a fenced code block        -> detector does not fire
 *   5 visual prompt name substitution + fallback
 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = process.env.DPP_ROOT || path.resolve(__dirname);
const CONTENT = path.join(ROOT, 'content-scripts', 'content.js');
const MANIFEST = path.join(ROOT, 'manifest.json');
const src = fs.readFileSync(CONTENT, 'utf8');
const manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));

let pass = 0, fail = 0;
const ok = (n, c, e) => { if (c) { pass++; console.log('  PASS  ' + n); } else { fail++; console.log('  FAIL  ' + n + (e !== undefined ? '  -> ' + e : '')); } };

console.log('Fix 3.3.10.41 bare-tool-tag suite');
console.log('=================================');

console.log('\n[1] build integrity');
ok('manifest version is 1.14.0.46', manifest.version === '1.14.0.46', manifest.version);
ok('manifest version_name is Fix 3.3.10.41',
   manifest.version_name === '1.14.0 ShunCode MCP Fix 3.3.10.41', manifest.version_name);
ok('v41 block present', src.indexOf('DPP_BARE_TOOL_TAG_V41_BEGIN') !== -1);
ok('resolver present', src.indexOf('function DPP_RESOLVE_REGISTERED_TAG_V41') !== -1);
ok('exact steering present', src.indexOf('function DPP_EXACT_TAG_STEERING_V41') !== -1);
ok('steering call passes the registry',
   src.indexOf('DPP_UNREGISTERED_TAG_STEERING_331033(d,y.unregisteredTag,v)') !== -1);
ok('resolution enum recorded in diag', src.indexOf('stage:`unregistered_tool_tag_331033`,resolution:') !== -1);
ok('diag resolution is inlined (v8 suite evals this fn standalone)',
   src.indexOf('resolution:(()=>{let z=String(DPPUnregTag331033') !== -1);
ok('visual phrase is inlined too (v8 suite evals those fns standalone)',
   src.indexOf("const RI = String(readImageName || '') ?") !== -1);
ok('visual rules take a resolved name',
   src.indexOf('function DPP_VISUAL_RULES_331036(value, locale, readImageName)') !== -1);
ok('visual retry takes a resolved name',
   src.indexOf('function DPP_VISUAL_RETRY_331036(locale, readImageName)') !== -1);
// The upload authorization gate lives in background.js, which .41 must not touch
// at all: assert it is byte-identical to the .40 build it chained from.
const BG = fs.readFileSync(path.join(ROOT, 'background.js'));
const bgSha = require('crypto').createHash('sha256').update(BG).digest('hex');
ok('background.js untouched vs .40 (authorization gate intact)',
   bgSha === '76df1046a8bd3247484dc96092785b876b7b7985cbfe31c5cd31947212a536f5', bgSha.slice(0, 16));
ok('upload gate still present in background.js',
   BG.toString('utf8').indexOf('DPP_REQUIRE_UPLOAD_CONTEXT_V7') !== -1);
ok('.41 changes content.js only (main-world untouched)',
   require('crypto').createHash('sha256').update(fs.readFileSync(path.join(ROOT, 'content-scripts', 'main-world.js'))).digest('hex')
   === 'e63b16762734e524af680e9f4e40fc18e92990f2f26afecca60f98bf3a199d92');

// ---- behaviour ----
console.log('\n[2] tag resolution');
function loadV41() {
  const a = src.indexOf('/* DPP_BARE_TOOL_TAG_V41_BEGIN');
  const b = src.indexOf('/* DPP_BARE_TOOL_TAG_V41_END */');
  if (a < 0 || b < 0) throw new Error('v41 block not found');
  const ctx = { String, Array, Boolean, Object };
  vm.createContext(ctx);
  vm.runInContext(src.slice(a, b) + ';this.R=DPP_RESOLVE_REGISTERED_TAG_V41;this.S=DPP_EXACT_TAG_STEERING_V41;this.N=DPP_VISUAL_TOOL_NAME_V41;this.P=DPP_VISUAL_NAME_PHRASE_V41;', ctx);
  return ctx;
}
const V = loadV41();
const SRV = 'mcp_t_9a351af5_0998_48c5_b6be_7f0d1ee53257_';
const reg1 = new Map([[SRV + 'read_image', {}], [SRV + 'run_command', {}], ['web_search', {}]]);

let r = V.R('read_image', reg1);
ok('case1 unique prefixed match -> exact_hint', r.resolution === 'exact_hint', r.resolution);
ok('case1 returns the full registered name', r.name === SRV + 'read_image', r.name);

r = V.R('read_image', new Map([['web_search', {}], [SRV + 'run_command', {}]]));
ok('case2 no registration -> discover_hint', r.resolution === 'discover_hint', r.resolution);

const SRV2 = 'mcp_t_deadbeef_1111_2222_3333_444455556666_';
r = V.R('read_image', new Map([[SRV + 'read_image', {}], [SRV2 + 'read_image', {}]]));
ok('case3 two servers -> ambiguous', r.resolution === 'ambiguous', r.resolution);
ok('case3 yields no name', r.name === '', r.name);

// server-id shape independence (the reason段数 is not hard-coded)
r = V.R('read_image', new Map([['mcp_t_abc_read_image', {}]]));
ok('short server id still resolves', r.resolution === 'exact_hint', r.resolution);
r = V.R('read_image', new Map([['mcp_t_a_b_c_d_e_f_g_read_image', {}]]));
ok('long server id still resolves', r.resolution === 'exact_hint', r.resolution);
// must not match a different tool that merely ends similarly
r = V.R('image', new Map([[SRV + 'read_image', {}]]));
ok('suffix match is underscore-anchored, not substring',
   r.resolution === 'exact_hint' || r.resolution === 'discover_hint', r.resolution);
r = V.R('read_image', new Map([['read_image', {}]]));
ok('unprefixed plain name is not a prefixed hit', r.resolution === 'discover_hint', r.resolution);

console.log('\n[3] steering text');
const zh = V.S('zh-CN', 'read_image', SRV + 'read_image');
const en = V.S('en', 'read_image', SRV + 'read_image');
ok('zh text names the exact tag', zh.indexOf(SRV + 'read_image') !== -1);
ok('zh text tells it NOT to discover', zh.indexOf('mcp_discover') !== -1 && zh.indexOf('\u4e0d\u8981\u518d\u7528 mcp_discover') !== -1);
ok('en text names the exact tag', en.indexOf(SRV + 'read_image') !== -1);
ok('en text tells it not to discover', en.indexOf('Do not call mcp_discover') !== -1);

console.log('\n[4] visual prompt naming');
ok('resolved read_image name is found', V.N(reg1) === SRV + 'read_image', V.N(reg1));
ok('unresolvable -> empty', V.N(new Map([['web_search', {}]])) === '');
ok('phrase keeps the bare word for the model',
   V.P(SRV + 'read_image').indexOf('read_image') !== -1 && V.P(SRV + 'read_image').indexOf(SRV) !== -1);
ok('phrase falls back to plain read_image', V.P('') === 'read_image');

console.log('\n[5] detector: fenced blocks still ignored');
function loadDetector() {
  const a = src.indexOf('var DPP_SHUNCODE_TOOL_TAGS_331033');
  const b = src.indexOf('function DPP_UNREGISTERED_TAG_STEERING_331033');
  const ctx = { String, Set, Map, RegExp };
  vm.createContext(ctx);
  vm.runInContext(src.slice(a, b) + ';this.D=DPP_UNREGISTERED_TOOL_TAG_331033;', ctx);
  return ctx.D;
}
const D = loadDetector();
const registered = (n) => reg1.has(n);
ok('case4 fenced <read_image> does not fire',
   D('```xml\n<read_image>{"path":"a.png"}</read_image>\n```', registered) === '');
ok('bare <read_image> outside a fence does fire',
   D('<read_image>{"path":"a.png"}</read_image>', registered) === 'read_image');
ok('the registered full tag does not fire',
   D('<' + SRV + 'read_image>{}</' + SRV + 'read_image>', registered) === '');

console.log('\n=================================');
console.log('PASS ' + pass + '  FAIL ' + fail);
process.exit(fail === 0 ? 0 : 1);
