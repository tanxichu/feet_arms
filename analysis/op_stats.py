#!/usr/bin/env python3
"""PREREG 修订 15: OP 组(v2 检测器 + 1.06·(−PickScore))三种子, 抱书 a8 大集(训练的人)。P8a OP 漏手 < O(合并三种子按人置换 p<0.05);
P8b OP 漏手不多于 F(差值 95% CI 上界 ≤ 3pp)。配对: 同 (人, 噪声) 题; 种子 1/2 的 OP/O/F 都在 108(3090) 上出图,
种子 3 的 O/F 在 A100 上、OP 在 108 上(B 内存不够, 10-04 挪 108), 跨卡配对照报(同噪声底座两卡判定一致 GpuAgree/GpuN)。输出 20T paper/op_stats.json。"""
import json, random, collections
from math import comb
R = "DATA/"
def cls_omit(v): return int(not v.get("ok") and v.get("TOTAL") == 2)
def cls_extra(v): return int(not v.get("ok") and (v.get("TOTAL") or 0) >= 3)
def load(p, pre=None):
    return {k.split("/", 1)[1]: v for k, v in json.load(open(R + p)).items() if "_a8_" in k and (pre is None or k.startswith(pre))}
G = {("O", 1): ("gen_v3/vl8b.json", "dd_v2/"), ("F", 1): ("gen_v3/vl8b_v5f.json", None), ("O", 2): ("seeds/vl8b_dd_O_s2.json", None), ("F", 2): ("seeds/vl8b_dd_F_s2.json", None),
     ("O", 3): ("seeds/vl8b_dd_O_s3_a100.json", None), ("F", 3): ("seeds/vl8b_dd_F_s3_a100.json", None),
     ("base", 1): ("gen_v3/vl8b.json", "base/"), ("base", 2): ("gen_v3/vl8b.json", "base/"), ("base", 3): ("seeds/vl8b_base_a100.json", None)}
for s in (1, 2, 3): G[("OP", s)] = (f"op_arm/vl8b_dd_OP_s{s}.json", None)
def mc(b, c):
    n = b + c; return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
def perm(d, it=200000):
    rng = random.Random(0); o = abs(sum(d)); return (sum(abs(sum(x if rng.random() < .5 else -x for x in d)) >= o - 1e-9 for _ in range(it)) + 1) / (it + 1)
out = {"rates": {}}
for a in ("base", "O", "F", "OP"):
    for s in (1, 2, 3):
        d = load(*G[(a, s)]); out["rates"][f"{a}{s}"] = {"n": len(d), "omit": sum(map(cls_omit, d.values())), "extra": sum(map(cls_extra, d.values())), "ok": sum(bool(v.get("ok")) for v in d.values())}
print(out["rates"])
for a1, a2 in (("O", "OP"), ("OP", "F"), ("base", "OP")):
    per = []; cl = collections.defaultdict(int); npp = collections.defaultdict(int); tot = [0, 0, 0]
    for s in (1, 2, 3):
        A, B = load(*G[(a1, s)]), load(*G[(a2, s)]); ks = sorted(set(A) & set(B))
        b = sum(cls_omit(A[k]) and not cls_omit(B[k]) for k in ks); c = sum(cls_omit(B[k]) and not cls_omit(A[k]) for k in ks)
        per.append({"seed": s, "n": len(ks), "a1_only": b, "a2_only": c, "p": mc(b, c)})
        for k in ks: i = k.split("_")[0]; cl[i] += cls_omit(A[k]) - cls_omit(B[k]); npp[i] += 1
        tot[0] += sum(cls_omit(A[k]) for k in ks); tot[1] += sum(cls_omit(B[k]) for k in ks); tot[2] += len(ks)
    ids = list(cl); rng = random.Random(1); bs = sorted(100 * sum(cl[i] for i in p) / sum(npp[i] for i in p) for p in ([rng.choice(ids) for _ in ids] for _ in range(20000)))
    r = {"per_seed": per, "pooled": {"a1": tot[0], "a2": tot[1], "n": tot[2], "p_perm_by_person": perm(list(cl.values())), "diff_pp": 100 * (tot[0] - tot[1]) / tot[2], "ci95_pp_by_person": (bs[500], bs[19499])}}
    out[f"{a1}{a2}"] = r
    print(a1, a2, [(x["a1_only"], x["a2_only"], round(x["p"], 4)) for x in per], tot, "p_perm", round(r["pooled"]["p_perm_by_person"], 5), "CI", [round(x, 1) for x in r["pooled"]["ci95_pp_by_person"]])
json.dump(out, open(R + "paper/op_stats.json", "w"), indent=1)
