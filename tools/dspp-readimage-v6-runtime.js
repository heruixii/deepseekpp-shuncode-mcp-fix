/* DPP_READIMAGE_V6_BEGIN - Web-only, run-scoped image handoff. */
function DPP_CREATE_READIMAGE_V6(options) {
  const MAX_BYTES = 8 * 1024 * 1024, MAX_IMAGES = 4, MAX_CACHE = 16;
  const MAX_TEXT = 12 * 1024 * 1024, TIMEOUT_MS = 20000;
  const signal = options.signal, cache = new Map(), pending = new Set();
  let notes = [], closed = false;
  const stopped = () => closed || !!signal?.aborted;
  const abortError = () => new DOMException('Image handoff aborted.', 'AbortError');
  function diag(stage, fields = {}) {
    const row = {version: 6, time: Date.now(), stage, ...fields};
    try {
      const key = 'dpp_read_image_diag_v6';
      let rows;
      try { rows = JSON.parse(localStorage.getItem(key) || '[]'); } catch { rows = []; }
      if (!Array.isArray(rows)) rows = [];
      localStorage.setItem(key, JSON.stringify([...rows.slice(-63), row]));
    } catch {}
    try { options.onDiagnostic?.(row); } catch {}
  }
  function note(code, count = 1) {
    if (notes.length < 8) notes.push(`read_image visual attachment: ${code} (${count}). Do not claim to have seen an image unless its visual content is actually available.`);
    diag(code, {count});
  }
  function isImageTool(execution) {
    const names = [execution?.name, execution?.result?.name];
    return names.some(x => typeof x === 'string' && /(?:^|[_.:/])(?:read_image|mcp_invoke)(?::dpp331019)?$/i.test(x));
  }
  function failed(o) { return o && typeof o === 'object' && (o.ok === false || o.isError === true || o.truncated === true || ['error', 'failed'].includes(o.status)); }
  function collect(root) {
    const images = [], seen = new WeakSet();
    let visits = 0, textBudget = MAX_TEXT, rejected = 0;
    function add(mime, data) {
      if (typeof mime !== 'string' || typeof data !== 'string' || data.length > Math.ceil(MAX_BYTES / 3) * 4 + 128) { rejected++; return; }
      mime = mime.toLowerCase();
      if (!['image/png', 'image/jpeg', 'image/gif', 'image/webp'].includes(mime)) { rejected++; return; }
      data = data.replace(/\s/g, '');
      if (!data || !/^[A-Za-z0-9+/]*={0,2}$/.test(data) || data.length % 4 === 1) { rejected++; return; }
      if (data.includes('=') && data.length % 4 !== 0) { rejected++; return; }
      data += '='.repeat((4 - data.length % 4) % 4);
      let raw;
      try { raw = atob(data); } catch { rejected++; return; }
      if (!raw.length || raw.length > MAX_BYTES || btoa(raw) !== data) { rejected++; return; }
      const valid = mime === 'image/png' ? raw.startsWith('\x89PNG\r\n\x1a\n') :
        mime === 'image/jpeg' ? raw.startsWith('\xff\xd8\xff') :
        mime === 'image/gif' ? /^(GIF87a|GIF89a)/.test(raw) : raw.startsWith('RIFF') && raw.slice(8, 12) === 'WEBP';
      if (!valid) { rejected++; return; }
      if (images.some(x => x.data === data && x.mime === mime)) return;
      if (images.length >= MAX_IMAGES) { rejected++; return; }
      images.push({mime, data, sizeBytes: raw.length});
    }
    function uri(value) {
      if (typeof value !== 'string') return;
      const match = /^data:(image\/[a-z0-9.+-]+);base64,([\s\S]*)$/i.exec(value);
      if (match) add(match[1], match[2]);
    }
    function walk(o, depth) {
      if (depth > 8 || ++visits > 256 || o == null) return;
      if (typeof o === 'string') {
        if (o.length > textBudget) { rejected++; return; }
        textBudget -= o.length;
        const text = o.trim();
        if (/^[\[{]/.test(text)) { try { walk(JSON.parse(text), depth + 1); } catch {} }
        return;
      }
      if (typeof o !== 'object' || seen.has(o) || failed(o)) return;
      seen.add(o);
      if (Array.isArray(o)) { for (const item of o.slice(0, 64)) walk(item, depth + 1); return; }
      if (o.type === 'image') add(o.mimeType || o.mime_type, o.data);
      uri(o.data_uri); uri(o.dataUri); uri(o.dataURL);
      if (o.type === 'text') walk(o.text, depth + 1);
      for (const key of ['result', 'details', 'output', 'structuredContent', 'content']) walk(o[key], depth + 1);
    }
    walk(root, 0);
    return {images, rejected};
  }
  // Clone only image-bearing results. Never put base64 in the next prompt or new diagnostics.
  function redact(root) {
    const seen = new WeakSet();
    let budget = 4096;
    function copy(value, depth) {
      if (--budget < 0 || depth > 12) return '[bounded image result]';
      if (typeof value === 'string') {
        if (value.length > MAX_TEXT) return '[oversized image result omitted]';
        const text = value.trim();
        if (/^[\[{]/.test(text)) { try { return JSON.stringify(copy(JSON.parse(text), depth + 1)); } catch {} }
        return value.replace(/data:image\/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=\s]+/gi, '[image bytes omitted]');
      }
      if (!value || typeof value !== 'object') return value;
      if (seen.has(value)) return '[repeated image result]';
      seen.add(value);
      if (Array.isArray(value)) return value.slice(0, 256).map(v => copy(v, depth + 1));
      const result = {};
      for (const key of Object.keys(value).slice(0, 128)) {
        if (key === '__proto__' || key === 'constructor' || key === 'prototype') continue;
        result[key] = ['data_uri', 'dataUri', 'dataURL'].includes(key) || (value.type === 'image' && key === 'data') ? '[image bytes omitted]' : copy(value[key], depth + 1);
      }
      return result;
    }
    return copy(root, 0);
  }
  function upload(image, timeout) {
    return new Promise((resolve, reject) => {
      let done = false, timer;
      const finish = (err, id) => {
        if (done) return;
        done = true; clearTimeout(timer); signal?.removeEventListener('abort', abort);
        err ? reject(err) : resolve(id);
      };
      const abort = () => finish(abortError());
      if (stopped()) return abort();
      signal?.addEventListener('abort', abort, {once: true});
      timer = setTimeout(() => finish(new Error('upload_timeout')), Math.max(1, timeout));
      try {
        chrome.runtime.sendMessage({type: 'UPLOAD_DEEPSEEK_IMAGE', payload: {
          dataUrl: `data:${image.mime};base64,${image.data}`, name: `read_image.${image.mime.split('/')[1]}`,
          mimeType: image.mime, sizeBytes: image.sizeBytes
        }}, response => {
          // Read lastError even after timeout, but never accept a late callback.
          const runtimeError = chrome.runtime.lastError;
          if (done) return;
          if (stopped()) return abort();
          const id = response?.file?.id;
          if (runtimeError || response?.ok !== true || typeof id !== 'string' || !id.trim() || id.length > 256)
            return finish(new Error('upload_failed'));
          finish(null, id);
        });
      } catch { finish(new Error('upload_failed')); }
    });
  }
  async function capture(execution) {
    if (options.backend !== 'web' || !isImageTool(execution)) return execution;
    if (stopped()) throw abortError();
    const isRead = /read_image(?::dpp331019)?$/i.test(execution?.name || '') || /read_image$/i.test(execution?.result?.name || '');
    if (failed(execution?.result)) { if (isRead) { note('tool_failed_or_truncated'); return redact(execution); } return execution; }
    const {images, rejected} = collect(execution?.result);
    if (!images.length && !rejected) { if (isRead) note('no_image_data'); return execution; }
    const cleaned = redact(execution);
    diag('capture', {count: images.length, rejected});
    if (rejected) note('unsupported_invalid_or_bounded_image', rejected);
    const deadline = Date.now() + TIMEOUT_MS;
    let bytes = 0;
    for (const image of images) {
      if (stopped()) throw abortError();
      bytes += image.sizeBytes;
      if (bytes > MAX_BYTES || pending.size >= MAX_IMAGES) { note('batch_limit'); break; }
      try {
        const raw = Uint8Array.from(atob(image.data), c => c.charCodeAt(0));
        const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', raw)), b => b.toString(16).padStart(2, '0')).join('');
        if (stopped()) throw abortError();
        let id = cache.get(hash);
        if (!id) {
          if (cache.size >= MAX_CACHE) { note('run_limit'); break; }
          if (Date.now() >= deadline) { note('upload_timeout'); break; }
          diag('upload_start', {bytes: image.sizeBytes});
          id = await upload(image, deadline - Date.now());
          if (stopped()) throw abortError();
          cache.set(hash, id); diag('upload_ok', {bytes: image.sizeBytes});
        } else diag('cache_hit');
        pending.add(id);
      } catch (error) {
        if (stopped() || error?.name === 'AbortError') throw abortError();
        note(error?.message === 'upload_timeout' ? 'upload_timeout' : 'upload_failed');
      }
    }
    return cleaned;
  }
  function wrapSubmit(submit) {
    return async (request, handlers, requestSignal) => {
      if (options.backend !== 'web') return submit(request, handlers, requestSignal);
      if (stopped() || requestSignal?.aborted) throw abortError();
      if (request.chatSessionId !== options.chatSessionId) { diag('session_mismatch'); throw new Error('Image handoff session mismatch.'); }
      const ids = [...pending], messages = notes.slice();
      const refs = [...new Set([...(request.refFileIds || []), ...ids])];
      const notice = [...messages, ...(ids.length ? [`${ids.length} read_image file reference(s) attached to this request. Describe only visual content actually available; file references alone do not prove image understanding.`] : [])];
      const next = ids.length || messages.length ? {...request, refFileIds: refs, prompt: `${request.prompt}\n\n[read_image attachment status]\n${notice.join('\n')}`} : request;
      if (ids.length || messages.length) diag('request_refs', {count: ids.length, warnings: messages.length});
      const result = await submit(next, handlers, requestSignal);
      if (!stopped() && !requestSignal?.aborted && result?.finished === true) {
        for (const id of ids) pending.delete(id);
        notes.splice(0, messages.length);
        if (ids.length) diag('request_ack', {count: ids.length});
      }
      return result;
    };
  }
  function close() { closed = true; pending.clear(); cache.clear(); notes = []; }
  diag('run_ready', {web: options.backend === 'web'});
  return {capture, wrapSubmit, close};
}
/* DPP_READIMAGE_V6_END */
