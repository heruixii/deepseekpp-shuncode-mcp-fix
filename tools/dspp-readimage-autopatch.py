#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeekPP `read_image` 自动读图 —— 幂等补丁脚本（Edge 解压扩展）

目标：让 read_image 返回的 image 内容块不再被丢弃，并复用 DeepSeek 原生
      上传通道（upload_file + ref_file_ids）使模型能"看到"。

安全设计：
  - --check 只检测锚点，不改任何文件；
  - 改动前自动备份为 *.dspp_bak；
  - 幂等：已打过补丁则跳过；
  - 锚点不唯一/缺失 → 拒绝改动并明确报错（绝不静默乱改）。

用法：
  python tools/dspp-readimage-autopatch.py --check
  python tools/dspp-readimage-autopatch.py
"""
import argparse, os, shutil, sys, time

EXT = r"D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3"
TARGET = os.path.join(EXT, "content-scripts", "content.js")

# 幂等标记
MARK = "/*DPP_READIMAGE_AUTOVISION*/"

# 正确路径 v3（两处锚点，完整逻辑）：
# 锚点1：捕获图像并异步上传（tool_execution_end 的 toolResult content 构造）
ANCHOR_1 = "content:[{type:`text`,text:Xz(e.result)}]"
REPL_1 = (
    "content:[{type:`text`,text:Xz(e.result)}],"
    "_dppImg:(function(){"
    "var _im=(e.result&&Array.isArray(e.result.content))"
    "?e.result.content.filter(function(b){return b&&b.type===`image`&&b.data}):[];"
    "if(_im.length){"
    "globalThis.DPP_RIF=globalThis.DPP_RIF||[];"
    "_im.forEach(function(b){"
    "var _m=b.mimeType||`image/png`;"
    "chrome.runtime.sendMessage({type:`UPLOAD_DEEPSEEK_IMAGE`,"
    "payload:{dataUrl:`data:${_m};base64,${b.data}`,name:`read_image`,mimeType:_m}},"
    "function(r){var id=r&&(r.fileId||r.id||(r.file&&(r.file.id||r.file.fileId))"
    "||(r.result&&(r.result.fileId||r.result.id)));"
    "if(id)globalThis.DPP_RIF.push(id);});"
    "});"
    "}"
    "return 0;"
    "})()"
)
# 锚点2：注入下一轮 ref_file_ids 并消费（turnDefaults）
ANCHOR_2 = "turnDefaults:{modelType:l.modelType,refFileIds:l.refFileIds,"
REPL_2 = (
    "turnDefaults:{modelType:l.modelType,refFileIds:(function(){"
    "var _f=(l.refFileIds||[]).slice();"
    "try{if(globalThis.DPP_RIF&&globalThis.DPP_RIF.length)"
    "_f=_f.concat(globalThis.DPP_RIF.splice(0));}catch(_e){}"
    "return _f;})(),"
)


def load(p):
    with open(p, "r", encoding="utf-8", errors="surrogateescape") as f:
        return f.read()


def save(p, s):
    tmp = p + ".tmp_%d" % int(time.time())
    with open(tmp, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(s)
    os.replace(tmp, p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true", help="显式确认后才真正改动")
    a = ap.parse_args()

    if not os.path.isfile(TARGET):
        print("ERROR: 未找到", TARGET); return 2
    d = load(TARGET)
    print("文件:", TARGET)
    print("大小:", len(d), "字节")
    print("已含标记:", MARK in d)

    n1 = d.count(ANCHOR_1)
    n2 = d.count(ANCHOR_2)
    print("锚点1(toolResult) 次数:", n1)
    print("锚点2(turnDefaults) 次数:", n2)

    if MARK in d:
        print("=> 已打过补丁，跳过。")
        return 0
    if n1 != 1 or n2 != 1:
        print("=> 锚点非唯一（需人工核对），拒绝改动。")
        return 3
    if a.check:
        print("=> --check：两锚点均就绪，可安全打补丁（--apply）。")
        return 0
    if not getattr(a, "apply", False):
        print("=> 未加 --apply，仅检查，不改动。（安全默认）")
        return 0

    bak = TARGET + ".dspp_bak"
    if not os.path.exists(bak):
        shutil.copy2(TARGET, bak); print("已备份 ->", bak)
    nd = d.replace(ANCHOR_1, MARK + REPL_1, 1).replace(ANCHOR_2, REPL_2, 1)
    if nd == d:
        print("=> 替换未生效，拒绝写入。")
        return 4
    save(TARGET, nd)
    # 安全网：apply 后立即 node --check，失败自动回滚
    import subprocess
    chk = TARGET + ".check.js"
    shutil.copy2(TARGET, chk)
    r = subprocess.run(["node", "--check", chk], capture_output=True, text=True)
    try:
        os.remove(chk)
    except OSError:
        pass
    if r.returncode != 0:
        shutil.copy2(bak, TARGET)
        print("=> 语法校验失败，已自动回滚！stderr:", (r.stderr or "")[:400])
        return 5
    print("=> 语法校验通过。已打补丁。请到 edge://extensions 重新加载扩展后测试。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
