"""Pure, hash-locked .34 -> v6 -> v7 transformations; no installation side effects.
Extracted unchanged in behavior from the validated historical builders.
"""
import hashlib
ORIGINAL = '6657748d6d644b32e288aa7264283122402950c920450d652293c3b9720b5962'
RUNTIME_SHA = 'c40d2a5cc594c570e13e023aadbc51e4de3dec1d27492671a559cdd26642f73e'
CANDIDATE_SHA = '251db07b3d1fc1aad31c492594b74bb11adac9143bde8032f120ce34d87d14d9'
BASE_CONTENT = CANDIDATE_SHA
BASE_BACKGROUND = 'ed5751c7dfa819e51bb8df24beea990c505db7eb6f7c3654fa58217177844f32'
def sha(data):
    return hashlib.sha256(data).hexdigest()

def replace_once(data, old, new):
    if isinstance(old, str):
        old = old.encode('utf-8')
    if isinstance(new, str):
        new = new.encode('utf-8')
    if data.count(old) != 1:
        raise ValueError('Anchor missing or ambiguous: ' + repr(old[:100]))
    return data.replace(old, new, 1)

once = replace_once

def build_v6(original, runtime):
    if sha(original) != ORIGINAL:
        raise ValueError('Original .34 baseline hash mismatch')
    if sha(runtime) != RUNTIME_SHA:
        raise ValueError('Runtime source hash mismatch')
    if runtime.count(b'DPP_READIMAGE_V6_BEGIN') != 1 or runtime.count(b'DPP_READIMAGE_V6_END') != 1:
        raise ValueError('Runtime markers missing or ambiguous')
    data = replace_once(original, 'async function Jz(e){', runtime + b'\nasync function Jz(e){')
    data = replace_once(data, 'g=[...t.toolExecutions],_=[],v=new Map',
                        'g=[...t.toolExecutions],DPPVisionV6=DPP_CREATE_READIMAGE_V6({backend:p,signal:i,chatSessionId:s,loopId:a}),_=[],v=new Map')
    data = replace_once(data, 'submitTurn:BR({powWasmUrl:u}),session:f,serializePrompt:',
                        'submitTurn:DPPVisionV6.wrapSubmit(BR({powWasmUrl:u})),session:f,serializePrompt:')
    data = replace_once(data, '_.push(DPPExecution),(()=>{try{if(String(e.toolName',
                        'DPPExecution=await DPPVisionV6.capture(DPPExecution);_.push(DPPExecution),(()=>{try{if(String(e.toolName')
    data = replace_once(data, 'try{await UN([{role:`user`,content:t.originalPrompt,',
                        'try{for(let DPPImageIndexV6=0;DPPImageIndexV6<g.length;DPPImageIndexV6++)g[DPPImageIndexV6]=await DPPVisionV6.capture(g[DPPImageIndexV6]);await UN([{role:`user`,content:t.originalPrompt,')
    data = replace_once(data, 'error:e instanceof Error?e.message:String(e)})}}function Yz(e)',
                        'error:e instanceof Error?e.message:String(e)})}finally{DPPVisionV6.close()}}function Yz(e)')
    if b'DPP_RIF' in data or b'DPP_READIMAGE_V5' in data:
        raise ValueError('Legacy image queue unexpectedly remains')
    if sha(data) != CANDIDATE_SHA:
        raise ValueError('Candidate output hash mismatch')
    return data

def build_v7(content, background, runtime, helper):
    if sha(content) != BASE_CONTENT or sha(background) != BASE_BACKGROUND:
        raise ValueError('Exact v6 input hashes required')
    start = content.index(b'/* DPP_READIMAGE_V6_BEGIN')
    endmarker = b'/* DPP_READIMAGE_V6_END */'
    end = content.index(endmarker, start) + len(endmarker)
    c = content[:start] + runtime.rstrip(b'\n') + content[end:]
    c = once(c, 'DPP_CREATE_READIMAGE_V6({backend:p,signal:i,chatSessionId:s,loopId:a})',
                'DPP_CREATE_READIMAGE_V7({backend:p,signal:i,chatSessionId:s,loopId:a})')
    # The existing local variable name DPPVisionV6 is retained to minimize owning-loop changes.
    b = once(background, 'SET_PENDING_PROJECT_CONTEXT.TOUCH_MEMORIES`.split(`.`)),SN=class',
              'SET_PENDING_PROJECT_CONTEXT.TOUCH_MEMORIES.UPLOAD_DEEPSEEK_IMAGE`.split(`.`)),SN=class')
    b = once(b, 'var LN=new Set([`CREATE_TOOL_AUTHORIZATION`,`CLOSE_TOOL_AUTHORIZATION`,`APPEND_EXTERNAL_TOOL_PAYLOAD_CHUNK`,`EXECUTE_TOOL_CALL`]);',
              'var LN=new Set([`CREATE_TOOL_AUTHORIZATION`,`CLOSE_TOOL_AUTHORIZATION`,`APPEND_EXTERNAL_TOOL_PAYLOAD_CHUNK`,`EXECUTE_TOOL_CALL`,`UPLOAD_DEEPSEEK_IMAGE`]);')
    b = once(b, 'function EN(e,t){t.surface!==`extension_context`&&(xN.has(e.type)||B(`Runtime command ${e.type} is not authorized for DeepSeek content.`))}',
              'function EN(e,t){t.surface!==`extension_context`&&(xN.has(e.type)||B(`Runtime command ${e.type} is not authorized for DeepSeek content.`));if(e.type===`UPLOAD_DEEPSEEK_IMAGE`)DPP_REQUIRE_UPLOAD_CONTEXT_V7(t)}')
    b = once(b, 'function UF(e){', helper + b'\nfunction UF(e){')
    b = once(b, '_F(`UPLOAD_DEEPSEEK_IMAGE`,(t,n)=>e.service.uploadImage(t,n.tabId))',
              '_F(`UPLOAD_DEEPSEEK_IMAGE`,(t,n)=>DPP_DISPATCH_UPLOAD_V7(e.service,t,n))')
    b = once(b, 're=async(t,n,r)=>{let i=await e.getChatEnabled();if(HF(n.signal),!i)return{ok:!1,error:`chat_disabled`};let a=bP(t);HF(n.signal);let o=await e.loadClientHeaders(r);if(HF(n.signal),!o)return{ok:!1,error:e.missingAuthMessage()};let s=await e.createUploadPowHeaders(o,n.signal);HF(n.signal);let c=await e.uploadFile({file:a.file,filename:a.name,modelType:`vision`,clientHeaders:o,powHeaders:s},n.signal);return HF(n.signal),{ok:!0,file:c}},ie=async(e,t)=>',
              're=async(t,n,r,DPPUploadV7)=>{await DPPUploadV7?.assertCurrent?.();let i=DPPUploadV7?.content===!0||await e.getChatEnabled();if(HF(n.signal),!i)return{ok:!1,error:`chat_disabled`};if(DPPUploadV7)DPPUploadV7.stage=`payload`;let a=bP(t);HF(n.signal);await DPPUploadV7?.assertCurrent?.();if(DPPUploadV7)DPPUploadV7.stage=`auth`;let o=await e.loadClientHeaders(r);if(HF(n.signal),!o)return{ok:!1,error:e.missingAuthMessage(),...DPPUploadV7?{code:`auth_missing`}:{}};await DPPUploadV7?.assertCurrent?.();if(DPPUploadV7)DPPUploadV7.stage=`pow`;let s=await e.createUploadPowHeaders(o,n.signal);HF(n.signal);await DPPUploadV7?.assertCurrent?.();if(DPPUploadV7)DPPUploadV7.stage=`upload`;let c=await e.uploadFile({file:a.file,filename:a.name,modelType:`vision`,clientHeaders:o,powHeaders:s},n.signal);return HF(n.signal),{ok:!0,file:c}},ie=async(e,t,DPPUploadV7)=>')
    b = once(b, 'let r=re(e,n.controller,t);n.settled=r.then(()=>void 0,()=>void 0);',
              'let r=re(e,n.controller,t,DPPUploadV7);n.settled=r.then(()=>void 0,()=>void 0);')
    return c, b
