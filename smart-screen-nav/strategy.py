#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方案选择状态层（strategy.py）  —— 持久化管理"设备可达性执行策略"当前生效模式
背景: 用户可在 Operit 选择任意一种方案执行屏幕操作；选了记住直到下次改；不选=true(智能混合择优)。

用法:
  strategy.py list                    列出 5 种方案 + 当前生效模式
  strategy.py get                     显示当前生效模式(优先临时任务覆盖,其次全局,默认 auto)
  strategy.py set  <auto|p1|p2|p3|p4|p5>  设置全局默认模式(持久化)
  strategy.py temp <auto|p1|p2|p3|p4|p5>  设置单次任务临时覆盖(下一个任务后建议清除)
  strategy.py clear                    清除临时任务覆盖(回到全局/默认)
  strategy.py mode <auto|p1|...>       兼容别名 = set

模式:
  auto  智能混合(默认)  5 种方案模型按场景择优(p1→p2→p3→p4 降级, p5 兜底)
  p1    系统框架 API 直调   命令直达优先(am start / pm / dumpsys 等)
  p2    预置脚本快路径      命中 Playbook 即整段执行, 免推理
  p3    全量人工注入        所有交互强制走拟人化注入(input), 禁用命令直达
  p4    混合分层            = p2 优先, 无脚本回退 p3
  p5    虚拟显示注入        需部分 root, 未 root 应降级提示

状态文件: <经验库目录>/strategy.json  (外部路径, 删除 Skill 不丢失)
"""
import sys, os, json, datetime

BASE = "/storage/emulated/0/Download/Operit/skill-data/smart-screen-nav/经验库"
STATE = os.path.join(BASE, "strategy.json")
MODES = {"auto", "p1", "p2", "p3", "p4", "p5"}
NAMES = {
    "auto": "智能混合(择优)",
    "p1": "系统框架 API 直调",
    "p2": "预置脚本快路径",
    "p3": "全量人工注入",
    "p4": "混合分层",
    "p5": "虚拟显示注入(需root)",
}


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def load():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save(d):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def get_effective():
    d = load()
    temp = d.get("temp")
    if temp in MODES:
        return temp
    g = d.get("global", "auto")
    return g if g in MODES else "auto"


def mode_list():
    d = load()
    cur = get_effective()
    print("当前生效模式: %s（%s）" % (cur, NAMES[cur]))
    print("  全局默认: %s | 临时覆盖: %s | 设置时间: %s" %
          (d.get("global", "auto"), d.get("temp", "无"), d.get("set_at", "-")))
    print("\n可选方案:")
    for m in ["p1", "p2", "p3", "p4", "p5"]:
        print("  %s  %-14s %s" % (m, NAMES[m], "← 当前" if cur == m else ""))


def set_global(mode):
    if mode not in MODES:
        print("非法模式: %s（可选 %s）" % (mode, ",".join(sorted(MODES)))); return
    d = load()
    d["global"] = mode
    d["set_at"] = now()
    save(d)
    print("已设置全局默认模式【%s】%s" % (mode, NAMES[mode]))


def set_temp(mode):
    if mode not in MODES:
        print("非法模式: %s（可选 %s）" % (mode, ",".join(sorted(MODES)))); return
    d = load()
    d["temp"] = mode
    d["set_at"] = now()
    save(d)
    print("已设置单次任务临时模式【%s】%s（任务后可用 clear 清除）" % (mode, NAMES[mode]))


def clear_temp():
    d = load()
    d.pop("temp", None)
    save(d)
    print("已清除临时覆盖，回到: %s" % get_effective())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(0)
    a = sys.argv
    if a[1] in ("list", "ls") :
        mode_list()
    elif a[1] == "get":
        m = get_effective()
        print("%s/%s" % (m, NAMES[m]))
    elif a[1] in ("set", "mode") and len(a) >= 3:
        set_global(a[2])
    elif a[1] == "temp" and len(a) >= 3:
        set_temp(a[2])
    elif a[1] == "clear":
        clear_temp()
    else:
        print(__doc__)