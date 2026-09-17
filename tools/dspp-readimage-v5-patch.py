#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeekPP read_image 自动读图 v5。
修复 v4 缺陷：v4 只在 e.result.content 找 image 块；实际结果结构是
{ok,name,summary,detail,output,...}，图像在 output/structuredContent/data_uri。
v5 多来源提取 data URL：content[].image → data_uri/dataUri → structuredContent.* → output.*
从 v4_bak 恢复原始后再打 v5；备份 *.v5_bak；幂等；--check 只检测。
"""
import argparse, os, shutil, sys, time

EXT = r"D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3"
T = os.path.join(EXT, "content-scripts", "content.js")
BAK4 = T + ".v4_bak"
BAK5 = T + ".v5_bak"
MARK = "/*DPP_READIMAGE_V5*/"

A_OLD = "content:[{type:`text`,text:Xz(e.result)}]"
B_OLD = "refFileIds:o.refFileIds,thinkingEnabled:o.thinkingEnabled"

JS_A = (
 MARK+"content:[{type:`text`,text:Xz(e.result)}],_dppUp:(function(){try{"
 "var _u=[];function _ad(d){if(typeof d!=='string')return;var m=d.match(/^data:(image\\/[a-z0-9.+-]+);base64,([\\s\\S]*)$/i);"
 "if(m)_u.push({mime:m[1],data:m[2].replace(/\\s/g,'')});}"
 "function _walk(o,dep){if(!o||dep>3)return;if(Array.isArray(o)){o.forEach(function(x){_walk(x,dep+1)});return;}"
 "if(typeof o!=='object')return;"
 "if(o.type==='image'&&o.data)_u.push({mime:o.mimeType||'image/png',data:o.data});"
 "_ad(o.data_uri);_ad(o.dataUri);_ad(o.dataURL);"
 "for(var k in o){try{if(k!=='data'&&k!=='content'||true)_walk(o[k],dep+1)}catch(_e){}}}"
 "var R=e.result||{};_walk(R,0);"
 "if(!_u.length)return 0;"
 "var _seen={};_u=_u.filter(function(x){if(_seen[x.data])return false;_seen[x.data]=1;return true;});"
 "globalThis.DPP_RIF=globalThis.DPP_RIF||[];"
 "_u.forEach(function(x){var _s=String(x.data||'').replace(/=+$/,'');var _z=Math.max(1,Math.floor(_s.length*3/4));"
 "chrome.runtime.sendMessage({type:'UPLOAD_DEEPSEEK_IMAGE',"
 "payload:{dataUrl:'data:'+x.mime+';base64,'+x.data,name:'read_image',mimeType:x.mime,sizeBytes:_z}},"
 "function(r){try{var id=r&&(r.file&&r.file.id||r.fileId||r.id||(r.result&&(r.result.file&&r.result.file.id||r.result.id)));"
 "if(id)globalThis.DPP_RIF.push(id);}catch(_e){}});});}catch(_e){}return 0;})()"
)

JS_B = (
 "refFileIds:(function(){var _f=(o.refFileIds||[]).slice();"
 "try{if(globalThis.DPP_RIF&&globalThis.DPP_RIF.length)_f=_f.concat(globalThis.DPP_RIF.splice(0));}"
 "catch(_e){}return _f;})(),thinkingEnabled:o.thinkingEnabled"
)


def load(p):
    return open(p, "r", encoding="utf-8", errors="surrogateescape").read()


def save(p, s):
    t = p + ".tmp_%d" % int(time.time())
    open(t, "w", encoding="utf-8", errors="surrogateescape").write(s)
    os.replace(t, p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not a.check:
        print("ERROR: v5 is retired; use dspp-readimage-v6-patch.py. --check remains read-only.")
        return 2
    cur = load(T)
    if ("DPP_READIMAGE_V4" in cur) or ("DPP_READIMAGE_V5" in cur):
        if not os.path.exists(BAK4):
            print("ERROR: 缺 v4_bak，无法恢复"); return 2
        if a.check:
            print("当前含旧补丁；将先由 v4_bak 恢复再打 v5。")
        else:
            shutil.copy2(BAK4, T); print("已由 v4_bak 恢复原始")
        cur = load(BAK4)
    na, nb = cur.count(A_OLD), cur.count(B_OLD)
    print("锚点A:", na, "| 锚点B:", nb)
    if na != 1 or nb != 1:
        print("=> 锚点非唯一，拒绝改动"); return 3
    if a.check:
        print("=> check OK，可打 v5"); return 0
    if not os.path.exists(BAK5):
        shutil.copy2(T, BAK5); print("备份 ->", BAK5)
    save(T, cur.replace(A_OLD, JS_A, 1).replace(B_OLD, JS_B, 1))
    print("v5 已应用；请到 edge://extensions 重载。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
