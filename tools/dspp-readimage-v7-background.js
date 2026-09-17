/* DPP_READIMAGE_V7_BACKGROUND_BEGIN */
function DPP_REQUIRE_UPLOAD_CONTEXT_V7(context) {
  if (context.surface !== 'deepseek_content') return;
  if (context.frameId !== 0 || context.documentLifecycle !== 'active' ||
      typeof context.documentId !== 'string' || !context.documentId ||
      typeof context.chatSessionId !== 'string' || !context.chatSessionId ||
      vN(context.senderUrl) !== context.chatSessionId)
    throw new SN(bN.unauthorizedSender, 'Image upload requires an active top-level conversation document.');
}
async function DPP_ASSERT_CURRENT_UPLOAD_V7(context) {
  if (context.surface !== 'deepseek_content') return;
  DPP_REQUIRE_UPLOAD_CONTEXT_V7(context);
  const current = await aI(context, {tabs: chrome.tabs, deepSeekOrigin: 'https://chat.deepseek.com'});
  if (current.chatSessionId !== context.chatSessionId)
    throw new SN(bN.unauthorizedSender, 'Image upload conversation changed.');
}
async function DPP_DISPATCH_UPLOAD_V7(service, payload, context) {
  // Trust comes ONLY from the runtime listener's normalized sender, never from payload.
  if (context.surface !== 'deepseek_content') return service.uploadImage(payload, context.tabId);
  const trusted = {content: true, stage: 'gate', assertCurrent: () => DPP_ASSERT_CURRENT_UPLOAD_V7(context)};
  try {
    await trusted.assertCurrent();
    const result = await service.uploadImage(payload, context.tabId, trusted);
    if (result?.ok === true) { await trusted.assertCurrent(); return result; }
    const code = result?.code === 'auth_missing' ? 'auth_missing' :
      result?.error === 'chat_disabled' ? 'chat_disabled' :
      result?.error === 'chat_already_running' ? 'upload_busy' : 'upload_failed';
    return {ok: false, error: code, code};
  } catch (error) {
    const code = error instanceof SN ? bN.unauthorizedSender :
      error?.name === 'AbortError' ? 'upload_aborted' :
      error?.name === 'DeepSeekAuthError' ? 'auth_rejected' :
      trusted.stage === 'payload' ? 'invalid_image' :
      trusted.stage === 'auth' ? 'auth_failed' :
      trusted.stage === 'pow' ? 'pow_failed' : 'upload_failed';
    return {ok: false, error: code, code};
  }
}
/* DPP_READIMAGE_V7_BACKGROUND_END */
