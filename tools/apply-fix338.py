from pathlib import Path
import hashlib,json,os,sys
EXPECTED={
'content':'6B723586B7E152562FDE7BC63E172ED5B37C3D91D97B40362979598074AF1746',
'policy':'2C0422976F114C43BCFDDF5E97187718BAA6C3712EF981FEBF4166CE2D9A1E4B',
'manifest':'5F049840D4381C9AE5297B300F1786833491CD85ABCBEE25B72C95A195AFC01D',
'en':'13B7D55B9BB71F41D1D5245AD840FADB5C45D5F42BE2B73795E03F3749E30EA1',
'zh':'AD44B32DCDE402C9CD79F07A7F43B2A2C578F8252B87F179EABBD3F1474B7D8F'}
OLD='1.14.0 ShunCode MCP Fix 3.3.7';NEW='1.14.0 ShunCode MCP Fix 3.3.8';OLDN='DeepSeek++ ShunCode MCP Fix 3.3.7';NEWN='DeepSeek++ ShunCode MCP Fix 3.3.8'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def rep(s,a,b,label,count=1):
 c=s.count(a)
 if c!=count:raise RuntimeError(f'{label}: expected {count}, found {c}')
 return s.replace(a,b,count)
def atomic(items):
 tmp=[]
 try:
  for p,s in items:
   q=p.with_name(p.name+'.fix338.tmp');q.write_text(s,encoding='utf8',newline='');tmp.append((q,p))
  for q,p in tmp:os.replace(q,p)
 finally:
  for q,_ in tmp:
   try:q.unlink()
   except FileNotFoundError:pass
def main(root):
 root=Path(root);cp=root/'content-scripts/content.js';pp=root/'fix3-policy.js';mp=root/'manifest.json';ep=root/'_locales/en/messages.json';zp=root/'_locales/zh_CN/messages.json'
 m=json.loads(mp.read_text(encoding='utf-8-sig'));en=json.loads(ep.read_text(encoding='utf-8-sig'));zh=json.loads(zp.read_text(encoding='utf-8-sig'));s=cp.read_text(encoding='utf-8-sig');p=pp.read_text(encoding='utf-8-sig')
 if m.get('version_name')==NEW and m.get('version')=='1.14.0.3' and 'DPP_AGENT_MIN_BUDGET_338=88' in s and 'return 128' in p and 'return 96' in p and 'return 88' in p:
  print('APPLY_FIX338_ALREADY_APPLIED');return 0
 if m.get('version_name')!=OLD or m.get('version')!='1.14.0.2':raise RuntimeError('expected Fix 3.3.7 baseline')
 for k,path in [('content',cp),('policy',pp),('manifest',mp),('en',ep),('zh',zp)]:
  got=h(path)
  if got!=EXPECTED[k]:raise RuntimeError(f'{k} hash mismatch {got} != {EXPECTED[k]}')
 old='function Hz(e=``){let t=String(e).toLowerCase(),n=/(?:\\u7ee7\\u7eed.*(?:\\u76f4\\u5230|\\u5230).*\\u5b8c\\u6210|\\u76f4\\u5230.*\\u5b8c\\u6210|\\u5f7b\\u5e95\\u5b8c\\u6210|until.*complete|until.*done|finish.*everything)/i.test(t)||DPP_SHORT_CONTINUE_31(t)?36:/(?:\\u4ee3\\u7801|\\u6587\\u4ef6|\\u9879\\u76ee|\\u4fee\\u590d|\\u6c49\\u5316|\\u4ed3\\u5e93|\\u6784\\u5efa|\\u6d4b\\u8bd5|code|file|project|fix|repo|build|test)/i.test(t)?24:12;return{maxSteps:n,maxNudges:8,stepTimeoutMs:NR,requestDelayMinMs:PR,requestDelayMaxMs:FR,fullToolResultWindow:4}}'
 new='var DPP_AGENT_MIN_BUDGET_338=88,DPP_AGENT_PROJECT_BUDGET_338=96,DPP_AGENT_COMPLETION_BUDGET_338=128;function Hz(e=``){let t=String(e).toLowerCase(),n=/(?:\\u7ee7\\u7eed.*(?:\\u76f4\\u5230|\\u5230).*\\u5b8c\\u6210|\\u76f4\\u5230.*\\u5b8c\\u6210|\\u5f7b\\u5e95\\u5b8c\\u6210|until.*complete|until.*done|finish.*everything)/i.test(t)||DPP_SHORT_CONTINUE_31(t)?DPP_AGENT_COMPLETION_BUDGET_338:/(?:\\u4ee3\\u7801|\\u6587\\u4ef6|\\u9879\\u76ee|\\u4fee\\u590d|\\u6c49\\u5316|\\u4ed3\\u5e93|\\u6784\\u5efa|\\u6d4b\\u8bd5|code|file|project|fix|repo|build|test)/i.test(t)?DPP_AGENT_PROJECT_BUDGET_338:DPP_AGENT_MIN_BUDGET_338;return{maxSteps:n,maxNudges:8,stepTimeoutMs:NR,requestDelayMinMs:PR,requestDelayMaxMs:FR,fullToolResultWindow:4}}'
 s=rep(s,old,new,'inline agent step budgets')
 oldp='function stepLimit(text){if(!flags.dynamicStepLimit)return 20;let q=String(text??``).toLowerCase();if(/^\\s*(?:\\u7ee7\\u7eed|\\u63a5\\u7740|\\u7ee7\\u7eed\\u5427|\\u7ee7\\u7eed\\u6267\\u884c|continue|go\\s+on|carry\\s+on)\\s*[\\u3002.!\\uff01\\uff1f?]*\\s*$/i.test(q)||/(?:\\u7ee7\\u7eed.*(?:\\u76f4\\u5230|\\u5230).*\\u5b8c\\u6210|\\u76f4\\u5230.*\\u5b8c\\u6210|\\u5f7b\\u5e95\\u5b8c\\u6210|until.*complete|until.*done|finish.*everything)/i.test(q))return 36;if(/(?:\\u4ee3\\u7801|\\u6587\\u4ef6|\\u9879\\u76ee|\\u4fee\\u590d|\\u6c49\\u5316|\\u4ed3\\u5e93|\\u6784\\u5efa|\\u6d4b\\u8bd5|code|file|project|fix|repo|build|test)/i.test(q))return 24;return 12}'
 newp='function stepLimit(text){if(!flags.dynamicStepLimit)return 20;let q=String(text??``).toLowerCase();if(/^\\s*(?:\\u7ee7\\u7eed|\\u63a5\\u7740|\\u7ee7\\u7eed\\u5427|\\u7ee7\\u7eed\\u6267\\u884c|continue|go\\s+on|carry\\s+on)\\s*[\\u3002.!\\uff01\\uff1f?]*\\s*$/i.test(q)||/(?:\\u7ee7\\u7eed.*(?:\\u76f4\\u5230|\\u5230).*\\u5b8c\\u6210|\\u76f4\\u5230.*\\u5b8c\\u6210|\\u5f7b\\u5e95\\u5b8c\\u6210|until.*complete|until.*done|finish.*everything)/i.test(q))return 128;if(/(?:\\u4ee3\\u7801|\\u6587\\u4ef6|\\u9879\\u76ee|\\u4fee\\u590d|\\u6c49\\u5316|\\u4ed3\\u5e93|\\u6784\\u5efa|\\u6d4b\\u8bd5|code|file|project|fix|repo|build|test)/i.test(q))return 96;return 88}'
 p=rep(p,oldp,newp,'fix3 policy step budgets')
 m['version']='1.14.0.3';m['version_name']=NEW
 for obj in (en,zh):
  for key in ('extension_name','extension_action_title'):
   if key in obj and isinstance(obj[key],dict) and obj[key].get('message')==OLDN:obj[key]['message']=NEWN
   elif key in obj and isinstance(obj[key],dict):raise RuntimeError(f'{key} locale old name mismatch')
 atomic([(cp,s),(pp,p),(mp,json.dumps(m,ensure_ascii=False,indent=2)+'\n'),(ep,json.dumps(en,ensure_ascii=False,indent=2)+'\n'),(zp,json.dumps(zh,ensure_ascii=False,indent=2)+'\n')]);print('APPLY_FIX338_PASS');return 0
if __name__=='__main__':
 try:sys.exit(main(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1]))
 except Exception as e:print('APPLY_FIX338_FAIL:',e,file=sys.stderr);sys.exit(1)
