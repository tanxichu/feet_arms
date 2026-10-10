#!/usr/bin/env python3
"""PREREG 修订 38(探索性): InternVL3.5-8B 当保守漏手计数器(人评集上漏手精度 1.00、召回 0.52)。
抱书大评测集 底座 + O/F/R × 种子 1~3; P22 三种子合并 InternVL 判的漏手 F < O(按人翻符号置换 p<0.05)。输出 20T paper/j3_stats.json。"""
import json, glob, random, collections
from math import comb
R = "DATA/"
def cls(v): T = v.get("TOTAL"); return "ok" if v.get("ok") else ("extra" if (T or 0) >= 3 else ("omit" if T == 2 else "other"))
P = {}
for f in glob.glob(R + "paper/j3/j3_ivl_[01].json"): P.update(json.load(open(f)))
P = {k: cls(v) for k, v in P.items()}
def mc(b, c): n = b + c; return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
def perm(d, it=20000):
    rng = random.Random(0); o = abs(sum(d)); return (sum(abs(sum(x if rng.random() < .5 else -x for x in d)) >= o - 1e-9 for _ in range(it)) + 1) / (it + 1)
A = {t: {k.split("/", 1)[1]: v for k, v in P.items() if k.startswith(t + "/")} for t in ("s1base", "s3base", "s1O", "s1F", "s1R", "s2O", "s2F", "s2R", "s3O", "s3F", "s3R")}
out = {"n_labels": len(P), "per_set": {t: len(v) for t, v in A.items()}, "omit": {t: sum(x == "omit" for x in v.values()) for t, v in A.items()}}
def test(a1, a2):
    b = c = 0; cl = collections.defaultdict(int)
    for s in (1, 2, 3):
        X, Y = A[f"s{s}{a1}"], A[f"s{s}{a2}"]
        for k in sorted(set(X) & set(Y)):
            x, y = X[k] == "omit", Y[k] == "omit"; b += x and not y; c += y and not x; cl[k.split("_")[0]] += x - y
    return {"a1_only": b, "a2_only": c, "p_mcnemar": mc(b, c), "p_perm": perm(list(cl.values()))}
out["tests"] = {f"{a}_{b}": test(a, b) for a, b in (("O", "F"), ("R", "F"), ("O", "R"))}
t = out["tests"]["O_F"]; out["P22"] = {"pass": t["a1_only"] > t["a2_only"] and t["p_perm"] < 0.05, **t}
out["pooled_omit"] = {a: sum(out["omit"][f"s{s}{a}"] for s in (1, 2, 3)) for a in ("O", "F", "R")}
json.dump(out, open(R + "paper/j3_stats.json", "w"), indent=1); print(json.dumps({k: out[k] for k in ("n_labels", "per_set", "pooled_omit", "P22")}), json.dumps(out["tests"]))
