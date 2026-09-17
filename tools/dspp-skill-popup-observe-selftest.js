'use strict';
// .40: skill-popup go() must not call MutationObserver.observe(null) when <body> is not there yet, and must still
// observe body once DOMContentLoaded fires; behaviour with an existing body is unchanged. Runs the real go()/_o() text.
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert/strict');
const root = process.argv[2], baselineRoot = process.argv[3];
if (!root || !baselineRoot) throw Error('Usage: node dspp-skill-popup-observe-selftest.js candidate-root baseline-36-root');
const mw = fs.readFileSync(path.join(root, 'content-scripts/main-world.js'), 'utf8');
const old = fs.readFileSync(path.join(baselineRoot, 'content-scripts/main-world.js'), 'utf8');
function slice(s, a, b) { const i = s.indexOf(a), j = s.indexOf(b, i); assert(i >= 0 && j > i, 'extract ' + a); return s.slice(i, j); }
function harness(source, withBody) {
  const listeners = {}, observed = [];
  const doc = {body: withBody ? {tag: 'body'} : null, contains: () => true, querySelector: () => null,
    addEventListener: (t, f) => { (listeners[t] ||= []).push(f); }, removeEventListener: () => {}, getElementById: () => null};
  class MutationObserver { constructor(cb) { this.cb = cb; } observe(node, opts) { if (!node || typeof node !== 'object') throw new TypeError("Failed to execute 'observe' on 'MutationObserver': parameter 1 is not of type 'Node'."); observed.push(node); } disconnect() {} }
  const box = {document: doc, MutationObserver, console};
  vm.createContext(box);
  vm.runInContext('var J=null,Y=null,uo=[],K=[],q=0;' + slice(source, 'function go(){', 'function vo(){'), box);
  return {box, doc, listeners, observed};
}
let groups = 0; const test = (n, f) => { f(); groups++; console.log('PASS ' + n); };
test('baseline reproduces the field error when body is missing', () => { const h = harness(old, false); assert.throws(() => vm.runInContext('go()', h.box), /not of type 'Node'/); });
test('candidate: body missing -> no throw, observes body on DOMContentLoaded', () => {
  const h = harness(mw, false); vm.runInContext('go()', h.box);
  assert.equal(h.observed.length, 0); assert.equal((h.listeners.DOMContentLoaded || []).length, 1);
  h.doc.body = {tag: 'body'}; h.listeners.DOMContentLoaded[0](); assert.equal(h.observed.length, 1); assert.equal(h.observed[0], h.doc.body);
});
test('candidate: body present -> identical immediate observe, no listener registered', () => {
  const h = harness(mw, true); vm.runInContext('go()', h.box); assert.equal(h.observed.length, 1); assert.equal(h.listeners.DOMContentLoaded, undefined);
});
test('only the observe expression changed inside go()', () => {
  const a = slice(mw, 'function go(){', 'function vo(){'), b = slice(old, 'function go(){', 'function vo(){');
  assert.notEqual(a, b);
  assert.equal(a.replace('document.body?Y.observe(document.body,{childList:!0,subtree:!0}):document.addEventListener(`DOMContentLoaded`,()=>{Y&&document.body&&Y.observe(document.body,{childList:!0,subtree:!0}),_o()},{once:!0})', 'Y.observe(document.body,{childList:!0,subtree:!0})'), b);
});
console.log(`RESULT ${groups}/${groups} .40 skill-popup observe groups passed.`);
