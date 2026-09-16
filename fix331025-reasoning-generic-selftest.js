const fs=require('fs'),path=require('path'),vm=require('vm');
const root=__dirname;
const content=fs.readFileSync(path.join(root,'content-scripts/content.js'),'utf8');
const main=fs.readFileSync(path.join(root,'content-scripts/main-world.js'),'utf8');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0,total=0;function test(n,c,d=''){total++;if(c){pass++;console.log('PASS',n,d)}else{console.error('FAIL',n,d);process.exitCode=1}}
function extract(a,b,s=content){const i=s.indexOf(a),j=s.indexOf(b,i);if(i<0||j<0)throw Error(`extract ${a}`);return s.slice(i,j)}
(async()=>{
test('version',['1.14.0.30','1.14.0.31','1.14.0.32','1.14.0.33','1.14.0.34','1.14.0.35','1.14.0.36','1.14.0.37','1.14.0.38'].includes(manifest.version));
test('version name',['1.14.0 ShunCode MCP Fix 3.3.10.25','1.14.0 ShunCode MCP Fix 3.3.10.26','1.14.0 ShunCode MCP Fix 3.3.10.27','1.14.0 ShunCode MCP Fix 3.3.10.28','1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30','1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32','1.14.0 ShunCode MCP Fix 3.3.10.33'].includes(manifest.version_name));
// Ephemeral reasoning bridge: bounded, validated, never added to the Agent prompt.
test('main response carries robust bounded reasoning tail',main.includes('dppReasoningTail331025:typeof n.assistantReasoningText==`string`?(n.assistantReasoningText.length>4096?n.assistantReasoningText.slice(-4096):n.assistantReasoningText):``'));
test('main bridge validator accepts optional tail',main.includes('ns(e.dppReasoningTail331025)&&as(e.chatSessionId)'));
test('content bridge validator accepts optional tail',content.includes('VK(e.dppReasoningTail331025)&&WK(e.chatSessionId)'));
test('content maps at most 4096 chars',content.includes('reasoningTail:typeof n.dppReasoningTail331025==`string`?n.dppReasoningTail331025.slice(-4096):``'));
test('manual escalation consumes reasoning signal',content.includes('DPP_TOOL_INTENT_331021(e.text,e.reasoningTail??``)'));
test('manual escalation still requires FINISHED',content.includes('n.length===0&&!DPPResume&&e.streamFinished===!0&&DPP_TOOL_INTENT_331021'));
test('manual escalation stage superseded by 331027',content.includes('content_manual_tool_intent_escalation_331027'));
test('manual diag stores reasoning length only',content.includes('reasoningChars:(e.reasoningTail??``).length,reasoningIntent:DPPManualReasoningIntent331025'));
const promptFn=extract('function DPP_MANUAL_TOOL_INTENT_PROMPT_331022','async function J$(');
test('manual Agent prompt does not include raw reasoning tail',!promptFn.includes('reasoningTail')&&!promptFn.includes('dppReasoningTail331025'));
test('preflight diag has only numeric/boolean reasoning fields',content.includes('reasoningChars:DPP_NUM_331018(t.reasoningChars),reasoningIntent:typeof t.reasoningIntent==`boolean`?t.reasoningIntent:null'));

// Evaluate production tool-intent classifier with minimal stubs.
const a=content.indexOf('var DPP_TOOL_INTENT_NUDGE_MAX_331021=');
const b=content.indexOf('function DPP_STEERING_MODE_331021',a);
const classifier=content.slice(a,b);
const ctx={String,RegExp};
// classifier depends on helpers; provide exact simple semantics for predicates not under test.
ctx.jz=e=>String(e??'').trim().slice(-600); ctx.Mz=e=>false; ctx.DPP_MIDSTEP_CUE_31=e=>false; ctx.DPP_STRICT_CONTINUATION_31=e=>false; ctx.Sz=e=>null; ctx.DPP_UNCONSUMED_TOOL_MARKUP_331024=e=>false;
vm.createContext(ctx);vm.runInContext(classifier+';globalThis.intentText=DPP_TOOL_INTENT_TEXT_331021;globalThis.intent=DPP_TOOL_INTENT_331021;globalThis.GMAX=DPP_GENERIC_NUDGE_MAX_331025;',ctx);
test('generic max is 3',ctx.GMAX===3);
test('real manual reasoning: invoke run_command',ctx.intentText('I need a fresh capability handle. Let me invoke run_command.')===true);
test('real failed step: run python script',ctx.intentText("Let me continue by extracting an overview. Let me run a python script to output each user message's visible prompt.")===true);
test('write script reasoning is tool intent',ctx.intentText("I'll write a script to extract the timeline.")===true);
test('ordinary analysis is not tool intent',ctx.intentText('The conversation contains several topics and the final result is ready.')===false);
test('empty visible text falls back to reasoning',ctx.intent('', 'Let me invoke run_command with the capability provided.')===true);
test('visible final text takes precedence over stale reasoning',ctx.intent('The task is complete and the file was verified.', 'Let me invoke run_command.')===false);

// Evaluate steering mode exactly.
const sm=extract('function DPP_STEERING_MODE_331021','function DPP_TOOL_INTENT_STEERING_331021');
const c2={DPP_TOOL_INTENT_NUDGE_MAX_331021:3,DPP_GENERIC_NUDGE_MAX_331025:3};vm.createContext(c2);vm.runInContext(sm+';globalThis.mode=DPP_STEERING_MODE_331021;',c2);
const base={turnIndex:2,nudgeCount:0,maxNudges:8,hasToolCall:false,hasParent:true,toolIntent:false,toolIntentNudgesInStep:0,needsContinuation:true};
test('generic nudge 0 allowed',c2.mode({...base,genericNudgesInStep:0})==='generic');
test('generic nudge 1 allowed',c2.mode({...base,genericNudgesInStep:1})==='generic');
test('generic nudge 2 allowed',c2.mode({...base,genericNudgesInStep:2})==='generic');
test('generic nudge 3 blocked',c2.mode({...base,genericNudgesInStep:3})==='none');
test('tool-intent budget remains separate',c2.mode({...base,toolIntent:true,toolIntentNudgesInStep:2,genericNudgesInStep:3})==='tool_intent');
test('tool-intent limit remains 3',c2.mode({...base,toolIntent:true,toolIntentNudgesInStep:3})==='none');
test('no parent blocks steering',c2.mode({...base,hasParent:false,genericNudgesInStep:0})==='none');
test('global nudge cap still authoritative',c2.mode({...base,nudgeCount:8,genericNudgesInStep:0})==='none');
test('actual tool call blocks steering',c2.mode({...base,hasToolCall:true,genericNudgesInStep:0})==='none');

// Production wiring / fail-closed boundaries.
test('state has genericNudgesInStep counter',content.includes('genericNudgesInStep:0,toolIntentNudgesInStep:0'));
test('generic steering increments counter',content.includes('y.genericNudgesInStep+=1,i=Pz('));
test('generic steering diagnostic exists',content.includes('stage:`generic_continuation_steering_331025`'));
test('generic steering diagnostic logs counter',content.includes('genericNudgesInStep:y.genericNudgesInStep,decision:`reemit_continuation`'));
test('tool call resets generic counter',content.includes('y.nudgedInStep=!1,y.genericNudgesInStep=0,y.toolIntentNudgesInStep=0'));
test('explicit generic continuation limit exists',content.includes('function DPP_GENERIC_NUDGE_LIMIT_331025'));
test('shouldStop emits explicit generic limit',content.includes('q(`generic_continuation_limit_331025`,!0)'));
test('generic limit requires non tool-intent',content.includes('if(!k&&y.genericNudgesInStep>=DPP_GENERIC_NUDGE_MAX_331025)'));
test('Agent turn diag persists generic count only',content.includes('genericNudgesInStep:DPP_NUM_331018(t.genericNudgesInStep)'));
test('legacy boolean no longer controls steering mode',!sm.includes('genericNudgedInStep'));
test('tool-intent wrapper guard retained',content.includes('DPP_UNCONSUMED_TOOL_MARKUP_331024(n)||DPP_TOOL_INTENT_TEXT_331021'));
test('generic wrapper parser retained',content.includes('DPP_PARSE_GENERIC_TOOL_WRAPPER_331024'));
test('old h shadow remains absent',!content.includes('let h=DPP_STAT_CLAIM_MISMATCH_33109'));
test('reasoning tail is not written into trace constructor',!extract('function b0(','function x0(').includes('reasoningTail'));
test('reasoning tail is not placed in persisted diagnostic object',!extract('function DPP_RECORD_AGENT_TURN_DIAG_331021','async function _Z').includes('reasoningTail'));
console.log(`FIX331025_PASS ${pass}/${total}`);if(pass!==total)process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});
