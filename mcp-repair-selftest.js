function DPP_TOOL_KIND_1140(e){let t=String(e??``).toLowerCase(),n=[`run_command`,`apply_patch`,`shell_exec`,`shell_session_exec`];for(let e of n)if(t===e||t.endsWith(`_${e}`)||t.endsWith(`:${e}`)||t.endsWith(`.${e}`)||t.endsWith(`/${e}`))return e;return t.split(/[.:/]/).pop()??``}function DPP_SCHEMA_RAW_KEY_1140(e){let t=e?.inputSchema,n=t?.properties;if(!DPP_PLAIN_OBJECT_1140(t)||!DPP_PLAIN_OBJECT_1140(n))return null;let r=Array.isArray(t.required)?t.required.filter(e=>typeof e==`string`):[],i=Object.entries(n).filter(([,e])=>DPP_PLAIN_OBJECT_1140(e)&&(e.type===`string`||Array.isArray(e.type)&&e.type.includes(`string`)));if(r.length===1&&i.some(([e])=>e===r[0]))return r[0];if(r.length===0&&Object.keys(n).length===1&&i.length===1)return i[0][0];return null}function DPP_SCHEMA_COERCE_1140(e,t){if(!DPP_PLAIN_OBJECT_1140(e))return e;let n=t?.inputSchema?.properties;if(!DPP_PLAIN_OBJECT_1140(n))return e;let r={...e},i=[[`cmd`,`command`],[`timeout`,`timeout_ms`],[`timeoutMs`,`timeout_ms`],[`working_directory`,`cwd`],[`workingDirectory`,`cwd`]];for(let[e,t]of i)if(e in r&&!(t in r)&&Object.prototype.hasOwnProperty.call(n,t)){r[t]=r[e];delete r[e]}for(let[e,t]of Object.entries(n)){if(!DPP_PLAIN_OBJECT_1140(t))continue;if(!(e in r)&&Object.prototype.hasOwnProperty.call(t,`default`))try{r[e]=JSON.parse(JSON.stringify(t.default))}catch{}if(!(e in r))continue;let i=r[e],a=Array.isArray(t.type)?t.type:[t.type];if(typeof i==`string`){if((a.includes(`integer`)||a.includes(`number`))&&i.trim()&&Number.isFinite(Number(i)))r[e]=Number(i);else if(a.includes(`boolean`)&&(i.toLowerCase()===`true`||i.toLowerCase()===`false`))r[e]=i.toLowerCase()===`true`}}return r}function DPP_PLAIN_OBJECT_1140(e){return!!(e&&typeof e==`object`&&!Array.isArray(e))}function DPP_NORMALIZE_TOOL_PAYLOAD_1140(e,t){let n=DPP_TOOL_KIND_1140(t),r=e;if(DPP_PLAIN_OBJECT_1140(r?.arguments)&&Object.keys(r).every(e=>e===`tool`||e===`name`||e===`arguments`))r=r.arguments;else if(DPP_PLAIN_OBJECT_1140(r?.payload)&&Object.keys(r).every(e=>e===`tool`||e===`name`||e===`payload`))r=r.payload;if(n===`run_command`){if(typeof r==`string`)r={command:r,background:!1};if(DPP_PLAIN_OBJECT_1140(r)){typeof r.command!=`string`&&typeof r.cmd==`string`&&(r={...r,command:r.cmd});typeof r.background!=`boolean`&&(r={...r,background:String(r.background).toLowerCase()===`true`});if(typeof r.timeout_ms==`string`&&r.timeout_ms.trim()&&Number.isFinite(Number(r.timeout_ms)))r={...r,timeout_ms:Number(r.timeout_ms)}}}else if(n===`apply_patch`){if(typeof r==`string`)r={patch:r};if(DPP_PLAIN_OBJECT_1140(r)&&typeof r.patch!=`string`){let e=typeof r.diff==`string`?r.diff:typeof r.content==`string`?r.content:typeof r.patch_text==`string`?r.patch_text:null;e!==null&&(r={...r,patch:e})}}return r}function DPP_STRUCTURAL_COMMA_1140(e,t){let n=t+1;for(;n<e.length&&/\s/.test(e[n]);)n++;return n>=e.length||e[n]===`"`||e[n]===`}`||e[n]===`]`}function DPP_REPAIR_JSON_TEXT_1140(e,t){let n=``,r=!1,a=!1,o=DPP_TOOL_KIND_1140(t),s=o===`run_command`||o===`shell_exec`||o===`shell_session_exec`;for(let t=0;t<e.length;t++){let o=e[t];if(!r){if(o===`"`){r=!0,a=!1;n+=o;continue}n+=o;continue}if(o===`:`&&s&&t>0&&/[A-Za-z]/.test(e[t-1]??``)&&e[t+1]===`\\`){a=!0;n+=o;continue}if(o===`\\`){let r=e[t+1];if(a){if(r===`\\`){n+=`\\\\`;t++}else n+=`\\\\`;continue}if(r!==void 0&&`"\\/bfnrt`.includes(r)){n+=`\\${r}`;t++;continue}if(r===`u`&&/^[0-9A-Fa-f]{4}$/.test(e.slice(t+2,t+6))){n+=e.slice(t,t+6);t+=5;continue}n+=`\\\\`;continue}if(o===`"`){let i=t+1;for(;i<e.length&&/\s/.test(e[i]);)i++;let s=e[i],c=s===void 0||s===`:`||s===`}`||s===`]`||s===`,`&&DPP_STRUCTURAL_COMMA_1140(e,i);if(c){r=!1,a=!1;n+=o}else{n+=`\\"`;a&&(a=!1)}continue}if(o===`\n`){n+=`\\n`;continue}if(o===`\r`){n+=`\\r`;continue}if(o===`\t`){n+=`\\t`;continue}if(o===`\b`){n+=`\\b`;continue}if(o===`\f`){n+=`\\f`;continue}n+=o}let c=``,l=!1,u=!1;for(let t=0;t<n.length;t++){let e=n[t];if(l){c+=e;if(u){u=!1;continue}if(e===`\\`){u=!0;continue}e===`"`&&(l=!1);continue}if(e===`"`){l=!0;c+=e;continue}if(e===`,`){let r=t+1;for(;r<n.length&&/\s/.test(n[r]);)r++;if(n[r]===`}`||n[r]===`]`)continue}c+=e}return c}function DPP_SAFE_JSON_PARSE_1140(e,t,d){let n=String(e??``).trim(),r=DPP_TOOL_KIND_1140(t);if(!n)return DPP_NORMALIZE_TOOL_PAYLOAD_1140({},t);let i=n.match(/^```(?:json|javascript|js)?\s*([\s\S]*?)\s*```$/i);i&&(n=i[1].trim());if(r===`run_command`&&!n.trimStart().startsWith(`{`))return{command:n,background:!1};if(r===`apply_patch`&&!n.trimStart().startsWith(`{`)){if(n.includes(`*** Begin Patch`)&&n.includes(`*** End Patch`))return{patch:n};throw new SyntaxError(`DeepSeek++ MCP argument repair failed: incomplete apply_patch raw body`)}let q=DPP_SCHEMA_RAW_KEY_1140(d);if(q&&!n.trimStart().startsWith(`{`))return DPP_SCHEMA_COERCE_1140({[q]:n},d);let a=n.indexOf(`{`),o=n.lastIndexOf(`}`);a>=0&&o>a&&(a>0||o<n.length-1)&&(n=n.slice(a,o+1).trim());let c=DPP_REPAIR_JSON_TEXT_1140(n,t),s=(r===`run_command`||r===`shell_exec`||r===`shell_session_exec`)&&/[A-Za-z]:\\/.test(n)&&c!==n?[c,n]:[n];c!==n&&!s.includes(c)&&s.push(c);let l;for(let e of s)try{return DPP_SCHEMA_COERCE_1140(DPP_NORMALIZE_TOOL_PAYLOAD_1140(JSON.parse(e),t),d)}catch(e){l=e}if(r===`run_command`&&!n.startsWith(`{`))return{command:n,background:!1};if(r===`apply_patch`&&n.includes(`*** Begin Patch`)&&n.includes(`*** End Patch`))return{patch:n};throw new SyntaxError(`DeepSeek++ MCP argument repair failed: ${l instanceof Error?l.message:String(l)}`)}

const cases = [
  ["valid", String.raw`{"command":"dir","background":false}`, "run_command", x => x.command==="dir" && x.background===false],
  ["win-unescaped", String.raw`{"command":"Get-Content D:\test\new\file.txt","background":false}`, "run_command", x => x.command.includes(String.raw`D:\test\new\file.txt`)],
  ["inner-quotes", String.raw`{"command":"powershell -Command "Get-ChildItem 'D:\test\new'"","background":false}`, "run_command", x => x.command.includes(String.raw`"Get-ChildItem 'D:\test\new'"`)],
  ["literal-newline", `{"command":"echo one
echo two","background":false}`, "run_command", x => x.command==="echo one\necho two"],
  ["fenced", "```json\n{\"command\":\"dir\",\"background\":false}\n```", "run_command", x => x.command==="dir"],
  ["wrapper", `{"tool":"run_command","arguments":{"command":"dir"}}`, "run_command", x => x.command==="dir" && x.background===false],
  ["trailing-comma", `{"command":"dir","background":false,}`, "run_command", x => x.command==="dir"],
  ["namespaced-run", String.raw`{"command":"dir"}`, "mcp__shuncode_run_command", x => x.command==="dir" && x.background===false],
  ["plain-command", String.raw`Get-ChildItem "D:\Some Path" | Select-Object -First 3`, "run_command", x => x.command.startsWith("Get-ChildItem") && x.background===false],
  ["raw-patch", `*** Begin Patch
*** Add File: x.txt
+hello
*** End Patch`, "apply_patch", x => x.patch.includes("*** Begin Patch")],
  ["apply-wrapper-alias", `{"tool":"apply_patch","arguments":{"diff":"*** Begin Patch\\n*** End Patch"}}`, "apply_patch", x => typeof x.patch==="string"]
];
let failed=0;
for (const [name,raw,tool,check] of cases) {
  try {
    const out=DPP_SAFE_JSON_PARSE_1140(raw,tool);
    const ok=!!check(out);
    console.log(`${ok?"PASS":"FAIL"} ${name}`, JSON.stringify(out));
    if(!ok) failed++;
  } catch(e) {
    console.log(`FAIL ${name} threw`, e && e.stack || e);
    failed++;
  }
}

const singleTextDesc={inputSchema:{type:"object",properties:{text:{type:"string"}},required:["text"]}};
try {
  const out=DPP_SAFE_JSON_PARSE_1140("line one\nline two","write_note",singleTextDesc);
  const ok=out.text==="line one\nline two";
  console.log(`${ok?"PASS":"FAIL"} generic-single-string`, JSON.stringify(out));
  if(!ok) failed++;
} catch(e) { console.log("FAIL generic-single-string threw",e); failed++; }

const typedDesc={inputSchema:{type:"object",properties:{count:{type:"integer"},enabled:{type:"boolean"}},required:["count","enabled"]}};
try {
  const out=DPP_SAFE_JSON_PARSE_1140('{"count":"12","enabled":"false"}',"typed_tool",typedDesc);
  const ok=out.count===12 && out.enabled===false;
  console.log(`${ok?"PASS":"FAIL"} schema-coercion`, JSON.stringify(out));
  if(!ok) failed++;
} catch(e) { console.log("FAIL schema-coercion threw",e); failed++; }

const patchDesc={inputSchema:{type:"object",properties:{patch:{type:"string"}},required:["patch"]}};
let rejected=false;
try { DPP_SAFE_JSON_PARSE_1140("*** Begin Patch\n*** Add File: x\n+partial","apply_patch",patchDesc); }
catch(e) { rejected=true; }
console.log(`${rejected?"PASS":"FAIL"} incomplete-patch-rejected`);
if(!rejected) failed++;

const aliasDesc={inputSchema:{type:"object",properties:{command:{type:"string"},timeout_ms:{type:"integer"},cwd:{type:"string"}}}};
try {
  const out=DPP_SAFE_JSON_PARSE_1140('{"cmd":"dir","timeout":"12000","working_directory":"D:/work"}',"generic_exec",aliasDesc);
  const good=out.command==="dir" && out.timeout_ms===12000 && out.cwd==="D:/work" && !("cmd" in out) && !("timeout" in out) && !("working_directory" in out);
  console.log(`${good?"PASS":"FAIL"} schema-aliases`,JSON.stringify(out)); if(!good) failed++;
} catch(e){console.log("FAIL schema-aliases threw",e);failed++;}

const defaultDesc={inputSchema:{type:"object",properties:{mode:{type:"string",default:"safe"}}}};
try {
  const out=DPP_SAFE_JSON_PARSE_1140('{}',"generic_default",defaultDesc);
  const good=out.mode==="safe";
  console.log(`${good?"PASS":"FAIL"} schema-default`,JSON.stringify(out)); if(!good) failed++;
} catch(e){console.log("FAIL schema-default threw",e);failed++;}

const noGuessDesc={inputSchema:{type:"object",properties:{cmd:{type:"string"}}}};
try {
  const out=DPP_SAFE_JSON_PARSE_1140('{"cmd":"echo"}',"custom_cmd",noGuessDesc);
  const good=out.cmd==="echo" && !("command" in out);
  console.log(`${good?"PASS":"FAIL"} schema-no-guess`,JSON.stringify(out)); if(!good) failed++;
} catch(e){console.log("FAIL schema-no-guess threw",e);failed++;}

if(failed) process.exit(1);
console.log(`ALL_PASS ${cases.length+6}`);
