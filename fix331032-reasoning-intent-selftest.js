#!/usr/bin/env node
/**
 * Fix 3.3.10.32 behaviour suite -- an announced-but-unemitted tool call must
 * never be promoted into a terminal answer, and the loop-end reload must not
 * race the batched diagnostics.
 *
 * Regression guarded: fix331025 / fix331027 pin the opposite-direction rule
 * ("a visible concrete final takes precedence over stale reasoning"). Both
 * rules must hold simultaneously, so this suite asserts both directions.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = process.env.DPP_ROOT || path.resolve(__dirname);
const CONTENT = path.join(ROOT, "content-scripts", "content.js");
const MANIFEST = path.join(ROOT, "manifest.json");

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  PASS  " + name); }
  else { fail++; console.log("  FAIL  " + name + (extra !== undefined ? "  -> " + extra : "")); }
}

const src = fs.readFileSync(CONTENT, "utf8");
const manifest = JSON.parse(fs.readFileSync(MANIFEST, "utf8"));

console.log("Fix 3.3.10.32 reasoning-intent / diag-flush suite");
console.log("=================================================");

// ---- group 1: build integrity ---------------------------------------------
console.log("\n[1] build integrity");
ok("manifest version is 1.14.0.41", manifest.version === "1.14.0.41", manifest.version);
ok("manifest version_name is Fix 3.3.10.36",
   manifest.version_name === "1.14.0 ShunCode MCP Fix 3.3.10.36", manifest.version_name);
ok("safe-final reasoning guard present",
   src.indexOf("if(!Sz(i)&&DPP_TOOL_INTENT_TEXT_331021(String(r??``))&&!(Array.isArray(t)&&t.some(e=>e?.result?.ok===!0)))return null;") !== -1);
ok("diag flush-all returns a promise",
   src.indexOf("let e=[];for(let t of DPP_DIAG_BATCH_STATE_331022.keys())") !== -1);
ok("reload awaits the diagnostics flush",
   src.indexOf("if(u){try{await DPP_DIAG_BATCH_FLUSH_ALL_331022()}catch(e){}_1()}") !== -1);
ok("bare unguarded reload call is gone", src.indexOf("}u&&_1()") === -1);
ok("reload itself is retained (per release decision)",
   src.indexOf("function _1(){window.location.reload()}") !== -1);

// ---- group 2: the promotion decision --------------------------------------
console.log("\n[2] terminal promotion");
function extract(startAnchor, endAnchor) {
  const a = src.indexOf(startAnchor);
  const b = src.indexOf(endAnchor, a);
  if (a < 0 || b < 0) throw new Error("anchor not found: " + startAnchor);
  return src.slice(a, b);
}
// Resolve the dependency closure of the promotion helper by iterative eval.
function grabFn(n) {
  const i = src.indexOf("function " + n + "(");
  if (i < 0) return null;
  let d = 0, k = src.indexOf("{", i);
  for (; k < src.length; k++) {
    const c = src[k];
    if (c === "{") d++;
    else if (c === "}") { d--; if (d === 0) { k++; break; } }
  }
  return src.slice(i, k) + "\n";
}
function grabVar(v) {
  const m = new RegExp("(?:var |,|;)" + v + "=").exec(src);
  if (!m) return null;
  let i = src.indexOf("=", m.index) + 1, depth = 0, inre = false, k = i;
  for (; k < src.length; k++) {
    const c = src[k];
    if (c === "/" && !inre && /[=,(:[]/.test(src[k - 1] || "")) { inre = true; continue; }
    if (inre) { if (c === "\\") { k++; continue; } if (c === "/") inre = false; continue; }
    if (c === "`") { k++; while (k < src.length && src[k] !== "`") { if (src[k] === "\\") k++; k++; } continue; }
    if ("([{".indexOf(c) >= 0) depth++;
    else if (")]}".indexOf(c) >= 0) depth--;
    else if ((c === "," || c === ";") && depth === 0) break;
  }
  return "var " + v + "=" + src.slice(i, k) + ";\n";
}

const TEXT_STUB = "\u7ee7\u7eed\u3002\u8fd0\u884c\u8bca\u65ad\u811a\u672c\u3002";
const REASON_INTENT = "But I should try to give a factual answer. Let me run one more tool call to get the diagnostic.";
const TEXT_FINAL = "The task is complete and the file was verified.";

let code = "", have = {};
function add(n) {
  if (have[n]) return true;
  const f = grabFn(n) || grabVar(n);
  if (!f) return false;
  have[n] = 1; code += f; return true;
}
["DPP_SAFE_FINAL_CANDIDATE_331021", "DPP_TOOL_INTENT_331021",
 "DPP_TOOL_INTENT_TEXT_331021", "Sz"].forEach(add);

let out = null;
for (let it = 0; it < 120; it++) {
  const ctx = { String, RegExp, Number, Array, Object, JSON, Math, Set, Boolean };
  vm.createContext(ctx);
  const probe = code + ";globalThis.__r={};" +
    "__r.stubPromoted=DPP_SAFE_FINAL_CANDIDATE_331021('task',[]," + JSON.stringify(TEXT_STUB) + "," + JSON.stringify(REASON_INTENT) + ")!==null;" +
    "__r.finalPromoted=DPP_SAFE_FINAL_CANDIDATE_331021('task',[{result:{ok:true}}]," + JSON.stringify(TEXT_FINAL) + "," + JSON.stringify(REASON_INTENT) + ")!==null;" +
    "__r.stubWithSuccessPromoted=DPP_SAFE_FINAL_CANDIDATE_331021('task',[{result:{ok:true}}]," + JSON.stringify(TEXT_STUB) + "," + JSON.stringify(REASON_INTENT) + ")!==null;" +
    "__r.precedence=DPP_TOOL_INTENT_331021(" + JSON.stringify(TEXT_FINAL) + "," + JSON.stringify(REASON_INTENT) + ");" +
    "__r.reasoningSeen=DPP_TOOL_INTENT_TEXT_331021(" + JSON.stringify(REASON_INTENT) + ");__r;";
  try { out = vm.runInContext(probe, ctx); break; }
  catch (e) {
    const m = String(e.message).match(/^(\w+) is not defined$/);
    if (m && add(m[1])) continue;
    console.log("  FAIL  could not evaluate promotion helper -> " + e.message);
    fail++; break;
  }
}
if (out) {
  ok("reasoning channel does expose the tool intent", out.reasoningSeen === true);
  ok("stub text + tool-intent reasoning is NOT promoted to final", out.stubPromoted === false);
  ok("genuine final after successful tool work IS still promoted", out.finalPromoted === true);
  ok("a successful execution lets even a terse text stand as final",
     out.stubWithSuccessPromoted === true);
  ok("visible concrete final still takes precedence (.25/.27 rule intact)",
     out.precedence === false);
}

console.log("\n=================================================");
console.log("PASS " + pass + "  FAIL " + fail);
process.exit(fail === 0 ? 0 : 1);
