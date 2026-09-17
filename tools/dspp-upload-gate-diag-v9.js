/* DPP_UPLOAD_GATE_DIAG_V9_BEGIN - fixed-enum rejection diagnostics; never relaxes any gate. */
var DPP_GATE_REASON_TABLE_V9 = Object.freeze({
  'Runtime sender does not belong to this extension.': 'sender_not_this_extension',
  'Runtime sender document is not active.': 'sender_lifecycle_not_active',
  'Runtime sender URL is missing.': 'sender_url_missing',
  'Runtime sender URL is invalid.': 'sender_url_invalid',
  'Runtime sender origin does not match its URL.': 'sender_origin_mismatch',
  'Runtime sender is not an extension context.': 'policy_no_deepseek_origin',
  'Runtime trust policy is missing the DeepSeek origin.': 'policy_no_deepseek_origin',
  'Runtime trust policy contains an invalid origin.': 'policy_origin_invalid',
  'Runtime content sender is not the DeepSeek top-level frame.': 'sender_not_top_frame',
  'Runtime sender tab is not a DeepSeek top-level document.': 'sender_tab_not_deepseek',
  'Runtime content sender has no top-level frame evidence.': 'sender_no_frame_evidence',
  'Runtime sender tab is invalid.': 'sender_field_invalid',
  'Runtime sender frame is invalid.': 'sender_field_invalid',
  'Runtime sender document ID is invalid.': 'sender_field_invalid',
  'Runtime sender browser tab does not match its receiving tab.': 'tab_id_mismatch',
  'Runtime sender browser tab URL is missing.': 'tab_url_missing',
  'Runtime sender browser tab URL is invalid.': 'tab_url_invalid',
  'Runtime sender browser tab is not a DeepSeek top-level document.': 'tab_not_deepseek',
  'Runtime content sender has no receiving browser tab.': 'tab_missing',
  'Runtime content sender browser tab is unavailable.': 'tabs_get_failed',
  'Image upload requires an active top-level conversation document.': 'upload_context_incomplete',
  'Image upload conversation changed.': 'conversation_changed'
});
function DPP_GATE_LIFECYCLE_V9(value) {
  if (value === undefined || value === null) return 'none';
  return ['active', 'prerender', 'cached', 'pending_deletion'].includes(value) ? value : 'other';
}
function DPP_GATE_SESSION_V9(value) {
  try { return typeof value === 'string' && value ? vN(value) : null; } catch { return null; }
}
// Booleans / short enums only. Never copies URL, token, documentId or the sender object.
function DPP_GATE_PROBE_V9(sender, context) {
  const probe = {};
  if (sender && typeof sender === 'object') {
    const tabUrl = sender.tab && typeof sender.tab === 'object' ? sender.tab.url : undefined;
    const senderSession = DPP_GATE_SESSION_V9(sender.url), tabSession = DPP_GATE_SESSION_V9(tabUrl);
    probe.frame = sender.frameId === 0 ? 'zero' : sender.frameId === undefined ? 'none' : 'other';
    probe.lifecycle = DPP_GATE_LIFECYCLE_V9(sender.documentLifecycle);
    probe.documentId = typeof sender.documentId === 'string' && sender.documentId.length > 0;
    probe.tab = !!(sender.tab && typeof sender.tab === 'object' && sender.tab.id != null);
    probe.tabUrl = typeof tabUrl === 'string' && tabUrl.length > 0;
    probe.senderSession = !!senderSession;
    probe.tabSession = !!tabSession;
    probe.sameSession = !!senderSession && senderSession === tabSession;
  }
  if (context && typeof context === 'object' && context.surface === 'deepseek_content') {
    const senderSession = DPP_GATE_SESSION_V9(context.senderUrl);
    probe.ctxSenderSession = !!senderSession;
    probe.ctxTabSession = typeof context.chatSessionId === 'string' && context.chatSessionId.length > 0;
    probe.ctxSameSession = !!senderSession && senderSession === context.chatSessionId;
  }
  return probe;
}
function DPP_GATE_REASON_V9(error, context) {
  const message = error && typeof error.message === 'string' ? error.message : '';
  let reason = DPP_GATE_REASON_TABLE_V9[message];
  if (!reason) reason = message.startsWith('Runtime command ') ? 'command_not_allowed' :
    message.startsWith('Runtime message must be') ? 'message_invalid' : 'unknown';
  if (reason === 'upload_context_incomplete' && context && typeof context === 'object') {
    const senderSession = DPP_GATE_SESSION_V9(context.senderUrl);
    reason = context.frameId !== 0 ? 'ctx_frame_not_zero' :
      context.documentLifecycle !== 'active' ? 'ctx_lifecycle_' + DPP_GATE_LIFECYCLE_V9(context.documentLifecycle) :
      !(typeof context.documentId === 'string' && context.documentId) ? 'ctx_document_id_missing' :
      !(typeof context.chatSessionId === 'string' && context.chatSessionId) ? 'ctx_tab_session_missing' :
      !senderSession ? 'ctx_sender_session_missing' :
      senderSession !== context.chatSessionId ? 'ctx_sender_tab_session_mismatch' : 'ctx_unexpected';
  }
  return reason;
}
var DPP_GATE_RECORD_TAIL_V9 = Promise.resolve();
function DPP_GATE_RECORD_V9(row) {
  try {
    const area = typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local;
    if (!area || typeof area.get !== 'function') return;
    const key = 'dpp_upload_gate_diag_v9';
    // Serialized read-modify-write: concurrent rejections must not drop rows.
    DPP_GATE_RECORD_TAIL_V9 = DPP_GATE_RECORD_TAIL_V9.then(() => Promise.resolve(area.get(key)).then(found => {
      const rows = Array.isArray(found && found[key]) ? found[key] : [];
      return area.set({[key]: [...rows.slice(-31), row]});
    })).catch(() => {});
  } catch {}
}
// Only for UPLOAD_DEEPSEEK_IMAGE runtime-boundary rejections. Returns the original DN() response
// with a fixed reason enum and a boolean probe attached; nothing else changes.
function DPP_GATE_DIAG_V9(error, message, sender, response, context) {
  try {
    if (!(error instanceof SN) || !message || message.type !== 'UPLOAD_DEEPSEEK_IMAGE') return response;
    const reason = DPP_GATE_REASON_V9(error, context), probe = DPP_GATE_PROBE_V9(sender, context);
    DPP_GATE_RECORD_V9({version: 9, time: Date.now(), code: response && response.error, reason, ...probe});
    return {...response, reason, probe};
  } catch { return response; }
}
/* DPP_UPLOAD_GATE_DIAG_V9_END */
