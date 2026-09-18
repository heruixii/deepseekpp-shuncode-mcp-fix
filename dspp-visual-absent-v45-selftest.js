#!/usr/bin/env node
// Fix 3.3.10.45 - visual tool absent selftest
const fs = require('fs');
const path = require('path');
const root = process.argv[2] || '.';
function read(p){return fs.readFileSync(path.join(root,p),'utf-8');}
function fail(m){console.error('FAIL '+m);process.exit(1);}
function pass(m){console.log('PASS '+m);}

let content = read('content-scripts/content.js');

if(!content.includes('DPPVisualToolAbsent331045')) fail('DPPVisualToolAbsent missing');
else pass('DPPVisualToolAbsent present');

if(!content.includes('DPP_VISUAL_TOOL_ABSENT_331045')) fail('DPP_VISUAL_TOOL_ABSENT func missing');
else pass('DPP_VISUAL_TOOL_ABSENT func present');

if(!content.includes('visual_tool_absent_331045')) fail('visual_tool_absent diag missing');
else pass('visual_tool_absent diag present');

if(!content.includes('!!DPP_VISUAL_TOOL_NAME_V41(v)')) fail('visual missing guard missing');
else pass('visual missing guard present');

if(content.includes('DPPVisualMissing331036=!r&&DPP_VISUAL_MISSING_331036(t.originalPrompt,g,p),k=')) fail('old visual missing still present');
else pass('old visual missing gone');

console.log('All v45 visual-absent checks passed');
