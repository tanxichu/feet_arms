#!/usr/bin/env python3
"""PREREG 修订 40: FLUX.1-schnell(NF4 底座)上 底座 vs 各组。口径同 flux_stats.py(修订 25): 留出的人 6 噪声 / 训练的人大集 8 噪声, 抱书 a8 / 拿花 a9。
用法: python flux40_stats.py O1000 [F R ...]  (组名 = out40/ 下的目录名; 判定 json 拉回 20T flux40/)。输出 20T paper/flux40_stats.json。"""
import json, random, collections, sys, os
from math import comb
R = "DATA/flux40/"; ARMS = ["base"] + sys.argv[1:]
def omit(v): return int(not v.get("ok") and v.get("TOTAL") == 2)
def extra(v): return int(not v.get("ok") and (v.get("TOTAL") or 0) >= 3)
def L(arm, big): return {k.split("/", 1)[1]: v for k, v in json.load(open(f"{R}vl8b_{arm}{'_big' if big else ''}.json")).items()}
def mc(b, c): n = b + c; return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
def perm(d, it=20000):
    rng = random.Random(0); o = abs(sum(d)); return (sum(abs(sum(x if rng.random() < .5 else -x for x in d)) >= o - 1e-9 for _ in range(it)) + 1) / (it + 1)
out = {}
for big, name in ((True, "train"), (False, "hold"), (None, "all")):
    J = {a: ({**L(a, True), **{"h_" + k: v for k, v in L(a, False).items()}} if big is None else L(a, big)) for a in ARMS}
    for act in ("a8", "a9", "all"):
        ks = sorted(k for k in J["base"] if (act == "all" or f"_{act}_" in k) and all(k in J[a] for a in J))
        rate = {a: {"n": len(ks), "omit": sum(omit(J[a][k]) for k in ks), "extra": sum(extra(J[a][k]) for k in ks), "ok": sum(bool(J[a][k].get("ok")) for k in ks)} for a in J}
        tests = {}
        for a2 in ARMS[1:]:
            b = sum(omit(J["base"][k]) and not omit(J[a2][k]) for k in ks); c = sum(omit(J[a2][k]) and not omit(J["base"][k]) for k in ks)
            cl = collections.defaultdict(int)
            for k in ks: cl[k.replace("h_", "").split("_")[0]] += omit(J["base"][k]) - omit(J[a2][k])
            eb = sum(extra(J["base"][k]) and not extra(J[a2][k]) for k in ks); ec = sum(extra(J[a2][k]) and not extra(J["base"][k]) for k in ks)
            tr = sum(extra(J["base"][k]) and omit(J[a2][k]) for k in ks)
            tests[f"base_{a2}"] = {"omit_base_only": b, "omit_arm_only": c, "p_mcnemar": mc(b, c), "p_perm_by_person": perm(list(cl.values())),
                                   "extra_base_only": eb, "extra_arm_only": ec, "p_extra": mc(eb, ec), "base_extra_to_omit": tr}
        for a1, a2 in (("O3000", "F40"), ("O3000", "R40"), ("R40", "F40"), ("O1000", "O3000"), ("F40", "F2"), ("Fc", "F2"), ("O3000", "F2"), ("F40", "Fc")):   # P24b/c 同步数组间比较; 修订 43 P27a/b: F40/Fc vs F2
            if a1 not in J or a2 not in J: continue
            b = sum(omit(J[a1][k]) and not omit(J[a2][k]) for k in ks); c = sum(omit(J[a2][k]) and not omit(J[a1][k]) for k in ks)
            cl = collections.defaultdict(int)
            for k in ks: cl[k.replace("h_", "").split("_")[0]] += omit(J[a1][k]) - omit(J[a2][k])
            tests[f"{a1}_{a2}"] = {"omit_a1_only": b, "omit_a2_only": c, "p_mcnemar": mc(b, c), "p_perm_by_person": perm(list(cl.values()))}
        out[f"{name}|{act}"] = {"rate": rate, "tests": tests}
        print(f"== {name} {act} n={len(ks)}", {a: (r["omit"], r["extra"], r["ok"]) for a, r in rate.items()}, {t: (v["omit_base_only"], v["omit_arm_only"], round(v["p_perm_by_person"], 4), v["extra_base_only"], v["extra_arm_only"], v["base_extra_to_omit"]) if t.startswith("base_") else (v["omit_a1_only"], v["omit_a2_only"], round(v["p_perm_by_person"], 4)) for t, v in tests.items()})
json.dump(out, open("DATA/paper/flux40_stats.json", "w"), indent=1)
