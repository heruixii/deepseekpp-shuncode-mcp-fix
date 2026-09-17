#!/usr/bin/env node
/**
 * Fix 3.3.10.34 behaviour suite -- run_command status must be read from the
 * RUN_COMMAND header only, and a manual message that supersedes a running
 * Agent must be visible (reason text + turn_diag record).
 *
 * Field evidence 2026-09-16 23:15-23:17: three `status: completed / exit_code: 0`
 * runs were reported as run_command_failed because the command output (a grep
 * over the extension's own sources) contained `status=failed`.
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

console.log("Fix 3.3.10.34 run_command status / manual supersede suite");
console.log("=========================================================");

console.log("\n[1] build integrity");
ok("manifest version is 1.14.0.40", manifest.version === "1.14.0.40", manifest.version);
ok("manifest version_name is Fix 3.3.10.35",
   manifest.version_name === "1.14.0 ShunCode MCP Fix 3.3.10.35", manifest.version_name);
ok("header parser present", src.indexOf("function DPP_RUN_COMMAND_STATUS_331034(") !== -1);
ok("normalizer uses header parser", src.indexOf("DPPStatus331034=DPP_RUN_COMMAND_STATUS_331034(n)") !== -1);
ok("r1 accepts a reason", src.indexOf("function r1(DPPReason331034){") !== -1);
ok("manual supersede records turn_diag", src.indexOf("decision:`manual_supersede_331034`") !== -1);
ok("manual supersede passes localized reason", src.indexOf("return r1(DPP_MANUAL_SUPERSEDE_TEXT_331034(") !== -1);
ok("pagehide path still plain r1()", src.indexOf("window.addEventListener(`pagehide`,()=>{t1()&&r1()})") !== -1);
ok(".33 core-tool floor still present", fs.readFileSync(path.join(ROOT, "background.js"), "utf8").indexOf("DPP_CORE_TOOL_FLOOR_331033") !== -1);
ok(".33 zero-tool gate still present", src.indexOf("q(`zero_tool_complete_331033`,!1)") !== -1);

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

console.log("\n[2] header-only status parsing");
{
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext(grabFn("DPP_RUN_COMMAND_HEADER_331034") + grabFn("DPP_RUN_COMMAND_STATUS_331034"), ctx);
  const st = ctx.DPP_RUN_COMMAND_STATUS_331034;
  const hdr = (status, code) => "=== RUN_COMMAND BEGIN ===\ncommand_id: cmd_x\nexecution: pty\ncommand: \"grep -n status content.js\"\nstatus: " + status + "\nexit_code: " + code + "\npipeline_exit_codes: []\ncwd: \"/d\"\n";
  const poison = "--- OUTPUT BEGIN ---\ncontent.js:449: if(status===`failed`) status=failed exit_code=1 \"exit_code\": 137\n--- OUTPUT END ---\n";
  let r = st(hdr("completed", 0) + poison);
  ok("completed/0 with poisoned output => not failed", r.failed === false && r.exitCode === 0 && r.source === "header", JSON.stringify(r));
  r = st(hdr("failed", 2) + poison);
  ok("failed/2 header => failed exit 2", r.failed === true && r.exitCode === 2, JSON.stringify(r));
  r = st(hdr("completed", 127) + "--- OUTPUT BEGIN ---\nbash: foo: command not found\n");
  ok("completed/127 => exit 127", r.failed === false && r.exitCode === 127, JSON.stringify(r));
  // JSON-escaped form (detail is JSON.stringify'd MCP content)
  const esc = JSON.stringify([{ type: "text", text: hdr("completed", 0) + poison }]);
  r = st(esc);
  ok("JSON-escaped header still parsed", r.failed === false && r.exitCode === 0 && r.source === "header", JSON.stringify(r));
  r = st("no marker here status=failed exit_code=3");
  ok("no marker => legacy fulltext scan", r.failed === true && r.exitCode === 3 && r.source === "fulltext", JSON.stringify(r));
  r = st("");
  ok("empty => neutral", r.failed === false && r.exitCode === null, JSON.stringify(r));
}

console.log("\n[3] normalizer end-to-end");
{
  const ctx = {};
  vm.createContext(ctx);
  let code = grabFn("DPP_RUN_COMMAND_HEADER_331034") + grabFn("DPP_RUN_COMMAND_STATUS_331034") +
             grabFn("DPP_RUN_COMMAND_TEXT_33108") + grabFn("DPP_NORMALIZE_RUN_COMMAND_RESULT_33108") +
             grabFn("DPP_PTY_EMPTY_33") + grabFn("DPP_ANNOTATE_EMPTY_PTY_331028") + grabFn("DPP_TOOL_NAME_33");
  vm.runInContext(code, ctx);
  const norm = ctx.DPP_NORMALIZE_RUN_COMMAND_RESULT_33108;
  const mk = (status, code, out, bytes) => ({ ok: true, summary: "MCP 工具已执行",
    detail: JSON.stringify([{ type: "text", text: "=== RUN_COMMAND BEGIN ===\nexecution: pty\ncommand: \"x\"\nstatus: " + status + "\nexit_code: " + code + "\ntotal_output_bytes: " + bytes + "\n--- OUTPUT BEGIN ---\n" + out + "\n--- OUTPUT END ---" }]) });
  let r = norm("run_command", mk("completed", 0, "content.js:1: status=failed exit_code=9", 40));
  ok("field case: completed/0 + poisoned grep output stays ok", r.ok === true && !r.error, JSON.stringify(r).slice(0, 200));
  r = norm("run_command", mk("failed", 2, "grep: bad", 10));
  ok("real failure still flagged", r.ok === false && r.error.code === "run_command_failed" && r.error.details.exitCode === 2);
  r = norm("run_command", mk("completed", 1, "", 0));
  ok("exit 1 flagged", r.ok === false && r.error.details.exitCode === 1);
  r = norm("read_files", { ok: true, summary: "status=failed" });
  ok("non-run_command untouched", r.ok === true);
  r = norm("run_command", mk("completed", 0, "", 0));
  ok("empty PTY success still annotated by .28", r.ok === true && r.dppEmptyPtySuccess === true, JSON.stringify(r).slice(0, 160));
}

console.log("\n[4] manual supersede text");
{
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext(grabFn("DPP_MANUAL_SUPERSEDE_TEXT_331034"), ctx);
  const f = ctx.DPP_MANUAL_SUPERSEDE_TEXT_331034;
  ok("zh text mentions 继续", /继续/.test(f("zh-CN")) && /新消息/.test(f("zh-CN")));
  ok("en text mentions continue", /continue/.test(f("en")) && /new message/.test(f("en")));
  ok("unknown locale falls back to en", /continue/.test(f("")));
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
