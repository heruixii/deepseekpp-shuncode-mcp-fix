#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeekPP read_image 自动读图 —— v4 补丁（修正 v3 的 sizeBytes 缺陷）

v3 失效根因：background 的 UPLOAD_DEEPSEEK_IMAGE 处理器 bP() 强校验 payload.sizeBytes，
            v3 未带 → 上传抛错。
v4 修正：payload 带 sizeBytes（由 base64 长度推算）；取 id 用 r.file.id
         （uploadImage 返回 {ok:true, file:{id,fileName,fileSize,mimeType}}）。

安全：--check 只检测；改动前备份 *.v4_bak；幂等；锚点非唯一则拒绝。
用法：
  python tools/dspp-readimage-v4-patch.py --check
  python tools/dspp-readimage-v4-patch.py
"""
import argparse, os, shutil, sys, time

EXT = r"D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3"
TARGET = os.path.join(EXT, "content-scripts", "content.js")
MARK = "/*DPP_READIMAGE_V4*/"

# 锚点 A：toolResult content（图像在此被丢弃）
A_OLD = "content:[{type:`text`,text:Xz(e.result)}]"
A_NEW = (
    MARK +
    "content:[{type:`text`,text:Xz(e.result)},"
    "...((e.result&&Array.isArray(e.result.content))"
    "?e.result.content.filter(function(b){return b&&b.type===`image`&&b.data}):[])],"
    "_dppUpload:(function(){try{var _im=(e.result&&Array.isArray(e.result.content))"
    "?e.result.content.filter(function(b){return b&&b.type===`image`&&b.data}):[];"
    "if(!_im.length)return 0;globalThis.DPP_RIF=globalThis.DPP_RIF||[];"
    "_im.forEach(function(b){var _m=b.mimeType||`image/png`;"
    "var _b64=String(b.data||``).replace(/=+$/,``);"
    "var _sz=Math.max(1,Math.floor(_b64.length*3/4));"
    "chrome.runtime.sendMessage({type:`UPLOAD_DEEPSEEK_IMAGE`,"
    "payload:{dataUrl:`data:${_m};base64,${b.data}`,name:`read_image`,"
    "mimeType:_m,sizeBytes:_sz}},function(r){"
    "try{var id=r&&(r.file&&r.file.id||r.fileId||r.id||"
    "(r.result&&(r.result.file&&r.result.file.id||r.result.id)));"
    "if(id)globalThis.DPP_RIF.push(id);}catch(_e){}});});}catch(_e){}return 0;})()"
)

# 锚点 B：每轮请求参数 refFileIds（turnDefaults 组装处）
B_OLD = "refFileIds:o.refFileIds,thinkingEnabled:o.thinkingEnabled"
B_NEW = (
    "refFileIds:(function(){var _f=(o.refFileIds||[]).slice();"
    "try{if(globalThis.DPP_RIF&&globalThis.DPP_RIF.length)"
    "_f=_f.concat(globalThis.DPP_RIF.splice(0));}catch(_e){}return _f;})(),"
    "thinkingEnabled:o.thinkingEnabled"
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
    if not os.path.isfile(TARGET):
        print("ERROR: 未找到", TARGET); return 2
    d = load(TARGET)
    print("文件:", TARGET, "| 大小:", len(d))
    print("已含 v4 标记:", MARK in d)
    na, nb = d.count(A_OLD), d.count(B_OLD)
    print("锚点A 次数:", na, "| 锚点B 次数:", nb)
    if MARK in d:
        print("=> 已打过 v4 补丁，跳过。"); return 0
    if na != 1 or nb != 1:
        print("=> 锚点非唯一，拒绝改动。"); return 3
    if a.check:
        print("=> --check：锚点就绪，可打 v4 补丁。"); return 0
    bak = TARGET + ".v4_bak"
    if not os.path.exists(bak):
        shutil.copy2(TARGET, bak); print("已备份 ->", bak)
    nd = d.replace(A_OLD, A_NEW, 1).replace(B_OLD, B_NEW, 1)
    assert nd != d
    save(TARGET, nd)
    print("v4 补丁已应用。请到 edge://extensions 重载扩展后测试。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
