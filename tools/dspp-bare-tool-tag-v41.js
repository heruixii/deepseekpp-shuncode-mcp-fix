/* DPP_BARE_TOOL_TAG_V41_BEGIN
 * Fix 3.3.10.41 -- resolve a bare ShunCode tool tag to its real registered name.
 *
 * Context: MCP tools register as `mcp_t_<serverId>_<base>`. The model learned the
 * full name for run_command but kept emitting a bare <read_image>. The .33 detector
 * flagged it as unregistered and the steering text told it to mcp_discover -- while
 * the tool was already in the catalogue (tools=24). Combined with the .36 visual
 * prompts naming `read_image` bare, the instructions contradicted each other and the
 * run burned its 3 tool-intent nudges and stopped with unexecuted_work_limit_331036.
 *
 * These helpers only compute a hint string. They never execute a tool and never
 * relax any authorization check.
 */
function DPP_RESOLVE_REGISTERED_TAG_V41(base, names) {
  const b = String(base == null ? '' : base).toLowerCase();
  if (!b) return { resolution: 'discover_hint', name: '' };
  let list = [];
  if (names && typeof names.forEach === 'function') names.forEach((v, k) => { list.push(typeof k === 'string' ? k : v); });
  else if (Array.isArray(names)) list = names.slice();
  const suffix = '_' + b;
  const hits = [];
  for (const raw of list) {
    const n = String(raw == null ? '' : raw);
    const low = n.toLowerCase();
    // Prefix-anchored, suffix-anchored. Server-id segment count is deliberately NOT
    // hard-coded: a different MCP server would otherwise silently fall back.
    if (low.length > suffix.length && low.indexOf('mcp_t_') === 0 && low.slice(-suffix.length) === suffix) {
      if (hits.indexOf(n) === -1) hits.push(n);
    }
  }
  if (hits.length === 1) return { resolution: 'exact_hint', name: hits[0] };
  if (hits.length > 1) return { resolution: 'ambiguous', name: '' };
  return { resolution: 'discover_hint', name: '' };
}

function DPP_EXACT_TAG_STEERING_V41(locale, bare, full) {
  return String(locale == null ? '' : locale).toLowerCase().startsWith('zh')
    ? '[Fix 3.3.10.41 \u5de5\u5177\u6807\u7b7e\u7ea0\u6b63] \u4f60\u4e0a\u4e00\u8f6e\u8f93\u51fa\u7684 <' + bare + '> \u4e0d\u662f\u53ef\u7528\u6807\u7b7e\uff0c\u5df2\u88ab\u5ffd\u7565\u3001\u672a\u6267\u884c\u3002\u8be5\u5de5\u5177\u5f53\u524d\u5df2\u6ce8\u518c\u4e3a <' + full + '>\uff0c\u5c31\u5728\u5f53\u524d\u5de5\u5177\u76ee\u5f55\u91cc\u3002\u4e0b\u4e00\u8f6e\u8bf7\u76f4\u63a5\u7528 <' + full + '> \u8c03\u7528\uff08\u53c2\u6570\u7ed3\u6784\u4e0d\u53d8\uff09\uff0c\u4e0d\u8981\u518d\u7528 mcp_discover\uff0c\u4e5f\u4e0d\u8981\u518d\u8f93\u51fa <' + bare + '>\u3002'
    : '[Fix 3.3.10.41 tool tag correction] Your previous turn emitted <' + bare + '>, which is not an available tag; it was ignored and nothing executed. That tool is already registered as <' + full + '> and is present in the current catalogue. In the very next turn call <' + full + '> directly with the same arguments. Do not call mcp_discover, and do not emit <' + bare + '> again.';
}

function DPP_VISUAL_TOOL_NAME_V41(names) {
  const r = DPP_RESOLVE_REGISTERED_TAG_V41('read_image', names);
  return r.resolution === 'exact_hint' ? r.name : '';
}

function DPP_VISUAL_NAME_PHRASE_V41(full) {
  const f = String(full == null ? '' : full);
  return f ? '`' + f + '` (read_image)' : 'read_image';
}
/* DPP_BARE_TOOL_TAG_V41_END */
