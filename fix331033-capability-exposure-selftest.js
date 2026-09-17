#!/usr/bin/env node
/**
 * Fix 3.3.10.33 behaviour suite -- capability exposure, handle lifecycle,
 * unregistered tool tags and zero-tool completion.
 *
 * Field evidence (2026-09-16 20:05-20:14, session c0ba574e): run_command was
 * never in the adaptive direct set, so <run_command> markup was silently
 * dropped; aliases outlived their consumed handles; <task_complete> with
 * zero tools was accepted.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = process.env.DPP_ROOT || path.resolve(__dirname);
const CONTENT = path.join(ROOT, "content-scripts", "content.js");
const BACKGROUND = path.join(ROOT, "background.js");
const MANIFEST = path.join(ROOT, "manifest.json");

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  PASS  " + name); }
  else { fail++; console.log("  FAIL  " + name + (extra !== undefined ? "  -> " + extra : "")); }
}

const src = fs.readFileSync(CONTENT, "utf8");
const bg = fs.readFileSync(BACKGROUND, "utf8");
const manifest = JSON.parse(fs.readFileSync(MANIFEST, "utf8"));

console.log("Fix 3.3.10.33 capability-exposure suite");
console.log("=======================================");

// ---- [1] build integrity ----------------------------------------------------
console.log("\n[1] build integrity");
ok("manifest version is 1.14.0.40", manifest.version === "1.14.0.40", manifest.version);
ok("manifest version_name is Fix 3.3.10.35",
   manifest.version_name === "1.14.0 ShunCode MCP Fix 3.3.10.35", manifest.version_name);
ok("background has core-tool rank floor", bg.indexOf("function DPP_CORE_TOOL_FLOOR_331033(") !== -1);
ok("background Cd() applies the floor", bg.indexOf("s=(r?1e4:0)+DPP_CORE_TOOL_FLOOR_331033(e);") !== -1);
ok("content has handle-code set", src.indexOf("var DPP_HANDLE_ERROR_CODES_331033=") !== -1);
ok("content has unregistered-tag detector", src.indexOf("function DPP_UNREGISTERED_TOOL_TAG_331033(") !== -1);
ok("content has zero-tool complete block", src.indexOf("function DPP_ZERO_TOOL_COMPLETE_BLOCK_331033(") !== -1);
ok("alias retired on any mcp_invoke completion", src.indexOf("DPPRemoveAlias331019(e,t)}}catch{}})(),DPPInstallAliases331019(DPPExecution)") !== -1);
ok("decision path records unregistered_tool_tag_331033", src.indexOf("decision:`unregistered_tool_tag_331033`") !== -1);
ok("decision path has zero_tool_complete_331033", src.indexOf("q(`zero_tool_complete_331033`,!1)") !== -1);
ok("transport steering receives the code", src.indexOf("DPP_TRANSPORT_STEERING_331031(d,y.transportFailuresInStep,y.lastTransportCode)") !== -1);
ok(".31 gate still intact", src.indexOf("q(`tool_transport_failure_limit_331031`,!0)") !== -1);
ok(".32 safe-final guard still intact",
   src.indexOf("if(!Sz(i)&&DPP_TOOL_INTENT_TEXT_331021(String(r??``))&&!(Array.isArray(t)&&t.some(e=>e?.result?.ok===!0)))return null;") !== -1);

// ---- helpers: extract functions from the bundle ---------------------------
function grabFn(n) {
  const i = src.indexOf("function " + n + "(");
  if (i < 0) return null;
  let d = 0, k = src.indexOf("{", i);
  for (; k < src.length; k++) {
    const c = src[k];
    if (c === "{") d++;
    else if (c === "}") { d--; if (d === 0) return src.slice(i, k + 1); }
  }
  return null;
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
function grabFnFrom(text, n) {
  const i = text.indexOf("function " + n + "(");
  if (i < 0) return null;
  let d = 0, k = text.indexOf("{", i);
  for (; k < text.length; k++) {
    const c = text[k];
    if (c === "{") d++;
    else if (c === "}") { d--; if (d === 0) return text.slice(i, k + 1); }
  }
  return null;
}

// ---- [2] adaptive picker: core tools survive the cut -------------------------
console.log("\n[2] adaptive exposure rank floor");
{
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext(grabFnFrom(bg, "DPP_CORE_TOOL_FLOOR_331033"), ctx);
  const f = ctx.DPP_CORE_TOOL_FLOOR_331033;
  ok("run_command (prefixed invocation name) gets 1600",
     f({ name: "run_command", invocationName: "mcp_t_9a351af5_0998_48c5_b6be_7f0d1ee53257_run_command" }) === 1600);
  ok("get_command_output gets 1000", f({ name: "get_command_output", invocationName: "mcp_x_get_command_output" }) === 1000);
  ok("apply_patch gets 700", f({ name: "apply_patch", invocationName: "mcp_x_apply_patch" }) === 700);
  ok("read_image gets 0", f({ name: "read_image", invocationName: "mcp_x_read_image" }) === 0);
  ok("unrelated tool gets 0", f({ name: "web_search", invocationName: "web_search" }) === 0);
  // Simulate the picker ordering with the real Cd/Td/Dd and an empty intent ("继续")
  const c2 = { globalThis: {} };
  vm.createContext(c2);
  vm.runInContext(grabFnFrom(bg, "DPP_CORE_TOOL_FLOOR_331033") + grabFnFrom(bg, "Cd") + grabFnFrom(bg, "Td") +
                  grabFnFrom(bg, "Dd") + grabFnFrom(bg, "Ed"), c2);
  const names = ["apply_patch", "find_files", "get_command_output", "read_image", "run_command", "search_files",
                 "list_directory", "read_files", "lsp", "get_diagnostics", "set_todos", "report_progress",
                 "send_command_input", "cancel_command", "update_plan"];
  const descs = names.map(n => ({ id: "mcp:s:" + n, name: n, invocationName: "mcp_t_s_" + n, title: n,
                                   description: "ShunCode " + n + " tool" }));
  const intent = c2.Td("继续");
  const words = c2.Dd(intent);
  const ranked = descs.map((d, i) => ({ d, i, s: c2.Cd(d, intent, words, false) }))
                      .sort((a, b) => b.s - a.s || c2.Ed(a.d.title, b.d.title) || a.i - b.i)
                      .slice(0, 5).map(x => x.d.name);
  ok("with intent '继续', top-5 contains run_command", ranked.includes("run_command"), ranked.join(","));
  ok("with intent '继续', top-5 contains get_command_output", ranked.includes("get_command_output"), ranked.join(","));
  ok("with intent '继续', top-5 contains read_files", ranked.includes("read_files"), ranked.join(","));
  ok("run_command ranks first", ranked[0] === "run_command", ranked.join(","));
}

// ---- [3] unregistered tool tag detector --------------------------------------
console.log("\n[3] unregistered tool tag");
{
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext(grabVar("DPP_SHUNCODE_TOOL_TAGS_331033") + grabFn("DPP_UNREGISTERED_TOOL_TAG_331033"), ctx);
  const f = ctx.DPP_UNREGISTERED_TOOL_TAG_331033;
  const registered = new Set(["mcp_discover", "mcp_invoke", "memory_save", "web_search",
                              "mcp_t_9a351af5_0998_48c5_b6be_7f0d1ee53257_apply_patch"]);
  ok("<run_command> raw body (not registered) is detected",
     f("检查 cv2。\n<run_command>\npython -c \"import cv2\"\n</run_command>", registered) === "run_command");
  ok("<run_command> JSON body is detected",
     f("<run_command>{\"command\":\"ls\",\"timeout_ms\":60000}</run_command>", registered) === "run_command");
  ok("prefixed mcp_t_ tag not registered is detected",
     f("<mcp_t_9a351af5_0998_48c5_b6be_7f0d1ee53257_run_command>ls</mcp_t_9a351af5_0998_48c5_b6be_7f0d1ee53257_run_command>", registered)
       === "mcp_t_9a351af5_0998_48c5_b6be_7f0d1ee53257_run_command");
  ok("registered prefixed tag is NOT flagged",
     f("<mcp_t_9a351af5_0998_48c5_b6be_7f0d1ee53257_apply_patch>*** Begin Patch</mcp_t_9a351af5_0998_48c5_b6be_7f0d1ee53257_apply_patch>", registered) === "");
  ok("registered mcp_discover is NOT flagged", f("<mcp_discover>{\"query\":\"x\"}</mcp_discover>", registered) === "");
  ok("plain prose is NOT flagged", f("方案 A 已完成，交付物已就位。任务结束。", registered) === "");
  ok("HTML-ish tags are NOT flagged", f("<div>hello</div> <b>x</b>", registered) === "");
  ok("unclosed tag is NOT flagged", f("<run_command>ls", registered) === "");
  ok("predicate form works", f("<run_command>ls</run_command>", n => n === "mcp_invoke") === "run_command");
  ok("empty text returns empty", f("", registered) === "");
}

// ---- [4] handle-lifecycle codes count as transport failures ----------------
console.log("\n[4] handle lifecycle codes");
{
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext(grabVar("DPP_TRANSPORT_ERROR_CODES_331031") + grabVar("DPP_HANDLE_ERROR_CODES_331033") +
                  grabFn("DPP_IS_TRANSPORT_FAILURE_331031") + grabFn("DPP_STEP_TRANSPORT_FAILURES_331031") +
                  grabFn("DPP_STEP_TRANSPORT_CODE_331033") + grabFn("DPP_TRANSPORT_STEERING_331031"), ctx);
  const exec = code => ({ name: "run_command", result: { ok: false, error: { code } } });
  ok("mcp_capability_handle_replayed is a transport failure",
     ctx.DPP_IS_TRANSPORT_FAILURE_331031(exec("mcp_capability_handle_replayed")) === true);
  ok("mcp_capability_handle_expired is a transport failure",
     ctx.DPP_IS_TRANSPORT_FAILURE_331031(exec("mcp_capability_handle_expired")) === true);
  ok("mcp_transport_timeout is a transport failure",
     ctx.DPP_IS_TRANSPORT_FAILURE_331031(exec("mcp_transport_timeout")) === true);
  ok("mcp_network_error still a transport failure",
     ctx.DPP_IS_TRANSPORT_FAILURE_331031(exec("mcp_network_error")) === true);
  ok("tool_call_json_invalid is NOT a transport failure",
     ctx.DPP_IS_TRANSPORT_FAILURE_331031(exec("tool_call_json_invalid")) === false);
  ok("ok=true is never a transport failure",
     ctx.DPP_IS_TRANSPORT_FAILURE_331031({ result: { ok: true } }) === false);
  ok("step code extraction returns the failing code",
     ctx.DPP_STEP_TRANSPORT_CODE_331033([{ result: { ok: true } }, exec("mcp_capability_handle_replayed")]) === "mcp_capability_handle_replayed");
  const zh = ctx.DPP_TRANSPORT_STEERING_331031("zh-CN", 1, "mcp_capability_handle_replayed");
  ok("zh steering for handle code mentions mcp_discover", /mcp_discover/.test(zh) && /3\.3\.10\.33/.test(zh));
  const en = ctx.DPP_TRANSPORT_STEERING_331031("en", 2, "mcp_capability_handle_expired");
  ok("en steering for handle code is the handle variant", /single-use/.test(en) && /attempt 2/.test(en));
  const net = ctx.DPP_TRANSPORT_STEERING_331031("en", 1, "mcp_network_error");
  ok("network code keeps the .31 steering", /Fix 3\.3\.10\.31 transport failure/.test(net));
  const legacy = ctx.DPP_TRANSPORT_STEERING_331031("en", 1);
  ok("two-arg legacy call still works", /Fix 3\.3\.10\.31 transport failure/.test(legacy));
}

// ---- [5] zero-tool completion block ----------------------------------------
console.log("\n[5] zero-tool completion");
{
  // DPP_ZERO_TOOL_COMPLETE_BLOCK_331033 depends on DPP_TOOL_INTENT_TEXT_331021 and its closure.
  const ctx = {};
  vm.createContext(ctx);
  const deps = ["jz", "Mz", "DPP_MIDSTEP_CUE_31", "DPP_DIRECT_CONTINUE_CUE_331027", "DPP_TOOL_INTENT_TEXT_331021",
                "DPP_ZERO_TOOL_COMPLETE_BLOCK_331033"];
  let code = "";
  for (const d of deps) { const f = grabFn(d); if (f) code += f + "\n"; }
  // resolve the dependency closure lazily via a probe call (same as the .32 suite)
  const probe = code => code + "\nDPP_ZERO_TOOL_COMPLETE_BLOCK_331033([],\"Let me run one more tool call to get the diagnostic.\",\"x\");" +
                        "DPP_ZERO_TOOL_COMPLETE_BLOCK_331033([],\"\",\"继续直到任务完成\");";
  for (let round = 0; round < 24; round++) {
    try { vm.runInContext(probe(code), ctx); break; }
    catch (e) {
      const m = /(\w+) is not defined/.exec(String(e.message));
      if (!m) throw e;
      const f = grabFn(m[1]) || grabVar(m[1]);
      if (!f) throw new Error("cannot resolve " + m[1]);
      code = f + "\n" + code;
    }
  }
  const f = ctx.DPP_ZERO_TOOL_COMPLETE_BLOCK_331033;
  const reasoningWithIntent = "The diagnostic keeps failing to parse. Let me run one more tool call to get the diagnostic.";
  ok("zero tools + '继续' prompt => blocked", f([], "", "继续") !== "");
  ok("zero tools + '继续直到任务完成' => blocked", f([], "", "继续直到任务完成") !== "");
  ok("zero tools + reasoning tool intent => blocked", f([], reasoningWithIntent, "为什么最佳版还有污渍") !== "");
  ok("zero tools + plain question + no intent => allowed", f([], "This is a knowledge question.", "什么是双边滤波") === "");
  ok("one successful tool => allowed even for '继续'", f([{ result: { ok: true } }], reasoningWithIntent, "继续") === "");
  ok("one failed tool => allowed (handled by .31 gate instead)", f([{ result: { ok: false } }], "", "继续") === "");
  ok("block message names task_complete", /task_complete/.test(f([], "", "continue")));
}

// ---- [6] real field texts from 2026-09-16 ----------------------------------
console.log("\n[6] field reproduction");
{
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext(grabVar("DPP_SHUNCODE_TOOL_TAGS_331033") + grabFn("DPP_UNREGISTERED_TOOL_TAG_331033"), ctx);
  const reg = new Set(["mcp_discover", "mcp_invoke", "mcp_t_9a351af5_0998_48c5_b6be_7f0d1ee53257_apply_patch",
                       "mcp_t_9a351af5_0998_48c5_b6be_7f0d1ee53257_find_files",
                       "mcp_t_9a351af5_0998_48c5_b6be_7f0d1ee53257_get_command_output"]);
  // 1eeb8389: 347 raw chars, 39 visible. The stripped remainder was a run_command block.
  const t1 = "没有 cv2 就装 opencv（双边滤波需要它）。一步到位：检查+按需安装。\n<run_command>\nPY=/c/Users/29066/AppData/Local/Programs/Python/Python311/python.exe; \"$PY\" -c \"import importlib.util as u; print(bool(u.find_spec('cv2')))\"\n</run_command>";
  ok("loop 1eeb8389 text flags run_command", ctx.DPP_UNREGISTERED_TOOL_TAG_331033(t1, reg) === "run_command");
  // 61ad9dfd step2: 196 raw / 0 visible, JSON-form run_command
  const t2 = "<run_command>\n{\"command\": \"python -c \\\"import cv2; print(cv2.__version__)\\\"\", \"timeout_ms\": 60000}\n</run_command>";
  ok("loop 61ad9dfd text flags run_command", ctx.DPP_UNREGISTERED_TOOL_TAG_331033(t2, reg) === "run_command");
  // 2c7896c5 step 16 final: plain prose, must not flag
  ok("loop 2c7896c5 final prose not flagged",
     ctx.DPP_UNREGISTERED_TOOL_TAG_331033("方案 A 已完成，交付物已就位、记忆与笔记均已落库。任务结束。", reg) === "");
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
