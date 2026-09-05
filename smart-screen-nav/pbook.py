#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
屏幕操作 Playbook 引擎  —— 环境指纹 → 最优命令剧本（肌肉记忆/免思考秒执行）
用法:
  pbook.py add <名字> <场景> <环境特征(;分隔)> <命令剧本(\n)>
            # 第一次摸索成功后，把"该环境特征"与"最优命令序列"绑定保存
  pbook.py match <当前界面特征(;分隔)>   # 提交当前dump特征，命中即给出剧本(免推理)
  pbook.py run <名字> [--dry]            # 执行剧本(--dry只打印供安卓shell执行)
  pbook.py list
"""
import sys, os, json, re, datetime

BASE = "/storage/emulated/0/Download/Operit/skill-data/smart-screen-nav/经验库"
DB = os.path.join(BASE, "pbook.json")


def load():
    if os.path.exists(DB):
        return json.load(open(DB, encoding="utf-8"))
    return {}


def save(store):
    json.dump(store, open(DB, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def toks(s):
    return set(re.split(r"[\s,，、。;；/+:-]+", s)) - {""}


def add(name, scene, sig, playbook):
    store = load()
    store[name] = {"scene": scene, "sig": sig, "playbook": playbook,
                   "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    save(store)
    print("已保存剧本 [%s] 场景:%s" % (name, scene))


def match(feat):
    store = load()
    ft = toks(feat)
    best = None; bestov = 0
    for n, e in store.items():
        ov = len(ft & toks(e["sig"]))
        if ov >= 2 and ov > bestov:
            best = n; bestov = ov
    if not best:
        print("无匹配剧本（可 add 保存新路径）"); return
    e = store[best]
    print("✔ 命中剧本 [%s] 环境重叠%d  %s" % (best, bestov, e["scene"]))
    print("【免推理直接执行】\n" + e["playbook"])


def run(name, dry=True):
    store = load()
    if name not in store:
        print("剧本不存在:", name); return
    pb = store[name]["playbook"]
    if dry:
        print("--dry-- 将依次执行：\n" + pb)
        return
    for ln in pb.splitlines():
        if ln.strip():
            print("执行: " + ln)


def lst():
    store = load()
    for n, e in store.items():
        print("[%s] %s  (环境特征: %s)  %s" % (n, e["scene"], e["sig"], e["ts"]))


if __name__ == "__main__":
    a = sys.argv
    if len(a) < 2:
        print(__doc__); sys.exit(0)
    if a[1] == "add" and len(a) >= 6:
        add(a[2], a[3], a[4], a[5].replace("\\n", "\n"))
    elif a[1] == "match" and len(a) >= 3:
        match(a[2])
    elif a[1] == "run":
        run(a[2], "--dry" in a)
    elif a[1] == "list":
        lst()
    else:
        print(__doc__)