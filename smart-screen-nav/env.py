#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本/环境指纹引擎 env.py —— 当"操作和上次不一样"时，先判断是App/系统升级还是纯UI变化
用法:
  env.py save <key> <appName> <appVer> <osVer> <sdk> <build>
            # 绑定某条经验对应的环境版本（App版本 + 系统版本）
  env.py check <key> <appVer> <osVer> [<sdk>]
            # 对比当前传入版本 vs 已存版本，诊断"是升级了还是纯UI变化"
  env.py list
"""
import sys, os, json

BASE = "/storage/emulated/0/Download/Operit/skill-data/smart-screen-nav/经验库"
DB = os.path.join(BASE, "env.json")


def load():
    if os.path.exists(DB):
        return json.load(open(DB, encoding="utf-8"))
    return {}


def save(store):
    json.dump(store, open(DB, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def save_env(key, app, aver, oser, sdk, build):
    store = load()
    store[key] = {"app": app, "appVer": aver, "osVer": oser, "sdk": sdk,
                  "build": build}
    save(store)
    print("已保存环境指纹 [%s] App:%s v%s | OS:%s sdk%s" % (key, app, aver, oser, sdk))


def check(key, cur_aver, cur_oser, cur_sdk=""):
    store = load()
    if key not in store:
        print("请先 env.py save 该经验的环境指纹:", key); return
    e = store[key]
    msgs = []
    # 系统版本对比
    if cur_oser and cur_oser != e["osVer"]:
        msgs.append("系统已升级：%s → %s（Android 版本变化，可能影响权限/界面/组件行为）"
                    % (e["osVer"], cur_oser))
    elif cur_sdk and cur_sdk != e["sdk"]:
        msgs.append("系统 SDK 已变化：%s → %s" % (e["sdk"], cur_sdk))
    # App版本对比
    if cur_aver and cur_aver != e["appVer"]:
        msgs.append("App 已升级：%s v%s → v%s（UI 布局/文案/菜单可能改变，旧路径可能失效）"
                    % (e["app"], e["appVer"], cur_aver))
    if msgs:
        print("⚠ 环境已变化：")
        print("\n".join(msgs))
        print("→ 旧经验/剧本可能失效，需【重新走通】并 update 该经验（绑定新版本指纹）。")
    else:
        print("✔ 版本未变（App v%s / OS v%s）。若仍操作异常，则是【同版本UI微调/布局变化】，"
              "重新 dump 定位即可，不必重设版本指纹。" % (cur_aver, cur_oser))


def lst():
    store = load()
    for k, e in store.items():
        print("[%s] %s v%s | OS:%s sdk%s build:%s" % (k, e["app"], e["appVer"],
              e["osVer"], e["sdk"], e["build"]))


if __name__ == "__main__":
    a = sys.argv
    if len(a) < 2:
        print(__doc__); sys.exit(0)
    if a[1] == "save" and len(a) >= 7:
        save_env(a[2], a[3], a[4], a[5], a[6], a[7])
    elif a[1] == "check" and len(a) >= 5:
        check(a[2], a[3], a[4], a[5] if len(a) >= 6 else "")
    elif a[1] == "list":
        lst()
    else:
        print(__doc__)