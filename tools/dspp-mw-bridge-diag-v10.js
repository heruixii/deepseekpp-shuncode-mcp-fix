/* DPP_MW_BRIDGE_DIAG_V10_BEGIN - MAIN-world local diagnostics; written straight to page localStorage,
   never through the content bridge (so they survive a broken bridge). Fixed enums / booleans / small counts only. */
var DPP_MW_DIAG_KEY_V10 = 'dpp_mw_bridge_diag_v10';
var DPP_MW_DIAG_STAGES_V10 = new Set(['boot', 'sync_state', 'bridge_open', 'bridge_close', 'navigate', 'fetch_route',
  'send_hook', 'augment', 'post_drop', 'main_crash', 'lifecycle_error']);
function DPP_MW_DIAG_V10(stage, fields) {
  try {
    if (!DPP_MW_DIAG_STAGES_V10.has(stage)) return;
    var row = {version: 10, time: Date.now(), stage: stage};
    var src = fields && typeof fields === 'object' ? fields : {};
    var keys = Object.keys(src);
    for (var k = 0; k < keys.length; k++) {
      var key = keys[k], value = src[key];
      if (!/^[a-z]{1,16}$/.test(key)) continue;
      if (typeof value === 'boolean') row[key] = value;
      else if (typeof value === 'number' && Number.isFinite(value)) row[key] = Math.max(-1, Math.min(9999, Math.trunc(value)));
      else if (typeof value === 'string' && /^[A-Za-z_]{1,40}$/.test(value)) row[key] = value;
    }
    var store = typeof localStorage !== 'undefined' ? localStorage : null;
    if (!store) return;
    var rows = [];
    try { var parsed = JSON.parse(store.getItem(DPP_MW_DIAG_KEY_V10) || '[]'); if (Array.isArray(parsed)) rows = parsed; } catch (e) { rows = []; }
    var last = rows.length ? rows[rows.length - 1] : null;
    if (last && last.stage === stage && last.kind === row.kind && last.route === row.route &&
        last.bridge === row.bridge && last.active === row.active && stage !== 'send_hook' && stage !== 'sync_state') {
      last.n = (last.n || 1) + 1; last.time = row.time;
    } else rows.push(row);
    store.setItem(DPP_MW_DIAG_KEY_V10, JSON.stringify(rows.slice(-64)));
  } catch (e) {}
}
DPP_MW_DIAG_V10('boot', {session: typeof location !== 'undefined' && /\/chat\/s\//.test(location.pathname), body: typeof document !== 'undefined' && !!document.body});
/* DPP_MW_BRIDGE_DIAG_V10_END */
