#!/usr/bin/env python3
"""PREREG 修订 29: 四个新训练动作(A12~A15)上 O/F/R 与底座, 种子 1, 4×3090 同机出图。每动作与合并: 漏手/多手/画对计数,
配对精确 McNemar + 按人翻符号置换(2 万次)。输出 20T paper/new4_stats.json。"""
import json, random, collections
from math import comb
D = "DATA/new4/"
def cls(v): T = v.get("TOTAL"); return "ok" if v.get("ok") else ("extra" if (T or 0) >= 3 else ("omit" if T == 2 else "other"))
J = {a: {k.split("/", 1)[1]: cls(v) for k, v in json.load(open(f"{D}vl8b_{a}.json")).items()} for a in ("base", "O", "F", "R")}
def mc(b, c): n = b + c; return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
def perm(d, it=20000):
    rng = random.Random(0); o = abs(sum(d)); return (sum(abs(sum(x if rng.random() < .5 else -x for x in d)) >= o - 1e-9 for _ in range(it)) + 1) / (it + 1)
out = {}
for act in ("12", "13", "14", "15", "all"):
    ks = sorted(k for k in J["base"] if (act == "all" or f"_a{act}_" in k) and all(k in J[a] for a in J))
    r = {"n": len(ks), "counts": {a: {c: sum(J[a][k] == c for k in ks) for c in ("omit", "extra", "ok")} for a in J}, "tests": {}}
    for a1, a2 in (("base", "O"), ("O", "F"), ("R", "F"), ("O", "R")):
        A, B = J[a1], J[a2]; b = sum(A[k] == "omit" and B[k] != "omit" for k in ks); c = sum(B[k] == "omit" and A[k] != "omit" for k in ks)
        cl = collections.defaultdict(int)
        for k in ks: cl[k.split("_")[0]] += (A[k] == "omit") - (B[k] == "omit")
        r["tests"][a1 + a2] = {"a1_only": b, "a2_only": c, "p_mcnemar": mc(b, c), "p_perm": perm(list(cl.values()))}
    out[act] = r
json.dump(out, open("DATA/paper/new4_stats.json", "w"), indent=1); print("ok")
