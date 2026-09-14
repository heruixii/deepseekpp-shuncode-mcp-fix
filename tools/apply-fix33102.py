#!/usr/bin/env python3
from pathlib import Path
import sys,json,hashlib
EXPECTED={
 'content-scripts/main-world.js':'E38E228E31A375EB164ADDB75E547E9584B8E74451C2CA2B08D5EE980B3AD9E1',
 'manifest.json':'6AFAA0E0271C62257931674CB38E44B7816F02DF5A413CD8F180031937E04059',
 '_locales/en/messages.json':'0E8C18509B612241795AB229A61F7CDD95827344C65386694CA046662A96CCBF',
 '_locales/zh_CN/messages.json':'7B6275E5030BCDF0AB35C702BD5BDFD5CCB28A6F2B6FFDF0848EE0E2A7136676',
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def one(s,a,b,label):
 c=s.count(a)
 if c!=1:raise RuntimeError(f'{label} anchor count {c}')
 return s.replace(a,b,1)
def transform(root):
 paths={k:root/Path(k) for k in EXPECTED}
 for k,p in paths.items():
  if not p.is_file():raise RuntimeError(f'missing {k}')
  got=sha(p)
  if got!=EXPECTED[k]:raise RuntimeError(f'{k} hash mismatch {got} != {EXPECTED[k]}')
 m=json.loads(paths['manifest.json'].read_text(encoding='utf8'))
 if m.get('version')!='1.14.0.6' or m.get('version_name')!='1.14.0 ShunCode MCP Fix 3.3.10.1':raise RuntimeError('expected Fix 3.3.10.1 manifest')
 s=paths['content-scripts/main-world.js'].read_text(encoding='utf8')
 anchor='function Xa(e){let t=z(e);return t&&(qn(t)===t?t:``)}'
 insert=r'''function DPP_PAGE_CONTROL_LINE_33102(e,t){let n=e.trim();if(!n)return!1;if(/^<\/\s*(?:invoke|parameter)\s*>$/i.test(n))return!0;if(/^<\/\s*[|｜]{1,2}\s*DSML\s*[|｜]{1,2}\s*(?:parameter|invoke|calls|tool_calls)\s*>$/i.test(n))return!0;let r=/^<\/\s*([A-Za-z_][A-Za-z0-9_.:-]*)\s*>$/.exec(n);return!!(r&&t.has(r[1]))}function DPP_PAGE_CONTROL_FILTER_33102(e,t,n){if(!e)return e;let r=``,i=0,a=/\r\n|\r|\n/g,o;for(;(o=a.exec(e))!==null;){let a=e.slice(i,o.index),s=o[0],c=(a.match(/```/g)||[]).length;if(!n.inFence&&c===0&&!DPP_PAGE_CONTROL_LINE_33102(a,t))r+=a+s;else if(n.inFence||c>0)r+=a+s;c%2===1&&(n.inFence=!n.inFence),i=o.index+s.length}let s=e.slice(i),c=(s.match(/```/g)||[]).length;return(!n.inFence&&c===0&&!DPP_PAGE_CONTROL_LINE_33102(s,t)||n.inFence||c>0)&&(r+=s),c%2===1&&(n.inFence=!n.inFence),r}function DPP_PAGE_CONTROL_SEQUENCE_33102(e,t){let n=e.trim();return!!n&&n.split(/\r\n|\r|\n/).every(e=>!e.trim()||DPP_PAGE_CONTROL_LINE_33102(e,t))}function DPP_PAGE_CONTROL_PREFIX_33102(e,t){let n=e.trim();if(!n.startsWith(`</`)||n.includes(`\n`)||n.includes(`\r`))return!1;let r=[`</invoke>`,`</parameter>`,`</｜｜DSML｜｜ parameter>`,`</｜｜DSML｜｜ invoke>`,`</｜｜DSML｜｜ calls>`,`</｜｜DSML｜｜ tool_calls>`,`</||DSML|| parameter>`,`</||DSML|| invoke>`,`</||DSML|| calls>`,`</||DSML|| tool_calls>`];for(let e of t)r.push(`</${e}>`);return r.some(e=>e.toLowerCase().startsWith(n.toLowerCase()))}'''
 s=one(s,anchor,insert+anchor,'Xa')
 s=one(s,'var $a=class{toolInvocationNameSet;visiblePrompt;state=`NORMAL`;currentTool=null;pendingText=``;pendingBlocks=[];encoder=new TextEncoder;stripTailLeadingNewlines=!1;lastEmittedTextEndsWithNewline=!1;blankLineFenceState={inFence:!1};constructor(e=[],t=``){this.visiblePrompt=t,this.toolInvocationNameSet=new Set(P(e).invocationNames)}','var $a=class{toolInvocationNameSet;visiblePrompt;state=`NORMAL`;currentTool=null;pendingText=``;pendingBlocks=[];encoder=new TextEncoder;stripTailLeadingNewlines=!1;lastEmittedTextEndsWithNewline=!1;blankLineFenceState={inFence:!1};controlNoiseFenceState={inFence:!1};constructor(e=[],t=``){this.visiblePrompt=t,this.toolInvocationNameSet=new Set(P(e).invocationNames)}','class')
 s=one(s,'processNormalTextBlock(e,t,n,r,i,a,o){if(this.stripTailLeadingNewlines){','processNormalTextBlock(e,t,n,r,i,a,o){let DPPPageClean=DPP_PAGE_CONTROL_FILTER_33102(a,this.toolInvocationNameSet,this.controlNoiseFenceState);if(DPPPageClean!==a){let DPPPageParsed=JSON.parse(JSON.stringify(i));Va(DPPPageParsed,DPPPageClean),i=DPPPageParsed,a=DPPPageClean,t=L(r,JSON.stringify(DPPPageParsed));if(!a)return}if(this.stripTailLeadingNewlines){','process-normal')
 s=one(s,'this.pendingText+=a,this.pendingBlocks.push({block:t,separator:n,sourceFrame:r,isFragmentCreation:o,parsed:i});let c=this.findFirstToolOpen(this.pendingText);','this.pendingText+=a,this.pendingBlocks.push({block:t,separator:n,sourceFrame:r,isFragmentCreation:o,parsed:i});if(!this.controlNoiseFenceState.inFence&&DPP_PAGE_CONTROL_SEQUENCE_33102(this.pendingText,this.toolInvocationNameSet)){this.pendingBlocks=[],this.pendingText=``;return}let c=this.findFirstToolOpen(this.pendingText);','pending')
 s=one(s,'couldBePartialToolOpen(e){return N(e,this.toolInvocationNameSet,{closing:!1})>0}','couldBePartialToolOpen(e){return N(e,this.toolInvocationNameSet,{closing:!1})>0||DPP_PAGE_CONTROL_PREFIX_33102(e,this.toolInvocationNameSet)}','partial')
 m['version']='1.14.0.7';m['version_name']='1.14.0 ShunCode MCP Fix 3.3.10.2'
 out={'content-scripts/main-world.js':s,'manifest.json':json.dumps(m,ensure_ascii=False,indent=2)+'\n'}
 for rel in ['_locales/en/messages.json','_locales/zh_CN/messages.json']:
  o=json.loads(paths[rel].read_text(encoding='utf8'))
  for v in o.values():
   if isinstance(v,dict) and isinstance(v.get('message'),str):v['message']=v['message'].replace('Fix 3.3.10.1','Fix 3.3.10.2')
  out[rel]=json.dumps(o,ensure_ascii=False,indent=2)+'\n'
 return out
def main():
 root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
 try:out=transform(root)
 except Exception as e:print(f'APPLY_FIX33102_FAIL: {e}',file=sys.stderr);return 1
 for rel,text in out.items():(root/rel).write_text(text,encoding='utf8',newline='')
 print('APPLY_FIX33102_PASS');return 0
if __name__=='__main__':raise SystemExit(main())