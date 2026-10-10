#!/usr/bin/env python3
"""PREREG 修订 16: 两个新动作(A10 托下巴+拿杯 / A11 挠后脑+拿手机)。全部状态都在 108(同一张 3090)上用同一批条件与噪声出图,
所以底座只有一份、各组按 (人, 动作, 噪声) 配对。检验同修订 14: 每种子精确 McNemar + 按人聚类翻符号置换(20 万次) + 按人自助法 95% CI。
每个新动作分别报, 再合并; 训练的人 / 留出的人分开(留出 = klein_hold_judge 里出现过的人)。输出 20T paper/newact_stats.json。"""
import json, os, random, collections, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from math import comb
R = "DATA/"; N = R + "newact/"
HOLD = {k.split("/", 1)[1].split("_")[0] for k in json.load(open(R + "klein_hold_judge/vl8b_base.json"))}
def omit(v, mode):
    if v.get("ok"): return 0
    T = v.get("TOTAL")
    if T is None: return 0
    return int(T == 2) if mode == "strict" else int(T <= 2)
def extra(v): return int(not v.get("ok") and (v.get("TOTAL") or 0) >= 3)
def load(k):
    p = f"{N}vl8b_{k}.json"
    return {x.split("/", 1)[1]: v for x, v in json.load(open(p)).items()} if os.path.exists(p) else None
def mcnemar(b, c):
    n = b + c; return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
def perm(d, it=200000, seed=0):
    rng = random.Random(seed); obs = abs(sum(d)); return (sum(abs(sum(x if rng.random() < .5 else -x for x in d)) >= obs - 1e-9 for _ in range(it)) + 1) / (it + 1)
J = {k: load(k) for k in ["base"] + [f"{a}{s}" for a in ("O", "F", "R", "OP") for s in (1, 2, 3)]}
J = {k: v for k, v in J.items() if v and len(v) == 800}
print("可用状态:", sorted(J))
res = {"_states": sorted(J), "_hold_ids": len(HOLD)}
def sel(keys, act, grp):
    return [k for k in keys if (act == "all" or f"_a{act}_" in k) and (grp == "all" or (k.split("_")[0] in HOLD) == (grp == "hold"))]
# 每组的率
for act in ("10", "11", "all"):
    for grp in ("train", "hold", "all"):
        for k, d in J.items():
            ks = sel(d, act, grp); res[f"rate|{act}|{grp}|{k}"] = {"n": len(ks), "omit_strict": sum(omit(d[x], "strict") for x in ks), "omit_loose": sum(omit(d[x], "loose") for x in ks), "extra": sum(extra(d[x]) for x in ks), "ok": sum(bool(d[x].get("ok")) for x in ks)}
for act in ("10", "11", "all"):
    for grp in ("all", "train", "hold"):
        for mode in ("strict", "loose"):
            for a1, a2 in (("O", "F"), ("R", "F"), ("O", "R"), ("base", "O"), ("base", "F"), ("OP", "F"), ("base", "OP")):
                seeds = [s for s in (1, 2, 3) if (a1 == "base" or f"{a1}{s}" in J) and f"{a2}{s}" in J]
                if not seeds: continue
                per = []; clus = collections.defaultdict(int); npp = collections.defaultdict(int); tot = [0, 0, 0]
                for s in seeds:
                    A = J["base" if a1 == "base" else f"{a1}{s}"]; B = J[f"{a2}{s}"]; keys = sel(sorted(set(A) & set(B)), act, grp)
                    b = sum(1 for k in keys if omit(A[k], mode) and not omit(B[k], mode)); c = sum(1 for k in keys if not omit(A[k], mode) and omit(B[k], mode))
                    per.append({"seed": s, "n": len(keys), "a1_only": b, "a2_only": c, "p": mcnemar(b, c)})
                    for k in keys: i = k.split("_")[0]; clus[i] += omit(A[k], mode) - omit(B[k], mode); npp[i] += 1
                    tot[0] += sum(omit(A[k], mode) for k in keys); tot[1] += sum(omit(B[k], mode) for k in keys); tot[2] += len(keys)
                ids = list(clus); rng = random.Random(1); bs = sorted(100 * sum(clus[i] for i in p) / sum(npp[i] for i in p) for p in ([rng.choice(ids) for _ in ids] for _ in range(20000)))
                r = {"seeds": seeds, "per_seed": per, "pooled": {"a1": tot[0], "a2": tot[1], "n": tot[2], "clusters": len(ids), "p_perm_by_person": perm(list(clus.values())), "diff_pp": 100 * (tot[0] - tot[1]) / max(1, tot[2]), "ci95_pp_by_person": (bs[500], bs[19499])}}
                res[f"{act}|{grp}|{mode}|{a1}{a2}"] = r
                if mode == "strict": print(f"a{act:3s} {grp:5s} {a1:>4s}-{a2:<3s}", [(x["a1_only"], x["a2_only"], round(x["p"], 4)) for x in per], tot, "p_perm", round(r["pooled"]["p_perm_by_person"], 5), "CI", [round(x, 1) for x in r["pooled"]["ci95_pp_by_person"]], flush=True)
json.dump(res, open(R + "paper/newact_stats.json", "w"), indent=1)
for act in ("10", "11", "all"):
    print(f"\n== 动作 a{act} 全部人: 张数 / 漏手(strict) / 多手 / 画对")
    for k in sorted(J): x = res[f"rate|{act}|all|{k}"]; print(f"  {k:5s} n={x['n']} 漏 {x['omit_strict']} ({100*x['omit_strict']/x['n']:.1f}%) 多 {x['extra']} 对 {x['ok']}")
