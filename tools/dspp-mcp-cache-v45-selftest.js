#!/usr/bin/env node
// Fix 3.3.10.45 - MCP cache clear regression selftest
// Checks: Vc excludes limits/timeouts, Sc auto ju, Nu self-heal, UPDATE handler refresh
const fs = require('fs');
const path = require('path');
const root = process.argv[2] || '.';
function read(p){return fs.readFileSync(path.join(root,p),'utf-8');}
function fail(m){console.error('FAIL '+m);process.exit(1);}
function pass(m){console.log('PASS '+m);}

let bg = read('background.js');

// Vc must NOT contain timeouts or limits inside its definition
let vcMatch = bg.match(/function Vc\(e\)\{[^}]*\}/);
if(!vcMatch) fail('Vc not found for check');
else if(vcMatch[0].includes('timeouts') || vcMatch[0].includes('limits')){
  fail('Vc still includes timeouts/limits');
}else pass('Vc excludes timeouts/limits');

// Vc must contain transport+headers+secrets only
if(!bg.includes('function Vc(e){return JSON.stringify({transport:')) fail('Vc not found');
else pass('Vc present');

// Sc must contain ju(e).catch
if(!bg.includes('ju(e).catch')) fail('Sc missing auto ju');
else pass('Sc auto ju present');

// Nu must contain self-heal logic (o=new Set and ju(e).catch and Tc() re-fetch)
if(!bg.includes('async function Nu(e)') ) fail('Nu not found');
else {
  // check for o=new Set and expiresAt check
  if(!bg.includes('o=new Set') || !bg.includes('expiresAt<=r')) fail('Nu self-heal not found');
  else pass('Nu self-heal present');
}

// UPDATE handler must contain refreshMcpServerDiscovery
if(!bg.includes('UPDATE_MCP_SERVER') || !bg.includes('refreshMcpServerDiscovery')) fail('UPDATE handler missing refresh');
else pass('UPDATE handler refresh present');

// Check that old Vc string is gone
if(bg.includes('timeouts:e.timeouts,limits:e.limits') && bg.match(/function Vc.*timeouts:e.timeouts,limits:e.limits/)) fail('old Vc still present');
else pass('old Vc gone');

console.log('All v45 mcp-cache checks passed');
