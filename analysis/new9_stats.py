#!/usr/bin/env python3
"""PREREG 修订 33/34: 给四个新训练动作(A12~A15)补它们自己的漏手例子(v9f)后, F9 是否少漏手。
与修订 29 的底座 / O / F / R(种子 1)配对; 修订 34 另有 F9 种子 2 与 O 种子 2。
预测: P18a F9 < O(四动作合并, 按人翻符号置换 p<0.05); P18b F9 < R9(同上); P18c 推眼镜+水瓶(A12) F9 < O(McNemar p<0.05)。
两种子合并: 每人把两种子的差相加再按人置换。检验与 new4_stats.py 同口径(双侧)。输出 20T paper/new9_stats.json。"""
import json, random, collections
from math import comb
D4 = "DATA/new4/"; D9 = "DATA/new9/"
def cls(v): T = v.get("TOTAL"); return "ok" if v.get("ok") else ("extra" if (T or 0) >= 3 else ("omit" if T == 2 else "other"))
def load(p): return {k.split("/", 1)[1]: cls(v) for k, v in json.load(open(p)).items()}
J = {a: load(f"{D4}vl8b_{a}.json") for a in ("base", "O", "F", "R")}
J.update({a: load(f"{D9}vl8b_{a}.json") for a in ("F9", "R9", "F9s2", "Os2")})
import os
NEW36 = all(os.path.exists(f"{D9}vl8b_{a}.json") for a in ("F9s3", "Os3", "F9s4", "Os4"))   # 修订 36
if NEW36: J.update({a: load(f"{D9}vl8b_{a}.json") for a in ("F9s3", "Os3", "F9s4", "Os4")})
def mc(b, c): n = b + c; return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
def perm(d, it=20000):
    rng = random.Random(0); o = abs(sum(d)); return (sum(abs(sum(x if rng.random() < .5 else -x for x in d)) >= o - 1e-9 for _ in range(it)) + 1) / (it + 1)
def test(pairs, ks):
    """pairs = [(a1, a2), ...] 同一人可有多对(两种子), 差相加后按人置换; McNemar 把各对的不一致张数加总。"""
    b = c = 0; cl = collections.defaultdict(int)
    for a1, a2 in pairs:
        A, B = J[a1], J[a2]
        for k in ks:
            x, y = A[k] == "omit", B[k] == "omit"; b += x and not y; c += y and not x; cl[k.split("_")[0]] += x - y
    return {"a1_only": b, "a2_only": c, "p_mcnemar": mc(b, c), "p_perm": perm(list(cl.values()))}
out = {}
for act in ("12", "13", "14", "15", "all"):
    ks = sorted(k for k in J["base"] if (act == "all" or f"_a{act}_" in k) and all(k in J[a] for a in J))
    r = {"n": len(ks), "counts": {a: {c: sum(J[a][k] == c for k in ks) for c in ("omit", "extra", "ok")} for a in J}, "tests": {}}
    for a1, a2 in (("O", "F9"), ("R9", "F9"), ("base", "F9"), ("F", "F9"), ("O", "R9"), ("Os2", "F9s2"), ("O", "Os2"), ("F9", "F9s2")):
        r["tests"][a1 + "_" + a2] = test([(a1, a2)], ks)
    r["tests"]["O+Os2_F9+F9s2"] = test([("O", "F9"), ("Os2", "F9s2")], ks)
    if NEW36:
        r["tests"]["s34"] = test([("Os3", "F9s3"), ("Os4", "F9s4")], ks)
        r["tests"]["s1234"] = test([("O", "F9"), ("Os2", "F9s2"), ("Os3", "F9s3"), ("Os4", "F9s4")], ks)
    out[act] = r
a, t = out["all"]["tests"], out["12"]["tests"]
out["predictions"] = {"P18a_F9_lt_O": {"pass": a["O_F9"]["a1_only"] > a["O_F9"]["a2_only"] and a["O_F9"]["p_perm"] < 0.05, **a["O_F9"]},
                      "P18b_F9_lt_R9": {"pass": a["R9_F9"]["a1_only"] > a["R9_F9"]["a2_only"] and a["R9_F9"]["p_perm"] < 0.05, **a["R9_F9"]},
                      "P18c_A12_F9_lt_O": {"pass": t["O_F9"]["a1_only"] > t["O_F9"]["a2_only"] and t["O_F9"]["p_mcnemar"] < 0.05, **t["O_F9"]},
                      "two_seed_F9_lt_O": {"pass": a["O+Os2_F9+F9s2"]["a1_only"] > a["O+Os2_F9+F9s2"]["a2_only"] and a["O+Os2_F9+F9s2"]["p_perm"] < 0.05, **a["O+Os2_F9+F9s2"]}}
if NEW36:
    out["predictions"]["P20a_s34_F9_lt_O"] = {"pass": a["s34"]["a1_only"] > a["s34"]["a2_only"] and a["s34"]["p_perm"] < 0.05, **a["s34"]}
    out["predictions"]["P20b_s1234_F9_lt_O"] = {"pass": a["s1234"]["a1_only"] > a["s1234"]["a2_only"] and a["s1234"]["p_perm"] < 0.05, **a["s1234"]}
json.dump(out, open("DATA/paper/new9_stats.json", "w"), indent=1)
for k, v in out["predictions"].items(): print(k, v)
print({a: out["all"]["counts"][a] for a in J})
