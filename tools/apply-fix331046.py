#!/usr/bin/env python3
"""Hash-locked .36 -> .46 builder, chains .45; output must be a new directory."""
import argparse,hashlib,importlib.util,json,re,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
VERSION='1.14.0.51'
NAME='1.14.0 ShunCode MCP Fix 3.3.10.46'
def sha(b):return hashlib.sha256(b).hexdigest()
def check_sources():
    locks=json.loads((HERE/'fix331046-source-sha256.json').read_text('utf-8'))
    for name,digest in locks.items():
        if sha((HERE/name).read_bytes())!=digest:raise ValueError('Source hash mismatch: '+name)
def build(base,output):
    check_sources()
    base=Path(base).resolve();output=Path(output).resolve()
    if output.exists() or output==base or base in output.parents:raise ValueError('Output must be new and outside baseline')
    stage=output.with_name(output.name+'.stage45')
    if stage.exists():raise ValueError('Staging path exists')
    spec=importlib.util.spec_from_file_location('b45',HERE/'apply-fix331045.py');b45=importlib.util.module_from_spec(spec);spec.loader.exec_module(b45)
    values=b45.build(base,stage)
    bg=values['background.js']
    for old,name in [(b45.NEW_NU,'dspp-cache-nu-v46.js'),(b45.NEW_SC,'dspp-cache-sc-v46.js')]:
        new=(HERE/name).read_text('utf-8').strip()
        bg=b45.once(bg,old.encode(),new.encode())
    values['background.js']=bg
    m=json.loads(values['manifest.json']);m['version']=VERSION;m['version_name']=NAME
    values['manifest.json']=(json.dumps(m,indent=2,ensure_ascii=False)+'\n').encode()
    for lang in ['en','zh_CN']:
        name=f'_locales/{lang}/messages.json'
        values[name]=b45.once(values[name],'DeepSeek++ ShunCode MCP Fix 3.3.10.45','DeepSeek++ ShunCode MCP Fix 3.3.10.46')
    for name in list(values):
        if '/' not in name and 'selftest' in name and name.endswith('.js'):
            s=values[name].decode().replace('1.14.0.50',VERSION).replace('1.14.0 ShunCode MCP Fix 3.3.10.45',NAME)
            s=s.replace('manifest version_name is Fix 3.3.10.45','manifest version_name is Fix 3.3.10.46').replace('|44|45)$','|44|45|46)$')
            if name=='dspp-bare-tool-tag-v41-selftest.js':s=re.sub(r"bgSha === '[0-9a-f]{64}'",f"bgSha === '{sha(bg)}'",s)
            if name=='dspp-mcp-cache-v45-selftest.js':
                s=s.replace("bg.includes('ju(e).catch')","bg.includes('ju(id).catch')")
                s=s.replace("bg.includes('o=new Set')","bg.includes('refreshIds=new Set')").replace("bg.includes('expiresAt<=r')","bg.includes('cache.expiresAt<=now')")
            values[name]=s.encode()
    values['dspp-mcp-cache-v46-selftest.js']=(HERE/'dspp-mcp-cache-v46-selftest.js').read_bytes()
    for name in ['background.js','content-scripts/content.js','content-scripts/main-world.js','fix3-policy.js']:
        r=subprocess.run(['node','--check','--input-type=module'],input=values[name],capture_output=True)
        if r.returncode:raise ValueError('Syntax failed: '+name+' '+r.stderr.decode(errors='replace'))
    output.mkdir(parents=True)
    for name,raw in values.items():
        p=output/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    shutil.rmtree(stage)
    print(json.dumps({'version':VERSION,'files':len(values),'background_sha256':sha(bg)}),flush=True)
    return values
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',nargs=2,required=True);a=p.parse_args()
    try:build(*a.build)
    except (ValueError,OSError) as e:raise SystemExit('FAIL-CLOSED: '+str(e))
