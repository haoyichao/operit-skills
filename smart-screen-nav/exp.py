#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能屏幕操作经验库（SQLite 版）  —— 快检索 / 省Token / 自动去重升级 / 方案归类
用法:
  exp.py add  <场景> <成功路径> <避坑> [高|中|低] [通用|个人] [策略]   添加
              # 策略 = auto(不限) / p1~p5 / 多值用逗号如 p1,p3
  exp.py query <关键词> [--brief] [n]                 检索(评分→top-N, 默认3)
  exp.py hit  <id>                                     标记该条目命中一次
  exp.py promote                                       自动把高命中条目升为"高"可复用度
  exp.py clean [days]                                  清理过时/待验证条目
  exp.py report                                        输出经验总结精华
  exp.py list                                          列表:id|场景|可复用度|命中|状态|通用/个人|策略
  exp.py tag  <id> 通用|个人                           改经验类型(通用/个人)
  exp.py strat <id> <p1|p2|...>                        改方案归类(auto或p1~p5可多值)
  exp.py seed ./generic-exp.seed                       导出【通用】经验为种子(带策略)
  exp.py import ./generic-exp.seed                     导入种子到本地(带策略归位)
  exp.py migrate                                       从旧 md 迁移
"""
import sys, os, sqlite3, datetime, re

BASE = "/storage/emulated/0/Download/Operit/skill-data/smart-screen-nav/经验库"
DB = os.path.join(BASE, "exp.db")
MD = os.path.join(BASE, "screen-nav-experience.md")
RW = {"高": 3, "中": 2, "低": 1}
STRATS = {"auto", "p1", "p2", "p3", "p4", "p5"}


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS exp(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scene TEXT, path TEXT, pit TEXT,
        reuse TEXT DEFAULT '中', hits INTEGER DEFAULT 0,
        status TEXT DEFAULT 'valid',
        created TEXT, updated TEXT)""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_scene ON exp(scene)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_reuse ON exp(reuse,hits)")
    try:
        c.execute("ALTER TABLE exp ADD COLUMN type TEXT DEFAULT '通用'")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE exp ADD COLUMN strategy TEXT DEFAULT 'auto'")
    except Exception:
        pass
    return c


def _reuse(reuse):
    return reuse if reuse in RW else "中"


def _merge_strat(a, b):
    """合并两段策略标记，去重；保留非auto的明确值，auto视为不限"""
    vals = []
    for s in [a, b]:
        for v in (s or "").replace("，", ",").split(","):
            v = v.strip()
            if v and v != "auto" and v not in vals:
                vals.append(v)
    return ",".join(vals) if vals else "auto"


def add(scene, path, pit, reuse="中", typ="通用", strat="auto"):
    c = db()
    kw = [w for w in re.split(r"[\s,，、。/+:-]+", scene) if len(w) >= 2]
    existed = None
    if kw:
        q = " OR ".join(["scene LIKE ?"] * len(kw))
        rows = c.execute("SELECT * FROM exp WHERE status!='deprecated' AND (" + q + ")",
                         ["%" + k + "%" for k in kw]).fetchall()
        best = max(rows, key=lambda r: sum(k in r[1] for k in kw), default=None)
        if best and sum(k in best[1] for k in kw) >= 2:
            existed = best
    if existed:
        rr = max(RW[_reuse(reuse)], RW[existed[4]])
        reuse_txt = [k for k, v in RW.items() if v == rr][0]
        ms = _merge_strat(existed[9] if len(existed) > 9 else None, strat)
        c.execute("UPDATE exp SET path=?, pit=?, reuse=?, hits=?, strategy=?, updated=? WHERE id=?",
                  (path, pit, reuse_txt, existed[5] + 1, ms, now(), existed[0]))
        c.commit()
        print("已合并更新 #%d: %s (命中+1, 策略=%s)" % (existed[0], scene, ms))
    else:
        c.execute("INSERT INTO exp(scene,path,pit,reuse,type,strategy,status,created,updated) VALUES(?,?,?,?,?,?,'valid',?,?)",
                  (scene, path, pit, _reuse(reuse), typ, strat if strat in STRATS or "," in strat else "auto", now(), now()))
        c.commit()
        print("已新增: %s [类型=%s 策略=%s]" % (scene, typ, strat))


def query(kw, brief=False, n=3):
    c = db()
    words = [w for w in re.split(r"[\s,，、。/+:-]+", kw) if len(w) >= 2]
    if not words:
        print("关键词太短"); return
    like = " OR ".join(["scene LIKE ?"] * len(words))
    rows = c.execute("SELECT * FROM exp WHERE status='valid' AND (" + like + ")",
                     ["%" + w + "%" for w in words]).fetchall()
    if len(words) == 1:
        ids = [r[0] for r in rows]
        pl = (" AND id NOT IN (" + ",".join(map(str, ids)) + ")") if ids else ""
        rows += c.execute("SELECT * FROM exp WHERE status='valid' AND (path LIKE ? OR pit LIKE ?)" + pl,
                          ["%" + words[0] + "%"] * 2).fetchall()
    scored = []
    for r in rows:
        s = sum(r[1].count(w) * 2 + (r[2] or "").count(w) + (r[3] or "").count(w) for w in words)
        s += RW.get(r[4], 1) * 3 + (r[5] or 0) * 2
        scored.append((s, r))
    scored.sort(key=lambda x: -x[0])
    if not scored:
        print("无匹配:", kw); return
    for s, r in scored[:n]:
        if brief:
            print("#%d [%s|命中%d|%s|策略%s] %s → %s" % (r[0], r[8], r[5], r[4],
                  r[9] if len(r) > 9 else "auto", r[1], (r[2] or "").replace("\n", " ")[:60]))
        else:
            print("【场景】%s\n【成功路径】\n%s\n【避坑】%s\n【可复用度】%s 命中%d  类型:%s 策略:%s  更新:%s\n----" %
                  (r[1], r[2], r[3], r[4], r[5], r[8] if len(r) > 8 else "通用", r[9] if len(r) > 9 else "auto", r[8]))


def hit(rid):
    c = db()
    c.execute("UPDATE exp SET hits=hits+1, updated=? WHERE id=?", (now(), rid))
    c.commit()
    print("已命中 #%s +1" % rid)


def promote():
    c = db()
    n = c.execute("UPDATE exp SET reuse='高' WHERE hits>=3 AND reuse!='高'").rowcount
    c.commit()
    print("已自动提升 %d 条为『高』可复用度" % n)


def clean(days=14):
    c = db()
    c.execute("UPDATE exp SET status='deprecated' WHERE hits=0 AND datetime(updated)<? ",
              (datetime.datetime.now() - datetime.timedelta(days=days),))
    c.commit()
    n = c.execute("SELECT COUNT(*) FROM exp WHERE status='deprecated'").fetchone()[0]
    print("已标记过时/未命中条目 %d 条（deprecated）" % n)


def report():
    c = db()
    rows = c.execute("SELECT * FROM exp WHERE status='valid' ORDER BY hits DESC").fetchall()
    if not rows:
        print("暂无经验"); return
    print("== 经验精华总结（共 %d 条，按命中优先） ==" % len(rows))
    for r in rows[:8]:
        print("[%s|命中%d|策略%s] %s\n  %s\n" % (r[4], r[5], r[9] if len(r) > 9 else "auto",
              r[1], (r[2] or "").replace("\n", " ")[:100]))


def lst():
    c = db()
    for r in c.execute("SELECT id,scene,reuse,hits,status,type,strategy FROM exp ORDER BY hits DESC, id"):
        print("#%d | %s | %s | 命中%d | %s | %s | 策略%s" % (r[0], r[1], r[2], r[3], r[4], r[5], r[6]))

import json as _json


def del_exp(rid):
    c = db()
    c.execute("DELETE FROM exp WHERE id=?", (rid,))
    c.commit()
    print("已删除经验 #%s" % rid)


def seed(file):
    """导出/累积【通用】经验为种子(带策略)；个人经验不导出"""
    c = db()
    rows = c.execute("SELECT scene,path,pit,reuse,strategy FROM exp WHERE status='valid' AND type='通用'").fetchall()
    existing = {}
    if os.path.exists(file):
        for ln in open(file, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try:
                    d = _json.loads(ln)
                    existing[d.get("scene", "")] = d
                except Exception:
                    pass
    for r in rows:
        existing[r[0]] = {"scene": r[0], "path": r[1] or "", "pit": r[2] or "",
                          "reuse": r[3], "strategy": r[4]}
    with open(file, "w", encoding="utf-8") as f:
        for d in existing.values():
            f.write(_json.dumps(d, ensure_ascii=False) + "\n")
    print("已累积 %d 条【通用】经验 → %s（个人经验不导出）" % (len(existing), file))


def tag(rid, typ):
    c = db()
    c.execute("UPDATE exp SET type=? WHERE id=?", (typ, rid))
    c.commit()
    print("已标记 #%s 为【%s】经验" % (rid, typ))


def strat(rid, s):
    c = db()
    c.execute("UPDATE exp SET strategy=? WHERE id=?", (s, rid))
    c.commit()
    print("已标记 #%s 方案归类为【%s】" % (rid, s))


def imp(file):
    if not os.path.exists(file):
        print("种子不存在:", file); return
    n = 0
    for ln in open(file, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = _json.loads(ln)
            add(d["scene"], d["path"] or "", d["pit"] or "", d.get("reuse", "中"),
                "通用", d.get("strategy", "auto"))
            n += 1
        except Exception:
            pass
    print("导入完成 %d 条" % n)


def migrate():
    if not os.path.exists(MD):
        print("旧md不存在"); return
    text = open(MD, encoding="utf-8").read()
    blocks = re.split(r"【时间】", text)
    n = 0
    for b in blocks[1:]:
        m = re.search(r"【场景】(.+)", b)
        p = re.search(r"【成功路径】\n```\n(.+?)\n```", b, re.S)
        x = re.search(r"【避坑/更新点】(.+)", b)
        if m:
            scene = m.group(1).strip()
            if scene.startswith("一句话") or scene.startswith("用MT打开md"):
                continue
            add(scene, (p.group(1).strip() if p else ""),
                (x.group(1).strip() if x else ""), "高")
            n += 1
    print("迁移完成（去重后 %d 块）" % n)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(0)
    a = sys.argv
    if a[1] == "add" and len(a) >= 5:
        add(a[2], a[3].replace("\\n", "\n"), a[4],
            a[5] if len(a) >= 6 else "中",
            a[6] if len(a) >= 7 else "通用",
            a[7] if len(a) >= 8 else "auto")
    elif a[1] == "query" and len(a) >= 3:
        brief = "--brief" in a
        n = 3
        for x in a:
            if x.isdigit():
                n = int(x)
        query(a[2], brief, n)
    elif a[1] == "hit":
        hit(a[2])
    elif a[1] == "promote":
        promote()
    elif a[1] == "clean":
        clean(int(a[2]) if len(a) >= 3 else 14)
    elif a[1] == "report":
        report()
    elif a[1] == "list":
        lst()
    elif a[1] == "del":
        del_exp(a[2])
    elif a[1] == "tag" and len(a) >= 4:
        tag(a[2], a[3])
    elif a[1] == "strat" and len(a) >= 4:
        strat(a[2], a[3])
    elif a[1] == "seed" and len(a) >= 3:
        seed(a[2])
    elif a[1] == "import" and len(a) >= 3:
        imp(a[2])
    elif a[1] == "migrate":
        migrate()
    else:
        print(__doc__)