#!/usr/bin/env python3
"""配对转移表推广到所有场景(10-06, 用户「先做 C」): 同人同提示同噪声, 底座判「多手」的图在各组变成什么,
以及底座「画对」的图有多少变成「漏手」; 同时给总错误率(多手 + 漏手)的变化, 看总数掩盖了什么。裁判标签。
输出 20T paper/transitions_all.json。"""
import json, collections
R = "DATA/"
def cls(v): T = v.get("TOTAL"); return "clean" if v.get("ok") else ("comm" if (T or 0) >= 3 else ("omit" if T == 2 else "other"))
def L(p, pre=None, act=None):
    return {k.split("/", 1)[1]: cls(v) for k, v in json.load(open(R + p)).items() if (pre is None or k.startswith(pre)) and (act is None or f"_{act}_" in k)}
S = {}   # 场景名 -> [(底座标签, 组标签), ...] 按组
def add(name, arm, base, X):
    ks = sorted(set(base) & set(X)); S.setdefault(name, {})[arm] = [(base[k], X[k]) for k in ks]
# Klein 抱书, 三种子(种子 3 用 A100 底座)
B1 = L("gen_v3/vl8b.json", "base/", "a8"); B3 = L("seeds/vl8b_base_a100.json", None, "a8")
for arm, files in (("O", [("gen_v3/vl8b.json", "dd_v2/"), ("seeds/vl8b_dd_O_s2.json", None), ("seeds/vl8b_dd_O_s3_a100.json", None)]),
                   ("F", [("gen_v3/vl8b_v5f.json", None), ("seeds/vl8b_dd_F_s2.json", None), ("seeds/vl8b_dd_F_s3_a100.json", None)]),
                   ("R", [("gen_v3/vl8b_v5r.json", None), ("seeds/vl8b_dd_R_s2.json", None), ("seeds/vl8b_dd_R_s3_a100.json", None)]),
                   ("OP", [("op_arm/vl8b_dd_OP_s1.json", None), ("op_arm/vl8b_dd_OP_s2.json", None), ("op_arm/vl8b_dd_OP_s3.json", None)])):
    pairs = []
    for s, (p, pre) in enumerate(files, 1):
        X = L(p, pre, "a8"); B = B3 if s == 3 else B1; pairs += [(B[k], X[k]) for k in sorted(set(B) & set(X))]
    S.setdefault("Klein book (3 seeds)", {})[arm] = pairs
# Klein 四个新训练动作(修订 29, 种子 1)
for act, nm in (("a12", "Klein glasses+bottle (trained)"), ("a14", "Klein ear+newspaper (trained)")):
    b = L("new4/vl8b_base.json", None, act)
    for arm in ("O", "F", "R"): add(nm, arm, b, L(f"new4/vl8b_{arm}.json", None, act))
# 两个只评估的新动作(修订 16, 三种子合并)
for act, nm in (("a11", "Klein head+phone (eval only)"),):
    b = {k.split("/", 1)[1]: cls(v) for k, v in json.load(open(R + "newact/vl8b_base.json")).items() if f"_{act}_" in k}
    for arm in ("O", "F", "R", "OP"):
        pairs = []
        for s in (1, 2, 3):
            X = {k.split("/", 1)[1]: cls(v) for k, v in json.load(open(R + f"newact/vl8b_{arm}{s}.json")).items() if f"_{act}_" in k}
            pairs += [(b[k], X[k]) for k in sorted(set(b) & set(X))]
        S.setdefault(nm, {})[arm] = pairs
# DiffDoctor 当奖励(最终图, 修订 30), 同机底座
add("Klein book, DiffDoctor reward (final image)", "DD_fin", L("fin/vl8b_base.json", None, "a8"), L("fin/vl8b_DD.json", None, "a8"))
# SANA 拿花(裁判在 SANA 上不可靠, 只作参考), 三种子
SB = L("sana_paper/vl8b_base.json", "base/", "a9")
for arm, fs in (("O", ["vl8b_O", "vl8b_O_s2", "vl8b_O_s3"]), ("F", ["vl8b_F2", "vl8b_F2_s2", "vl8b_F2_s3"]), ("R", ["vl8b_R2", "vl8b_R2_s2", "vl8b_R2_s3"])):
    pairs = []
    for f in fs:
        X = L(f"sana_paper/{f}.json", None, "a9"); pairs += [(SB[k], X[k]) for k in sorted(set(SB) & set(X))]
    S.setdefault("SANA flower (3 seeds, judge unreliable)", {})[arm] = pairs
out = {}
for name, arms in S.items():
    out[name] = {}
    for arm, pr in arms.items():
        n = len(pr); c = collections.Counter(pr); bc = sum(v for (b, x), v in c.items() if b == "comm"); bk = sum(v for (b, x), v in c.items() if b == "clean")
        err_b = sum(v for (b, x), v in c.items() if b in ("comm", "omit")); err_x = sum(v for (b, x), v in c.items() if x in ("comm", "omit"))
        r = {"n": n, "base_comm": bc, "comm_to_omit": c[("comm", "omit")], "comm_to_clean": c[("comm", "clean")], "comm_to_comm": c[("comm", "comm")],
             "base_clean": bk, "clean_to_omit": c[("clean", "omit")], "base_omit": sum(1 for b, x in pr if b == "omit"), "arm_omit": sum(1 for b, x in pr if x == "omit"),
             "base_comm_total": sum(1 for b, x in pr if b == "comm"), "arm_comm_total": sum(1 for b, x in pr if x == "comm"),
             "err_base_pct": 100 * err_b / n, "err_arm_pct": 100 * err_x / n}
        out[name][arm] = r
        print(f"{name:45s} {arm:6s} n={n:5d} 底座多手 {bc:4d} → 漏手 {r['comm_to_omit']:3d} ({100*r['comm_to_omit']/max(bc,1):4.1f}%) 画对 {r['comm_to_clean']:3d} ({100*r['comm_to_clean']/max(bc,1):4.1f}%) | 画对→漏手 {r['clean_to_omit']:3d} | 总错 {r['err_base_pct']:.1f}% → {r['err_arm_pct']:.1f}% | 漏 {r['base_omit']}→{r['arm_omit']} 多 {r['base_comm_total']}→{r['arm_comm_total']}")
json.dump(out, open(R + "paper/transitions_all.json", "w"), indent=1)
