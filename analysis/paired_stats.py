#!/usr/bin/env python3
"""配对检验(回应 10-03 两份审稿意见): 各组共用 (人, 动作, 采样噪声), 三个训练种子又共用同一批评估题,
所以不能把合并计数当独立样本做 Fisher。这里做两种:
 ① 每个种子内 O vs F(或其它两组)按同一张题配对, 精确 McNemar(只看不一致对, 二项检验);
 ② 三个种子合并: 以「人」为聚类单位, 每个人的 (O 遗漏数 − F 遗漏数) 求和, 随机翻符号置换检验(20 万次),
    这样同一个人的多个噪声、三个种子的重复都留在一个聚类里。
两种口径: strict = 预注册的「一共两只手且有一件事没人做」; loose = 式(2) 的 h≤K(含只画出一只手)。
输出 paired_stats.json, paper_numbers.py 读它生成宏。"""
import json, random, collections
from math import comb
R = "DATA/"
def omit(v, mode):
    if v.get("ok"): return 0
    T = v.get("TOTAL")
    if T is None: return 0
    return int(T == 2) if mode == "strict" else int(T <= 2)
def load(p, pre=None, act="a8"):
    d = json.load(open(R + p)); out = {}
    for k, v in d.items():
        if f"_{act}_" not in k or (pre and not k.startswith(pre)): continue
        out[k.split("/", 1)[1]] = v
    return out
def mcnemar(b, c):   # 精确双侧
    n = b + c
    if n == 0: return 1.0
    k = min(b, c); return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)
def perm(diffs, it=200000, seed=0):
    rng = random.Random(seed); obs = abs(sum(diffs)); hit = 0
    for _ in range(it):
        if abs(sum(d if rng.random() < 0.5 else -d for d in diffs)) >= obs - 1e-9: hit += 1
    return (hit + 1) / (it + 1)
K = {("base", 1): ("gen_v3/vl8b.json", "base/"), ("O", 1): ("gen_v3/vl8b.json", "dd_v2/"), ("F", 1): ("gen_v3/vl8b_v5f.json", None), ("R", 1): ("gen_v3/vl8b_v5r.json", None),
     ("O", 2): ("seeds/vl8b_dd_O_s2.json", None), ("F", 2): ("seeds/vl8b_dd_F_s2.json", None), ("R", 2): ("seeds/vl8b_dd_R_s2.json", None),
     ("O", 3): ("seeds/vl8b_dd_O_s3_a100.json", None), ("F", 3): ("seeds/vl8b_dd_F_s3_a100.json", None), ("R", 3): ("seeds/vl8b_dd_R_s3_a100.json", None)}
S = {("base", 1): "base", ("O", 1): "O", ("F", 1): "F2", ("R", 1): "R2", ("O", 2): "O_s2", ("F", 2): "F2_s2", ("R", 2): "R2_s2", ("O", 3): "O_s3", ("F", 3): "F2_s3", ("R", 3): "R2_s3"}
def getter(model, act):
    if model == "klein": return lambda a, s: load(*K[(a, s)] if a != "base" else (("seeds/vl8b_base_a100.json", None) if s == 3 else K[("base", 1)]), act=act)   # 种子 3 在 A100 上出图, 底座也用 A100 上同噪声出的那份
    return lambda a, s: load(f"sana_paper/vl8b_{S[(a if a != 'base' else 'base', s if a != 'base' else 1)]}.json", act=act)
res = {}
for model, act in (("klein", "a8"), ("sana", "a9")):
    g = getter(model, act)
    for mode in ("strict", "loose"):
        for a1, a2 in (("O", "F"), ("R", "F"), ("O", "R"), ("base", "O"), ("base", "F")):
            per = []; clus = collections.defaultdict(int); tot = [0, 0, 0]
            for s in (1, 2, 3):
                A, B = g(a1, s), g(a2, s); keys = sorted(set(A) & set(B))
                b = sum(1 for k in keys if omit(A[k], mode) and not omit(B[k], mode)); c = sum(1 for k in keys if not omit(A[k], mode) and omit(B[k], mode))
                per.append({"seed": s, "n": len(keys), "a1_only": b, "a2_only": c, "p": mcnemar(b, c)})
                for k in keys: clus[k.split("_")[0]] += omit(A[k], mode) - omit(B[k], mode)
                tot[0] += sum(omit(A[k], mode) for k in keys); tot[1] += sum(omit(B[k], mode) for k in keys); tot[2] += len(keys)
            # 差值(百分点)的 95% 置信区间: 按人自助法(每人的 遗漏差 与 张数 一起抽), 2 万次
            npp = collections.defaultdict(int)
            for s in (1, 2, 3):
                A, B = g(a1, s), g(a2, s)
                for k in set(A) & set(B): npp[k.split("_")[0]] += 1
            ids = list(clus); rng = random.Random(1); bs = []
            for _ in range(20000):
                pick = [rng.choice(ids) for _ in ids]; bs.append(100 * sum(clus[i] for i in pick) / sum(npp[i] for i in pick))
            bs.sort(); ci = (bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1])
            res[f"{model}_{mode}_{a1}{a2}"] = {"per_seed": per, "pooled": {"a1": tot[0], "a2": tot[1], "n": tot[2], "clusters": len(clus), "p_perm_by_person": perm(list(clus.values())), "diff_pp": 100 * (tot[0] - tot[1]) / tot[2], "ci95_pp_by_person": ci}}
            print(model, mode, a1, a2, [(x["a1_only"], x["a2_only"], round(x["p"], 4)) for x in per], tot, len(clus), round(res[f"{model}_{mode}_{a1}{a2}"]["pooled"]["p_perm_by_person"], 5), [round(x, 2) for x in res[f"{model}_{mode}_{a1}{a2}"]["pooled"]["ci95_pp_by_person"]], flush=True)
# 留出的人(训练与检测器都没见过), 三个训练种子各 84 张抱书; 底座只有一份
HJ = R + "klein_hold_judge/"
HF = {("base", s): ("vl8b_base_a100" if s == 3 else "vl8b_base") for s in (1, 2, 3)}   # 种子 3 的底座 = A100 上出的
HF.update({("O", 1): "vl8b_limbs_dd_v2_s2000", ("F", 1): "vl8b_limbs_dd_v5f_s2000", ("R", 1): "vl8b_limbs_dd_v5r_s2000"})
for a in "OFR":
    for s in (2, 3): HF[(a, s)] = f"vl8b_limbs_dd_{a}_s{s}_s2000"
def hload(a, s):
    d = json.load(open(HJ + HF[(a, s)] + ".json")); return {k.split("/", 1)[1]: v for k, v in d.items() if "_a8_" in k}
for mode in ("strict", "loose"):
    for a1, a2 in (("O", "F"), ("R", "F"), ("O", "R"), ("base", "O"), ("base", "F")):
        per = []; clus = collections.defaultdict(int); npp = collections.defaultdict(int); tot = [0, 0, 0]
        for s in (1, 2, 3):
            A, B = hload(a1, s), hload(a2, s); keys = sorted(set(A) & set(B))
            b = sum(1 for k in keys if omit(A[k], mode) and not omit(B[k], mode)); c = sum(1 for k in keys if not omit(A[k], mode) and omit(B[k], mode))
            per.append({"seed": s, "n": len(keys), "a1_only": b, "a2_only": c, "p": mcnemar(b, c)})
            for k in keys: clus[k.split("_")[0]] += omit(A[k], mode) - omit(B[k], mode); npp[k.split("_")[0]] += 1
            tot[0] += sum(omit(A[k], mode) for k in keys); tot[1] += sum(omit(B[k], mode) for k in keys); tot[2] += len(keys)
        ids = list(clus); rng = random.Random(1); bs = []
        for _ in range(20000):
            pick = [rng.choice(ids) for _ in ids]; bs.append(100 * sum(clus[i] for i in pick) / sum(npp[i] for i in pick))
        bs.sort()
        res[f"hold_{mode}_{a1}{a2}"] = {"per_seed": per, "pooled": {"a1": tot[0], "a2": tot[1], "n": tot[2], "clusters": len(ids), "p_perm_by_person": perm(list(clus.values())), "diff_pp": 100 * (tot[0] - tot[1]) / tot[2], "ci95_pp_by_person": (bs[500], bs[19499])}}
        print("hold", mode, a1, a2, [(x["a1_only"], x["a2_only"], round(x["p"], 3)) for x in per], tot, len(ids), round(res[f"hold_{mode}_{a1}{a2}"]["pooled"]["p_perm_by_person"], 5), [round(x, 1) for x in res[f"hold_{mode}_{a1}{a2}"]["pooled"]["ci95_pp_by_person"]], flush=True)
json.dump(res, open(R + "paper/paired_stats.json", "w"), indent=1)
