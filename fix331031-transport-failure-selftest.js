#!/usr/bin/env node
/**
 * Fix 3.3.10.31 behaviour suite — MCP transport failure must never be mistaken
 * for task completion, and a mislabelled `complete` trace must never block resume.
 *
 * Runs against the built content.js by extracting the patched helpers, plus
 * pure-logic reimplementations of the two decision points the patch changes.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const ROOT = process.env.DPP_ROOT || path.resolve(__dirname);
const CONTENT = path.join(ROOT, "content-scripts", "content.js");
const MANIFEST = path.join(ROOT, "manifest.json");

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  PASS  " + name); }
  else { fail++; console.log("  FAIL  " + name + (extra ? "  -> " + extra : "")); }
}

const src = fs.readFileSync(CONTENT, "utf8");
const manifest = JSON.parse(fs.readFileSync(MANIFEST, "utf8"));

console.log("Fix 3.3.10.31 transport-failure suite");
console.log("=====================================");

// ---- group 1: build integrity -------------------------------------------
console.log("\n[1] build integrity");
ok("manifest version is 1.14.0.53", manifest.version === "1.14.0.53", manifest.version);
ok("transport code set present", src.indexOf("DPP_TRANSPORT_ERROR_CODES_331031") >= 0);
ok("transport predicate present", src.indexOf("DPP_IS_TRANSPORT_FAILURE_331031") >= 0);
ok("step counter present", src.indexOf("DPP_STEP_TRANSPORT_FAILURES_331031") >= 0);
ok("real-success predicate present", src.indexOf("DPP_TRACE_HAS_REAL_SUCCESS_331031") >= 0);
ok("retry cap present", src.indexOf("DPP_TRANSPORT_RETRY_MAX_331031") >= 0);
ok("steer decision emitted", src.indexOf("tool_transport_failure_331031") >= 0);
ok("limit decision emitted", src.indexOf("tool_transport_failure_limit_331031") >= 0);
ok("state carries transportFailuresInStep", src.indexOf("transportFailuresInStep:0") >= 0);
ok("state carries lastStepHadTransportFailure", src.indexOf("lastStepHadTransportFailure:!1") >= 0);
ok("watermark now gated by real success",
   src.indexOf("if(t?.chatSessionId!==e.chatSessionId||t?.status!==`complete`)return!1;") >= 0);
ok("watermark filter is self-contained (no external helper call)",
   /let a=Math\.max\(0,\.\.\.t\.filter\(t=>\{/.test(src));
ok("transport check precedes the final branch",
   src.indexOf("if(y.lastStepHadTransportFailure){") <
   src.indexOf("return o?q(k?`tool_intent_needed`:`continuation_needed`,!1):(ie=n,q(`final`,!0))"));
ok("limit path sets oe (routes to AGENT_LOOP_ERROR)",
   /tool_transport_failure_limit_331031/.test(src) && /oe=!0,se=DPP_TRANSPORT_LIMIT_331031/.test(src));
ok(".30 DOM fence still present (no regression)",
   fs.readFileSync(path.join(ROOT, "content-scripts", "main-world.js"), "utf8")
     .indexOf("DPP_DOM_FENCE_331030") >= 0);

// ---- extract the real helpers from the bundle ---------------------------
function extract(name) {
  const i = src.indexOf("function " + name);
  if (i < 0) throw new Error("helper not found: " + name);
  // walk braces from the first '{' after the signature
  let j = src.indexOf("{", i), depth = 0, k = j;
  for (; k < src.length; k++) {
    if (src[k] === "{") depth++;
    else if (src[k] === "}") { depth--; if (depth === 0) { k++; break; } }
  }
  return src.slice(i, k);
}

const sandbox = {};
const helperSrc = [
  "var DPP_TRANSPORT_ERROR_CODES_331031=new Set([`mcp_network_error`,`mcp_timeout`,`mcp_unauthorized`,`mcp_server_error`,`capability_expired`,`capability_not_found`,`bridge_unavailable`]);",
  extract("DPP_IS_TRANSPORT_FAILURE_331031"),
  extract("DPP_STEP_TRANSPORT_FAILURES_331031"),
  extract("DPP_TRACE_HAS_REAL_SUCCESS_331031"),
  "module.exports={DPP_IS_TRANSPORT_FAILURE_331031,DPP_STEP_TRANSPORT_FAILURES_331031,DPP_TRACE_HAS_REAL_SUCCESS_331031};"
].join("\n");
const mod = { exports: {} };
new Function("module", "exports", helperSrc)(mod, mod.exports);
const H = mod.exports;

const netFail = { name: "run_command", result: { ok: false, error: { code: "mcp_network_error", message: "Cannot reach MCP server" } } };
const timeoutFail = { name: "run_command", ok: false, result: { ok: false, error: { code: "mcp_timeout" } } };
const logicFail = { name: "run_command", result: { ok: false, error: { code: "command_failed", message: "exit 1" } } };
const good = { name: "read_files", result: { ok: true, summary: "read 3 files" } };

// ---- group 2: transport predicate ---------------------------------------
console.log("\n[2] transport-failure predicate");
ok("mcp_network_error is transport failure", H.DPP_IS_TRANSPORT_FAILURE_331031(netFail) === true);
ok("mcp_timeout is transport failure", H.DPP_IS_TRANSPORT_FAILURE_331031(timeoutFail) === true);
ok("ordinary command failure is NOT transport", H.DPP_IS_TRANSPORT_FAILURE_331031(logicFail) === false);
ok("successful call is NOT transport failure", H.DPP_IS_TRANSPORT_FAILURE_331031(good) === false);
ok("null is safe", H.DPP_IS_TRANSPORT_FAILURE_331031(null) === false);
ok("missing result is safe", H.DPP_IS_TRANSPORT_FAILURE_331031({ name: "x" }) === false);
ok("non-object error is safe", H.DPP_IS_TRANSPORT_FAILURE_331031({ result: { ok: false, error: "boom" } }) === false);
ok("counts only transport failures",
   H.DPP_STEP_TRANSPORT_FAILURES_331031([netFail, logicFail, good, timeoutFail]) === 2);
ok("empty step counts zero", H.DPP_STEP_TRANSPORT_FAILURES_331031([]) === 0);
ok("non-array is safe", H.DPP_STEP_TRANSPORT_FAILURES_331031(undefined) === 0);

// ---- group 3: real-success predicate (resume watermark) -----------------
console.log("\n[3] genuine-success predicate for the resume watermark");
const badTrace = { status: "complete", initialExecutions: [{ name: "mcp_discover", result: { ok: true } }],
  steps: [{ toolExecutions: [netFail] }, { toolExecutions: [netFail] }, { toolExecutions: [] }] };
const theRealIncident = { status: "complete", initialExecutions: [],
  steps: [{ toolExecutions: [{ name: "mcp_invoke", result: { ok: false, error: { code: "mcp_network_error" } } }] },
          { toolExecutions: [netFail] }, { toolExecutions: [] }] };
const goodTrace = { status: "complete", initialExecutions: [], steps: [{ toolExecutions: [good] }] };
ok("all-failed run has no genuine success", H.DPP_TRACE_HAS_REAL_SUCCESS_331031(theRealIncident) === false);
ok("successful run counts as genuine", H.DPP_TRACE_HAS_REAL_SUCCESS_331031(goodTrace) === true);
ok("successful initialExecution counts", H.DPP_TRACE_HAS_REAL_SUCCESS_331031(badTrace) === true);
ok("empty trace is not a success", H.DPP_TRACE_HAS_REAL_SUCCESS_331031({ steps: [] }) === false);
ok("null trace is safe", H.DPP_TRACE_HAS_REAL_SUCCESS_331031(null) === false);

// ---- group 4: decision logic (mirrors the patched branch) ---------------
console.log("\n[4] turn decision under transport failure");
const RETRY_MAX = 3;
function decide(state, hasToolCall, needsContinuation) {
  if (hasToolCall) return "tool_call";
  if (state.lastStepHadTransportFailure) {
    if (state.transportFailuresInStep >= RETRY_MAX) return "tool_transport_failure_limit_331031";
    return "tool_transport_failure_331031";
  }
  return needsContinuation ? "continuation_needed" : "final";
}
function foldStep(state, execs) {
  state.lastStepHadTransportFailure = H.DPP_STEP_TRANSPORT_FAILURES_331031(execs) > 0;
  if (state.lastStepHadTransportFailure) state.transportFailuresInStep += 1;
  else state.transportFailuresInStep = 0;
  return state;
}
let st = { transportFailuresInStep: 0, lastStepHadTransportFailure: false };

foldStep(st, [netFail]);
ok("THE BUG: transport failure + no continuation cue no longer yields final",
   decide(st, false, false) === "tool_transport_failure_331031", decide(st, false, false));
foldStep(st, [netFail]);
ok("second failure still re-steers", decide(st, false, false) === "tool_transport_failure_331031");
foldStep(st, [netFail]);
ok("third failure hits the limit and stops as error",
   decide(st, false, false) === "tool_transport_failure_limit_331031");
ok("retry budget is exactly 3", st.transportFailuresInStep === 3);

let st2 = { transportFailuresInStep: 0, lastStepHadTransportFailure: false };
foldStep(st2, [netFail]);
foldStep(st2, [good]);
ok("a successful step resets the counter", st2.transportFailuresInStep === 0);
ok("after recovery a real finish is still allowed", decide(st2, false, false) === "final");

let st3 = { transportFailuresInStep: 0, lastStepHadTransportFailure: false };
foldStep(st3, [logicFail]);
ok("ordinary tool failure still allows final (not our concern)",
   decide(st3, false, false) === "final");
ok("continuation cue still wins normally", decide(st3, false, true) === "continuation_needed");
foldStep(st3, [netFail]);
ok("a real tool call always takes priority", decide(st3, true, false) === "tool_call");

// ---- group 5: end-to-end resume gating ----------------------------------
console.log("\n[5] resume gateway no longer blocked");
function watermarkOld(traces, sid) {
  return Math.max(0, ...traces.filter(t => t.chatSessionId === sid && t.status === "complete")
    .map(t => Number(t.updatedAt || 0)));
}
function watermarkNew(traces, sid) {
  return Math.max(0, ...traces.filter(t => t.chatSessionId === sid && t.status === "complete" &&
    H.DPP_TRACE_HAS_REAL_SUCCESS_331031(t)).map(t => Number(t.updatedAt || 0)));
}
const SID = "c0ba574e";
const traces = [
  Object.assign({ chatSessionId: SID, updatedAt: 1000, status: "error" },
    { steps: [{ toolExecutions: [netFail] }] }),
  Object.assign({ chatSessionId: SID, updatedAt: 2000 }, theRealIncident),
];
ok("old watermark was raised by the mislabelled run", watermarkOld(traces, SID) === 2000);
ok("new watermark ignores the all-failed run", watermarkNew(traces, SID) === 0);
const resumableOld = traces.filter(t => (t.status === "error" || t.status === "stopping") &&
  t.updatedAt > watermarkOld(traces, SID));
const resumableNew = traces.filter(t => (t.status === "error" || t.status === "stopping") &&
  t.updatedAt > watermarkNew(traces, SID));
ok("before: nothing was resumable (the reported symptom)", resumableOld.length === 0);
ok("after: the interrupted run is resumable again", resumableNew.length === 1);
const legit = [{ chatSessionId: SID, updatedAt: 3000, status: "complete",
  steps: [{ toolExecutions: [good] }], initialExecutions: [] },
  { chatSessionId: SID, updatedAt: 1000, status: "error", steps: [{ toolExecutions: [netFail] }] }];
ok("a genuinely finished task still blocks pointless resume",
   legit.filter(t => t.status === "error" && t.updatedAt > watermarkNew(legit, SID)).length === 0);

console.log("\n=====================================");
console.log("PASS " + pass + "  FAIL " + fail);
process.exit(fail === 0 ? 0 : 1);
