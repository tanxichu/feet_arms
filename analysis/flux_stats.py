#!/usr/bin/env python3
"""PREREG 修订 25: FLUX.1-schnell 的 O/F/R 与底座, 种子 1。留出的人(vl8b_<组>.json, 每条件 6 噪声)与训练的人大集(vl8b_<组>_big.json, 8 噪声)分开报;
抱书 a8 / 拿花 a9 分开。配对: 同 (人, 动作, 噪声) 精确 McNemar + 按人翻符号置换(2 万次)。输出 20T paper/flux_stats.json。"""
import json, random, collections
from math import comb
R = "DATA/flux/"
def omit(v): return int(not v.get("ok") and v.get("TOTAL") == 2)
def extra(v): return int(not v.get("ok") and (v.get("TOTAL") or 0) >= 3)
def L(arm, big): return {k.split("/", 1)[1]: v for k, v in json.load(open(f"{R}vl8b_{arm}{'_big' if big else ''}.json")).items()}
def mc(b, c):
    n = b + c; return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
def perm(d, it=20000):
    rng = random.Random(0); o = abs(sum(d)); return (sum(abs(sum(x if rng.random() < .5 else -x for x in d)) >= o - 1e-9 for _ in range(it)) + 1) / (it + 1)
out = {}
for big, name in ((True, "train"), (False, "hold"), (None, "all")):
    J = {a: ({**L(a, True), **{"h_" + k: v for k, v in L(a, False).items()}} if big is None else L(a, big)) for a in ("base", "O", "F", "R")}
    for act in ("a8", "a9", "all"):
        ks = sorted(k for k in J["base"] if (act == "all" or f"_{act}_" in k) and all(k in J[a] for a in J))
        rate = {a: {"n": len(ks), "omit": sum(omit(J[a][k]) for k in ks), "extra": sum(extra(J[a][k]) for k in ks), "ok": sum(bool(J[a][k].get("ok")) for k in ks)} for a in J}
        tests = {}
        for a1, a2 in (("base", "O"), ("O", "F"), ("O", "R"), ("R", "F"), ("base", "F")):
            b = sum(omit(J[a1][k]) and not omit(J[a2][k]) for k in ks); c = sum(omit(J[a2][k]) and not omit(J[a1][k]) for k in ks)
            cl = collections.defaultdict(int)
            for k in ks: cl[k.split("_")[0].replace("h", "") if k.startswith("h_") else k.split("_")[0]] += omit(J[a1][k]) - omit(J[a2][k])
            tests[f"{a1}{a2}"] = {"a1_only": b, "a2_only": c, "p_mcnemar": mc(b, c), "p_perm_by_person": perm(list(cl.values()))}
        out[f"{name}|{act}"] = {"rate": rate, "tests": tests}
        print(f"== {name} {act} n={len(ks)}", {a: (r["omit"], r["extra"], r["ok"]) for a, r in rate.items()})
        for t, v in tests.items(): print(f"   {t}: {v['a1_only']}:{v['a2_only']} McNemar {v['p_mcnemar']:.4f} 按人 {v['p_perm_by_person']:.4f}")
json.dump(out, open("DATA/paper/flux_stats.json", "w"), indent=1)
